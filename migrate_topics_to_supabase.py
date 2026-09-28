import sqlite3
import os
import psycopg

SQLITE_DB = "signalprep.db"

# ---------------------------------------
# Load local topics
# ---------------------------------------

sqlite_conn = sqlite3.connect(SQLITE_DB)

local_topics = sqlite_conn.execute("""
    SELECT id, subject, name
    FROM question_topics
    ORDER BY id
""").fetchall()

sqlite_conn.close()

print()
print("===== SAFE TOPIC MIGRATION =====")
print(f"Local topics:             {len(local_topics)}")

if len(local_topics) != 182:
    raise RuntimeError(
        f"SAFETY STOP: Expected 182 local topics, found {len(local_topics)}."
    )

# ---------------------------------------
# Connect to Supabase
# ---------------------------------------

pg_conn = psycopg.connect(os.environ["SUPABASE_DB_URL"])

try:

    with pg_conn.transaction():

        with pg_conn.cursor() as cur:

            # ---------------------------------------
            # Read existing Supabase topics
            # ---------------------------------------

            cur.execute("""
                SELECT id, subject, name
                FROM public.question_topics
            """)

            remote_topics = cur.fetchall()

            before_count = len(remote_topics)

            print(f"Supabase topics before:   {before_count}")

            # ---------------------------------------
            # Build subject/name lookup
            # ---------------------------------------

            remote_by_name = {
                (row[1], row[2]): row[0]
                for row in remote_topics
            }

            local_keys = {
                (row[1], row[2])
                for row in local_topics
            }

            # ---------------------------------------
            # Determine matches and missing topics
            # ---------------------------------------

            matched = []
            missing = []

            for local_id, subject, name in local_topics:

                key = (subject, name)

                if key in remote_by_name:
                    matched.append(
                        (local_id, subject, name, remote_by_name[key])
                    )
                else:
                    missing.append(
                        (local_id, subject, name)
                    )

            print(f"Topics matched by name:   {len(matched)}")
            print(f"Topics needing insertion: {len(missing)}")

            # ---------------------------------------
            # Insert only genuinely new topics
            # ---------------------------------------

            if missing:

                insert_sql = """
                    INSERT INTO public.question_topics
                        (id, subject, name)
                    VALUES
                        (%s, %s, %s)
                """

                print("Inserting new topics...")

                cur.executemany(insert_sql, missing)

            # ---------------------------------------
            # Verify final topic count
            # ---------------------------------------

            cur.execute("""
                SELECT COUNT(*)
                FROM public.question_topics
            """)

            after_count = cur.fetchone()[0]

            expected_count = before_count + len(missing)

            print(f"Supabase topics after:    {after_count}")

            if after_count != expected_count:
                raise RuntimeError(
                    f"SAFETY STOP: Expected {expected_count} topics, "
                    f"found {after_count}."
                )

            # ---------------------------------------
            # Re-read topics and verify every local
            # subject/name has a Supabase topic
            # ---------------------------------------

            cur.execute("""
                SELECT id, subject, name
                FROM public.question_topics
            """)

            final_topics = cur.fetchall()

            final_by_name = {
                (row[1], row[2]): row[0]
                for row in final_topics
            }

            unresolved = []

            for local_id, subject, name in local_topics:

                if (subject, name) not in final_by_name:
                    unresolved.append(
                        (local_id, subject, name)
                    )

            if unresolved:
                raise RuntimeError(
                    f"SAFETY STOP: {len(unresolved)} local topics "
                    "could not be mapped to Supabase."
                )

            print()
            print("All topic mapping checks passed.")
            print("Committing transaction...")

    print()
    print("==============================================")
    print("? TOPIC MIGRATION COMPLETED")
    print("==============================================")
    print(f"Local topics:             {len(local_topics)}")
    print(f"Matched existing topics:  {len(matched)}")
    print(f"New topics inserted:      {len(missing)}")
    print(f"Supabase final topics:    {after_count}")
    print("Unresolved topics:        0")
    print("==============================================")

except Exception as error:

    print()
    print("==============================================")
    print("? TOPIC MIGRATION FAILED")
    print("==============================================")
    print(str(error))
    print()
    print("Transaction rolled back.")
    print("==============================================")

finally:
    pg_conn.close()
