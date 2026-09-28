> **Verified foundation required:** PYQ-pattern generation requires a reviewed actual PYQ mapped to the official syllabus. MATCHED/HARDER drafts retain source lineage and require alignment checks plus human approval. Original challenges do not satisfy this requirement.

> **Exam preparation update:** The 190 starter questions remain Basic Practice. The official CEN 02/2025 syllabus is mapped; 20 original patterns and 2 supplementary examples are added, with source/coverage and duplicate-review views. See [MATERIAL_REPORT.md](MATERIAL_REPORT.md) for limits and [EXAM_PREPARATION.md](EXAM_PREPARATION.md) for safe Windows upgrade steps.

# SignalPrep — RRB Technician Grade-I Signal

A runnable React/TypeScript + FastAPI preparation application built around a persistent question bank. Includes Supabase/PostgreSQL migrations, Supabase Auth integration, server-side CBT generation/scoring, original seed questions, and a provider-neutral AI draft/review workflow.

## Delivery status — read first

The local application is implemented and tested. The hosted Sites frontend is an **explicit preview until you connect a deployed FastAPI backend**. It can browse 190 original educational questions and run an unsaved 10-question sample without credentials. It does not pretend to save accounts or results.

Production activation requires your Supabase project/database connection, a deployed FastAPI service, and optional AI credentials. Live Supabase login, PostgreSQL migration execution, and real AI-provider generation were not end-to-end tested because no external project or credentials were supplied. This is not a claim of a fully commissioned or security-audited production service.

The default exam distribution follows the supplied specification (100 questions, 90 minutes, 35/20/20/15/10 and −1/3 wrong). It is configurable, not a certification of any current RRB notification. Check the applicable official notification before publication.

Seed questions are **ORIGINAL**, not real PYQs. There are no verified PYQs bundled. They are introductory educational material, including deterministic numerical variants. Difficulty labels are initial editorial labels; obtain subject-expert review and calibration before advertising them as hard exam-standard questions. The bank is not comprehensive syllabus coverage.

## Windows quick start (PowerShell)

Install Python 3.12 or 3.13 and Node.js 24 first. Extract the project, then open a terminal in the `rrb-signal-mock` folder. Keep both terminals running.

Terminal 1 — backend:

```powershell
cd "C:\Users\mamil\Downloads\rrb-signal-mock"
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Using the venv's Python directly avoids PowerShell activation-policy problems. The first launch creates `signalprep.db` and seeds 190 questions plus full/quick test configurations. Development mode signs you in as a **local-only administrator**. Do not run this mode on a publicly accessible host.

Terminal 2 — frontend:

```powershell
cd "C:\Users\mamil\Downloads\rrb-signal-mock"
npx --yes pnpm@11.25.0 install --frozen-lockfile
npx --yes pnpm@11.25.0 dev
```

Open **http://localhost:5173**. If the app says Preview, open **Settings & connection**, enter **http://127.0.0.1:8000**, and press **Test & connect**. The API documentation is at **http://127.0.0.1:8000/docs**.

Start with **Mock Tests → Practice mode** for immediate feedback, or **Exam mode** for hidden answers. Admin tools are in Question Bank, AI Generator, Admin Review, and Settings.

Tests:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
npx --yes pnpm@11.25.0 exec tsc --noEmit
npx --yes pnpm@11.25.0 build
```

The tests use an isolated temporary SQLite database, not your local history. Do not remove `signalprep.db` if you want to retain your local data. Back it up while the backend is stopped.

## Project map

```text
app/                         React app routing, layout and API proxy
frontend/src/                Dashboard, CBT, admin UI and API client
components/ui/               Accessible shared interface primitives
backend/app/
  main.py                    REST endpoints and request orchestration
  auth.py                    Supabase user validation and admin authorization
  db.py                      SQLAlchemy models and session management
  schemas.py                 Typed input validation
  engine.py                  Attempts, scoring, expiry and analytics
  flow.py                    Exact quota selection with exposure preference
  quality.py                 Arithmetic and duplicate checks
  ai.py                      Provider adapters and generation stages
  seed.py                    190 original questions
backend/tests/               API regression suite
supabase/migrations/         PostgreSQL schema, constraints and RLS
supabase/seed.sql             Idempotent original question/config seed
question_bank/templates/     CSV import template
backend/Dockerfile           Backend production image
Dockerfile.frontend          Self-contained frontend Worker server image
docker-compose.yml           Local persistent API container
.env.example                 Configuration template
DEPLOYMENT.md                Production setup and smoke tests
VALIDATION.md                Tests performed and boundaries
```

The root retains the Sites-compatible React/Vinext framework configuration. Product frontend code lives in `frontend/src`; backend and database responsibilities are separate. React, TypeScript, Tailwind and accessible Radix-based components are used. No unrelated existing project was overwritten.

## How the platform behaves

- The bank is canonical; tests select only ACTIVE questions. All selected IDs, order, question snapshots and scoring policy persist with the attempt.
- Subject, source and difficulty totals are exact (percentage weights use largest-remainder rounding). The bounded quota solver fails with a descriptive 409 when inventory is insufficient. Cooldown is a soft preference and does not permanently exclude questions. Concept diversity is preferred within each feasible group.
- Defaults use ORIGINAL=100 because the starter has no verified PYQs. Admin can change source weights once reviewed source inventory exists.
- Practice answers return feedback immediately. Exam endpoints omit keys, explanations and generation metadata until submission. Practice scores use final selections and may therefore reflect corrections after feedback; practice is excluded from exam-readiness analytics.
- Scores are +1 correct, −1/3 wrong, 0 blank by default. Marked answered questions count normally. Configuration snapshots prevent later admin edits changing an in-progress test.
- The server controls deadlines. Expired attempts finalize when accessed or answered; the visible client auto-submits at zero. A background scheduler is not required for score integrity, but an unopened abandoned attempt is finalized lazily on its next access.
- Optimistic version updates serialize answer/submission changes. Concurrent-tab conflicts return 409 and require reloading the attempt. Resume is available in Recent activity and Mock Tests.
- Analytics report subjects/topics, history and weak topics. Weak requires at least 5 attempted questions across 2 EXAM attempts and accuracy below 60%. Weak-topic tests select up to 20 active questions; extra AI variations enter only after normal admin review.
- Bookmarks and exposure are user-specific. The temporary preview is memory-only and is never mixed into account history.
- Admin can search/filter, create/edit, copy a draft, preview, approve/reject/archive, import CSV and request similar/harder/easier questions. Editing returns a question to pending review.
- A claimed PYQ import is stored as PYQ_PATTERN plus claimed-source metadata until an administrator explicitly verifies its reference/year. Only then is source_type changed to PYQ. A model can never request PYQ generation.
- CSV files are UTF-8, maximum 2 MB / 1,000 rows. Imports report imported, duplicate, invalid and total rejected rows. Blank optional values are accepted. The template contains an existing seed example, so reimporting the unchanged example correctly reports a duplicate.
- All account administration is server-controlled. Users cannot promote themselves. An administrator is assigned by the database owner as documented in DEPLOYMENT.md.

## AI configuration and limits

Set in the backend `.env`:

```dotenv
AI_PROVIDER=openai-compatible
AI_MODEL=your-model-name
AI_API_KEY=your-provider-secret
AI_BASE_URL=https://your-provider.example/v1
```

Supported adapters: `openai`, `openai-compatible`, `anthropic`. The compatible provider must implement chat completions and JSON output. Anthropic uses its messages endpoint. Provider names/model IDs are configuration, not hard-coded product behavior. Keys never enter the frontend.

The agent extracts concept/structure/formula/traps, generates new reasoning variants and explanations, performs bounded arithmetic checks when a numeric proof is supplied, detects exact/near duplicates, and asks for an independent model answer. All generated items remain PENDING_REVIEW. Review notes are mandatory for activation.

Arithmetic verification only verifies the supplied expression and numeric option values; it cannot establish that the physical model/formula is appropriate or that the provider faithfully mapped every visible option. Conceptual answers are not independently grounded in a comprehensive trusted reference corpus. The UI lists these human-review requirements. A second model response is an additional check, not proof of correctness.

Generation is synchronous, capped at 20 questions/job and 10 jobs/admin/hour, with persisted job records. PostgreSQL serializes rate-limit reservations across workers. There is no durable job queue/retry worker; a process interruption may leave a RUNNING job for operator inspection. Use a background worker before high-volume generation. Provider failures return explicit errors and never activate questions.

## Separate prototype practice session

The uploaded specification records “Hard Practice CBT 01”: **9/20 completed, next Q21**. That session was not imported into the production question bank, reset, or resumed. Its original Q1–Q20 content was not supplied, so this application does not invent those answers or claim to reproduce its saved history. Preserve that separate session and resume it from Q21 when continuing it.
