# Layer 5 — Example questions / SQL patterns

Given to the Genie space as representative query patterns (Databricks
"example SQL" / "sample questions" feature), so Genie generalizes correctly
to a JD it hasn't seen before.

### Example 1

> "Find all registered candidates who have Python evidence and show the
> repositories and confidence."

```sql
SELECT s.name, r.repo_name, rs.confidence
FROM job_registration jr
JOIN student s ON jr.student_id = s.student_id
JOIN repository r ON s.student_id = r.student_id
JOIN repository_skill rs ON r.repo_id = rs.repo_id
JOIN skill sk ON rs.skill_id = sk.skill_id
WHERE jr.job_id = 'J001' AND sk.skill_name = 'Python';
```

### Example 2

> "For each candidate, retrieve all repositories demonstrating the required
> skills."

```sql
SELECT s.name, sk.skill_name, r.repo_name, rs.confidence, se.evidence
FROM job_registration jr
JOIN student s ON jr.student_id = s.student_id
JOIN repository r ON s.student_id = r.student_id
JOIN repository_skill rs ON r.repo_id = rs.repo_id
JOIN skill sk ON rs.skill_id = sk.skill_id
JOIN skill_evidence se ON rs.repo_id = se.repo_id AND rs.skill_id = se.skill_id
WHERE jr.job_id = :job_id
AND sk.skill_name IN (:required_skill_names);
```

### Example 3

> "Find the strongest repository evidence for each candidate and skill."

```sql
SELECT s.name, sk.skill_name, r.repo_name, rs.confidence
FROM repository_skill rs
JOIN repository r ON rs.repo_id = r.repo_id
JOIN student s ON r.student_id = s.student_id
JOIN skill sk ON rs.skill_id = sk.skill_id
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY s.student_id, sk.skill_id ORDER BY rs.confidence DESC
) = 1;
```

**All three are illustrative.** Genie generates the actual query at request
time — these exist to teach it the intended join pattern and column
selection, not to be executed verbatim.
