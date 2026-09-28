import os
import psycopg

conn = psycopg.connect(os.environ["SUPABASE_DB_URL"])
cur = conn.cursor()

cur.execute("""
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'questions'
ORDER BY ordinal_position
""")

print("SUPABASE QUESTIONS SCHEMA:")
for row in cur.fetchall():
    print(f"{row[0]} | {row[1]}")

cur.close()
conn.close()
