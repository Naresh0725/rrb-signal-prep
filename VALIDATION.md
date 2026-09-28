# Validation report

## Passed in this environment

- Backend: 14 pytest tests passed with an isolated SQLite database.
- TypeScript: `tsc --noEmit` passed.
- React/Vinext Worker production build passed.
- Browser: dashboard rendered; preview quick practice opened; correct selection returned explanation; wrong selection returned correct answer/explanation; marking updated the palette; Save & Next navigated; submission confirmation showed unanswered count; final result correctly reported 1 correct, 1 wrong, 8 unanswered and 0.67 points.
- API: a full 100-question attempt generated with exactly 35/20/20/15/10 subject counts and 30/50/20 difficulty counts; no duplicate IDs.
- API: exam answer responses withheld correctness and explanations; final submission released review data.
- API: stable question order on reload, immutable attempt snapshot after bank edits, negative marking, idempotent submission, prevention of post-submission changes, server expiry rejecting late answers, ownership isolation, student admin-access rejection, immediate practice feedback, impossible quota handling, safe arithmetic parsing, option uniqueness and AI-disabled behavior.
- CSV: unverified claimed PYQ imported as pending PYQ_PATTERN; activation required review notes; explicit source verification permitted promotion to PYQ; duplicate import detected.

## Not executed / remaining commissioning

- No Supabase project or provider credentials supplied: live email confirmation/login, real PostgreSQL migrations and RLS enforcement, and actual AI generation were not tested.
- Windows instructions target portable frontend scripts and direct venv Python execution, but no Windows host was available to execute them.
- No mobile-device browser or load/security audit was performed. CSS includes responsive breakpoints and accessible shared controls.
- WebMCP is feature-detected and a question-bank search tool is implemented; the available browser reported modelContext unavailable, so runtime WebMCP validation could not run.
- The hosted frontend has no deployed Python API configured; sample practice is deliberately unsaved. No real-user account or progress is fabricated.

## Known limitations

- Generated concepts, formula choice, distractor plausibility, syllabus coverage and difficulty require human expertise. Arithmetic checking and a second AI response are not full verification.
- The seed bank is introductory and includes repeated mathematical templates. It has 24 topics, not complete RRB syllabus coverage, and contains no real verified PYQs.
- Supabase access tokens are held in memory and not automatically refreshed. Users reauthenticate after reload/expiry; server-side attempt history persists.
- AI jobs execute synchronously; interrupted RUNNING jobs need operator inspection. There is no durable job queue in this version.
- Deadline completion for a disconnected/abandoned test is finalized on its next server access. Late answers are rejected regardless.
- Exact-quota selection is bounded. An unusually fragmented feasible inventory could hit the search bound and report that the mix is unavailable. A dedicated optimization library would be appropriate for very large/more complex constraint sets.
- The public preview seed is bundled with its answers. These educational items are not suitable for high-stakes, secure assessment.
