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

Ran the seeded J001 JD through the live agent's chat, 3 rounds, tightening
`config/instructions.md` between rounds based on real failures observed —
not hypothetical ones:

| Round | Found | Fix |
|---|---|---|
| 1 | Correct retrieval (all repo/skill/confidence rows matched seed data exactly, restricted to the 3 registered students) — but response collapsed evidence into a checkmark table and labeled Arjun "Not Qualified," both violations of "retrieval only" | Added explicit bans on qualification language and boolean-only tables |
| 2 | Qualification wording gone, but agent switched to comparative phrasing ("strongest alignment") — same violation, different words. Raw confidence numbers confirmed present and correct when asked directly for the raw table | Added explicit ban on comparative/superlative language between candidates |
| 3 | No qualification or comparative language; all confidence values and evidence text correct and present in the narrative response. One chat-UI "overview" grid still renders Yes/NULL instead of numbers | Left as-is — this is a chat-UI rendering default, not a data problem; the Conversation API path reads literal numeric SQL results regardless of what the chat bubble renders |

Every evidence row across all 3 rounds was checked field-by-field against
`seed/seed_data.sql` — no row invented, none dropped, none silently averaged.
This confirms Layers 1–5 all functioning correctly on a real Genie Agent.

**Still open**: this was verified through the chat UI, which returns
prose/CSV, not the structured JSON `/shared/genie.retrieval.schema.json`
needs. The Conversation API script (`start-conversation` → poll
`get_message` → `statement_id` → literal rows) that turns this into
something Module C can call programmatically isn't written yet.

## Verifying it

Submit the seeded JD (`seed/seed_data.sql`, job J001) to the real Genie
Agent — through the UI or the Conversation API — and export the response as
JSON. Then:

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
