import os
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import (
    event,
    create_engine,
    String,
    Text,
    JSON,
    ForeignKey,
    Integer,
    Float,
    Boolean,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from dotenv import load_dotenv

load_dotenv()


def uid():
    return str(uuid4())


def now():
    return datetime.now(timezone.utc).isoformat()


class Base(DeclarativeBase):
    pass


url = os.getenv("DATABASE_URL", "sqlite:///./signalprep.db")
engine = create_engine(
    url,
    connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
    pool_pre_ping=True,
)
if url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def sqlite_foreign_keys(conn, record):
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")


Session = sessionmaker(engine, expire_on_commit=False)


class Profile(Base):
    __tablename__ = "profiles"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, default="Learner")
    role: Mapped[str] = mapped_column(String, default="student")


class Topic(Base):
    __tablename__ = "question_topics"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    subject: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    __table_args__ = (UniqueConstraint("subject", "name"),)


class Source(Base):
    __tablename__ = "question_sources"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    reference: Mapped[str] = mapped_column(Text)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)


class Question(Base):
    __tablename__ = "questions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    question_text: Mapped[str] = mapped_column(Text)
    option_a: Mapped[str] = mapped_column(Text)
    option_b: Mapped[str] = mapped_column(Text)
    option_c: Mapped[str] = mapped_column(Text)
    option_d: Mapped[str] = mapped_column(Text)
    correct_option: Mapped[str] = mapped_column(String)
    explanation: Mapped[str] = mapped_column(Text)
    # Optional structured, beginner-friendly explanation. All nullable so existing
    # questions and conceptual questions (no formula/calculation) keep working
    # unchanged; the plain `explanation` above remains the fallback.
    concept: Mapped[str | None] = mapped_column(Text, nullable=True)
    formula: Mapped[str | None] = mapped_column(Text, nullable=True)
    given: Mapped[str | None] = mapped_column(Text, nullable=True)
    calculation: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    why_correct: Mapped[str | None] = mapped_column(Text, nullable=True)
    # {"A": "reason option A is wrong", ...} — never includes the correct option.
    why_wrong: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    subject: Mapped[str] = mapped_column(String, index=True)
    topic: Mapped[str] = mapped_column(String, index=True)
    subtopic: Mapped[str] = mapped_column(String, default="")
    topic_id: Mapped[str | None] = mapped_column(
        ForeignKey("question_topics.id"), nullable=True
    )
    source_id: Mapped[str | None] = mapped_column(
        ForeignKey("question_sources.id"), nullable=True
    )
    difficulty: Mapped[str] = mapped_column(String, default="Medium")
    source_type: Mapped[str] = mapped_column(String, default="ORIGINAL", index=True)
    source_reference: Mapped[str] = mapped_column(Text, default="")
    verification_status: Mapped[str] = mapped_column(String, default="UNVERIFIED")
    exam: Mapped[str] = mapped_column(String, default="RRB Technician Grade-I Signal")
    exam_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shift: Mapped[str] = mapped_column(String, default="")
    parent_question_id: Mapped[str | None] = mapped_column(
        ForeignKey("questions.id"), nullable=True
    )
    generation_method: Mapped[str] = mapped_column(String, default="manual")
    generation_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String, default="PENDING_REVIEW", index=True)
    created_at: Mapped[str] = mapped_column(String, default=now)
    updated_at: Mapped[str] = mapped_column(String, default=now)


class Config(Base):
    __tablename__ = "test_configs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String)
    distribution: Mapped[dict] = mapped_column(JSON)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=90)
    source_mix: Mapped[dict] = mapped_column(JSON, default=lambda: {"ORIGINAL": 100})
    difficulty_mix: Mapped[dict] = mapped_column(
        JSON, default=lambda: {"Easy": 30, "Medium": 50, "Hard": 20}
    )
    cooldown_days: Mapped[int] = mapped_column(Integer, default=7)
    correct_marks: Mapped[float] = mapped_column(Float, default=1)
    wrong_penalty: Mapped[float] = mapped_column(Float, default=1 / 3)


class Attempt(Base):
    __tablename__ = "test_attempts"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), index=True)
    config_id: Mapped[str] = mapped_column(ForeignKey("test_configs.id"))
    name: Mapped[str] = mapped_column(String)
    mode: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="IN_PROGRESS")
    started_at: Mapped[str] = mapped_column(String, default=now)
    deadline: Mapped[str] = mapped_column(String)
    submitted_at: Mapped[str | None] = mapped_column(String, nullable=True)
    policy: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=0)


class TestQuestion(Base):
    __tablename__ = "test_questions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    attempt_id: Mapped[str] = mapped_column(ForeignKey("test_attempts.id"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"))
    position: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict] = mapped_column(JSON)
    __table_args__ = (
        UniqueConstraint("attempt_id", "position"),
        UniqueConstraint("attempt_id", "question_id"),
    )


class Answer(Base):
    __tablename__ = "user_answers"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    attempt_id: Mapped[str] = mapped_column(ForeignKey("test_attempts.id"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"))
    selected: Mapped[str | None] = mapped_column(String, nullable=True)
    marked: Mapped[bool] = mapped_column(Boolean, default=False)
    visited: Mapped[bool] = mapped_column(Boolean, default=True)
    first_selected: Mapped[str | None] = mapped_column(String, nullable=True)
    __table_args__ = (UniqueConstraint("attempt_id", "question_id"),)


class Review(Base):
    __tablename__ = "question_reviews"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"))
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"))
    decision: Mapped[str] = mapped_column(String)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(String, default=now)


class Job(Base):
    __tablename__ = "question_generation_jobs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), index=True)
    status: Mapped[str] = mapped_column(String, default="RUNNING")
    request: Mapped[dict] = mapped_column(JSON)
    output: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(String, default=now)


class Bookmark(Base):
    __tablename__ = "bookmarks"
    user_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), primary_key=True)
    question_id: Mapped[str] = mapped_column(
        ForeignKey("questions.id"), primary_key=True
    )


def asdict(obj):
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


def db():
    with Session() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
