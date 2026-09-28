import re, ast, operator, math, unicodedata
from difflib import SequenceMatcher
from sqlalchemy import select
from .db import Question


def normalized(s):
    return re.sub(
        r"[^\w√+*/=−^.-]+", " ", unicodedata.normalize("NFKC", s).casefold()
    ).strip()


def detect_duplicate(session, text, exclude=None):
    n = normalized(text)
    for q in session.scalars(select(Question)):
        if q.id == exclude:
            continue
        old = normalized(q.question_text)
        if old == n:
            return {"id": q.id, "kind": "exact", "similarity": 1}
        ratio = SequenceMatcher(None, n, old).ratio()
        if ratio >= 0.91:
            return {"id": q.id, "kind": "near", "similarity": round(ratio, 3)}
    return None


OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def calculate(expression):
    if len(expression) > 200:
        raise ValueError("Expression too long")

    def visit(n):
        if isinstance(n, ast.Constant) and type(n.value) in (int, float):
            return n.value
        if isinstance(n, ast.UnaryOp) and type(n.op) in OPS:
            return OPS[type(n.op)](visit(n.operand))
        if isinstance(n, ast.BinOp) and type(n.op) in OPS:
            a, b = visit(n.left), visit(n.right)
            if isinstance(n.op, ast.Pow) and (abs(b) > 10 or abs(a) > 1e10):
                raise ValueError("Exponent too large")
            v = OPS[type(n.op)](a, b)
            if not math.isfinite(v) or abs(v) > 1e15:
                raise ValueError("Out of bounds")
            return v
        raise ValueError("Only arithmetic is supported")

    return visit(ast.parse(expression, mode="eval").body)


def extract_number(text):
    # Best-effort: the last standalone number in a piece of text (e.g. the
    # result of a worked calculation, or a final answer like "45 W").
    if not text:
        return None
    matches = re.findall(r"-?\d+(?:\.\d+)?", text)
    return float(matches[-1]) if matches else None


def validate_structured_explanation(q):
    # Best-effort, non-blocking-by-default checks for the optional structured
    # explanation fields. Never required: conceptual questions may leave every
    # field here empty.
    issues = []
    if q.get("why_wrong") and q.get("correct_option") in q["why_wrong"]:
        issues.append("why_wrong must not explain the correct option")
    calc, final = q.get("calculation"), q.get("final_answer")
    if calc and final:
        a, b = extract_number(calc), extract_number(final)
        if a is not None and b is not None and abs(a - b) > max(1e-6, abs(b) * 1e-3):
            issues.append("final_answer does not match the last number in calculation")
    if calc and not final:
        issues.append("calculation is given but final_answer is missing")
    return issues


def validate_question(q, session=None, exclude=None, verification=None):
    issues = []
    opts = [q["option_" + k.lower()] for k in "ABCD"]
    issues += validate_structured_explanation(q)
    if len(set(normalized(x) for x in opts)) != 4:
        issues.append("Options must be distinct")
    if q["source_type"] == "PYQ" and (
        not q.get("source_reference") or not q.get("exam_year")
    ):
        issues.append("PYQ needs reference and exam year")
    if q["source_type"] == "PYQ_PATTERN" and not (
        q.get("parent_question_id") or q.get("source_reference")
    ):
        issues.append("Pattern needs parent or concept reference")
    if session:
        dup = detect_duplicate(session, q["question_text"], exclude)
        if dup:
            issues.append(f"{dup['kind']} duplicate: {dup['id']}")
    computed = None
    if verification:
        try:
            computed = calculate(verification["expression"])
            values = verification["option_values"]
            hits = [
                k
                for k, v in values.items()
                if math.isclose(float(v), computed, rel_tol=1e-6, abs_tol=1e-8)
            ]
            if len(hits) != 1 or hits[0] != q["correct_option"]:
                issues.append("Numerical answer check failed")
        except (
            ValueError,
            KeyError,
            TypeError,
            ZeroDivisionError,
            OverflowError,
            SyntaxError,
        ):
            issues.append("Numerical proof is invalid")
    return {
        "issues": issues,
        "arithmetic_result": computed,
        "requires_human_review": True,
        "checks": ["structure", "distinct options", "exact/near duplication"],
        "manual_checks": [
            "formula validity",
            "syllabus relevance",
            "difficulty",
            "explanation consistency",
            "ambiguity",
            "conceptual reference",
            "structured explanation clarity",
        ],
    }
