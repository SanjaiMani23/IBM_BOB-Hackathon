-- DevFlow CodeLens — Seed data for development / demo
-- Run after schema.sql:  psql -U devflow -d devflow -f seed.sql

-- Demo user  (password: devflow123)
-- Hash generated with passlib: bcrypt.hash("devflow123")
INSERT INTO users (id, email, full_name, hashed_password, is_active)
VALUES (
    'seed-user-0001',
    'demo@devflow.local',
    'Demo Developer',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TsCHSKyF7GdSHBvXkzEmLqKMrJbO',
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- Demo repository
INSERT INTO repositories (id, full_name, owner_id, description, default_branch, language)
VALUES (
    'seed-repo-0001',
    'acme-corp/checkout-service',
    'seed-user-0001',
    'E-commerce checkout microservice',
    'main',
    'JavaScript'
) ON CONFLICT (full_name) DO NOTHING;

-- Demo analysis
INSERT INTO code_analyses (id, repository, branch, commit_sha, files_analyzed, total_findings, duration_ms)
VALUES (
    'seed-analysis-0001',
    'acme-corp/checkout-service',
    'feature/payment-refactor',
    'a7f3c2e',
    7,
    8,
    1420
);

-- Demo findings
INSERT INTO findings (id, analysis_id, title, severity, finding_type, explanation, recommendation, file_path, line_number, confidence)
VALUES
    ('seed-finding-0001', 'seed-analysis-0001', 'SQL injection vector removed — verify migration',
     'critical', 'security',
     'Raw string interpolation was found in a SQL query. The diff shows it was changed to a parameterized query, but other callsites may still be vulnerable.',
     'Run a codebase-wide audit of all db.query() callsites.',
     'src/services/payment.js', 69, 'confirmed'),
    ('seed-finding-0002', 'seed-analysis-0001', 'Potential null reference',
     'high', 'bug',
     'Response object accessed without null validation.',
     'Add optional chaining (?.) or explicit null guard before accessing result properties.',
     'src/services/payment.js', 44, 'likely'),
    ('seed-finding-0003', 'seed-analysis-0001', 'Repeated async call inside loop',
     'high', 'optimization',
     'getPrice() awaited inside for...of loop causes N serial database round-trips.',
     'Batch the price lookup with a single query outside the loop.',
     'src/services/payment.js', 73, 'confirmed'),
    ('seed-finding-0004', 'seed-analysis-0001', 'Console.log left in production path',
     'low', 'quality',
     'console.log outputs sensitive order data to server logs.',
     'Remove or replace with a structured logger.',
     'src/routes/checkout.js', 12, 'confirmed');

-- Demo friction logs (30 days of sample data)
INSERT INTO friction_logs (repository, metric_name, metric_value, pr_number, recorded_at)
VALUES
    ('acme-corp/checkout-service', 'time_to_merge_hours', 18.5, 101, NOW() - INTERVAL '25 days'),
    ('acme-corp/checkout-service', 'time_to_merge_hours', 6.2,  102, NOW() - INTERVAL '20 days'),
    ('acme-corp/checkout-service', 'time_to_merge_hours', 42.0, 103, NOW() - INTERVAL '15 days'),
    ('acme-corp/checkout-service', 'time_to_merge_hours', 9.8,  104, NOW() - INTERVAL '10 days'),
    ('acme-corp/checkout-service', 'time_to_merge_hours', 24.1, 105, NOW() - INTERVAL '5 days'),
    ('acme-corp/checkout-service', 'review_cycles', 2.0, 101, NOW() - INTERVAL '25 days'),
    ('acme-corp/checkout-service', 'review_cycles', 1.0, 102, NOW() - INTERVAL '20 days'),
    ('acme-corp/checkout-service', 'review_cycles', 3.0, 103, NOW() - INTERVAL '15 days'),
    ('acme-corp/checkout-service', 'review_cycles', 1.0, 104, NOW() - INTERVAL '10 days'),
    ('acme-corp/checkout-service', 'review_cycles', 2.0, 105, NOW() - INTERVAL '5 days');
