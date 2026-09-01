# /shared — contract schemas

JSON Schema (draft 2020-12) for the output of each module. Published day 1; every
module builds and unit-tests against fixtures shaped like these, so nobody waits
on a working upstream module.

## Change of plan (2026-09-01)

Originally Module C computed a deterministic Evidence Score from raw signals
supplied by Modules A and B (see git history for `scoring.repository_skill.schema.json`,
now removed). That coupled Module C to both A and B before it could do anything.

**Now Module B (Gemini) assigns the per-skill confidence directly** when it
analyses a repository. `REPOSITORY_SKILL.confidence` is written straight from
Module B's output — there is no separate scoring-formula step, and Module C
no longer depends on Module A or Module B's internals at all. Module C's only
job is ranking: aggregate already-scored evidence per skill (MAX across
repos) and apply the JD's required/preferred/bonus weights.

This means Modules A, B, and C can be built, tested, and demoed fully in
parallel — C only needs evidence rows shaped like `genie.retrieval.schema.json`
to do its job, whether they came from real Genie retrieval or a hand-built
fixture. Module A's raw features are now optional prompt context for Module
B, not a required scoring input.

| File | Owner | What it describes |
|---|---|---|
| `common.schema.json` | joint | ID patterns, `unit_interval`, `requirement_level`, provenance |
| `ingestion.raw_features.schema.json` | A | one doc per repo: language %, dependencies, code signals, README — optional context for B, no longer feeds a score |
| `llm_evidence.schema.json` | B | one doc per repo: summary, skill labels, NL evidence, **and the Evidence Score itself** |
| `scoring.ranking_result.schema.json` | C | per job: aggregated skill strengths + final candidate scores (C's only output now) |
| `genie.retrieval.schema.json` | D | per job: JD interpretation, generated SQL, retrieved evidence rows |
| `app.requests.schema.json` | E | inbound: student registration, JD submission |
| `app.recruiter_result.schema.json` | E | recruiter dashboard response (ranking + `ai_summarize` justification) |
| `app.placement_dashboard.schema.json` | E | cohort aggregates, no per-student fields by design |

`fixtures/` holds one valid instance per schema, using the Rahul / J001 example
from `ARCHITECTURE.md` (confidence values kept the same as the original
worked example — they're just attributed to Module B directly now, not to a
formula).

The one invariant still enforced structurally, not by convention:

- Module D's output has no score or rank field, and `additionalProperties: false`
  keeps one from being added. Genie retrieves; Module C ranks.

## Validate

```bash
pip install jsonschema referencing && python shared/validate.py
```

## Changing a contract

Bump `schema_version` (semver). Additive optional field = minor. Removing or
renaming a field, or tightening a constraint = major, and needs the consuming
module's owner to agree before merge.
