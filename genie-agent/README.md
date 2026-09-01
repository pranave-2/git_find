# genie-agent — Module D

Owns everything that makes the Recruitment Genie interpret a raw JD
correctly: table/column metadata, relationships, skill synonyms, retrieval
instructions and example queries, configured on a Databricks Genie space.

**What Genie does: retrieve. What it never does: score.** That rule is
enforced structurally — [`/shared/genie.retrieval.schema.json`](../shared/genie.retrieval.schema.json)
has no score/rank field and `additionalProperties: false`, so Genie's output
literally cannot carry a ranking. Aggregation and scoring are Module C's job.

## Layout

```
ddl/schema.sql              draft DB schema to configure/test against, until
                             Person C publishes the real one (reconcile at
                             Checkpoint 1)
seed/seed_data.sql           fabricated rows (Rahul/Priya/Arjun) for a live
                             warehouse — straight out of ARCHITECTURE.md
seed/seed_data.json          same data, machine-readable, used by mock_genie.py
config/tables.md             Layer 1 — table & column descriptions
config/relationships.md      Layer 2 — how tables join
config/synonyms.yaml         Layer 3 — JD terminology -> canonical skill
config/instructions.md       Layer 4 — retrieval rules ("retrieve, never score")
config/example_questions.md  Layer 5 — representative NL question -> SQL pairs
scripts/mock_genie.py        offline stand-in for a live Genie space
scripts/validate_retrieval.py  checks output against the shared contract
tests/sample_retrieval_output.json  mock_genie.py's output for J001, committed
                             as a regression fixture
```

## Why a mock Genie exists

Module D "needs Person C's schema shape to configure against; needs real
ingested data only for final testing" — but a live Databricks Genie space
still needs credentials and configuration to hit. `mock_genie.py` applies
the same five layers (synonyms + instructions) to `seed_data.json` in plain
Python, so:

- The retrieval **contract shape** can be proven correct today, no
  Databricks connection required.
- Person C can build the ranking scorer against real-shaped output from D,
  not a hand-written fixture.
- Regressions in the synonym vocabulary or requirement-level detection show
  up as a diff in `tests/sample_retrieval_output.json`, not silently.

It is *not* a substitute for the real Genie space — it can't do semantic
reasoning past literal substring matches. Swap it out once the space is live.

## Run it

```bash
# Regenerate the sample retrieval output for job J001
python3 scripts/mock_genie.py --job-id J001 --out tests/sample_retrieval_output.json

# Validate it against /shared/genie.retrieval.schema.json
python3 scripts/validate_retrieval.py tests/sample_retrieval_output.json

# Try a different JD ad hoc
python3 scripts/mock_genie.py --jd-text "Looking for a Java engineer with Spring Boot experience" \
    --job-id J999 --registered S003
```

Requires `pyyaml`, `jsonschema`, `referencing`:

```bash
pip install pyyaml jsonschema referencing
```

## Wiring into a real Databricks Genie space

1. Create a Genie space over the tables in `ddl/schema.sql` (or Person C's
   real schema once published).
2. Paste `config/tables.md` into each table/column's description field.
3. Configure the joins in `config/relationships.md`.
4. Add every row in `config/synonyms.yaml` as Genie's semantic vocabulary.
5. Paste `config/instructions.md` as the space's instructions.
6. Add the patterns in `config/example_questions.md` as example
   questions/SQL.
7. Submit the seeded JD (`seed/seed_data.sql`, job J001) as a smoke test and
   diff the result against `tests/sample_retrieval_output.json` — they
   should agree on `interpreted_requirements` and `evidence_rows`, modulo
   Genie's SQL phrasing.
8. Wire `ai_summarize` over the retrieved evidence for the justification
   text (feeds Module E's recruiter result, not this module's contract).

## Checkpoints (per the work-split doc)

- **Checkpoint 1**: reconcile `ddl/schema.sql` against Person C's real
  published schema; re-run `mock_genie.py` against real ingested data once
  A -> B -> C are wired.
- **Checkpoint 2**: point this module at the live Genie space instead of
  `mock_genie.py`; verify the ranking scorer + `ai_summarize` end to end.
