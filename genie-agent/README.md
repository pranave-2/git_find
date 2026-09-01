# genie-agent — Module D

Owns everything that makes the Recruitment Genie interpret a raw JD
correctly: table/column metadata, relationships, skill synonyms, retrieval
instructions and example queries, configured on a real Databricks Genie
space.

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
config/relationships.md      Layer 2 — how tables join
config/synonyms.yaml         Layer 3 — JD terminology -> canonical skill
config/instructions.md       Layer 4 — retrieval rules ("retrieve, never score")
config/example_questions.md  Layer 5 — representative NL question -> SQL pairs
scripts/validate_retrieval.py  checks a REAL Genie response against the
                             shared contract
```

## Setting up the real Genie space

1. Stand up a Databricks (Free Edition) workspace and SQL warehouse.
2. Run `ddl/schema.sql` against it to create the tables, then `seed/seed_data.sql`
   to populate them.
3. Create a Genie space over those tables.
4. Paste `config/tables.md` into each table/column's description field.
5. Configure the joins from `config/relationships.md`.
6. Add every row in `config/synonyms.yaml` as Genie's semantic vocabulary.
7. Paste `config/instructions.md` as the space's instructions.
8. Add the patterns in `config/example_questions.md` as example
   questions/SQL.
9. Wire `ai_summarize` over retrieved evidence for the justification text
   (feeds Module E's recruiter result, not this module's own contract).

## Verifying it

Submit the seeded JD (`seed/seed_data.sql`, job J001) to the real Genie
space — through the UI or the Conversation API — and export the response as
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
