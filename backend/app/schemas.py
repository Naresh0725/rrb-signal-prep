from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Literal

STRUCTURED_EXPLANATION_FIELDS = [
    "concept",
    "formula",
    "given",
    "calculation",
    "final_answer",
    "why_correct",
    "why_wrong",
]

PLACEHOLDER_TEXT = {"n/a", "na", "tbd", "todo", "-", "none", "xxx", "..."}


def reject_placeholder(v: str | None, label: str) -> str | None:
    if v is not None and v.strip().lower() in PLACEHOLDER_TEXT:
        raise ValueError(f"{label} looks like a placeholder, not real content")
    return v

SUBJECTS = [
    "Science & Engineering",
    "Computers",
    "Mathematics",
    "Reasoning",
    "General Awareness",
]


class QuestionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    question_text: str = Field(min_length=12, max_length=5000)
    option_a: str = Field(min_length=1, max_length=1000)
    option_b: str = Field(min_length=1, max_length=1000)
    option_c: str = Field(min_length=1, max_length=1000)
    option_d: str = Field(min_length=1, max_length=1000)
    correct_option: Literal["A", "B", "C", "D"]
    explanation: str = Field(min_length=10, max_length=10000)
    # Optional structured, beginner-friendly explanation fields. None of these are
    # required: conceptual questions may skip formula/given/calculation entirely.
    concept: str | None = Field(default=None, max_length=3000)
    formula: str | None = Field(default=None, max_length=1000)
    given: str | None = Field(default=None, max_length=1000)
    calculation: str | None = Field(default=None, max_length=4000)
    final_answer: str | None = Field(default=None, max_length=500)
    why_correct: str | None = Field(default=None, max_length=3000)
    why_wrong: dict[str, str] | None = None

    @field_validator(
        "concept", "formula", "given", "calculation", "final_answer", "why_correct"
    )
    @classmethod
    def _no_placeholder(cls, v, info):
        return reject_placeholder(v, info.field_name)

    @field_validator("why_wrong")
    @classmethod
    def _why_wrong_shape(cls, v):
        if v is None:
            return v
        cleaned = {}
        for k, reason in v.items():
            k = k.strip().upper()
            if k not in "ABCD":
                raise ValueError("why_wrong keys must be option letters A-D")
            reject_placeholder(reason, f"why_wrong.{k}")
            if reason and reason.strip():
                cleaned[k] = reason.strip()
        return cleaned or None

    subject: Literal[
        "Science & Engineering",
        "Computers",
        "Mathematics",
        "Reasoning",
        "General Awareness",
    ]
    topic: str = Field(min_length=2, max_length=200)
    subtopic: str = Field(default="", max_length=200)
    difficulty: Literal["Easy", "Medium", "Hard"] = "Medium"
    source_type: Literal["PYQ", "PYQ_PATTERN", "ORIGINAL", "SUPPLEMENTARY"] = "ORIGINAL"
    source_reference: str = Field(default="", max_length=2000)
    exam: str = "RRB Technician Grade-I Signal"
    exam_year: int | None = Field(default=None, ge=1990, le=2100)
    shift: str = ""
    parent_question_id: str | None = None


class StartTest(BaseModel):
    config_id: str = "grade1"
    mode: Literal["PRACTICE", "EXAM"] = "PRACTICE"
    weak_topics: bool = False
    # Optional ad-hoc custom-practice filters (PRACTICE mode only). config_id
    # is still required and supplies scoring policy defaults; leaving all of
    # these unset preserves the existing config-driven behavior exactly.
    subject: Literal[
        "Science & Engineering",
        "Computers",
        "Mathematics",
        "Reasoning",
        "General Awareness",
    ] | None = None
    topics: list[str] | None = Field(default=None, max_length=5)
    difficulty: Literal["Easy", "Medium", "Hard"] | None = None
    source_type: Literal["PYQ", "PYQ_PATTERN", "ORIGINAL", "MIXED"] | None = None
    count: int | None = Field(default=None, ge=1, le=100)


class AnswerInput(BaseModel):
    selected: Literal["A", "B", "C", "D"] | None = None
    marked: bool = False


class ReviewInput(BaseModel):
    status: Literal["ACTIVE", "REJECTED", "ARCHIVED", "PENDING_REVIEW"]
    notes: str = Field(default="", max_length=3000)
    verified_pyq: bool = False


class ConfigInput(BaseModel):
    name: str = Field(min_length=3, max_length=200)
    distribution: dict[str, int]
    duration_minutes: int = Field(ge=1, le=300)
    source_mix: dict[str, int]
    difficulty_mix: dict[str, int]
    cooldown_days: int = Field(ge=0, le=365)
    correct_marks: float = Field(default=1, gt=0, le=10)
    wrong_penalty: float = Field(default=1 / 3, ge=0, le=10)


class GenerateInput(BaseModel):
    subject: Literal[
        "Science & Engineering",
        "Computers",
        "Mathematics",
        "Reasoning",
        "General Awareness",
    ]
    topic: str = Field(min_length=2, max_length=200)
    subtopic: str = Field(default="", max_length=200)
    difficulty: Literal["Easy", "Medium", "Hard"] = "Medium"
    count: int = Field(default=5, ge=1, le=20)
    source_type: Literal["PYQ_PATTERN", "ORIGINAL"] = "ORIGINAL"
    parent_question_id: str | None = None
    concept: str = Field(default="", max_length=2000)
    style: str = Field(default="Mixed conceptual and numerical", max_length=500)
    variant_kind: Literal["MATCHED", "HARDER"] = "MATCHED"


class SyllabusAssignment(BaseModel):
    unit_ids: list[str] = Field(min_length=1, max_length=10)
