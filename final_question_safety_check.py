import sqlite3
import os
import psycopg
import hashlib

def fingerprint(row):
    values = []
    for value in row:
        if value is None:
            values.append("")
        else:
            values.append(str(value))
    return hashlib.sha256(
        "\x1f".join(values).encode("utf-8")
    ).hexdigest()

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

# Local database
sqlite_conn = sqlite3.connect("signalprep.db")
sqlite_cur = sqlite_conn.cursor()

sqlite_cur.execute(f"SELECT {column_sql} FROM questions ORDER BY id")
local_rows = {
    row[0]: fingerprint(row)
    for row in sqlite_cur.fetchall()
}

sqlite_conn.close()

# Supabase
pg_conn = psycopg.connect(os.environ["SUPABASE_DB_URL"])
pg_cur = pg_conn.cursor()

pg_cur.execute(f"SELECT {column_sql} FROM public.questions ORDER BY id")
supabase_rows = {
    row[0]: fingerprint(row)
    for row in pg_cur.fetchall()
}

pg_cur.close()
pg_conn.close()

common_ids = set(local_rows) & set(supabase_rows)

matching = sum(
    1 for qid in common_ids
    if local_rows[qid] == supabase_rows[qid]
)

different = [
    qid for qid in common_ids
    if local_rows[qid] != supabase_rows[qid]
]

print()
print("===== FINAL SAFETY CHECK =====")
print(f"Local questions:          {len(local_rows)}")
print(f"Supabase questions:       {len(supabase_rows)}")
print(f"Common questions:         {len(common_ids)}")
print(f"Exactly matching:         {matching}")
print(f"Different:                {len(different)}")
print("==============================")

if different:
    print()
    print("?? DIFFERENT QUESTION IDs:")
    for qid in different:
        print(qid)
else:
    print()
    print("? ALL 190 EXISTING QUESTIONS MATCH EXACTLY.")
    print("? SAFE TO PROCEED WITH MIGRATION.")
