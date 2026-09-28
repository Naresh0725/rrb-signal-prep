import sqlite3
import os
import psycopg
import json

columns = [
    "id",
    "question_text",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "correct_option",
    "explanation",
    "concept",
    "formula",
    "given",
    "calculation",
    "final_answer",
    "why_correct",
    "why_wrong",
    "subject",
    "topic",
    "subtopic",
    "topic_id",
    "source_id",
    "difficulty",
    "source_type",
    "source_reference",
    "verification_status",
    "exam",
    "exam_year",
    "shift",
    "parent_question_id",
    "generation_method",
    "generation_metadata",
    "status",
    "created_at",
    "updated_at",
]

column_sql = ", ".join(columns)

sqlite_conn = sqlite3.connect("signalprep.db")
sqlite_conn.row_factory = sqlite3.Row
local_rows = {
    row["id"]: dict(row)
    for row in sqlite_conn.execute(
        f"SELECT {column_sql} FROM questions"
    ).fetchall()
}
sqlite_conn.close()

pg_conn = psycopg.connect(os.environ["SUPABASE_DB_URL"])
pg_cur = pg_conn.cursor()
pg_cur.execute(f"SELECT {column_sql} FROM public.questions")
supabase_rows = {
    row[0]: dict(zip(columns, row))
    for row in pg_cur.fetchall()
}
pg_cur.close()
pg_conn.close()

common_ids = set(local_rows) & set(supabase_rows)

counts = {column: 0 for column in columns}

for qid in common_ids:
    local = local_rows[qid]
    remote = supabase_rows[qid]

    for column in columns:
        lv = local[column]
        rv = remote[column]

        if column in ("why_wrong", "generation_metadata"):
            if isinstance(lv, str):
                try:
                    lv = json.loads(lv)
                except Exception:
                    pass
            if isinstance(rv, str):
                try:
                    rv = json.loads(rv)
                except Exception:
                    pass

        if lv != rv:
            counts[column] += 1

print()
print("===== DIFFERENCE SUMMARY FOR 190 EXISTING QUESTIONS =====")
for column in columns:
    if counts[column]:
        print(f"{column}: {counts[column]}")
print("=========================================================")
