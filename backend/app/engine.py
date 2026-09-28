import random, re
import unicodedata
from datetime import datetime, timedelta, timezone
from collections import Counter
from sqlalchemy import select, update
from fastapi import HTTPException
from .db import *
from .schemas import STRUCTURED_EXPLANATION_FIELDS


def quotas(mix, n):
    total = sum(mix.values())
    raw = {k: v * n / total for k, v in mix.items()}
    result = {k: int(v) for k, v in raw.items()}
    for k in sorted(raw, key=lambda k: raw[k] - result[k], reverse=True)[
        : n - sum(result.values())
    ]:
        result[k] += 1
    return result


def exam_eligible(q, by_id, reviewed_ids):
    if (
        q.status != "ACTIVE"
        or q.id.startswith("seed-")
        or (q.generation_metadata or {}).get("seed")
    ):
        return False
    if (q.generation_metadata or {}).get("duplicate_review", {}).get(
        "status"
    ) == "PENDING":
        return False
    if q.source_type == "PYQ":
        return bool(
            q.verification_status == "VERIFIED_PYQ"
            and q.source_reference
            and q.exam_year
            and q.id in reviewed_ids
            and (q.generation_metadata or {}).get("syllabus_units")
        )
    parent = by_id.get(q.parent_question_id)
    return bool(
        q.source_type == "PYQ_PATTERN"
        and q.verification_status == "REVIEWED"
        and q.id in reviewed_ids
        and (q.generation_metadata or {}).get("variant_kind") in {"MATCHED", "HARDER"}
        and (q.generation_metadata or {}).get("alignment_check", {}).get("aligned")
        is True
        and parent
        and set((q.generation_metadata or {}).get("syllabus_units", []))
        & set((parent.generation_metadata or {}).get("syllabus_units", []))
        and parent.source_type == "PYQ"
        and exam_eligible(parent, by_id, reviewed_ids)
    )


def question_family(text):
    # Conservative duplicate protection includes trivial numerical substitutions.
    return re.sub(
        r"[^a-z0-9]+",
        " ",
        re.sub(
            r"\d+(?:[.,]\d+)*",
            " number ",
            unicodedata.normalize("NFKC", text).casefold(),
        ),
    ).strip()


def strict_pool(session, user_id, pool, supplementary=False):
    reviewed = set(
        session.scalars(
            select(Review.question_id).where(
                Review.decision == "ACTIVE", Review.notes != ""
            )
        )
    )
    by_id = {q.id: q for q in pool}
    past = list(
        session.scalars(
            select(TestQuestion)
            .join(Attempt, TestQuestion.attempt_id == Attempt.id)
            .where(Attempt.user_id == user_id)
        )
    )
    used_ids = {q.question_id for q in past}
    used_families = {question_family(q.snapshot["question_text"]) for q in past}
    result = []
    for q in sorted(pool, key=lambda q: (q.source_type != "PYQ", q.id)):
        family = question_family(q.question_text)
        if (
            (
                exam_eligible(q, by_id, reviewed)
                or (
                    supplementary
                    and q.source_type == "SUPPLEMENTARY"
                    and q.status == "ACTIVE"
                    and (q.generation_metadata or {})
                    .get("duplicate_review", {})
                    .get("status")
                    != "PENDING"
                )
            )
            and q.id not in used_ids
            and family not in used_families
        ):
            result.append(q)
            used_families.add(family)
    return result


def choose_questions(session, user_id, config, weak_topics=None):
    pool = list(session.scalars(select(Question).where(Question.status == "ACTIVE")))
    if config.id in {"exam-prep", "hard-patterns", "supplementary"}:
        pool = strict_pool(
            session, user_id, pool, supplementary=config.id == "supplementary"
        )
    if weak_topics:
        pool = [q for q in pool if q.topic in weak_topics]
    distribution = (
        config.distribution
        if not weak_topics
        else dict(Counter(q.subject for q in pool))
    )
    if weak_topics:
        if len(pool) < 5:
            raise HTTPException(
                409, "At least 5 active questions are needed for your weak topics"
            )
        distribution = quotas(distribution, min(20, len(pool)))
    n = sum(distribution.values())
    sources = quotas(config.source_mix, n)
    difficulties = quotas(config.difficulty_mix, n)
    cutoff = (
        datetime.now(timezone.utc) - timedelta(days=config.cooldown_days)
    ).isoformat()
    recent = set(
        session.scalars(
            select(TestQuestion.question_id)
            .join(Attempt, TestQuestion.attempt_id == Attempt.id)
            .where(Attempt.user_id == user_id, Attempt.started_at >= cutoff)
        )
    )
    # Exact subject/source/difficulty quotas are solved as a capacitated flow.
    # Fail clearly when unavailable; never silently substitute a source type.
    from .flow import solve

    try:
        chosen = solve(pool, distribution, sources, difficulties, recent)
    except HTTPException as exc:
        if config.id in {"exam-prep", "hard-patterns", "supplementary"}:
            raise HTTPException(
                409,
                "Exam preparation needs more unseen, source-reviewed questions for this mix. Starter questions and previously reserved questions are excluded; nothing will be recycled. "
                + str(exc.detail),
            )
        raise
    random.SystemRandom().shuffle(chosen)
    return chosen


def choose_custom_practice(
    session, user_id, subject=None, topics=None, difficulty=None, source_type=None, count=10
):
    # Ad-hoc single-combination practice (Subject/Topic/Difficulty/Count), for
    # Practice Mode's quick filters. Deliberately independent of the quota
    # flow-solver in flow.py: there is only one bucket to fill here, so no
    # capacitated search is needed. Mirrors solve()'s own preference order
    # (unseen concepts first, then not-recently-attempted) rather than
    # inventing a new rule.
    pool = list(session.scalars(select(Question).where(Question.status == "ACTIVE")))
    if subject:
        pool = [q for q in pool if q.subject == subject]
    if topics:
        pool = [q for q in pool if q.topic in topics]
    if difficulty:
        pool = [q for q in pool if q.difficulty == difficulty]
    if source_type and source_type != "MIXED":
        pool = [q for q in pool if q.source_type == source_type]
    if len(pool) < count:
        raise HTTPException(
            409,
            f"Only {len(pool)} active questions match this filter — lower the "
            "question count or widen the subject/topic/difficulty filters.",
        )
    seen = set(
        session.scalars(
            select(TestQuestion.question_id)
            .join(Attempt, TestQuestion.attempt_id == Attempt.id)
            .where(Attempt.user_id == user_id)
        )
    )
    rng = random.SystemRandom()
    rng.shuffle(pool)
    remaining = pool[:]
    concepts = Counter()
    chosen = []
    for _ in range(count):
        q = min(
            remaining,
            key=lambda q: (q.id in seen, concepts[(q.topic, q.subtopic)]),
        )
        chosen.append(q)
        concepts[(q.topic, q.subtopic)] += 1
        remaining.remove(q)
    rng.shuffle(chosen)
    return chosen


def get_attempt(session, id, user_id):
    a = session.get(Attempt, id)
    if not a or a.user_id != user_id:
        raise HTTPException(404, "Attempt not found")
    return a


def lock_attempt(session, a):
    version = a.version
    r = session.execute(
        update(Attempt)
        .where(Attempt.id == a.id, Attempt.version == version)
        .values(version=version + 1)
    )
    if r.rowcount != 1:
        raise HTTPException(409, "Attempt changed in another tab. Reload and retry.")
    session.flush()


def finish(session, a):
    if a.status == "SUBMITTED":
        return a.result
    snapshots = list(
        session.scalars(
            select(TestQuestion)
            .where(TestQuestion.attempt_id == a.id)
            .order_by(TestQuestion.position)
        )
    )
    answers = {
        r.question_id: r
        for r in session.scalars(select(Answer).where(Answer.attempt_id == a.id))
    }
    correct = wrong = 0
    subjects = {}
    topics = {}
    review = []
    for tq in snapshots:
        q = tq.snapshot
        ans = answers.get(tq.question_id)
        selected = ans.selected if ans else None
        ok = selected == q["correct_option"]
        correct += bool(selected and ok)
        wrong += bool(selected and not ok)
        for group, key in [(subjects, q["subject"]), (topics, q["topic"])]:
            s = group.setdefault(
                key, {"total": 0, "attempted": 0, "correct": 0, "wrong": 0}
            )
            s["total"] += 1
            s["attempted"] += bool(selected)
            s["correct"] += bool(selected and ok)
            s["wrong"] += bool(selected and not ok)
        review.append(
            {
                **q,
                "selected": selected,
                "is_correct": ok,
                "marked": ans.marked if ans else False,
            }
        )
    n = len(snapshots)
    attempted = correct + wrong
    score = correct * a.policy["correct_marks"] - wrong * a.policy["wrong_penalty"]
    for g in [subjects, topics]:
        for s in g.values():
            s["accuracy"] = (
                round(100 * s["correct"] / s["attempted"], 1) if s["attempted"] else 0
            )
    elapsed = (
        datetime.now(timezone.utc) - datetime.fromisoformat(a.started_at)
    ).total_seconds()
    a.status = "SUBMITTED"
    a.submitted_at = now()
    a.result = {
        "total": n,
        "max_score": n * a.policy["correct_marks"],
        "attempted": attempted,
        "correct": correct,
        "wrong": wrong,
        "unanswered": n - attempted,
        "score": round(score, 2),
        "accuracy": round(100 * correct / attempted, 1) if attempted else 0,
        "percentage": round(score / (n * a.policy["correct_marks"]) * 100, 1),
        "time_used_seconds": int(min(elapsed, a.policy["duration_seconds"])),
        "subjects": subjects,
        "topics": topics,
        "review": review,
        "mode": a.mode,
    }
    session.flush()
    return a.result


def attempt_payload(session, a):
    if a.status == "IN_PROGRESS" and datetime.now(
        timezone.utc
    ) >= datetime.fromisoformat(a.deadline):
        lock_attempt(session, a)
        finish(session, a)
    answers = {
        x.question_id: asdict(x)
        for x in session.scalars(select(Answer).where(Answer.attempt_id == a.id))
    }
    questions = []
    for tq in session.scalars(
        select(TestQuestion)
        .where(TestQuestion.attempt_id == a.id)
        .order_by(TestQuestion.position)
    ):
        q = dict(tq.snapshot)
        if a.status != "SUBMITTED":
            q.pop("correct_option", None)
            q.pop("explanation", None)
            q.pop("generation_metadata", None)
            for k in STRUCTURED_EXPLANATION_FIELDS:
                q.pop(k, None)
        questions.append(q)
    return {
        **asdict(a),
        "questions": questions,
        "answers": answers,
        "server_time": now(),
    }


def analytics(session, user_id):
    rows = list(
        session.scalars(
            select(Attempt)
            .where(Attempt.user_id == user_id, Attempt.status == "SUBMITTED")
            .order_by(Attempt.started_at.desc())
        )
    )
    topics = {}
    subjects = {}
    for a in rows:
        # Practice with revealed answers is tracked separately and excluded from exam-readiness analytics.
        if a.mode != "EXAM" or not a.policy.get("exam_preparation"):
            continue
        for group, key in [(topics, "topics"), (subjects, "subjects")]:
            for name, s in a.result[key].items():
                t = group.setdefault(
                    name, {"total": 0, "correct": 0, "attempted": 0, "tests": 0}
                )
                for k in ["total", "correct", "attempted"]:
                    t[k] += s[k]
                t["tests"] += 1
    for group in [topics, subjects]:
        for t in group.values():
            t["accuracy"] = (
                round(t["correct"] / t["attempted"] * 100, 1) if t["attempted"] else 0
            )
    weak = [
        k
        for k, v in topics.items()
        if v["attempted"] >= 5 and v["tests"] >= 2 and v["accuracy"] < 60
    ]
    return {
        "topics": topics,
        "subjects": subjects,
        "weak_topics": weak,
        "completed": len(rows),
        "exam_completed": sum(
            a.mode == "EXAM" and bool(a.policy.get("exam_preparation")) for a in rows
        ),
        "history": [
            {
                "id": a.id,
                "name": a.name,
                "mode": a.mode,
                "exam_preparation": bool(a.policy.get("exam_preparation")),
                "started_at": a.started_at,
                **{
                    k: v
                    for k, v in a.result.items()
                    if k not in ["review", "subjects", "topics"]
                },
            }
            for a in rows
        ],
    }
