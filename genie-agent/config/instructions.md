# Layer 4 — Recruitment retrieval instructions

Pasted verbatim into the Genie space's instructions field. Instruction 6 and
8 are the ones that keep the architecture's separation of concerns intact —
don't let them get edited away for "convenience."

1. When processing a job description, identify technical skills and
   requirements relevant to candidate matching.
2. Map terminology in the JD to the canonical skills in the `skill` table,
   using the synonym vocabulary — never invent a skill that isn't a row in
   that table.
3. Restrict candidates to those registered for the current job
   (`job_registration`). Never return a candidate who is not registered,
   regardless of how strong their evidence is.
4. Retrieve repository-level evidence for relevant skills, joining
   `repository_skill` and `skill_evidence` on both `repo_id` AND `skill_id`.
5. Preserve multiple repositories demonstrating the same skill — do not
   collapse or average them. Aggregation happens downstream, not in Genie.
6. **Never treat `repository_skill.confidence` as a final candidate score.**
   It is per-repository evidence, not a ranking.
7. Return, at minimum: student name, repository name, skill name,
   confidence, and evidence text, for every matching row.
8. **Do not calculate a final candidate ranking.** Retrieval only. Scoring
   is performed externally by Module C, after Genie's output is returned.
