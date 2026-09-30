# Signal Practice

Fresh standalone RRB Technician Grade-I Signal practice website. Built from the user-supplied `rrb-432-question-bank.zip`, without reusing the old application.

## Architecture

Dependency-free HTML, CSS and JavaScript ES modules. Static question data; browser localStorage for sessions, deadlines, answers, review flags, theme, recent results, and question selection history. No application server, authentication, accounts, Supabase, secrets or environment configuration.

Public deployment: https://signal-practice-432.mamillanaresh717.chatgpt.site/

## Source preservation

`source/original-question-bank.zip` is an unchanged copy of the supplied archive, kept outside the public static directory. `dist/questions.json` contains all 432 question records and all original fields. JSON-valued database fields are parsed into objects. All fields have been compared with the read-only database. Display-time decoding repairs common pre-existing text encoding artifacts without modifying stored data.

430 ORIGINAL and 2 SUPPLEMENTARY records. No official-PYQ claims are added. The 431 ACTIVE questions are available for scored practice; the original pending-review KEY_CONFLICT record is preserved and browseable with a warning, excluded from scoring.

Subject counts: Science & Engineering 129, Computers 105, Mathematics 95, Reasoning 83, General Awareness 20.

## Features

- Full mock: 100 distinct questions, 90-minute absolute deadline, 100 marks, +1 / -1/3 / 0.
- Subject, topic and 10/20-question quick practice; caps sessions at available pool size.
- Instant feedback and supplied structured explanations, including why-wrong explanations where available. Missing separate option rationale is disclosed rather than invented.
- Clickable numbered palette; answered/review/unanswered states and counters.
- Previous, Save/Next, clear, review, jump, and confirmation before manual submission.
- Auto-submit on expiry, including after reload; timer never becomes negative.
- Results, subject/topic breakdown, mistake flags, and read-only answer review.
- Browser-local session recovery and last 20 results. Timer continues while away; scoring uses final selections, clearly disclosed.
- Unseen questions prioritized across sessions, no duplicate IDs within a session.
- Bank filters, source metadata, light/dark themes, responsive desktop/tablet/mobile layouts.

## Validation

`npm run check`: JavaScript syntax checks.
`npm test`: 16 core and application-handler tests, including controlled-clock automatic expiry and reload tests.
`npm run build`: validates production assets and all 432 records. Static assets are authored directly in dist; no compilation or runtime packages required.

Live browser verification completed on 2026-09-29 UTC:
- Home opens without authentication; Full Mock Test starts 100 questions.
- No correct answer displayed before selection.
- Wrong and correct feedback, Concept, Formula, Given, Calculation, Final Answer.
- Clear resets answer/feedback; review remains independent.
- Save/Next, Previous and direct jump to question 50.
- Timer counts down and survives reload; review state and current question recover.
- Submission: 1 correct / 99 unanswered -> 1.00 / 100.
- Negative marking: 1 wrong / 9 unanswered -> -0.33 / 10.
- Subject/topic performance visible after submission.
- Mathematics subject session, topic session capped at 3 available records, quick session of 10 questions.
- Question-bank subject/difficulty filters and explanations; theme switching.

Automatic deadline expiry was verified with controlled-clock application tests, not by waiting 90 minutes in the live browser. Responsive breakpoints are implemented; live UI flow verification used a desktop browser.

## Layer 2 update — 2026-09-30

The original JSON SHA-256 remains `d0048cb99f595e07544e1c17c05cd60034e6a1f5094f55ff9afe1a2cf637830b`. All 432 original records remain unchanged, with 431 eligible and the existing conflict excluded.

`dist/layer2.json` adds 1,000 **NEW — BANK-BASED PRACTICE** questions separately. Distribution: Science & Engineering 300, Computers 245, Mathematics 220, Reasoning 190, General Awareness 45. Coverage spans 161 supplied topic labels; some labels in the source overlap in meaning. Difficulties are editorial estimates: Medium 286, Medium-Hard 509, Hard 205.

### Content scope and limitations

These are **1,000 distinct paired-case combinations constructed from 216 retained application cases**, not 1,000 wholly independent case narratives. Each item requires classifying two conclusions. Component cases recur across different pairs. Each unordered pair occurs once, and no numeric-only variants are generated. This finite bank permits ongoing practice through least-recently-used repetition; it does not provide unlimited novel content. No external AI call occurs at Start Test.

248 cases were authored, and 32 were excluded because of source-setup similarity or editorial duplicate review. Automated checks verify 142 authored arithmetic equations (including cases subsequently excluded), four unique choices and exactly one option matching the two statement truth values. Answer rationales are authored, not independently expert-certified.

Digit-normalized unigram/bigram TF-IDF checks found no whole-question candidates at the 0.78 threshold, no exact/normalized question-stem duplicates, and no repeated case pairs. Maximum final new/original similarity is 0.3175; new/new is 0.7157. Text similarity is a screening method, not proof of semantic novelty. Reused component cases remain an explicit limitation.

Machine-readable distribution and duplicate report: `dist/layer2-summary.json`. Offline generator and authored inputs: `scripts/layer2/` (Python, NumPy and scikit-learn for audit only; none required at runtime).

### Integration

- Original, New, Mixed (0/25/50/75/100% original) full CBT, each 100 questions and 90 minutes.
- Continue Practice fills with unseen originals before moving to New.
- Subject, topic and quick sessions offer pool controls; limited pools cap session size.
- Each question has an explicit pool label. Bank browsing filters original/new/both.
- Mixed results separate original/new attempts and accuracy, alongside unchanged scoring and subject/topic tables.
- Existing `signal432.v1.seen` history remains the original history; `signal432.v1.seen.new` stores generated IDs. Each is least-recent-first after update.
- Existing original sessions/results remain readable. New and mixed sessions use the same persisted absolute-deadline model.
- This standalone site has **no separate Exam Mode**. None was created or altered; all new selection controls are practice-only.

Validation: 33 tests pass, including all 16 previous tests, original-byte preservation, generated truth/key structure, mixed ratios, unseen-first selection, controlled repetition, mixed score reconciliation, and new/mixed application-state recovery. Syntax and production-asset checks pass.

Live Layer-2 browser checks completed after deployment: New CBT starts 100 questions at 90:00; feedback is hidden before selection and appears immediately afterward. Mark/reload/jump recovery retained question 50, one answer, one review flag and the continuing countdown. New result showed 1/100 attempted and 1.00 marks. Mixed 25/75 and 50/50 tests showed their exact original/new counts on the results table. Original-only regression started 100 questions at 90:00 with ORIGINAL BANK labels and no generated-pool results. Original-bank browsing still showed 432 records; New + General Awareness filtering showed 45. Incorrect-answer feedback and clear-answer behavior passed in the mixed flow. Live proof is stored at `source/layer2-live-verification.jpg`.
