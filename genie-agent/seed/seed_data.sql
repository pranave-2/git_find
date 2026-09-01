-- Fabricated seed data, straight out of ARCHITECTURE.md Sections 3, 4, 5, 6.
-- Load this into the dev warehouse so the Genie space can be configured and
-- queried end-to-end before real ingestion (Modules A/B) exists.

INSERT INTO student (student_id, name, github_username) VALUES
('S001', 'Rahul', 'rahul-dev'),
('S002', 'Priya', 'priya-code'),
('S003', 'Arjun', 'arjun-dev');

INSERT INTO repository (repo_id, student_id, repo_name, summary) VALUES
('R001', 'S001', 'ecommerce-api',      'Backend e-commerce REST service'),
('R002', 'S001', 'ml-price-predictor', 'ML-based price prediction'),
('R003', 'S001', 'chatbot',            'Python chatbot application'),
('R004', 'S002', 'banking-api',        'Banking REST API'),
('R005', 'S002', 'cloud-monitor',      'Cloud monitoring system'),
('R006', 'S003', 'spring-backend',     'Java Spring backend');

INSERT INTO skill (skill_id, skill_name, category, description) VALUES
('SK01', 'Python',      'Programming', 'Python programming language'),
('SK02', 'FastAPI',     'Framework',   'Python web framework'),
('SK03', 'Flask',       'Framework',   'Python web framework'),
('SK04', 'REST API',    'Backend',     'HTTP API development'),
('SK05', 'PostgreSQL',  'Database',    'Relational database'),
('SK06', 'Docker',      'DevOps',      'Containerization'),
('SK07', 'AWS',         'Cloud',       'AWS cloud platform'),
('SK08', 'Java',        'Programming', 'Java programming language'),
('SK09', 'Spring Boot', 'Framework',   'Java backend framework');

INSERT INTO repository_skill (repo_id, skill_id, confidence) VALUES
('R001', 'SK01', 0.98), ('R001', 'SK02', 0.96), ('R001', 'SK04', 0.95), ('R001', 'SK05', 0.92),
('R002', 'SK01', 0.90),
('R003', 'SK01', 0.75), ('R003', 'SK06', 0.85),
('R004', 'SK01', 0.91), ('R004', 'SK04', 0.94),
('R005', 'SK06', 0.88), ('R005', 'SK07', 0.93),
('R006', 'SK08', 0.97), ('R006', 'SK09', 0.96);

INSERT INTO skill_evidence (evidence_id, repo_id, skill_id, evidence) VALUES
('E001', 'R001', 'SK01', 'Backend services implemented in Python'),
('E002', 'R001', 'SK02', 'REST endpoints implemented using FastAPI'),
('E003', 'R001', 'SK04', 'Product and order endpoints exposed through REST'),
('E004', 'R001', 'SK05', 'PostgreSQL used for application persistence'),
('E005', 'R002', 'SK01', 'ML preprocessing and prediction pipeline implemented in Python'),
('E006', 'R003', 'SK01', 'Chatbot backend implemented in Python'),
('E007', 'R003', 'SK06', 'Application containerized using Docker'),
('E008', 'R004', 'SK01', 'Banking backend implemented using Python'),
('E009', 'R004', 'SK04', 'Banking services exposed through REST APIs'),
('E010', 'R005', 'SK06', 'Monitoring application containerized with Docker'),
('E011', 'R005', 'SK07', 'Monitoring infrastructure deployed using AWS');

INSERT INTO job (job_id, title, jd_text) VALUES
('J001', 'Backend Software Engineer',
 'We are looking for candidates with strong experience developing production-grade backend services using Python. Experience building REST APIs is required. Experience with FastAPI or Flask is preferred. PostgreSQL and Docker experience are preferred. AWS experience is a plus.');

INSERT INTO job_registration (job_id, student_id) VALUES
('J001', 'S001'), ('J001', 'S002'), ('J001', 'S003');
