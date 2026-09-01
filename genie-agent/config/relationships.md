# Layer 2 — Table relationships

Pasted into the Genie space's relationship/join configuration so Genie
doesn't have to infer joins from column names alone.

```
student            (student_id)
  └─ 1:N ─ repository          (student_id)  join key: student_id
              └─ 1:N ─ repository_skill      (repo_id)     join key: repo_id
                          └─ N:1 ─ skill                    join key: skill_id
              └─ 1:N ─ skill_evidence        (repo_id)     join key: repo_id
                          └─ N:1 ─ skill                    join key: skill_id

job                (job_id)
  └─ 1:N ─ job_registration    (job_id)      join key: job_id
              └─ N:1 ─ student               join key: student_id
```

Composite join for evidence retrieval (both keys required, not just repo_id):

```
repository_skill.repo_id  = skill_evidence.repo_id
AND
repository_skill.skill_id = skill_evidence.skill_id
```

This composite condition is worth calling out explicitly — a join on
`repo_id` alone will cross-join every skill's evidence against every other
skill's confidence for the same repo.
