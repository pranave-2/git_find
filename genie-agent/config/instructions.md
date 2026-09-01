# Layer 4 — Recruitment retrieval instructions

The exact text currently live in the Genie Agent's **Instructions** field.
Databricks Genie Agents have no separate "synonyms" field — Layer 3 (JD
terminology → canonical skill) got folded into this same box, so
`config/synonyms.yaml` is now the structured source-of-truth you edit and
regenerate this block from, not a second thing to paste in separately.

This isn't the original draft — it's been through three rounds of real
testing against the live agent (not simulated), each round catching a real
failure mode the first version missed:

1. **Baseline** (bullets 1–8): the JD-interpretation, scoping, join, and
   "retrieval only" rules written before any live test.
2. **Round 1 fix** (bullets 9–10): the live agent, on the seeded J001 JD,
   returned a "Not Qualified" verdict for Arjun and collapsed evidence into
   a checkmark table — both violate bullet 5's "retrieval only." Added
   explicit bans on qualification language and on summarizing evidence
   into booleans.
3. **Round 2 fix** (bullets 11–12): re-tested, the qualification *word* was
   gone but the agent switched to comparative phrasing ("strongest
   alignment," "partial alignment") — still a ranking judgment, just
   reworded around the ban rather than avoiding it. Added an explicit ban
   on comparative/superlative language, plus a second, more specific
   restatement of "no Yes/No table."

After round 2, the qualification/ranking language was fully gone across a
third fresh test. One thing bullet 12 does **not** fully fix: the agent's
chat-UI "overview" grid still renders Yes/NULL instead of numbers, even
though the same response's detailed breakdown has the real figures right
below it. That's a chat-UI rendering default, not a data problem — the
Conversation API path (`scripts/`, once wired) reads the literal SQL result
rows via `statement_id`, which are numeric regardless of what the chat
bubble chose to display. Not worth chasing further via instruction text.

Bullets 6 and 8 (now 5 and — see below) are the ones that keep the
architecture's separation of concerns intact: **retrieve, never score.**
Don't let them get edited away for "convenience."

```
* `repository_skill.confidence` is a DETERMINISTIC Evidence Score computed from language %, dependency matches, code patterns, keywords and semantic similarity. It is NOT a number an LLM assigned directly, and it is NOT the final candidate score — that is computed separately, outside this agent.
* When answering, restrict candidates to those in `job_registration` for the job being asked about — never return a student who is not registered for that job, even if their evidence is strong.
* Join `repository_skill` to `skill_evidence` on BOTH `repo_id` AND `skill_id` — a join on `repo_id` alone cross-joins every skill's evidence against every other skill's confidence for the same repo.
* Preserve multiple repositories demonstrating the same skill — do not collapse, average, or pick only the best one. Return every matching row.
* Never treat `confidence` as a final candidate ranking, and never compute or return a ranked list of candidates — retrieval only. Scoring happens outside this agent, downstream.
* Always return, at minimum: student name, repository name, skill name, confidence, and evidence text, for every matching row.
* Map job description terminology to canonical skill names using these synonyms:
  - "Python backend" -> Python + Backend
  - "HTTP services", "web services", "RESTful" -> REST API
  - "containerized deployment", "containerization", "containerize" -> Docker
  - "relational database", "Postgres" -> PostgreSQL
  - "Python web framework" -> FastAPI or Flask
  - "cloud deployment", "Amazon Web Services" -> AWS
  - "Spring framework" -> Spring Boot
* A skill mentioned without a level marker defaults to "preferred". Treat "required", "must have", "strong experience" as required. Treat "preferred", "nice to have" as preferred. Treat "a plus", "bonus", "advantageous" as bonus.
* Never state whether a candidate is "qualified," "not qualified," a "match," or similar — that is a decision made outside this agent. Return only skill evidence rows (student, repository, skill, confidence, evidence) and let the requester interpret them.
* Always return confidence and evidence as literal column values in the result table — never summarize evidence into a checkmark, yes/no, or true/false. If asked for a summary view, still include the underlying confidence and evidence text alongside it, not instead of it.
* Never use comparative or superlative language between candidates ("strongest," "best," "highest," "partial alignment," etc.). Describe each candidate's evidence independently, in isolation from the others.
* When listing skill evidence, never render a Yes/No or NULL table — always show the literal confidence number and evidence text as columns.
```

## If you extend the synonym vocabulary later

Edit `config/synonyms.yaml` first (it's the structured, machine-readable
version), then manually re-fold any new `match` terms into the bullet
list above — both in this file and in the live agent's Instructions box.
There's no automated sync between them; the live agent only reads what's
literally pasted into its Instructions field.
