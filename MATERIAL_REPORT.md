> **Policy update:** The 20 original challenges below are no longer counted as PYQ-matched coverage. Under the verified-foundation requirement, all 75 units currently have a foundation gap; no verified-based generated patterns are approved. Counts below describe the original material audit, not current exam eligibility.

# Material audit — 23 September 2026

## Obtained before implementation

| Material | Extraction | Classification |
|---|---:|---|
| User-supplied 70-page CEN 02/2025 notification | Syllabus and pattern; zero questions | Authoritative syllabus, §13.1(A), printed pp.16–17 / PDF pp.20–21 |
| Official Secunderabad CEN 02/2025 category notice | Indexed access notice; zero official question records | Official notice only; direct retrieval returned 502 |
| Official Secunderabad CEN 02/2024 category page and objection notice | Page, notice and candidate portal URL; zero official question records | Official notice only |
| CareerPower 19 December 2024 shift 1 PDF | 100 numbered blocks, 6 empty/incomplete stems | Unverified third-party copy |
| CareerPower 13 March 2026 shift 1 PDF | 100 numbered blocks, 7 empty/incomplete stems | Unverified third-party copy |

Sources and URLs are stored in frontend/src/preparation.json. The notification's SHA-256 fingerprint is recorded. The official 2024 notice offered candidate access from 26–31 December 2024. The indexed 2026 notice offered access from 28 March–6 April 2026. Those notices establish access arrangements, not the authenticity or final-key status of a third-party question copy. The candidate portal did not yield public question data.

The 200 external records are an inspection index, not 200 imported questions. Image questions, mathematical images and coloured key indicators can be missing from extracted text even where a stem exists. Full externally retrieved compilations are linked references rather than republished in this package. Two short excerpts are imported and independently solved. They are labelled SUPPLEMENTARY / RECONSTRUCTED_UNVERIFIED; this is a conservative handling category, not a claim that their publisher necessarily reconstructed them from memory.

## Implemented content

- 190 existing ORIGINAL starter questions retained as Basic Practice.
- 0 newly officially verified PYQs. No item was upgraded to verified based only on a notice or a publisher's “official paper” title.
- 2 supplementary examples: 2024 shift 1 Q54 (binary conversion), 2026 shift 1 Q92 (electromagnetic induction). Their answers are independently solved; no official final-key certification is claimed. Q54 matches the copy’s visual marking. Q92 conflicts with its copy’s marked motor answer; it is PENDING_REVIEW / KEY_CONFLICT and excluded from all test generation. Only one supplementary example is ready for practice.
- 20 original PYQ-style challenge questions, separately marked PYQ_PATTERN / SOLUTION_CHECKED. They are not copied or number-swapped PYQs. Each records its syllabus mapping, worked solution, pattern basis and difficulty rationale. Difficulty is editorial and provisional; author checking is not independent human review.

## Coverage after this addition (clean starter database)

| Subject | Checklist units | Units with original patterns | Missing exam-bank units |
|---|---:|---:|---:|
| General Awareness | 9 | 0 | 9 |
| Reasoning | 15 | 3 | 12 |
| Computers | 10 | 4 | 6 |
| Mathematics | 14 | 5 | 9 |
| Science & Engineering | 27 | 8 | 19 |
| Total | 75 | 20 | 55 |

All 20 represented units have one pattern each and are underrepresented against the clearly labelled editorial stock target of five per unit. All 75 units still lack officially verified PYQs. Neither 75 checklist rows nor subject quotas prove full syllabus mastery. The notification itself says the listed topics are illustrative, not exhaustive, and the subject allocation is indicative.

Represented pattern units: quadratics, dispersion, probability, set operations, heights/distances; data representation, storage, MS Office, networking; syllogism, data sufficiency, analytical reasoning; resistance networks, meter range extension, induction, CRO, transducers, digital logic, work/energy, heat.

Missing units include all General Awareness; most reasoning topics; computer architecture, I/O, operating systems, internet/email, browsers and viruses; number systems, BODMAS, progressions, geometry/trigonometric ratios, mensuration and set foundations; units, mass/density, motion, fields/potential, materials, Ohm law, electrical power, magnetism, general electronics/devices, microcontrollers/processors, measurement systems and displays. The in-app checklist gives every row and live counts for the user's database.

## Duplicate and history handling

New content is compared against the existing bank. Exact/number-substitution duplicates are archived rather than deleted. Possible textual paraphrases are flagged and excluded from preparation pending an administrator's comparison decision. This is a text-similarity heuristic, not a guarantee of semantic duplicate detection. Existing starter variants are retained in Basic Practice as requested.

Strict sessions reserve question IDs and normalized numerical families using all saved attempts, including unfinished and basic-practice sessions. A user-row write lock serializes starts. A shortage produces an error, never silent reuse. Historical sessions not present in the local database cannot be inferred. Data is scoped to the account/database; deleting history removes its evidence.
