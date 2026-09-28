"""Official syllabus registry, idempotent content additions and coverage audit.
No destructive migrations; source copies are linked, never authenticated by inference.
"""

import json
from pathlib import Path
from collections import Counter
from difflib import SequenceMatcher
from sqlalchemy import select
from .db import Question, Config, Topic, TestQuestion, Attempt
from .quality import normalized, validate_question

ROOT = Path(__file__).resolve().parents[2]
CATALOG = json.loads((ROOT / "frontend/src/preparation.json").read_text())
CONTENT = json.loads((ROOT / "backend/data/preparation_questions.json").read_text(encoding="utf-8"))
STRICT_CONFIGS = {"exam-prep", "hard-patterns", "supplementary"}


def possible_duplicate(a, b):
    from .engine import question_family

    if normalized(a) == normalized(b):
        return "EXACT"
    if question_family(a) == question_family(b):
        return "NUMERICAL_VARIANT"
    na, nb = normalized(a), normalized(b)
    sa, sb = set(na.split()), set(nb.split())
    overlap = len(sa & sb) / max(1, len(sa | sb))
    if SequenceMatcher(None, na, nb).ratio() >= 0.76 or overlap >= 0.62:
        return "POSSIBLE_PARAPHRASE"
    return None


def seed_preparation(s):
    for id, name, dist, source, difficulty in [
        (
            "hard-patterns",
            "Hard patterns · 10 questions · provisional difficulty",
            {
                "Science & Engineering": 4,
                "Mathematics": 3,
                "Computers": 2,
                "Reasoning": 1,
            },
            {"PYQ_PATTERN": 100},
            {"Hard": 100},
        ),
        (
            "supplementary",
            "Supplementary example · NOT a verified PYQ",
            {"Computers": 1},
            {"SUPPLEMENTARY": 100},
            {"Medium": 100},
        ),
    ]:
        if not s.get(Config, id):
            s.add(
                Config(
                    id=id,
                    name=name,
                    distribution=dist,
                    duration_minutes=15 if id == "hard-patterns" else 3,
                    source_mix=source,
                    difficulty_mix=difficulty,
                    cooldown_days=365,
                )
            )
    for row in CONTENT:
        existing = s.get(Question, row["id"])
        if existing:
            if (
                existing.generation_method == "syllabus-authored-v1"
                and existing.question_text == row["question_text"]
                and existing.source_type == "PYQ_PATTERN"
            ):
                existing.source_type = "ORIGINAL"
                existing.generation_metadata = {
                    **existing.generation_metadata,
                    "source_status": "ORIGINAL_CHALLENGE",
                    "bank_track": "ORIGINAL_CHALLENGE",
                }
            continue
        data = dict(row)
        metadata = dict(data["generation_metadata"])
        for old in s.scalars(select(Question)):
            flag = possible_duplicate(data["question_text"], old.question_text)
            if flag in {"EXACT", "NUMERICAL_VARIANT"}:
                data["status"] = "ARCHIVED"
                metadata["duplicate_review"] = {
                    "status": "DUPLICATE",
                    "kind": flag,
                    "against": old.id,
                }
                break
            if flag:
                metadata["duplicate_review"] = {
                    "status": "PENDING",
                    "kind": flag,
                    "against": old.id,
                }
        data["generation_metadata"] = metadata
        if data["generation_method"] == "syllabus-authored-v1":
            check = validate_question(data, verification=metadata.get("numeric_check"))
            if check["issues"]:
                raise ValueError(
                    f"Invalid preparation content {row['id']}: {check['issues']}"
                )
        topic = s.scalar(
            select(Topic).where(
                Topic.subject == row["subject"], Topic.name == row["topic"]
            )
        )
        if not topic:
            topic = Topic(subject=row["subject"], name=row["topic"])
            s.add(topic)
            s.flush()
        s.add(Question(**data, topic_id=topic.id))
        s.flush()


def coverage(s, user_id):
    from .engine import strict_pool, exam_eligible

    rows = list(s.scalars(select(Question)))
    available = {
        q.id
        for q in strict_pool(
            s, user_id, [q for q in rows if q.status == "ACTIVE"], supplementary=True
        )
    }
    from .db import Review

    reviewed = set(
        s.scalars(
            select(Review.question_id).where(
                Review.decision == "ACTIVE", Review.notes != ""
            )
        )
    )
    by_id = {q.id: q for q in rows}
    units = []
    for unit in CATALOG["units"]:
        matching = [
            q
            for q in rows
            if unit["id"] in (q.generation_metadata or {}).get("syllabus_units", [])
        ]
        active = [
            q
            for q in matching
            if q.status == "ACTIVE"
            and (q.generation_metadata or {}).get("duplicate_review", {}).get("status")
            != "PENDING"
        ]
        verified = sum(
            q.source_type == "PYQ" and exam_eligible(q, by_id, reviewed) for q in active
        )
        patterns = sum(
            q.source_type == "PYQ_PATTERN" and exam_eligible(q, by_id, reviewed)
            for q in active
        )
        supplementary = sum(q.source_type == "SUPPLEMENTARY" for q in active)
        total = verified + patterns
        units.append(
            {
                **unit,
                "verified": verified,
                "patterns": patterns,
                "supplementary": supplementary,
                "unused": sum(q.id in available for q in active),
                "status": (
                    "MISSING"
                    if total == 0
                    else "UNDERREPRESENTED" if total < 5 else "STOCK_TARGET_MET"
                ),
            }
        )
    flags = [
        {
            "id": q.id,
            "text": q.question_text,
            "source": q.source_type,
            **q.generation_metadata["duplicate_review"],
        }
        for q in rows
        if (q.generation_metadata or {}).get("duplicate_review", {}).get("status")
        == "PENDING"
    ]
    return {
        "authority": CATALOG["authority"],
        "scope_note": CATALOG["scope_note"],
        "pattern": CATALOG["pattern"],
        "sources": CATALOG["sources"],
        "units": units,
        "duplicate_flags": flags,
        "key_conflicts": [
            {
                "id": q.id,
                "text": q.question_text,
                "note": q.generation_metadata.get(
                    "key_review_note", "Conflicting answer evidence"
                ),
            }
            for q in rows
            if q.verification_status == "KEY_CONFLICT"
        ],
        "summary": {
            "basic": sum(q.id.startswith("seed-") for q in rows),
            "verified": sum(
                q.source_type == "PYQ"
                and q.verification_status == "VERIFIED_PYQ"
                and q.status == "ACTIVE"
                for q in rows
            ),
            "patterns": sum(
                q.source_type == "PYQ_PATTERN" and exam_eligible(q, by_id, reviewed)
                for q in rows
            ),
            "original_challenges": sum(
                q.generation_method == "syllabus-authored-v1" for q in rows
            ),
            "supplementary": sum(
                q.source_type == "SUPPLEMENTARY" and q.status == "ACTIVE" for q in rows
            ),
            "external_indexed": len(CATALOG["external_records"]),
            "missing_units": sum(u["status"] == "MISSING" for u in units),
            "underrepresented_units": sum(
                u["status"] == "UNDERREPRESENTED" for u in units
            ),
        },
    }


def duplicate_metadata(s, text, exclude=None):
    for other in s.scalars(select(Question)):
        if other.id == exclude:
            continue
        flag = possible_duplicate(text, other.question_text)
        if flag:
            return {"status": "PENDING", "kind": flag, "against": other.id}
    return None
