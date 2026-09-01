-- =============================================================================
-- Recruitment Genie: Canonical Database Schema DDL
-- Owned by Module C (Person C)
-- All table definitions, foreign keys, and indices for the platform.
-- =============================================================================

-- 1. Student Table
CREATE TABLE IF NOT EXISTS student (
    student_id          VARCHAR(32) PRIMARY KEY,      -- Format: S001, S002...
    name                VARCHAR(128) NOT NULL,
    email               VARCHAR(255),
    github_username     VARCHAR(39) NOT NULL UNIQUE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Repository Table
CREATE TABLE IF NOT EXISTS repository (
    repo_id             VARCHAR(32) PRIMARY KEY,      -- Format: R001, R002...
    student_id          VARCHAR(32) NOT NULL REFERENCES student(student_id) ON DELETE CASCADE,
    repo_name           VARCHAR(128) NOT NULL,
    repo_url            TEXT NOT NULL,
    default_branch      VARCHAR(64) DEFAULT 'main',
    commit_sha          VARCHAR(40),
    summary             TEXT,                         -- Module B one-paragraph repo summary
    is_fork             BOOLEAN DEFAULT FALSE,
    stars               INTEGER DEFAULT 0,
    ingested_at         TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_repository_student_id ON repository(student_id);

-- 3. Skill Vocabulary Table
CREATE TABLE IF NOT EXISTS skill (
    skill_id            VARCHAR(32) PRIMARY KEY,      -- Format: SK01, SK02...
    skill_name          VARCHAR(64) NOT NULL UNIQUE,  -- Canonical name (e.g. 'Python', 'Docker')
    category            VARCHAR(64),                  -- e.g. 'Language', 'Framework', 'Database'
    description         TEXT
);

-- 4. Repository Skill (Deterministic Evidence Score from Module C.1)
CREATE TABLE IF NOT EXISTS repository_skill (
    repo_id             VARCHAR(32) NOT NULL REFERENCES repository(repo_id) ON DELETE CASCADE,
    skill_id            VARCHAR(32) NOT NULL REFERENCES skill(skill_id) ON DELETE CASCADE,
    confidence          DECIMAL(5, 4) NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0), -- Evidence Score [0.0, 1.0]
    formula_version     VARCHAR(32) DEFAULT 'evidence-v1',
    computed_at         TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (repo_id, skill_id)
);

CREATE INDEX IF NOT EXISTS idx_repository_skill_skill_id ON repository_skill(skill_id);

-- 5. Skill Evidence (Audit trail / NL explanation & signal breakdown)
CREATE TABLE IF NOT EXISTS skill_evidence (
    evidence_id         VARCHAR(32) PRIMARY KEY,      -- Format: E001, E002...
    repo_id             VARCHAR(32) NOT NULL,
    skill_id            VARCHAR(32) NOT NULL,
    evidence            TEXT NOT NULL,                -- 1-sentence NL explanation from Module B
    signals_json        JSON,                         -- Signal values, matches & weights breakdown
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repo_id, skill_id) REFERENCES repository_skill(repo_id, skill_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_skill_evidence_repo_skill ON skill_evidence(repo_id, skill_id);

-- 6. Job Posting Table
CREATE TABLE IF NOT EXISTS job (
    job_id              VARCHAR(32) PRIMARY KEY,      -- Format: J001, J002...
    title               VARCHAR(200) NOT NULL,
    jd_text             TEXT NOT NULL,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Job Registration (Students in scope for a specific job)
CREATE TABLE IF NOT EXISTS job_registration (
    job_id              VARCHAR(32) NOT NULL REFERENCES job(job_id) ON DELETE CASCADE,
    student_id          VARCHAR(32) NOT NULL REFERENCES student(student_id) ON DELETE CASCADE,
    registered_at       TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (job_id, student_id)
);

CREATE INDEX IF NOT EXISTS idx_job_registration_student_id ON job_registration(student_id);
