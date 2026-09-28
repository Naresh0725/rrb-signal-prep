from pathlib import Path
import os, tempfile, shutil

LIVE_DB = Path(__file__).resolve().parents[2] / "signalprep.db"
TEST_DB = Path(tempfile.mktemp(suffix=".db"))
shutil.copy2(LIVE_DB, TEST_DB)

os.environ["DATABASE_URL"] = "sqlite:///" + str(TEST_DB)
os.environ["APP_ENV"] = "development"
os.environ["DEV_AUTH"] = "true"
import pytest
from datetime import datetime, timedelta, timezone
from collections import Counter
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import Session, Attempt, Question, Profile, TestQuestion
from backend.app.auth import user
from backend.app.quality import calculate, validate_question


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def start(c, mode="EXAM", config="quick"):
    r = c.post("/api/attempts", json={"mode": mode, "config_id": config})
    assert r.status_code == 200, r.text
    return r.json()


def test_seed_and_config(client):
    r = client.get("/api/stats").json()
    assert r["total"] == 432 and r["sources"]["ORIGINAL"] == 430
    assert (
        r["sources"]["SUPPLEMENTARY"] == 2 and r["sources"].get("PYQ_PATTERN", 0) == 0
    )


def test_full_test_exact_distribution_and_no_answer_leak(client):
    a = start(client, config="grade1")
    assert len(a["questions"]) == 100
    assert len(set(q["id"] for q in a["questions"])) == 100
    assert Counter(q["subject"] for q in a["questions"]) == {
        "Science & Engineering": 35,
        "Computers": 20,
        "Mathematics": 20,
        "Reasoning": 15,
        "General Awareness": 10,
    }
    assert Counter(q["difficulty"] for q in a["questions"]) == {
        "Easy": 30,
        "Medium": 50,
        "Hard": 20,
    }
    assert all(
        "correct_option" not in q
        and "explanation" not in q
        and "generation_metadata" not in q
        for q in a["questions"]
    )
    again = client.get("/api/attempts/" + a["id"]).json()
    assert [q["id"] for q in a["questions"]] == [q["id"] for q in again["questions"]]


def test_scoring_and_exam_feedback(client):
    a = start(client)
    q1, q2 = a["questions"][:2]
    with Session() as s:
        k1 = s.get(Question, q1["id"]).correct_option
        k2 = s.get(Question, q2["id"]).correct_option
    r = client.put(
        f"/api/attempts/{a['id']}/answers/{q1['id']}",
        json={"selected": k1, "marked": True},
    )
    assert r.json()["feedback"] is None
    bad = next(k for k in "ABCD" if k != k2)
    client.put(f"/api/attempts/{a['id']}/answers/{q2['id']}", json={"selected": bad})
    r = client.post(f"/api/attempts/{a['id']}/submit").json()["result"]
    assert (r["correct"], r["wrong"], r["unanswered"], r["score"]) == (1, 1, 8, 0.67)
    assert r["accuracy"] == 50 and len(r["review"]) == 10
    assert client.post(f"/api/attempts/{a['id']}/submit").json()["result"] == r
    assert (
        client.put(
            f"/api/attempts/{a['id']}/answers/{q1['id']}", json={"selected": "A"}
        ).status_code
        == 409
    )


def test_practice_immediate_feedback(client):
    a = start(client, "PRACTICE")
    q = a["questions"][0]
    r = client.put(
        f"/api/attempts/{a['id']}/answers/{q['id']}", json={"selected": "A"}
    ).json()
    assert r["feedback"]["correct_option"] in "ABCD"
    assert r["feedback"]["explanation"]


def test_timeout_rejects_late_answer_and_scores(client):
    a = start(client)
    with Session() as s:
        obj = s.get(Attempt, a["id"])
        obj.deadline = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        s.commit()
    r = client.put(
        f"/api/attempts/{a['id']}/answers/{a['questions'][0]['id']}",
        json={"selected": "A"},
    ).json()
    assert r["expired"] and r["result"]["attempted"] == 0
    assert client.get("/api/attempts/" + a["id"]).json()["status"] == "SUBMITTED"


def test_answer_must_belong_to_attempt(client):
    a = start(client)
    assert (
        client.put(
            f"/api/attempts/{a['id']}/answers/no-such-question", json={"selected": "A"}
        ).status_code
        == 404
    )


def test_attempt_ownership(client):
    a = start(client)
    with Session() as s:
        s.add(Profile(id="other-user", name="Other", role="student"))
        s.commit()
    app.dependency_overrides[user] = lambda: Profile(
        id="other-user", name="Other", role="student"
    )
    try:
        assert client.get("/api/attempts/" + a["id"]).status_code == 404
        assert client.post("/api/attempts/" + a["id"] + "/submit").status_code == 404
        assert client.get("/api/jobs").status_code == 403
        q = client.get("/api/questions").json()["items"][0]
        assert "correct_option" not in q
    finally:
        app.dependency_overrides.clear()


def test_impossible_source_mix_fails(client):
    cfg = client.get("/api/configs").json()[0]
    id = cfg.pop("id")
    cfg["source_mix"] = {"PYQ": 100}
    assert client.put("/api/configs/impossible", json=cfg).status_code == 200
    assert (
        client.post("/api/attempts", json={"config_id": "impossible"}).status_code
        == 409
    )


def test_snapshot_survives_edit(client):
    a = start(client)
    qid = a["questions"][0]["id"]
    with Session() as s:
        q = s.get(Question, qid)
        old = q.question_text
        q.question_text = "Edited after the attempt began"
        s.commit()
    assert (
        client.get("/api/attempts/" + a["id"]).json()["questions"][0]["question_text"]
        == old
    )
    with Session() as s:
        s.get(Question, qid).question_text = old
        s.commit()


def test_math_safety():
    assert calculate("230 * 2 / 5") == 92
    with pytest.raises(ValueError):
        calculate('__import__("os").system("ls")')
    with pytest.raises(ValueError):
        calculate("2**1000000")


def test_duplicate_options_rejected():
    q = {
        "option_a": "same",
        "option_b": "same",
        "option_c": "three",
        "option_d": "four",
        "source_type": "ORIGINAL",
    }
    assert "Options must be distinct" in validate_question(q)["issues"]


def test_no_ai_key(client):
    assert (
        client.post(
            "/api/generate", json={"subject": "Computers", "topic": "Databases"}
        ).status_code
        == 503
    )


def test_csv_claim_is_not_verified_pyq(client):
    raw = "question_text,option_a,option_b,option_c,option_d,correct_option,explanation,subject,topic,source_type,source_reference,exam_year\nWhich mechanism allows a diode to conduct predominantly in one direction?,PN junction,Metal spring,Optical lens,Hydraulic valve,A,A PN junction has asymmetric current voltage characteristics.,Science & Engineering,Semiconductors,PYQ,Test reference requiring verification,2024\n"
    r = client.post("/api/import", files={"file": ("test.csv", raw, "text/csv")})
    assert r.status_code == 200, r.text
    assert r.json()["imported"] == 1
    q = client.get("/api/questions?search=predominantly").json()["items"][0]
    assert (
        q["status"] == "PENDING_REVIEW"
        and q["source_type"] == "PYQ_PATTERN"
        and q["verification_status"] == "UNVERIFIED"
    )
    assert (
        client.post(
            "/api/questions/" + q["id"] + "/review", json={"status": "ACTIVE"}
        ).status_code
        == 422
    )
    r = client.post(
        "/api/questions/" + q["id"] + "/review",
        json={
            "status": "ACTIVE",
            "verified_pyq": True,
            "notes": "Synthetic test confirmation, not an actual external-source claim.",
        },
    )
    assert r.status_code == 200
    assert r.json()["source_type"] == "PYQ"
    assert (
        client.post(
            "/api/import", files={"file": ("test.csv", raw, "text/csv")}
        ).json()["duplicate"]
        == 1
    )


def test_weak_topics_need_evidence(client):
    assert client.post("/api/attempts", json={"weak_topics": True}).status_code == 409


def test_exam_prep_excludes_starter_bank(client):
    r = client.post("/api/attempts", json={"config_id": "exam-prep", "mode": "EXAM"})
    assert r.status_code == 409
    assert "nothing will be recycled" in r.json()["detail"]


def test_strict_reservations_and_numeric_duplicates(client):
    from backend.app.db import Config, Review
    from backend.app.engine import strict_pool, question_family
    from backend.app.seed import ROWS

    with Session() as s:
        owner = s.query(Profile).first().id
        rows = []
        for qid, text in [
            ("fixture-pyq-a", "Compute the flux through 30 turns of this coil."),
            ("fixture-pyq-b", "Compute the flux through 90 turns of this coil."),
            ("fixture-pyq-c", "Identify the operating region of this transistor."),
        ]:
            data = {
                **ROWS[0],
                "id": qid,
                "question_text": text,
                "source_type": "PYQ",
                "verification_status": "VERIFIED_PYQ",
                "generation_method": "test-fixture",
                "generation_metadata": {"syllabus_units": ["science-circuits"]},
                "source_reference": "Synthetic test fixture only",
                "exam_year": 2024,
            }
            q = Question(**data)
            s.add(q)
            s.flush()
            s.add(
                Review(
                    question_id=qid,
                    reviewer_id=owner,
                    decision="ACTIVE",
                    notes="Test fixture",
                )
            )
            rows.append(q)
        s.flush()
        assert len(strict_pool(s, owner, rows)) == 2
        a = Attempt(
            user_id=owner,
            config_id="exam-prep",
            name="Fixture",
            mode="EXAM",
            deadline=datetime.now(timezone.utc).isoformat(),
            policy={},
        )
        s.add(a)
        s.flush()
        s.add(
            TestQuestion(
                attempt_id=a.id,
                question_id=rows[0].id,
                position=0,
                snapshot={"question_text": rows[0].question_text},
            )
        )
        s.flush()
        assert [q.id for q in strict_pool(s, owner, rows)] == ["fixture-pyq-c"]
        # Reservations in an unfinished attempt exclude other IDs with changed numbers.
        assert question_family(rows[0].question_text) == question_family(
            rows[1].question_text
        )
        s.rollback()


def test_seed_upgrade_preserves_attempts(client):
    from backend.app.seed import seed

    with Session() as s:
        before = s.query(Attempt).count()
        seed(s)
        s.flush()
        assert s.query(Attempt).count() == before
        assert s.query(Question).filter(Question.id.like("seed-%")).count() == 190
        s.rollback()


def test_preparation_coverage_and_provenance(client):
    d = client.get("/api/preparation").json()
    assert len(d["units"]) == 75
    assert d["summary"]["patterns"] == 0
    assert d["summary"]["supplementary"] == 1
    assert d["summary"]["external_indexed"] == 200
    assert [q["id"] for q in d["key_conflicts"]] == ["supp-2026-s1-092"]
    assert d["summary"]["missing_units"] == 75
    assert d["summary"]["underrepresented_units"] == 0
    assert sum(u["patterns"] for u in d["units"]) == 0
    assert all(u["verified"] == 0 for u in d["units"])


def test_hard_pattern_history_is_strict(client):
    r = client.post(
        "/api/attempts", json={"config_id": "hard-patterns", "mode": "PRACTICE"}
    )
    assert r.status_code == 409
    assert "nothing will be recycled" in r.json()["detail"]


def test_supplementary_never_counts_as_verified(client):
    a = start(client, "PRACTICE", "supplementary")
    assert all(
        q["source_type"] == "SUPPLEMENTARY"
        and q["verification_status"] == "UNVERIFIED_SOURCE"
        for q in a["questions"]
    )
    assert (
        client.post("/api/attempts", json={"config_id": "supplementary"}).status_code
        == 409
    )


def test_numerical_variants_and_paraphrase_flags():
    from backend.app.preparation import possible_duplicate

    assert (
        possible_duplicate(
            "Find current with 12 V across 3 ohms.",
            "Find current with 24 V across 6 ohms.",
        )
        == "NUMERICAL_VARIANT"
    )
    assert (
        possible_duplicate(
            "A resistor is connected to a battery. Calculate the current in the circuit.",
            "A resistor is connected to a battery. Determine the current in the circuit.",
        )
        == "POSSIBLE_PARAPHRASE"
    )
    assert not validate_question(
        {
            "option_a": "√10",
            "option_b": "2√10",
            "option_c": "5√2",
            "option_d": "10",
            "source_type": "ORIGINAL",
        }
    )["issues"]


def test_pattern_generation_requires_verified_foundation(client):
    for parent in [None, "seed-0001", "prep-pattern-001", "supp-2024-s1-054"]:
        r = client.post(
            "/api/generate",
            json={
                "subject": "Science & Engineering",
                "topic": "Circuits",
                "source_type": "PYQ_PATTERN",
                "parent_question_id": parent,
            },
        )
        assert r.status_code == 422
        assert "source-verified actual PYQ" in r.json()["detail"]


def test_matched_and_harder_require_alignment_and_review():
    from types import SimpleNamespace as Q
    from backend.app.engine import exam_eligible

    parent = Q(
        id="actual-pyq",
        status="ACTIVE",
        source_type="PYQ",
        source_reference="Official reference fixture",
        exam_year=2024,
        verification_status="VERIFIED_PYQ",
        generation_metadata={"syllabus_units": ["science-circuits"]},
    )
    for variant, difficulty in [("MATCHED", "Medium"), ("HARDER", "Hard")]:
        child = Q(
            id="generated",
            status="ACTIVE",
            source_type="PYQ_PATTERN",
            difficulty=difficulty,
            verification_status="REVIEWED",
            parent_question_id=parent.id,
            generation_metadata={
                "variant_kind": variant,
                "alignment_check": {"aligned": True},
                "syllabus_units": ["science-circuits"],
            },
        )
        assert exam_eligible(child, {parent.id: parent}, {parent.id, child.id})
        assert not exam_eligible(child, {parent.id: parent}, {parent.id})
        child.generation_metadata["alignment_check"]["aligned"] = False
        assert not exam_eligible(child, {parent.id: parent}, {parent.id, child.id})


# ---------------------------------------------------------------------------
# Phase 2: structured, beginner-friendly explanations
# ---------------------------------------------------------------------------
from pydantic import ValidationError
from backend.app.schemas import QuestionInput

STRUCTURED_KEYS = [
    "concept",
    "formula",
    "given",
    "calculation",
    "final_answer",
    "why_correct",
    "why_wrong",
]


from sqlalchemy import select as _select
from fastapi import HTTPException


def _set_snapshot_fields(attempt_id, qid, **fields):
    # Attempts store an immutable snapshot of each question at start() time
    # (by design, see test_snapshot_survives_edit) — editing the live Question
    # row afterwards has no effect on an attempt already in progress. To test
    # feedback/review rendering we must edit the attempt's own snapshot.
    with Session() as s:
        tq = s.scalars(
            _select(TestQuestion).where(
                TestQuestion.attempt_id == attempt_id,
                TestQuestion.question_id == qid,
            )
        ).one()
        tq.snapshot = {**tq.snapshot, **fields}
        s.commit()
        return tq.snapshot


def test_old_explanation_still_works_in_practice_feedback(client):
    a = start(client, "PRACTICE")
    q = a["questions"][0]
    _set_snapshot_fields(a["id"], q["id"], **{k: None for k in STRUCTURED_KEYS})
    r = client.put(
        f"/api/attempts/{a['id']}/answers/{q['id']}", json={"selected": "A"}
    ).json()
    assert r["feedback"]["explanation"]
    assert not any(k in r["feedback"] for k in STRUCTURED_KEYS)


def test_structured_explanation_accepted_and_returned_in_feedback(client):
    a = start(client, "PRACTICE")
    q = a["questions"][0]
    correct_option = _set_snapshot_fields(a["id"], q["id"])["correct_option"]
    wrong_letter = next(k for k in "ABCD" if k != correct_option)
    _set_snapshot_fields(
        a["id"],
        q["id"],
        concept="Ohm's law relates voltage, current and resistance.",
        formula="V = IR",
        given="I = 2 A\nR = 5 Ω",
        calculation="V = 2 x 5\nV = 10 V",
        final_answer="10 V",
        why_correct="Applying Ohm's law directly gives the voltage.",
        why_wrong={wrong_letter: "This confuses current with voltage."},
    )
    r = client.put(
        f"/api/attempts/{a['id']}/answers/{q['id']}",
        json={"selected": wrong_letter},
    ).json()
    fb = r["feedback"]
    assert fb["concept"] and fb["formula"] == "V = IR"
    assert fb["final_answer"] == "10 V"
    assert fb["correct"] is False
    assert fb["why_wrong"][wrong_letter] == "This confuses current with voltage."


def test_structured_fields_not_leaked_in_active_exam_attempt(client):
    a = start(client, "EXAM")
    q = a["questions"][0]
    _set_snapshot_fields(
        a["id"],
        q["id"],
        concept="leak-check concept",
        formula="leak-check formula",
        given="leak-check given",
        calculation="leak-check calc",
        final_answer="leak-check answer",
        why_correct="leak-check why correct",
        why_wrong={"A": "leak-check wrong"},
    )
    payload = client.get("/api/attempts/" + a["id"]).json()
    leaked_q = next(x for x in payload["questions"] if x["id"] == q["id"])
    for k in ["correct_option", "explanation", "generation_metadata", *STRUCTURED_KEYS]:
        assert k not in leaked_q


def test_structured_fields_not_leaked_via_non_admin_question_listing(client):
    with Session() as s:
        s.add(Profile(id="phase2-student", name="Phase2 Student", role="student"))
        obj = s.query(Question).filter(Question.status == "ACTIVE").first()
        obj.concept = "leak-check concept"
        obj.formula = "leak-check formula"
        obj.why_wrong = {"A": "leak-check wrong"}
        s.commit()
    app.dependency_overrides[user] = lambda: Profile(
        id="phase2-student", name="Phase2 Student", role="student"
    )
    try:
        items = client.get("/api/questions").json()["items"]
        assert items
        for q in items:
            for k in ["correct_option", "explanation", *STRUCTURED_KEYS]:
                assert k not in q
    finally:
        app.dependency_overrides.clear()


def _base_question_input(**overrides):
    base = dict(
        question_text="Which law relates voltage, current and resistance?",
        option_a="Ohm's law",
        option_b="Newton's law",
        option_c="Faraday's law",
        option_d="Boyle's law",
        correct_option="A",
        explanation="Ohm's law states V = IR for a resistor.",
        subject="Science & Engineering",
        topic="Basic electrical",
    )
    base.update(overrides)
    return base


def test_why_wrong_rejects_letters_outside_a_to_d():
    with pytest.raises(ValidationError):
        QuestionInput(**_base_question_input(why_wrong={"Z": "not a real option"}))


def test_why_wrong_accepts_valid_incorrect_option_letters():
    qi = QuestionInput(
        **_base_question_input(
            why_wrong={"B": "Newton's law is about motion, not circuits."}
        )
    )
    assert qi.why_wrong == {"B": "Newton's law is about motion, not circuits."}


def test_why_wrong_containing_correct_option_is_flagged():
    q = dict(
        option_a="a",
        option_b="b",
        option_c="c",
        option_d="d",
        source_type="ORIGINAL",
        correct_option="A",
        why_wrong={"A": "should not explain the correct option"},
    )
    issues = validate_question(q)["issues"]
    assert "why_wrong must not explain the correct option" in issues


def test_numeric_final_answer_consistent_with_calculation_passes():
    q = dict(
        option_a="a",
        option_b="b",
        option_c="c",
        option_d="d",
        source_type="ORIGINAL",
        correct_option="A",
        calculation="P = 15**2/5 = 45",
        final_answer="45 W",
    )
    issues = validate_question(q)["issues"]
    assert not any("final_answer" in i for i in issues)


def test_numeric_final_answer_inconsistent_with_calculation_is_rejected():
    q = dict(
        option_a="a",
        option_b="b",
        option_c="c",
        option_d="d",
        source_type="ORIGINAL",
        correct_option="A",
        calculation="P = 15**2/5 = 45",
        final_answer="99 W",
    )
    issues = validate_question(q)["issues"]
    assert any("final_answer" in i for i in issues)


def test_existing_exam_flow_unchanged_for_questions_without_structured_fields(client):
    a = start(client, "EXAM")
    qid = a["questions"][0]["id"]
    _set_snapshot_fields(a["id"], qid, **{k: None for k in STRUCTURED_KEYS})
    client.put(f"/api/attempts/{a['id']}/answers/{qid}", json={"selected": "A"})
    r = client.post(f"/api/attempts/{a['id']}/submit").json()["result"]
    reviewed = next(x for x in r["review"] if x["id"] == qid)
    assert reviewed["explanation"]
    assert all(reviewed.get(k) is None for k in STRUCTURED_KEYS)


# ---------------------------------------------------------------------------
# Phase 3: custom practice (subject/topic/difficulty filters, no-repeat,
# question count) and the /api/topics helper endpoint it relies on.
# ---------------------------------------------------------------------------


def test_custom_practice_filters_by_subject_topic_difficulty(client):
    r = client.post(
        "/api/attempts",
        json={
            "config_id": "quick",
            "mode": "PRACTICE",
            "subject": "Mathematics",
            "topics": ["Simple Interest"],
            "difficulty": "Medium",
            "count": 5,
        },
    )
    assert r.status_code == 200, r.text
    a = r.json()
    assert len(a["questions"]) == 5
    assert all(
        q["subject"] == "Mathematics"
        and q["topic"] == "Simple Interest"
        and q["difficulty"] == "Medium"
        for q in a["questions"]
    )
    assert "Mathematics" in a["name"] and "Simple Interest" in a["name"]


def test_custom_practice_respects_source_type_filter(client):
    r = client.post(
        "/api/attempts",
        json={
            "config_id": "quick",
            "mode": "PRACTICE",
            "subject": "Mathematics",
            "topics": ["Simple Interest"],
            "source_type": "ORIGINAL",
            "count": 4,
        },
    )
    assert r.status_code == 200, r.text
    assert len(r.json()["questions"]) == 4


def test_custom_practice_insufficient_pool_is_rejected_not_recycled(client):
    r = client.post(
        "/api/attempts",
        json={
            "config_id": "quick",
            "mode": "PRACTICE",
            "subject": "Mathematics",
            "topics": ["Simple Interest"],
            "difficulty": "Hard",
            "count": 10,
        },
    )
    assert r.status_code == 409


def test_custom_practice_avoids_immediate_duplicates(client):
    r = client.post(
        "/api/attempts",
        json={
            "config_id": "quick",
            "mode": "PRACTICE",
            "subject": "Mathematics",
            "topics": ["Simple Interest"],
            "count": 6,
        },
    )
    ids = [q["id"] for q in r.json()["questions"]]
    assert len(ids) == len(set(ids)) == 6


def test_custom_practice_conflicts_with_weak_topics(client):
    r = client.post(
        "/api/attempts",
        json={
            "config_id": "quick",
            "mode": "PRACTICE",
            "subject": "Mathematics",
            "weak_topics": True,
        },
    )
    assert r.status_code == 422


def test_custom_practice_gives_immediate_feedback_and_explanation(client):
    a = client.post(
        "/api/attempts",
        json={
            "config_id": "quick",
            "mode": "PRACTICE",
            "subject": "Mathematics",
            "topics": ["Simple Interest"],
            "count": 3,
        },
    ).json()
    q = a["questions"][0]
    r = client.put(
        f"/api/attempts/{a['id']}/answers/{q['id']}", json={"selected": "A"}
    ).json()
    assert r["feedback"]["explanation"]
    assert "correct" in r["feedback"]


def test_topics_endpoint_lists_active_topics_by_subject(client):
    data = client.get("/api/topics").json()
    assert "Simple Interest" in data.get("Mathematics", [])


def test_regular_mock_test_config_flow_unaffected_by_custom_practice(client):
    # No subject/topic/difficulty/count/source_type set — must behave exactly
    # like the pre-Phase-3 config-driven flow (unrelated to custom practice).
    a = start(client, "PRACTICE", "quick")
    assert len(a["questions"]) == 10
    assert a["name"] != "" and not a["name"].startswith("Custom practice")


# ---------------------------------------------------------------------------
# Phase 4: CBT mock test state transitions (palette, mark/clear, session
# stability across "refresh", concurrent-tab conflict). The underlying quota
# engine, palette and scoring already worked (see Phase 1 audit) — these
# tests verify the state transitions rather than rebuild anything.
# ---------------------------------------------------------------------------


def test_mark_for_review_then_clear_response_updates_state(client):
    a = start(client, "EXAM")
    qid = a["questions"][0]["id"]
    client.put(
        f"/api/attempts/{a['id']}/answers/{qid}",
        json={"selected": "A", "marked": True},
    )
    mid = client.get(f"/api/attempts/{a['id']}").json()
    assert mid["answers"][qid]["selected"] == "A"
    assert mid["answers"][qid]["marked"] is True
    client.put(
        f"/api/attempts/{a['id']}/answers/{qid}",
        json={"selected": None, "marked": False},
    )
    cleared = client.get(f"/api/attempts/{a['id']}").json()
    assert cleared["answers"][qid]["selected"] is None
    assert cleared["answers"][qid]["marked"] is False


def test_refresh_does_not_lose_in_progress_session(client):
    a = start(client, "EXAM")
    qid = a["questions"][0]["id"]
    client.put(f"/api/attempts/{a['id']}/answers/{qid}", json={"selected": "B"})
    first = client.get(f"/api/attempts/{a['id']}").json()
    second = client.get(f"/api/attempts/{a['id']}").json()
    assert first["id"] == second["id"] == a["id"]
    assert first["status"] == second["status"] == "IN_PROGRESS"
    assert first["deadline"] == second["deadline"]
    assert [q["id"] for q in first["questions"]] == [
        q["id"] for q in second["questions"]
    ]
    assert second["answers"][qid]["selected"] == "B"


def test_concurrent_tab_version_conflict_is_rejected(client):
    # Each HTTP request re-reads the attempt fresh, so the race window
    # lock_attempt() actually protects is between two requests that both
    # read the same version before either one writes. Reproduce that
    # directly rather than mutating the DB version out from under a client
    # that never read it (which every real request already tolerates).
    from backend.app.engine import get_attempt, lock_attempt

    a = start(client, "EXAM")
    with Session() as s1:
        stale = get_attempt(s1, a["id"], "local-developer")
    with Session() as s2:
        fresh = get_attempt(s2, a["id"], "local-developer")
        lock_attempt(s2, fresh)  # a concurrent "tab" writes first
        s2.commit()
    with Session() as s3:
        with pytest.raises(HTTPException) as exc:
            lock_attempt(s3, stale)
        assert exc.value.status_code == 409







