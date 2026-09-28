import os, csv, io, json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func
from sqlalchemy.orm import Session as DBSession
from pydantic import ValidationError
from .db import *
from .schemas import *
from .auth import user, admin, MODE, SUPABASE, ANON
from .quality import validate_question, detect_duplicate
from .engine import *
from .ai import agent


@asynccontextmanager
async def lifespan(app):
    if MODE == "development":
        Base.metadata.create_all(engine)
        from .seed import seed

        with Session() as s:
            seed(s)
            s.commit()
    yield


app = FastAPI(title="SignalPrep API", version="1.0.0", lifespan=lifespan)
origins = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:4173"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "environment": MODE,
        "ai_enabled": agent.enabled,
        "supabase_url": SUPABASE,
        "supabase_anon_key": ANON if SUPABASE else "",
        "development_auth": MODE == "development"
        and os.getenv("DEV_AUTH", "true").lower() == "true",
    }


@app.get("/api/me")
def me(p=Depends(user)):
    return asdict(p)


@app.put("/api/me")
def profile(data: dict, p=Depends(user), s: DBSession = Depends(db)):
    name = str(data.get("name", "")).strip()
    if not 1 <= len(name) <= 100:
        raise HTTPException(422, "Name must be 1–100 characters")
    p.name = name
    return asdict(p)


@app.get("/api/stats")
def stats(p=Depends(user), s: DBSession = Depends(db)):
    rows = list(s.scalars(select(Question)))
    if p.role != "admin":
        rows = [q for q in rows if q.status == "ACTIVE"]
    return {
        "total": len(rows),
        "sources": dict(Counter(q.source_type for q in rows)),
        "statuses": dict(Counter(q.status for q in rows)),
        "subjects": dict(Counter(q.subject for q in rows)),
        "topics": len(set(q.topic for q in rows)),
    }


@app.get("/api/questions")
def questions(
    search: str = "",
    subject: str = "",
    topic: str = "",
    difficulty: str = "",
    source_type: str = "",
    status: str = "",
    year: int | None = None,
    bookmarked: bool = False,
    page: int = Query(1, ge=1),
    p=Depends(user),
    s: DBSession = Depends(db),
):
    stmt = select(Question)
    if p.role != "admin":
        stmt = stmt.where(Question.status == "ACTIVE")
    for key, value in [
        ("subject", subject),
        ("topic", topic),
        ("difficulty", difficulty),
        ("source_type", source_type),
        ("status", status),
        ("exam_year", year),
    ]:
        if value:
            stmt = stmt.where(getattr(Question, key) == value)
    if search:
        stmt = stmt.where(Question.question_text.ilike("%" + search[:200] + "%"))
    if bookmarked:
        stmt = stmt.join(Bookmark, Bookmark.question_id == Question.id).where(
            Bookmark.user_id == p.id
        )
    count = s.scalar(select(func.count()).select_from(stmt.subquery()))
    data = [
        asdict(q)
        for q in s.scalars(
            stmt.order_by(Question.created_at.desc()).offset((page - 1) * 25).limit(25)
        )
    ]
    marks = set(s.scalars(select(Bookmark.question_id).where(Bookmark.user_id == p.id)))
    for q in data:
        q["bookmarked"] = q["id"] in marks
        if p.role != "admin":
            for k in [
                "correct_option",
                "explanation",
                "generation_metadata",
                *STRUCTURED_EXPLANATION_FIELDS,
            ]:
                q.pop(k, None)
    return {
        "items": data,
        "total": count,
        "page": page,
        "pages": max(1, (count + 24) // 25),
    }


def insert_question(data, s, method="manual", metadata=None):
    data = dict(data)
    metadata = dict(metadata or {})
    from .preparation import duplicate_metadata

    duplicate_flag = duplicate_metadata(s, data["question_text"])
    if duplicate_flag:
        metadata["duplicate_review"] = duplicate_flag
    if data["source_type"] == "PYQ":
        metadata["claimed_source_type"] = "PYQ"
        data["source_type"] = "PYQ_PATTERN"
    q = Question(**data, generation_method=method, generation_metadata=metadata)
    topic = s.scalar(
        select(Topic).where(Topic.subject == q.subject, Topic.name == q.topic)
    )
    if not topic:
        topic = Topic(subject=q.subject, name=q.topic)
        s.add(topic)
        s.flush()
    q.topic_id = topic.id
    if q.source_reference:
        source = Source(reference=q.source_reference)
        s.add(source)
        s.flush()
        q.source_id = source.id
    if q.parent_question_id and not s.get(Question, q.parent_question_id):
        raise HTTPException(422, "Parent question not found")
    s.add(q)
    s.flush()
    return q


@app.post("/api/questions")
def create_question(data: QuestionInput, p=Depends(admin), s: DBSession = Depends(db)):
    quality = validate_question(data.model_dump(), s)
    if any("duplicate:" in x for x in quality["issues"]):
        raise HTTPException(409, quality["issues"])
    q = insert_question(data.model_dump(), s, metadata={"quality": quality})
    return asdict(q)


@app.put("/api/questions/{id}")
def edit_question(
    id: str, data: QuestionInput, p=Depends(admin), s: DBSession = Depends(db)
):
    q = s.get(Question, id)
    if not q:
        raise HTTPException(404, "Question not found")
    quality = validate_question(data.model_dump(), s, id)
    if any("duplicate:" in x for x in quality["issues"]):
        raise HTTPException(409, quality["issues"])
    if data.parent_question_id and (
        data.parent_question_id == id or not s.get(Question, data.parent_question_id)
    ):
        raise HTTPException(422, "Invalid parent")
    values = data.model_dump()
    if values["source_type"] == "PYQ":
        values["source_type"] = "PYQ_PATTERN"
        q.generation_metadata = {**q.generation_metadata, "claimed_source_type": "PYQ"}
    for k, v in values.items():
        setattr(q, k, v)
    topic = s.scalar(
        select(Topic).where(Topic.subject == q.subject, Topic.name == q.topic)
    )
    if not topic:
        topic = Topic(subject=q.subject, name=q.topic)
        s.add(topic)
        s.flush()
    q.topic_id = topic.id
    q.status = "PENDING_REVIEW"
    q.verification_status = "UNVERIFIED"
    q.updated_at = now()
    from .preparation import duplicate_metadata

    metadata = {**q.generation_metadata, "quality": quality}
    metadata.pop("duplicate_review", None)
    metadata.pop("syllabus_units", None)
    flag = duplicate_metadata(s, q.question_text, q.id)
    if flag:
        metadata["duplicate_review"] = flag
    q.generation_metadata = metadata
    return asdict(q)


@app.post("/api/questions/{id}/review")
def review(id: str, data: ReviewInput, p=Depends(admin), s: DBSession = Depends(db)):
    q = s.get(Question, id)
    if not q:
        raise HTTPException(404, "Question not found")
    quality = validate_question(asdict(q), s, id)
    if data.status == "ACTIVE":
        if quality["issues"]:
            raise HTTPException(422, quality["issues"])
        if not data.notes.strip():
            raise HTTPException(
                422, "Record how you checked the answer, explanation and source"
            )
        if q.source_type == "PYQ" and not data.verified_pyq:
            raise HTTPException(
                422, "Explicit source verification is required for PYQ approval"
            )
        if data.verified_pyq:
            if not q.source_reference or not q.exam_year:
                raise HTTPException(
                    422, "Verified PYQs require reference and exam year"
                )
            q.source_type = "PYQ"
            if q.source_id:
                s.get(Source, q.source_id).verified = True
        if q.verification_status == "KEY_CONFLICT":
            q.generation_metadata = {
                **q.generation_metadata,
                "answer_status": "HUMAN_REVIEWED_NOT_OFFICIAL_KEY",
                "key_resolution_notes": data.notes,
            }
        q.verification_status = "VERIFIED_PYQ" if q.source_type == "PYQ" else "REVIEWED"
    q.status = data.status
    q.updated_at = now()
    s.add(
        Review(question_id=id, reviewer_id=p.id, decision=data.status, notes=data.notes)
    )
    return asdict(q)


@app.post("/api/questions/{id}/duplicate")
def duplicate(id: str, p=Depends(admin), s: DBSession = Depends(db)):
    old = s.get(Question, id)
    if not old:
        raise HTTPException(404, "Question not found")
    data = {k: getattr(old, k) for k in QuestionInput.model_fields}
    data["source_type"] = "ORIGINAL"
    data["parent_question_id"] = id
    return asdict(
        insert_question(
            data,
            s,
            "draft-copy",
            {"quality": {"issues": ["Duplicate draft: rewrite before approval"]}},
        )
    )


@app.post("/api/questions/{id}/bookmark")
def bookmark(id: str, p=Depends(user), s: DBSession = Depends(db)):
    q = s.get(Question, id)
    if not q or (q.status != "ACTIVE" and p.role != "admin"):
        raise HTTPException(404, "Question not found")
    mark = s.get(Bookmark, (p.id, id))
    if mark:
        s.delete(mark)
    else:
        s.add(Bookmark(user_id=p.id, question_id=id))
    return {"bookmarked": not bool(mark)}


@app.get("/api/topics")
def topics_list(p=Depends(user), s: DBSession = Depends(db)):
    rows = s.execute(
        select(Question.subject, Question.topic)
        .where(Question.status == "ACTIVE")
        .distinct()
    ).all()
    result: dict[str, list[str]] = {}
    for subject, topic in rows:
        result.setdefault(subject, []).append(topic)
    return {k: sorted(set(v)) for k, v in result.items()}


@app.get("/api/configs")
def configs(p=Depends(user), s: DBSession = Depends(db)):
    return [asdict(x) for x in s.scalars(select(Config))]


@app.put("/api/configs/{id}")
def config(id: str, data: ConfigInput, p=Depends(admin), s: DBSession = Depends(db)):
    d = data.model_dump()
    for key, allowed in [
        ("distribution", SUBJECTS),
        ("source_mix", ["PYQ", "PYQ_PATTERN", "ORIGINAL", "SUPPLEMENTARY"]),
        ("difficulty_mix", ["Easy", "Medium", "Hard"]),
    ]:
        mix = d[key]
        if (
            not mix
            or any(k not in allowed or v < 0 for k, v in mix.items())
            or sum(mix.values()) <= 0
        ):
            raise HTTPException(422, "Invalid " + key)
    if sum(d["distribution"].values()) > 200:
        raise HTTPException(422, "Maximum 200 questions")
    q = s.get(Config, id)
    if not q:
        q = Config(id=id, **d)
        s.add(q)
    else:
        for k, v in d.items():
            setattr(q, k, v)
    return asdict(q)


@app.post("/api/attempts")
def start(data: StartTest, p=Depends(user), s: DBSession = Depends(db)):
    # Acquire a database write lock before reading reservations. SQLite serializes
    # writers; PostgreSQL locks this user's row until the request commits.
    s.execute(update(Profile).where(Profile.id == p.id).values(name=Profile.name))
    config = s.get(Config, data.config_id)
    if not config:
        raise HTTPException(404, "Configuration not found")
    custom = data.mode == "PRACTICE" and (
        data.subject
        or data.topics
        or data.difficulty
        or (data.source_type and data.source_type != "MIXED")
        or data.count
    )
    if custom and data.weak_topics:
        raise HTTPException(
            422, "Choose either weak-topic practice or custom filters, not both."
        )
    weak = analytics(s, p.id)["weak_topics"] if data.weak_topics else None
    if data.weak_topics and not weak:
        raise HTTPException(
            409,
            "Weak topics need at least 5 answers across 2 exam attempts with accuracy below 60%.",
        )
    if custom:
        selected = choose_custom_practice(
            s,
            p.id,
            subject=data.subject,
            topics=data.topics,
            difficulty=data.difficulty,
            source_type=data.source_type,
            count=data.count or 10,
        )
        duration = config.duration_minutes
        name = "Custom practice: " + " · ".join(
            [
                data.subject or "All subjects",
                *([", ".join(data.topics)] if data.topics else []),
                *([data.difficulty] if data.difficulty else []),
            ]
        )
    else:
        selected = choose_questions(s, p.id, config, weak)
        duration = 20 if weak else config.duration_minutes
        name = "Weak topic practice" if weak else config.name
    a = Attempt(
        user_id=p.id,
        config_id=config.id,
        name=name,
        mode=data.mode,
        deadline=(datetime.now(timezone.utc) + timedelta(minutes=duration)).isoformat(),
        policy={
            "exam_preparation": config.id in {"exam-prep", "hard-patterns"},
            "correct_marks": config.correct_marks,
            "wrong_penalty": config.wrong_penalty,
            "duration_seconds": duration * 60,
        },
    )
    s.add(a)
    s.flush()
    for i, q in enumerate(selected):
        s.add(
            TestQuestion(
                attempt_id=a.id, question_id=q.id, position=i, snapshot=asdict(q)
            )
        )
    s.flush()
    return attempt_payload(s, a)


@app.get("/api/attempts")
def attempts(p=Depends(user), s: DBSession = Depends(db)):
    rows = list(
        s.scalars(
            select(Attempt)
            .where(Attempt.user_id == p.id)
            .order_by(Attempt.started_at.desc())
        )
    )
    for a in rows:
        if a.status == "IN_PROGRESS" and datetime.now(
            timezone.utc
        ) >= datetime.fromisoformat(a.deadline):
            lock_attempt(s, a)
            finish(s, a)
    return [{k: v for k, v in asdict(a).items() if k != "result"} for a in rows]


@app.get("/api/attempts/{id}")
def attempt(id: str, p=Depends(user), s: DBSession = Depends(db)):
    return attempt_payload(s, get_attempt(s, id, p.id))


@app.put("/api/attempts/{id}/answers/{qid}")
def answer(
    id: str, qid: str, data: AnswerInput, p=Depends(user), s: DBSession = Depends(db)
):
    a = get_attempt(s, id, p.id)
    lock_attempt(s, a)
    if a.status != "IN_PROGRESS":
        raise HTTPException(409, "Test already submitted")
    if datetime.now(timezone.utc) >= datetime.fromisoformat(a.deadline):
        finish(s, a)
        return {"expired": True, "result": a.result}
    tq = s.scalar(
        select(TestQuestion).where(
            TestQuestion.attempt_id == id, TestQuestion.question_id == qid
        )
    )
    if not tq:
        raise HTTPException(404, "Question is not in this attempt")
    ans = s.scalar(
        select(Answer).where(Answer.attempt_id == id, Answer.question_id == qid)
    )
    if not ans:
        ans = Answer(attempt_id=id, question_id=qid)
        s.add(ans)
    if ans.first_selected is None and data.selected:
        ans.first_selected = data.selected
    ans.selected = data.selected
    ans.marked = data.marked
    ans.visited = True
    s.flush()
    feedback = None
    if a.mode == "PRACTICE" and data.selected:
        feedback = {k: tq.snapshot[k] for k in ["correct_option", "explanation"]}
        for k in STRUCTURED_EXPLANATION_FIELDS:
            if tq.snapshot.get(k):
                feedback[k] = tq.snapshot[k]
        feedback["correct"] = data.selected == tq.snapshot["correct_option"]
        feedback["selected"] = data.selected
    return {"answer": asdict(ans), "feedback": feedback}


@app.post("/api/attempts/{id}/submit")
def submit(id: str, p=Depends(user), s: DBSession = Depends(db)):
    a = get_attempt(s, id, p.id)
    lock_attempt(s, a)
    finish(s, a)
    return attempt_payload(s, a)


@app.get("/api/analytics")
def analysis(p=Depends(user), s: DBSession = Depends(db)):
    return analytics(s, p.id)


@app.get("/api/jobs")
def jobs(p=Depends(admin), s: DBSession = Depends(db)):
    return [
        asdict(j)
        for j in s.scalars(select(Job).order_by(Job.created_at.desc()).limit(30))
    ]


@app.post("/api/generate")
async def generate(data: GenerateInput, p=Depends(admin), s: DBSession = Depends(db)):
    parent = (
        s.get(Question, data.parent_question_id) if data.parent_question_id else None
    )
    if data.source_type == "PYQ_PATTERN":
        reviews = set(
            s.scalars(
                select(Review.question_id).where(
                    Review.decision == "ACTIVE", Review.notes != ""
                )
            )
        )
        if (
            not parent
            or parent.source_type != "PYQ"
            or not exam_eligible(parent, {parent.id: parent}, reviews)
        ):
            raise HTTPException(
                422,
                "PYQ-pattern generation requires an active, source-verified actual PYQ with a reviewed source and syllabus mapping. Unverified copies and original challenges cannot be used as the foundation.",
            )
        if data.subject != parent.subject:
            raise HTTPException(
                422,
                "Generated questions must keep the foundation PYQ's subject and mapped syllabus units",
            )
    if not agent.enabled:
        raise HTTPException(
            503, "AI disabled: configure provider, model and API key on the backend."
        )
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    # Lock the profile row on PostgreSQL to serialize rate-limit reservations across workers.
    s.execute(select(Profile).where(Profile.id == p.id).with_for_update())
    if (
        s.scalar(
            select(func.count())
            .select_from(Job)
            .where(Job.user_id == p.id, Job.created_at >= cutoff)
        )
        >= 10
    ):
        raise HTTPException(429, "Maximum 10 generation jobs per hour")
    parent = (
        s.get(Question, data.parent_question_id) if data.parent_question_id else None
    )
    if data.parent_question_id and not parent:
        raise HTTPException(422, "Parent not found")
    job = Job(user_id=p.id, request=data.model_dump())
    s.add(job)
    s.commit()
    try:
        analysis = await agent.analyze_pyq(
            asdict(parent) if parent else {"concept": data.concept or data.topic}
        )
        request = data.model_dump()
        if data.source_type == "PYQ_PATTERN":
            request["difficulty"] = (
                parent.difficulty if data.variant_kind == "MATCHED" else "Hard"
            )
            request["verified_foundation"] = asdict(parent)
        raw = await agent.generate_questions(request, analysis)
        generated = raw.get("questions", [])
        if len(generated) != data.count:
            raise ValueError("Provider returned the wrong number of questions")
        ids = []
        rejected = []
        for item in generated:
            verification = item.pop("verification", None)
            item = {k: v for k, v in item.items() if k in QuestionInput.model_fields}
            item.update(
                source_type=data.source_type,
                parent_question_id=data.parent_question_id,
                source_reference=(
                    data.concept
                    or (
                        "Derived concept from " + parent.id
                        if parent
                        else "AI-authored original; human review required"
                    )
                ),
            )
            if data.source_type == "PYQ_PATTERN":
                item.update(
                    subject=parent.subject,
                    difficulty=request["difficulty"],
                    source_reference="Generated from verified PYQ "
                    + parent.id
                    + "; "
                    + parent.source_reference,
                )
            try:
                qdata = QuestionInput(**item).model_dump()
            except ValidationError as e:
                rejected.append(str(e))
                continue
            quality = validate_question(qdata, s, verification=verification)
            independent = await agent.validate_question(qdata)
            if (
                independent.get("correct_option") != qdata["correct_option"]
                or independent.get("ambiguous")
                or not independent.get("consistent")
            ):
                quality["issues"].append(
                    "Independent model check flagged this question"
                )
            alignment = (
                await agent.check_alignment(qdata, asdict(parent), data.variant_kind)
                if data.source_type == "PYQ_PATTERN"
                else {}
            )
            if data.source_type == "PYQ_PATTERN":
                alignment["aligned"] = all(
                    alignment.get(k) is True
                    for k in [
                        "aligned",
                        "same_concept",
                        "difficulty_fit",
                        "wording_style_fit",
                        "trap_fit",
                        "not_number_swap_or_paraphrase",
                    ]
                )
            if (
                data.source_type == "PYQ_PATTERN"
                and alignment.get("aligned") is not True
            ):
                quality["issues"].append(
                    "Source-pattern alignment requires human review"
                )
            q = insert_question(
                qdata,
                s,
                "ai:" + agent.provider,
                {
                    "syllabus_units": (
                        (parent.generation_metadata or {}).get("syllabus_units", [])
                        if parent
                        else []
                    ),
                    "variant_kind": (
                        data.variant_kind if data.source_type == "PYQ_PATTERN" else None
                    ),
                    "foundation_snapshot": (
                        asdict(parent) if data.source_type == "PYQ_PATTERN" else None
                    ),
                    "alignment_check": alignment,
                    "model": agent.model,
                    "job_id": job.id,
                    "analysis": analysis,
                    "verification": verification,
                    "quality": quality,
                    "independent_check": independent,
                },
            )
            ids.append(q.id)
        job.status = "COMPLETED"
        job.output = {"question_ids": ids, "invalid": rejected, "analysis": analysis}
        s.commit()
        return asdict(job)
    except Exception:
        s.rollback()
        job = s.get(Job, job.id)
        job.status = "FAILED"
        job.output = {
            "error": "Provider request or structured-output validation failed. No unreviewed question was activated."
        }
        s.commit()
        raise HTTPException(502, job.output["error"])


@app.post("/api/import")
async def import_csv(
    file: UploadFile = File(...), p=Depends(admin), s: DBSession = Depends(db)
):
    raw = await file.read(2_000_001)
    if len(raw) > 2_000_000:
        raise HTTPException(413, "CSV limit is 2 MB")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    except UnicodeDecodeError:
        raise HTTPException(422, "CSV must be UTF-8")
    out = {"imported": 0, "rejected": 0, "duplicate": 0, "invalid": 0, "errors": []}
    for i, row in enumerate(reader, 2):
        if i > 1001:
            raise HTTPException(422, "Maximum 1,000 rows per import")
        try:
            row = {
                k: v
                for k, v in row.items()
                if k in QuestionInput.model_fields and v != ""
            }
            data = QuestionInput(**row).model_dump()
            if detect_duplicate(s, data["question_text"]):
                out["duplicate"] += 1
                continue
            quality = validate_question(data, s)
            if quality["issues"]:
                out["invalid"] += 1
                out["errors"].append({"row": i, "message": quality["issues"]})
                continue
            # Imports are always unverified drafts, even if the source column says PYQ.
            insert_question(data, s, "csv", {"quality": quality})
            out["imported"] += 1
        except (ValidationError, HTTPException) as e:
            out["invalid"] += 1
            out["errors"].append({"row": i, "message": str(e)[:400]})
    out["rejected"] = out["invalid"] + out["duplicate"]
    return out


@app.get("/api/preparation")
def preparation(p=Depends(user), s: DBSession = Depends(db)):
    from .preparation import coverage

    return coverage(s, p.id)


@app.post("/api/preparation/duplicates/{id}/resolve")
def resolve_possible_duplicate(
    id: str, data: ReviewInput, p=Depends(admin), s: DBSession = Depends(db)
):
    q = s.get(Question, id)
    if not q:
        raise HTTPException(404, "Question not found")
    if data.status not in {"ACTIVE", "ARCHIVED"} or not data.notes.strip():
        raise HTTPException(
            422,
            "Choose ACTIVE (distinct) or ARCHIVED (duplicate), with a comparison rationale",
        )
    q.generation_metadata = {
        **(q.generation_metadata or {}),
        "duplicate_review": {
            "status": "CLEARED" if data.status == "ACTIVE" else "DUPLICATE",
            "reviewer": p.id,
            "notes": data.notes,
        },
    }
    if data.status == "ARCHIVED":
        q.status = "ARCHIVED"
    s.add(
        Review(question_id=id, reviewer_id=p.id, decision=data.status, notes=data.notes)
    )
    return {"id": id, "duplicate_review": q.generation_metadata["duplicate_review"]}


@app.put("/api/questions/{id}/syllabus")
def map_syllabus(
    id: str, data: SyllabusAssignment, p=Depends(admin), s: DBSession = Depends(db)
):
    from .preparation import CATALOG

    q = s.get(Question, id)
    if not q:
        raise HTTPException(404, "Question not found")
    valid = {u["id"] for u in CATALOG["units"] if u["subject"] == q.subject}
    if any(u not in valid for u in data.unit_ids):
        raise HTTPException(422, "Choose syllabus units matching this question subject")
    q.generation_metadata = {
        **(q.generation_metadata or {}),
        "syllabus_units": list(dict.fromkeys(data.unit_ids)),
        "syllabus_mapping_reviewer": p.id,
    }
    return asdict(q)
