import sqlite3
import os
import psycopg

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

# Pick one known common question
question_id = "seed-0001"

# SQLite
sqlite_conn = sqlite3.connect("signalprep.db")
sqlite_conn.row_factory = sqlite3.Row
local = sqlite_conn.execute(
    f"SELECT {column_sql} FROM questions WHERE id = ?",
    (question_id,)
).fetchone()
sqlite_conn.close()

# Supabase
pg_conn = psycopg.connect(os.environ["SUPABASE_DB_URL"])
pg_cur = pg_conn.cursor()
pg_cur.execute(
    f"SELECT {column_sql} FROM public.questions WHERE id = %s",
    (question_id,)
)
remote = pg_cur.fetchone()
pg_cur.close()
pg_conn.close()

print()
print("===== FIRST QUESTION DIFFERENCE CHECK =====")
print(f"Question ID: {question_id}")
print()

differences = 0

for column, local_value, remote_value in zip(columns, local, remote):

    # Normalize JSON values so we compare their actual data,
    # rather than SQLite string formatting vs PostgreSQL JSON objects.
    if column in ("why_wrong", "generation_metadata"):
        import json

        def normalize(value):
            if value is None:
                return None
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except Exception:
                    return value
            return value

        local_value = normalize(local_value)
        remote_value = normalize(remote_value)

    if local_value != remote_value:
        differences += 1
        print(f"DIFFERENT COLUMN: {column}")
        print(f"  LOCAL:    {local_value!r}")
        print(f"  SUPABASE: {remote_value!r}")
        print()

print("-------------------------------------------")
print(f"Different columns: {differences}")

if differences == 0:
    print("? seed-0001 is actually identical after JSON normalization.")
else:
    print("?? There are genuine field differences to investigate.")
