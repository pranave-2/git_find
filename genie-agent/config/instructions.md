# Layer 4 — Recruitment retrieval instructions

The exact text currently live in the Genie Agent's **Instructions** field.
Databricks Genie Agents have no separate "synonyms" field — Layer 3 (JD
terminology → canonical skill) got folded into this same box, so
`config/synonyms.yaml` is now the structured source-of-truth you edit and
regenerate this block from, not a second thing to paste in separately.

It's been through seven rounds of real testing against the live agent (not
simulated), each round catching a real failure the previous version missed:

1. **Baseline** (12 bullets, unconsolidated): JD-interpretation, scoping,
   join, and "retrieval only" rules written before any live test.
2. **Round 1**: retrieval was accurate, but the agent returned a "Not
   Qualified" verdict and collapsed evidence into a checkmark table — both
   violate "retrieval only." Added bans on qualification language and on
   boolean-only summaries.
3. **Round 2**: the qualification *word* was gone, but the agent switched
   to comparative phrasing ("strongest alignment") — same violation,
   reworded around the ban. Added a ban on comparative/superlative
   language between candidates.
4. **Round 3 (token trim)**: consolidated 12 bullets down to 8 (404 → ~220
   words). This introduced two regressions in the same test: the merged
   "no judgment" bullet only banned specific *words*, and the agent found
   new wording for the same judgment ("two candidates meet the required
   skills, one does not") — fixed by banning the *concept* (any verdict,
   any count of who satisfies a requirement) instead of a phrase list. The
   merged "literal values" bullet also dropped the explicit "as a table"
   wording, so correct data came back as prose bullets — fixed by
   re-adding "respond with a table" explicitly.
5. **Round 4**: clean via the JD-paste entry path — 11/11 rows correct,
   proper table, no judgment language. But testing the *same* instructions
   through a different entry path (typing a short retrieval question
   instead of pasting the JD) reproduced the exact violations round 3
   fixed: an inaccurate registered-candidate count that silently omitted
   the zero-evidence candidate, and full narrative paragraphs alongside
   the table. Root cause: bullet 6 had a carve-out ("if a candidate has
   zero rows, state that in one neutral sentence") — that one permitted
   exception gave the model license to add other sentences too, and the
   carve-out's own target case still went unmentioned. Fixed by removing
   the exception entirely: table only, zero prose, no exceptions.
6. **Round 5**: the "zero rows → include a placeholder row" replacement
   backfired — for the candidate with no JD-relevant evidence, the agent
   returned his *real* unrelated repository_skill rows (actual confidence
   numbers) with just `skill_name`/`evidence` blanked to NULL, which is
   more misleading than omission (a bare number with no label saying what
   it measures). Fixed by dropping the placeholder-row idea altogether —
   the table now contains only real matching rows, full stop. A candidate
   with zero JD-relevant evidence has zero rows; distinguishing "zero
   evidence" from "not registered" is handled downstream by Module C via
   `registered_student_ids` in the API contract (see
   `/shared/genie.retrieval.schema.json`), not by anything Genie renders.
7. **Round 6**: table data now fully correct and correctly silent on
   zero-evidence candidates — but the response also included an
   auto-generated chart alongside the table. Bullet 6 banned prose, never
   said "chart." Added an explicit ban on charts/visualizations.

After round 6: table-only, no prose, no chart, no placeholder rows,
zero-evidence candidates correctly absent from the table and handled via
the API contract instead. Stable at 8 bullets.

The 1st and 5th bullets below are the ones that keep the architecture's
separation of concerns intact: **retrieve, never score, never judge, never
decorate.** Don't let them get edited away for "convenience" or trimmed
further — rounds 3–6 all show what happens when they're compressed or
carved-out.

```
* `repository_skill.confidence` is a DETERMINISTIC Evidence Score (language %, dependencies, code patterns, keywords, semantic similarity) — not an LLM output, not a final candidate score.
* Restrict every answer to students in `job_registration` for the job being asked about.
* Join `repository_skill` to `skill_evidence` on BOTH `repo_id` AND `skill_id`.
* Preserve every repository demonstrating a skill — never collapse, average, or pick only the best one.
* Retrieval only: never rank, score, compare, count, or judge candidates in any form — no verdicts ("qualified," "best," "strongest," "meets requirements," etc.) and no summary statement about how many candidates satisfy or lack a requirement. Describe each candidate's evidence independently, with no framing sentence comparing them.
* Respond with a table ONLY, in every case, regardless of how the question is phrased — no introductory sentence, no per-candidate narrative, no concluding summary, no chart, no visualization, no exceptions, no placeholder rows for candidates with no evidence. Columns: student name, repository name, skill name, confidence (number), evidence text — one row per actual matching evidence row, nothing else. Never a Yes/No/NULL-summary column, never a chart or graph in place of or alongside the table.
* Map JD terminology to canonical skills:
  - "Python backend" -> Python + Backend
  - "HTTP services", "web services", "RESTful" -> REST API
  - "containerized deployment", "containerization" -> Docker
  - "relational database", "Postgres" -> PostgreSQL
  - "Python web framework" -> FastAPI or Flask
  - "cloud deployment", "Amazon Web Services" -> AWS
  - "Spring framework" -> Spring Boot
* Requirement level: "required", "must have", "strong experience" -> required. "preferred", "nice to have" -> preferred (default when unmarked). "a plus", "bonus", "advantageous" -> bonus.
```

## If you extend the synonym vocabulary later

Edit `config/synonyms.yaml` first (it's the structured, machine-readable
version), then manually re-fold any new `match` terms into the bullet
list above — both in this file and in the live agent's Instructions box.
There's no automated sync between them; the live agent only reads what's
literally pasted into its Instructions field.
