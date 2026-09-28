import sqlite3
import os
import json
import psycopg
from psycopg.types.json import Json

SQLITE_DB = "signalprep.db"

COLUMNS = [
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

JSON_COLUMNS = {
    "why_wrong",
    "generation_metadata",
}


def parse_json(value):
    if value is None:
        return None

    if isinstance(value, (dict, list)):
        return value

    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception as error:
            raise RuntimeError(
                f"Invalid JSON value: {value[:100]}"
            ) from error

    return value


# =========================================================
# 1. Load local database
# =========================================================

sqlite_conn = sqlite3.connect(SQLITE_DB)
sqlite_conn.row_factory = sqlite3.Row

rows = sqlite_conn.execute(
    f"SELECT {', '.join(COLUMNS)} FROM questions"
).fetchall()

local_topics = sqlite_conn.execute("""
    SELECT id, subject, name
    FROM question_topics
    ORDER BY subject, name
""").fetchall()

sqlite_conn.close()

print()
print("===== SIGNALPREP QUESTION MIGRATION =====")
print(f"Local questions:          {len(rows)}")
print(f"Local topics:             {len(local_topics)}")

if len(rows) != 432:
    raise RuntimeError(
        f"SAFETY STOP: Expected 432 local questions, found {len(rows)}."
    )

if len(local_topics) == 0:
    raise RuntimeError(
        "SAFETY STOP: No local topics found."
    )


# =========================================================
# 2. Connect to Supabase
# =========================================================

pg_conn = psycopg.connect(os.environ["SUPABASE_DB_URL"])

try:

    with pg_conn.transaction():

        with pg_conn.cursor() as cur:

            # =================================================
            # 3. Load existing Supabase topics
            # =================================================

            cur.execute("""
                SELECT id, subject, name
                FROM public.question_topics
            """)

            supabase_topics = cur.fetchall()

            print(f"Supabase topics before: {len(supabase_topics)}")

            supabase_by_name = {
                (row[1], row[2]): row[0]
                for row in supabase_topics
            }

            # =================================================
            # 4. Insert missing topics
            # =================================================

            missing_topics = []

            for topic in local_topics:
                key = (topic["subject"], topic["name"])

                if key not in supabase_by_name:
                    missing_topics.append(topic)

            print(f"Missing Supabase topics: {len(missing_topics)}")

            if missing_topics:
                for topic in missing_topics:
                    cur.execute(
                        """
                        INSERT INTO public.question_topics
                            (id, subject, name)
                        VALUES
                            (%s, %s, %s)
                        ON CONFLICT (subject, name)
                        DO NOTHING
                        RETURNING id
                        """,
                        (
                            topic["id"],
                            topic["subject"],
                            topic["name"],
                        ),
                    )

                    inserted = cur.fetchone()

                    if inserted:
                        supabase_by_name[
                            (topic["subject"], topic["name"])
                        ] = inserted[0]
                    else:
                        # Another ID already exists for this subject/name.
                        cur.execute(
                            """
                            SELECT id
                            FROM public.question_topics
                            WHERE subject = %s
                              AND name = %s
                            """,
                            (
                                topic["subject"],
                                topic["name"],
                            ),
                        )

                        existing = cur.fetchone()

                        if not existing:
                            raise RuntimeError(
                                f"SAFETY STOP: Could not resolve topic "
                                f"{topic['subject']} / {topic['name']}"
                            )

                        supabase_by_name[
                            (topic["subject"], topic["name"])
                        ] = existing[0]

            # =================================================
            # 5. Rebuild local -> Supabase topic ID mapping
            # =================================================

            local_topic_map = {}

            for topic in local_topics:
                key = (topic["subject"], topic["name"])

                if key not in supabase_by_name:
                    raise RuntimeError(
                        f"SAFETY STOP: Missing Supabase topic mapping "
                        f"for {topic['subject']} / {topic['name']}"
                    )

                local_topic_map[topic["id"]] = supabase_by_name[key]

            print(
                f"Topic ID mappings created: {len(local_topic_map)}"
            )

            # =================================================
            # 6. Verify all local questions have mapped topics
            # =================================================

            mapped_count = 0

            for row in rows:
                local_topic_id = row["topic_id"]

                if local_topic_id is None:
                    raise RuntimeError(
                        f"SAFETY STOP: Question {row['id']} "
                        f"has NULL topic_id."
                    )

                if local_topic_id not in local_topic_map:
                    raise RuntimeError(
                        f"SAFETY STOP: Question {row['id']} references "
                        f"unknown local topic_id {local_topic_id}."
                    )

                mapped_count += 1

            print(
                f"Questions with mapped topic IDs: {mapped_count}"
            )

            if mapped_count != len(rows):
                raise RuntimeError(
                    "SAFETY STOP: Not all questions have mapped topics."
                )

            # =================================================
            # 7. Count existing questions
            # =================================================

            cur.execute("""
                SELECT COUNT(*)
                FROM public.questions
            """)

            before_count = cur.fetchone()[0]

            print(
                f"Supabase questions before: {before_count}"
            )

            # =================================================
            # 8. Prepare question UPSERT
            # =================================================

            placeholders = ", ".join(["%s"] * len(COLUMNS))

            update_columns = [
                column
                for column in COLUMNS
                if column != "id"
            ]

            update_clause = ", ".join(
                f"{column} = EXCLUDED.{column}"
                for column in update_columns
            )

            question_sql = f"""
                INSERT INTO public.questions (
                    {", ".join(COLUMNS)}
                )
                VALUES (
                    {placeholders}
                )
                ON CONFLICT (id)
                DO UPDATE SET
                    {update_clause}
            """

            print(
                f"Uploading/updating {len(rows)} questions..."
            )

            values = []

            for row in rows:

                row_values = []

                for column in COLUMNS:

                    value = row[column]

                    if column == "topic_id":
                        value = local_topic_map[value]

                    elif column in JSON_COLUMNS:
                        value = parse_json(value)

                        if value is not None:
                            value = Json(value)

                    row_values.append(value)

                values.append(row_values)

            # =================================================
            # 9. Upload all questions
            # =================================================

            cur.executemany(
                question_sql,
                values,
            )

            print("Question upsert completed.")

            # =================================================
            # 10. Verify final question count
            # =================================================

            cur.execute("""
                SELECT COUNT(*)
                FROM public.questions
            """)

            after_count = cur.fetchone()[0]

            print(
                f"Supabase questions after:  {after_count}"
            )

            if after_count != len(rows):
                raise RuntimeError(
                    f"SAFETY STOP: Expected {len(rows)} Supabase "
                    f"questions, found {after_count}."
                )

            # =================================================
            # 11. Verify every local question exists
            # =================================================

            local_ids = [row["id"] for row in rows]

            cur.execute(
                """
                SELECT COUNT(*)
                FROM public.questions
                WHERE id = ANY(%s)
                """,
                (local_ids,),
            )

            matching_count = cur.fetchone()[0]

            print(
                f"Local question IDs found in Supabase: "
                f"{matching_count}"
            )

            if matching_count != len(rows):
                raise RuntimeError(
                    "SAFETY STOP: Not all local question IDs "
                    "exist in Supabase."
                )

            # =================================================
            # 12. Verify no migrated questions have NULL topic
            # =================================================

            cur.execute(
                """
                SELECT COUNT(*)
                FROM public.questions
                WHERE id = ANY(%s)
                  AND topic_id IS NULL
                """,
                (local_ids,),
            )

            null_topic_count = cur.fetchone()[0]

            print(
                f"Migrated questions with NULL topic_id: "
                f"{null_topic_count}"
            )

            if null_topic_count != 0:
                raise RuntimeError(
                    "SAFETY STOP: Some migrated questions "
                    "have NULL topic_id."
                )

            # =================================================
            # 13. Verify structured explanation fields
            # =================================================

            cur.execute(
                """
                SELECT
                    COUNT(*) FILTER (WHERE concept IS NOT NULL),
                    COUNT(*) FILTER (WHERE formula IS NOT NULL),
                    COUNT(*) FILTER (WHERE given IS NOT NULL),
                    COUNT(*) FILTER (WHERE calculation IS NOT NULL),
                    COUNT(*) FILTER (WHERE final_answer IS NOT NULL),
                    COUNT(*) FILTER (WHERE why_correct IS NOT NULL),
                    COUNT(*) FILTER (WHERE why_wrong IS NOT NULL)
                FROM public.questions
                WHERE id = ANY(%s)
                """,
                (local_ids,),
            )

            structured_counts = cur.fetchone()

            print()
            print("Structured explanation fields:")
            print(f"  concept:      {structured_counts[0]}")
            print(f"  formula:      {structured_counts[1]}")
            print(f"  given:        {structured_counts[2]}")
            print(f"  calculation:  {structured_counts[3]}")
            print(f"  final_answer: {structured_counts[4]}")
            print(f"  why_correct:  {structured_counts[5]}")
            print(f"  why_wrong:    {structured_counts[6]}")

            # =================================================
            # 14. Final topic count
            # =================================================

            cur.execute("""
                SELECT COUNT(*)
                FROM public.question_topics
            """)

            final_topic_count = cur.fetchone()[0]

            print()
            print(
                f"Supabase topics after:    {final_topic_count}"
            )

            print()
            print("==============================================")
            print("QUESTION MIGRATION SUCCESS")
            print("==============================================")
            print(
                f"Questions migrated: {after_count}"
            )
            print(
                f"Topics available:   {final_topic_count}"
            )
            print(
                "All questions have valid topic mappings."
            )
            print(
                "Structured explanation fields verified."
            )
            print("==============================================")

finally:
    pg_conn.close()
