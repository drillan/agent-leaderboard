"""Database schema definitions for DuckDB.

This module contains all DDL statements for creating tables, indexes,
and views in the DuckDB database.
"""

# Schema version for migration tracking
SCHEMA_VERSION = 1

# DDL for schema metadata table
CREATE_SCHEMA_METADATA_TABLE = """
CREATE TABLE IF NOT EXISTS schema_metadata (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

# DDL for task_submissions table
CREATE_TASK_SUBMISSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS task_submissions (
    id INTEGER PRIMARY KEY,
    prompt TEXT NOT NULL CHECK(length(trim(prompt)) > 0),
    submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_TASK_SUBMISSIONS_INDEX = """
CREATE INDEX IF NOT EXISTS idx_task_submissions_submitted_at
ON task_submissions(submitted_at DESC);
"""

# DDL for agent_executions table
CREATE_AGENT_EXECUTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS agent_executions (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES task_submissions(id),
    model_provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('running', 'completed', 'failed', 'timeout')),
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds REAL,
    token_count INTEGER,
    all_messages JSON,
    FOREIGN KEY (task_id) REFERENCES task_submissions(id) ON DELETE CASCADE
);
"""

CREATE_AGENT_EXECUTIONS_TASK_ID_INDEX = """
CREATE INDEX IF NOT EXISTS idx_agent_executions_task_id
ON agent_executions(task_id);
"""

CREATE_AGENT_EXECUTIONS_STATUS_INDEX = """
CREATE INDEX IF NOT EXISTS idx_agent_executions_status
ON agent_executions(status);
"""

CREATE_AGENT_EXECUTIONS_STARTED_AT_INDEX = """
CREATE INDEX IF NOT EXISTS idx_agent_executions_started_at
ON agent_executions(started_at DESC);
"""

# DDL for evaluations table
CREATE_EVALUATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY,
    execution_id INTEGER NOT NULL REFERENCES agent_executions(id),
    score INTEGER NOT NULL CHECK(score >= 0 AND score <= 100),
    explanation TEXT NOT NULL CHECK(length(trim(explanation)) > 0),
    evaluated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (execution_id) REFERENCES agent_executions(id) ON DELETE CASCADE
);
"""

CREATE_EVALUATIONS_EXECUTION_ID_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_evaluations_execution_id
ON evaluations(execution_id);
"""

CREATE_EVALUATIONS_SCORE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_evaluations_score
ON evaluations(score DESC);
"""

# DDL for leaderboard view
CREATE_LEADERBOARD_VIEW = """
CREATE OR REPLACE VIEW leaderboard_entries AS
SELECT
    ae.id AS execution_id,
    ae.task_id,
    ae.model_provider,
    ae.model_name,
    ae.status,
    ae.duration_seconds,
    ae.token_count,
    ae.all_messages,
    ev.score,
    ev.explanation AS evaluation_text,
    ts.prompt,
    ts.submitted_at
FROM agent_executions ae
JOIN evaluations ev ON ae.id = ev.execution_id
JOIN task_submissions ts ON ae.task_id = ts.id
ORDER BY ev.score DESC, ae.duration_seconds ASC;
"""

# All DDL statements in execution order
ALL_DDL_STATEMENTS = [
    CREATE_SCHEMA_METADATA_TABLE,
    CREATE_TASK_SUBMISSIONS_TABLE,
    CREATE_TASK_SUBMISSIONS_INDEX,
    CREATE_AGENT_EXECUTIONS_TABLE,
    CREATE_AGENT_EXECUTIONS_TASK_ID_INDEX,
    CREATE_AGENT_EXECUTIONS_STATUS_INDEX,
    CREATE_AGENT_EXECUTIONS_STARTED_AT_INDEX,
    CREATE_EVALUATIONS_TABLE,
    CREATE_EVALUATIONS_EXECUTION_ID_INDEX,
    CREATE_EVALUATIONS_SCORE_INDEX,
    CREATE_LEADERBOARD_VIEW,
]
