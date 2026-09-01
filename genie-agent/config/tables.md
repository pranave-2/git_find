# Layer 1 — Table & column metadata

Pasted into the Genie space's table/column description fields. Wording matters:
this is how Genie learns what a column *means*, not just its type.

## `repository_skill`

> Stores evidence that a repository demonstrates a particular canonical skill.
> Each row represents one repository-skill relationship.

- `confidence` — **"This is a deterministic Evidence Score computed from
  language %, dependency matches, code patterns, keywords and semantic
  similarity. It is NOT a number an LLM assigned directly, and it is NOT the
  final candidate score — that is computed separately, outside Genie."**
  Without this sentence, Genie may treat `confidence` as an arbitrary numeric
  column and rank or filter on it in ways that bypass Module C's scoring.

## `skill_evidence`

> Contains textual evidence explaining how a skill was actually implemented
> within a repository. One evidence row exists per (repository, skill) pair
> that has observable evidence; a pair with no evidence has no row here.

## `repository`

> GitHub repositories belonging to students. `summary` is generated once
> during ingestion and does not change per job description.

## `student`

> Registered students. `github_username` is the ingestion key, not a
> display field — always show `name` to recruiters.

## `skill`

> The canonical skill vocabulary. JD wording must be mapped to a row here
> before it can be used in retrieval — see Layer 3 (synonyms). Never invent
> a skill row on the fly.

## `job`

> One row per job description. `jd_text` is the raw, unmodified JD — this
> is the actual retrieval input, not a summary or extracted keyword list.

## `job_registration`

> Which students applied to which job. **All retrieval must be scoped to
> this table** — never return a candidate who isn't registered for the job
> being queried, even if their evidence is strong.
