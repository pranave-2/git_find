# /shared — contract schemas

JSON Schema (draft 2020-12) for the output of each module. Published day 1; every
module builds and unit-tests against fixtures shaped like these, so nobody waits
on a working upstream module.

| File | Owner | What it describes |
|---|---|---|
| `common.schema.json` | joint | ID patterns, `unit_interval`, `requirement_level`, provenance |
| `ingestion.raw_features.schema.json` | A | one doc per repo: language %, dependencies, code signals, README |
| `llm_evidence.schema.json` | B | one doc per repo: summary, skill labels, NL evidence, similarity |
| `scoring.repository_skill.schema.json` | C | one doc per (repo, skill): Evidence Score + full signal breakdown |
| `scoring.ranking_result.schema.json` | C | per job: aggregated skill strengths + final candidate scores |
| `genie.retrieval.schema.json` | D | per job: JD interpretation, generated SQL, retrieved evidence rows |
| `app.requests.schema.json` | E | inbound: student registration, JD submission |
| `app.recruiter_result.schema.json` | E | recruiter dashboard response (ranking + `ai_summarize` justification) |
| `app.placement_dashboard.schema.json` | E | cohort aggregates, no per-student fields by design |

`fixtures/` holds one valid instance per schema, using the Rahul / J001 example
from `ARCHITECTURE.md`.

Two invariants the schemas enforce structurally, not by convention:

- Module B's output has no confidence/score field, and `additionalProperties: false`
  keeps one from being added. Gemini never scores.
- Module D's output has no score or rank field. Genie retrieves; Module C scores.

## Validate

```bash
pip install jsonschema referencing && python shared/validate.py
```

## Changing a contract

Bump `schema_version` (semver). Additive optional field = minor. Removing or
renaming a field, or tightening a constraint = major, and needs the consuming
module's owner to agree before merge.
