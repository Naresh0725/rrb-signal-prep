import sqlite3
import os
import psycopg

# Local SQLite
sqlite_conn = sqlite3.connect("signalprep.db")
sqlite_cur = sqlite_conn.cursor()

sqlite_cur.execute("SELECT id FROM questions")
local_ids = {row[0] for row in sqlite_cur.fetchall()}

sqlite_cur.execute("SELECT COUNT(*) FROM questions")
local_count = sqlite_cur.fetchone()[0]

sqlite_conn.close()

# Supabase PostgreSQL
pg_conn = psycopg.connect(os.environ["SUPABASE_DB_URL"])
pg_cur = pg_conn.cursor()

pg_cur.execute("SELECT id FROM public.questions")
supabase_ids = {row[0] for row in pg_cur.fetchall()}

pg_cur.execute("SELECT COUNT(*) FROM public.questions")
supabase_count = pg_cur.fetchone()[0]

pg_cur.close()
pg_conn.close()

common = local_ids & supabase_ids
local_only = local_ids - supabase_ids
supabase_only = supabase_ids - local_ids

print()
print("===== QUESTION DATABASE COMPARISON =====")
print(f"Local questions:              {local_count}")
print(f"Supabase questions:           {supabase_count}")
print(f"IDs existing in both:        {len(common)}")
print(f"IDs only in local DB:         {len(local_only)}")
print(f"IDs only in Supabase:         {len(supabase_only)}")
print("========================================")
print()

if local_only:
    print("LOCAL-ONLY QUESTION IDs:")
    for qid in sorted(local_only):
        print(qid)

if supabase_only:
    print()
    print("SUPABASE-ONLY QUESTION IDs:")
    for qid in sorted(supabase_only):
        print(qid)
