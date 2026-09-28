> **Verified-foundation policy:** Actual source-verified, reviewed and syllabus-mapped PYQs are required before generating PYQ_PATTERN content. MATCHED uses the parent difficulty; HARDER requests a harder within-syllabus variation. Every draft stores its parent snapshot, concept/trap/style analysis, alignment check and syllabus mapping. It remains pending until human review. The 20 syllabus-authored challenges are retained but excluded from PYQ-matched exam coverage. All 75 units currently lack a verified foundation; full-syllabus generation is blocked until those gaps are filled.

# Exam preparation update

The 190 ORIGINAL starter items remain basic concept practice. Their difficulty labels are initial editorial labels, not evidence of exam-level difficulty. They do not establish complete syllabus coverage.

Select **EXAM** and configuration **exam-prep** for the new preparation track. Its initial configurable mix is 50 verified PYQs and 50 hard PYQ-pattern questions, all labelled Hard. This is a practice preference, not a claim about the official exam's difficulty distribution. Timed basic tests remain available under grade1 / quick and are excluded from readiness analytics.

## Source and syllabus upgrade

See MATERIAL_REPORT.md for obtained materials, extraction counts and coverage. The official CEN 02/2025 Grade-I Signal syllabus is now mapped into 75 checklist units. The app separates 190 Basic Practice questions, 20 original challenge patterns, 2 short supplementary examples and verified PYQs (none newly obtained). A 200-record external inspection index is not counted as an imported bank.

Open **Exam Preparation** for the source register and live coverage. Select **Hard patterns** for a 10-question session once sufficient verified-foundation patterns are approved, or **Supplementary** for the one ready unverified example (the second is withheld for a key conflict). Neither is presented as an actual official paper. The full exam-prep mix remains blocked until its verified-PYQ quota can be satisfied.

Original pattern answers have been checked during authoring, with arithmetic checks where supplied. Their difficulty remains provisional. Possible paraphrases are withheld until an administrator compares the flagged pair and records a decision. Review decisions and mappings can be managed in Exam Preparation and the Question Bank preview. A syllabus mapping can be added to imported questions without changing their content or historical snapshots.

## Non-repetition

exam-prep, hard-patterns and supplementary exclude every question ID already reserved in any saved attempt for the current account, including unfinished tests and practice. It also excludes identical normalized wording and simple number-substitution variants, both within a test and against historical snapshots. These conservative checks can exclude legitimate distinct items; they cannot detect every semantic paraphrase. Reviewers must also check near-duplicates. Repeated concepts are allowed; reusing the same question is not.

Insufficient eligible inventory returns an explicit error, without falling back to starter questions or recycling used items. Restarting the backend does not reset reservations. Deleting the database, deleting history, or using another account loses that protection. Concurrent starts serialize through a database write lock.

## Windows update, preserving your work

1. Stop the frontend and backend using Ctrl+C in their terminals.
2. Make a backup copy of your existing project folder, especially signalprep.db and your .env file.
3. Extract this ZIP to a separate folder. Copy its contents into your existing project folder, replacing matching source files. It contains no database, .env, .venv or node_modules. Keep those existing files/folders.
4. In your existing project folder run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

In a second PowerShell window in the same folder:

```powershell
npx.cmd --yes pnpm@11.25.0 install --frozen-lockfile
npx.cmd --yes pnpm@11.25.0 dev
```

Connect the local UI to http://127.0.0.1:8000. Development startup adds exam-prep idempotently and preserves questions, attempts and snapshots. SQLite requires no schema change. PostgreSQL/Supabase deployments must first apply supabase/migrations/002_supplementary_source.sql, then run the seed module explicitly after backing up their database; development auto-seeding is disabled in production. The hosted frontend does not run the Python backend.
