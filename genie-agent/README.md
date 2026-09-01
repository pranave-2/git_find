# genie-agent — Module D

Owns everything that makes the Recruitment Genie interpret a raw JD
correctly: table/column metadata, relationships, skill synonyms, retrieval
instructions and example queries, configured on a real Databricks Genie
Agent (renamed from "Genie space" in July 2026 — same underlying thing,
same `/api/2.0/genie/spaces/{space_id}/...` API).

**What Genie does: retrieve. What it never does: score.** That rule is
enforced structurally — [`/shared/genie.retrieval.schema.json`](../shared/genie.retrieval.schema.json)
has no score/rank field and `additionalProperties: false`, so Genie's output
literally cannot carry a ranking. Aggregation and scoring are Module C's job.

**No mocks. No offline stand-ins.** The only thing that counts as
verification is a real JD run through a real Genie space configured with the
layers below, checked against the shared contract. If it hasn't gone through
Databricks, it isn't verified — it's a draft.

## Layout

```
ddl/schema.sql              draft DB schema to configure Genie against, until
                             Person C publishes the real one (reconcile at
                             Checkpoint 1)
seed/seed_data.sql           fabricated rows (Rahul/Priya/Arjun), loaded into
                             the REAL Databricks warehouse so the REAL Genie
                             space has something to query before A/B/C's real
                             ingestion pipeline is wired up — straight out of
                             ARCHITECTURE.md, not a simulation of Genie itself
config/tables.md             Layer 1 — table & column descriptions
config/relationships.md      Layer 2 — how tables join (reference only —
                             the live agent auto-derives these from the
                             FK constraints in ddl/schema.sql)
config/synonyms.yaml         Layer 3 — JD terminology -> canonical skill,
                             structured source; folded into instructions.md
                             below, since the live UI has no separate field
config/instructions.md       Layers 3+4 combined — the exact text pasted
                             into the agent's Instructions field, evolved
                             through 3 rounds of live testing (see that
                             file's own header for what each round fixed)
config/example_questions.md  Layer 5 — representative NL question -> SQL pairs
scripts/validate_retrieval.py  checks a REAL Genie response against the
                             shared contract
```

## Setting up the real Genie Agent

What the config layers actually map to, in the real UI (confirmed against
a live Free Edition workspace — the four tabs on an agent's config panel
are **About, Sources, Instructions, Examples**; there is no separate
"synonyms" or "relationships" tab):

1. Stand up a Databricks (Free Edition) workspace and SQL warehouse.
2. In the SQL Editor: `CREATE SCHEMA IF NOT EXISTS workspace.recruitment_genie;`,
   then `USE CATALOG workspace; USE SCHEMA recruitment_genie;`, then run
   `ddl/schema.sql` (creates the 7 tables), then `seed/seed_data.sql`.
3. Sidebar → **Genie Agents** → new agent, add all 7 tables from
   `workspace.recruitment_genie` as its **Sources**.
4. On each table under **Sources**, click the pencil to set the table
   description, and the pencil on each column for its description —
   `config/tables.md` has the text for all 7 tables. The `confidence`
   column's description is the load-bearing one (see Layer 1 notes there).
5. Check the **Examples** tab — it auto-populates JOIN entries from the
   `FOREIGN KEY` constraints in `ddl/schema.sql`. Verify they match
   `config/relationships.md`; you shouldn't need to add anything by hand.
6. Still on **Examples**, click **Add** and add the 3 question/SQL pairs
   from `config/example_questions.md`.
7. On **Instructions**, paste the full text block from `config/instructions.md`
   verbatim — this is Layers 3 (synonyms) and 4 (retrieval rules) combined
   into one field.
8. Wire `ai_summarize` over retrieved evidence for the justification text
   (feeds Module E's recruiter result, not this module's own contract) —
   not yet done, tracked as an open item below.

## What's actually been verified (live, not simulated)

Ran the seeded J001 JD — and several shorter retrieval-style questions,
through both the JD-paste and typed-question entry paths — through the
live agent's chat, 6 rounds, tightening `config/instructions.md` between
rounds based on real failures observed, not hypothetical ones. Full
blow-by-blow is in `config/instructions.md`'s own header; summary:

| Round | Found | Fix |
|---|---|---|
| 1 | Correct retrieval, but response collapsed evidence into a checkmark table and labeled a candidate "Not Qualified" | Banned qualification language and boolean-only tables |
| 2 | Qualification wording gone, replaced with comparative phrasing ("strongest alignment") | Banned comparative/superlative language between candidates |
| 3 (token trim) | Consolidating 12→8 bullets reintroduced both prior issues via new wording ("meets the required skills") plus dropped the explicit table format, returning prose bullets | Banned the *concept* of judgment (not just phrases); re-added explicit table requirement |
| 4 | Same instructions, different entry path (typed question vs. JD paste) reproduced the round-3 violations — traced to a carve-out in the table-only rule that gave the model license for other prose too | Removed the exception entirely: table only, zero prose, no exceptions |
| 5 | The "placeholder row for zero-evidence candidates" fix backfired — leaked a candidate's real *unrelated* confidence scores with the skill label blanked, more misleading than omission | Dropped placeholder rows entirely; zero-evidence candidates are correctly absent from the table, handled downstream via `registered_student_ids` instead |
| 6 | Table fully correct, but response included an auto-generated chart alongside it — never explicitly banned | Added explicit ban on charts/visualizations |

Every evidence row across every round was checked field-by-field against
`seed/seed_data.sql` — no row invented, none dropped, none silently
averaged. This confirms Layers 1–5 all functioning correctly on a real
Genie Agent, across multiple question phrasings, not just one lucky path.

All of the above was through the chat UI, which returns prose/CSV, not the
structured JSON `/shared/genie.retrieval.schema.json` needs. That gap is
now closed by `scripts/run_genie_query.py`.

## Calling it programmatically

`scripts/run_genie_query.py` calls the real Conversation API
(`start-conversation` → poll `get_message` → `statement_id` → literal SQL
result rows), and produces a `genie.retrieval.schema.json`-shaped document.
Two things it does that the chat UI doesn't give you for free:

- **ID resolution**: Genie's table columns are names (`name`, `repo_name`,
  `skill_name`), not surrogate keys — the schema wants
  `student_id`/`repo_id`/`skill_id` too. The script runs a second, real
  query against `student`/`repository`/`skill` in the same warehouse and
  joins the IDs on in Python.
- **`interpreted_requirements` / `mapped_skills`**: the round-4 "table
  only" instruction fix means Genie's response no longer narrates its own
  required/preferred/bonus classification anywhere. The script derives it
  from the JD text using `config/synonyms.yaml` — the same vocabulary
  already loaded into Genie's Instructions, just applied outside the
  agent instead of asking it to narrate what it already knows internally.

```bash
pip install -r requirements.txt
export DATABRICKS_HOST=https://<your-workspace>.cloud.databricks.com
export DATABRICKS_TOKEN=<personal access token>   # never commit this, never pass on argv

python3 scripts/run_genie_query.py --job-id J001 --out out.json
python3 scripts/validate_retrieval.py out.json
```

## Verifying it

```bash
pip install jsonschema referencing
python3 scripts/validate_retrieval.py path/to/genie_response.json
```

This checks the real response against `/shared/genie.retrieval.schema.json`:
right fields present, `confidence` passed through untouched, and critically,
no score or rank field anywhere in it. A response that fails this is either
a contract bug (fix Layer 1's `confidence` description) or an instruction
leak (Genie tried to rank — tighten Layer 4).

There is no expected-output fixture checked into this repo, because a
canned "expected" JSON is exactly the kind of unverified stand-in this
module is trying to avoid. The real Genie space's own generated SQL and
returned rows are the only source of truth — read them, don't diff against
a static file.

## Checkpoints (per the work-split doc)

- **Checkpoint 1**: reconcile `ddl/schema.sql` against Person C's real
  published schema; re-run the seeded JD against real ingested data once
  A -> B -> C are wired.
- **Checkpoint 2**: verify the ranking scorer + `ai_summarize` end to end
  against this module's real Genie output.
