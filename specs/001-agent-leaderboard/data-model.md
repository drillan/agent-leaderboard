# Data Model: Multi-Agent Competition System

**Feature**: Multi-Agent Competition System
**Date**: 2025-10-31
**Purpose**: Define data entities, relationships, validation rules, and persistence schema

## Overview

This document defines the data model for the multi-agent competition system, including domain entities, database schema, and validation rules. The model supports parallel agent execution, evaluation, historical tracking, and performance metrics visualization.

## Domain Entities

### 1. ModelConfiguration

Represents an AI model configuration for task agents or evaluation agent.

**Attributes**:
- `provider: str` - AI provider name ("openai", "anthropic", "gemini")
- `model: str` - Model identifier (e.g., "gpt-4o", "claude-sonnet-4")
- `api_key_env: str` - Environment variable name for API key
- `role: str` - "task_agent" or "evaluation_agent"
- `enabled: bool` - Whether this model is active

**Validation Rules**:
- `provider` must be one of supported providers
- `model` must be non-empty string
- `api_key_env` must reference existing environment variable
- `role` must be "task_agent" or "evaluation_agent"

**Source**: FR-017, FR-021

**Persistence**: Stored in TOML configuration file, loaded into memory

### 2. TaskSubmission

Represents a user's natural language prompt for task execution.

**Attributes**:
- `id: int` - Primary key
- `prompt: str` - Natural language task description
- `submitted_at: datetime` - Submission timestamp

**Validation Rules**:
- `prompt` must be non-empty after stripping whitespace
- `submitted_at` auto-generated at creation

**Relationships**:
- One TaskSubmission has many AgentExecutions

**Source**: FR-001, Entity definition from spec

**Persistence**: DuckDB table `task_submissions`

### 3. AgentExecution

Represents a single agent's attempt to complete a task.

**Attributes**:
- `id: int` - Primary key
- `task_id: int` - Foreign key to TaskSubmission
- `model_provider: str` - AI provider used
- `model_name: str` - Model identifier used
- `status: str` - Execution status ("running", "completed", "failed", "timeout")
- `started_at: datetime` - Execution start timestamp
- `completed_at: datetime | None` - Execution completion timestamp
- `duration_seconds: float | None` - Execution duration
- `token_count: int | None` - Total tokens consumed
- `all_messages_json: str` - Pydantic AI's all_messages_json output

**Validation Rules**:
- `status` must be one of: "running", "completed", "failed", "timeout"
- `duration_seconds` calculated as `completed_at - started_at` if both exist
- `all_messages_json` must be valid JSON string

**Relationships**:
- Many AgentExecutions belong to one TaskSubmission
- One AgentExecution has one EvaluationResult

**Lifecycle States**:
1. **running** - Agent is currently executing
2. **completed** - Agent finished successfully
3. **failed** - Agent encountered error during execution
4. **timeout** - Agent exceeded configured timeout (FR-028, FR-029)

**Source**: FR-002, FR-005, FR-028, FR-029, Entity definition from spec

**Persistence**: DuckDB table `agent_executions`

### 4. ToolCall

Represents a single invocation of a utility tool by an agent.

**Attributes**:
- `tool_name: str` - Tool identifier
- `input_parameters: dict` - Tool input arguments
- `output_result: any` - Tool return value
- `timestamp: datetime` - Call timestamp
- `parent_id: str | None` - Parent tool call ID (for nesting)

**Validation Rules**:
- `tool_name` must be one of: "get_datetime", "check_prime", "check_palindrome"
- `input_parameters` schema validated per tool

**Relationships**:
- Extracted from AgentExecution.all_messages_json (not stored as separate table)
- Hierarchical parent-child relationships for nested calls

**Source**: FR-003, FR-004, FR-015, Entity definition from spec

**Persistence**: Embedded in AgentExecution.all_messages_json (JSON column)

### 5. EvaluationResult

Represents the evaluation agent's assessment of an agent execution.

**Attributes**:
- `id: int` - Primary key
- `execution_id: int` - Foreign key to AgentExecution
- `score: int` - Numeric score (0-100)
- `explanation: str` - Text explanation of score
- `evaluated_at: datetime` - Evaluation timestamp

**Validation Rules**:
- `score` must be between 0 and 100 (inclusive)
- `explanation` must be non-empty string
- `evaluated_at` auto-generated at creation

**Relationships**:
- Many EvaluationResults belong to one AgentExecution

**Source**: FR-006, Entity definition from spec

**Persistence**: DuckDB table `evaluations`

### 6. PerformanceMetrics

Represents resource consumption data for an agent execution.

**Attributes**:
- `execution_id: int` - Foreign key to AgentExecution
- `duration_seconds: float` - Execution time
- `token_count: int` - Total tokens used

**Validation Rules**:
- `duration_seconds` must be > 0
- `token_count` must be >= 0

**Relationships**:
- Derived from AgentExecution (not separate table)

**Source**: FR-012, Entity definition from spec

**Persistence**: Columns in `agent_executions` table

### 7. LeaderboardEntry

Represents a single row in the leaderboard display.

**Attributes**:
- `execution_id: int` - AgentExecution ID
- `model_name: str` - AI model identifier
- `score: int` - Evaluation score
- `evaluation_text: str` - Evaluation explanation
- `task_output: str` - Agent's final result
- `tool_hierarchy: list[dict]` - Hierarchical tool call tree
- `duration_seconds: float` - Execution duration
- `token_count: int` - Token consumption

**Validation Rules**:
- Aggregated view (not stored entity)
- All fields derived from AgentExecution + EvaluationResult

**Relationships**:
- Joins AgentExecution and EvaluationResult

**Source**: FR-009, Entity definition from spec

**Persistence**: SQL view (query-time join)

## Database Schema (DuckDB)

### Table: task_submissions

```sql
CREATE TABLE task_submissions (
    id INTEGER PRIMARY KEY,
    prompt TEXT NOT NULL CHECK(length(trim(prompt)) > 0),
    submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_task_submissions_submitted_at
ON task_submissions(submitted_at DESC);
```

### Table: agent_executions

```sql
CREATE TABLE agent_executions (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES task_submissions(id),
    model_provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('running', 'completed', 'failed', 'timeout')),
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds REAL,
    token_count INTEGER,
    all_messages JSON,  -- DuckDB native JSON type
    FOREIGN KEY (task_id) REFERENCES task_submissions(id) ON DELETE CASCADE
);

CREATE INDEX idx_agent_executions_task_id
ON agent_executions(task_id);

CREATE INDEX idx_agent_executions_status
ON agent_executions(status);

CREATE INDEX idx_agent_executions_started_at
ON agent_executions(started_at DESC);
```

### Table: evaluations

```sql
CREATE TABLE evaluations (
    id INTEGER PRIMARY KEY,
    execution_id INTEGER NOT NULL REFERENCES agent_executions(id),
    score INTEGER NOT NULL CHECK(score >= 0 AND score <= 100),
    explanation TEXT NOT NULL CHECK(length(trim(explanation)) > 0),
    evaluated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (execution_id) REFERENCES agent_executions(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX idx_evaluations_execution_id
ON evaluations(execution_id);

CREATE INDEX idx_evaluations_score
ON evaluations(score DESC);
```

### View: leaderboard_entries

```sql
CREATE VIEW leaderboard_entries AS
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
```

## Configuration Data Model (TOML)

### Configuration Schema

```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class ModelConfig(BaseModel):
    provider: Literal["openai", "anthropic", "gemini"]
    model: str = Field(min_length=1)
    api_key_env: str = Field(min_length=1)

    @field_validator('api_key_env')
    def validate_api_key_env(cls, v):
        import os
        if v not in os.environ:
            raise ValueError(f"Environment variable {v} not found")
        return v

class ExecutionConfig(BaseModel):
    timeout_seconds: int = Field(default=60, ge=1, le=600)

class EvaluationConfig(BaseModel):
    provider: Literal["openai", "anthropic", "gemini"]
    model: str = Field(min_length=1)
    api_key_env: str = Field(min_length=1)
    prompt: str = Field(default=DEFAULT_EVALUATION_PROMPT)

class DatabaseConfig(BaseModel):
    path: str = Field(default="agent_leaderboard.duckdb")

class AppConfig(BaseModel):
    execution: ExecutionConfig
    task_agents: list[ModelConfig] = Field(min_length=2, max_length=5)
    evaluation_agent: EvaluationConfig
    database: DatabaseConfig

    @field_validator('task_agents')
    def validate_unique_models(cls, v):
        models = [(m.provider, m.model) for m in v]
        if len(models) != len(set(models)):
            raise ValueError("Duplicate models detected in task_agents")
        return v
```

## Entity Relationships Diagram

```
┌─────────────────┐
│ TaskSubmission  │
│ ─────────────── │
│ id (PK)         │
│ prompt          │
│ submitted_at    │
└────────┬────────┘
         │ 1
         │
         │ N
┌────────▼────────────┐       ┌──────────────────┐
│ AgentExecution      │ 1   1 │ EvaluationResult │
│ ─────────────────── │───────│ ──────────────── │
│ id (PK)             │       │ id (PK)          │
│ task_id (FK)        │       │ execution_id (FK)│
│ model_provider      │       │ score            │
│ model_name          │       │ explanation      │
│ status              │       │ evaluated_at     │
│ started_at          │       └──────────────────┘
│ completed_at        │
│ duration_seconds    │
│ token_count         │
│ all_messages (JSON) │
└─────────────────────┘
         │
         │ (embedded)
         │
┌────────▼────────┐
│ ToolCall        │ (extracted from all_messages)
│ ─────────────── │
│ tool_name       │
│ input_params    │
│ output_result   │
│ timestamp       │
│ parent_id       │
└─────────────────┘
```

## Validation Rules Summary

| Entity | Field | Validation |
|--------|-------|------------|
| TaskSubmission | prompt | Non-empty after trim |
| AgentExecution | status | One of: running, completed, failed, timeout |
| AgentExecution | all_messages | Valid JSON |
| EvaluationResult | score | 0 <= score <= 100 |
| EvaluationResult | explanation | Non-empty after trim |
| ModelConfig | provider | One of: openai, anthropic, gemini |
| ModelConfig | api_key_env | Exists in environment |
| AppConfig | task_agents | 2-5 unique models |
| ExecutionConfig | timeout_seconds | 1 <= timeout <= 600 |

## Data Access Patterns

### Query: Get latest execution for leaderboard display

```sql
SELECT * FROM leaderboard_entries
WHERE task_id = ?
ORDER BY score DESC, duration_seconds ASC;
```

### Query: Get historical executions

```sql
SELECT
    ts.id,
    ts.prompt,
    ts.submitted_at,
    COUNT(ae.id) AS agent_count,
    AVG(ev.score) AS avg_score
FROM task_submissions ts
JOIN agent_executions ae ON ts.id = ae.task_id
LEFT JOIN evaluations ev ON ae.id = ev.execution_id
GROUP BY ts.id, ts.prompt, ts.submitted_at
ORDER BY ts.submitted_at DESC
LIMIT 50;
```

### Query: Get performance metrics for chart

```sql
SELECT
    model_name,
    AVG(duration_seconds) AS avg_duration,
    AVG(token_count) AS avg_tokens
FROM agent_executions
WHERE status = 'completed'
  AND task_id = ?
GROUP BY model_name;
```

## Migration Strategy

1. **Initial Schema Creation**: Run DDL on first application start
2. **Schema Versioning**: Store schema version in metadata table
3. **Migration Scripts**: Future schema changes via numbered migration files

```sql
CREATE TABLE IF NOT EXISTS schema_metadata (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_metadata (version) VALUES (1);
```

## Data Retention

- No automatic deletion of historical data
- Manual cleanup via UI or script (future enhancement)
- DuckDB file size monitored for warnings

## Implementation Notes

1. **JSON Column Usage**: DuckDB's native JSON type allows indexing and querying
2. **Cascading Deletes**: ON DELETE CASCADE ensures referential integrity
3. **Index Strategy**: Optimized for leaderboard queries (score DESC) and history browsing (submitted_at DESC)
4. **Concurrency**: DuckDB handles concurrent reads; writes serialized via connection pool
5. **Type Safety**: Pydantic models enforce validation before database writes

## Success Criteria Mapping

- **SC-002**: Leaderboard view query returns >= 2 agents per task
- **SC-013**: all_messages_json stored in DuckDB for 100% of executions
- **SC-014**: Performance chart queries execute efficiently (<100ms)
- **SC-016**: Historical executions queryable and displayable

This data model supports all functional requirements and success criteria defined in the specification.
