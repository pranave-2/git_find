-- DRAFT schema for standalone Genie configuration and testing.
--
-- Person C owns and publishes the real DB schema to /shared. This file lets
-- Module D (Genie space setup) start configuring metadata, relationships and
-- synonyms on hour 2 without waiting for that publish. At Checkpoint 1,
-- reconcile column-for-column against C's real DDL and delete this notice.
--
-- Entities per ARCHITECTURE.md Section 3-6: STUDENT, REPOSITORY, SKILL,
-- REPOSITORY_SKILL, SKILL_EVIDENCE, JOB, JOB_REGISTRATION.

CREATE TABLE IF NOT EXISTS student (
    student_id       STRING NOT NULL,   -- e.g. 'S001'
    name             STRING NOT NULL,
    github_username  STRING NOT NULL,
    email            STRING,
    CONSTRAINT pk_student PRIMARY KEY (student_id)
);

CREATE TABLE IF NOT EXISTS repository (
    repo_id       STRING NOT NULL,      -- e.g. 'R001'
    student_id    STRING NOT NULL,
    repo_name     STRING NOT NULL,
    repo_url      STRING,
    summary       STRING,               -- Gemini repo summary (Module B), written once at ingestion
    commit_sha    STRING,
    ingested_at   TIMESTAMP,
    CONSTRAINT pk_repository PRIMARY KEY (repo_id),
    CONSTRAINT fk_repository_student FOREIGN KEY (student_id) REFERENCES student(student_id)
);

CREATE TABLE IF NOT EXISTS skill (
    skill_id     STRING NOT NULL,       -- e.g. 'SK01'
    skill_name   STRING NOT NULL,
    category     STRING,                -- Programming | Framework | Backend | Database | DevOps | Cloud
    description  STRING,
    CONSTRAINT pk_skill PRIMARY KEY (skill_id)
);

CREATE TABLE IF NOT EXISTS repository_skill (
    repo_id      STRING NOT NULL,
    skill_id     STRING NOT NULL,
    confidence   DOUBLE NOT NULL,       -- deterministic Evidence Score in [0,1] from Module C. NOT an LLM output.
    formula_version STRING,
    computed_at  TIMESTAMP,
    CONSTRAINT pk_repository_skill PRIMARY KEY (repo_id, skill_id),
    CONSTRAINT fk_rs_repository FOREIGN KEY (repo_id) REFERENCES repository(repo_id),
    CONSTRAINT fk_rs_skill FOREIGN KEY (skill_id) REFERENCES skill(skill_id)
);

CREATE TABLE IF NOT EXISTS skill_evidence (
    evidence_id  STRING NOT NULL,       -- e.g. 'E001'
    repo_id      STRING NOT NULL,
    skill_id     STRING NOT NULL,
    evidence     STRING NOT NULL,       -- natural-language evidence text (Module B), shown to the recruiter
    CONSTRAINT pk_skill_evidence PRIMARY KEY (evidence_id),
    CONSTRAINT fk_se_repository FOREIGN KEY (repo_id) REFERENCES repository(repo_id),
    CONSTRAINT fk_se_skill FOREIGN KEY (skill_id) REFERENCES skill(skill_id)
);

CREATE TABLE IF NOT EXISTS job (
    job_id       STRING NOT NULL,       -- e.g. 'J001'
    title        STRING NOT NULL,
    jd_text      STRING NOT NULL,       -- raw JD, unmodified — this is what Genie reads
    created_at   TIMESTAMP,
    CONSTRAINT pk_job PRIMARY KEY (job_id)
);

CREATE TABLE IF NOT EXISTS job_registration (
    job_id       STRING NOT NULL,
    student_id   STRING NOT NULL,
    CONSTRAINT pk_job_registration PRIMARY KEY (job_id, student_id),
    CONSTRAINT fk_jr_job FOREIGN KEY (job_id) REFERENCES job(job_id),
    CONSTRAINT fk_jr_student FOREIGN KEY (student_id) REFERENCES student(student_id)
);
