# Internal API Contract: Multi-Agent Competition System

**Feature**: Multi-Agent Competition System
**Date**: 2025-10-31
**Purpose**: Define internal module interfaces and contracts for component integration

## Overview

This system does not expose external REST or GraphQL APIs. Instead, it defines internal Python module contracts for interaction between UI components, business logic, and persistence layers. All interfaces use type-safe Python protocols and Pydantic models.

## Module Contracts

### 1. Configuration Module (`src/config/`)

#### Interface: ConfigLoader

```python
from pydantic import BaseModel
from pathlib import Path

class ConfigLoader:
    """Loads and validates TOML configuration."""

    @staticmethod
    def load(config_path: Path) -> AppConfig:
        """Load configuration from TOML file.

        Args:
            config_path: Path to config.toml file

        Returns:
            Validated AppConfig instance

        Raises:
            FileNotFoundError: Config file not found
            ValueError: Invalid configuration (validation errors)
        """
        ...

    @staticmethod
    def save(config: AppConfig, config_path: Path) -> None:
        """Save configuration to TOML file.

        Args:
            config: AppConfig instance to save
            config_path: Path to config.toml file

        Raises:
            IOError: Failed to write file
        """
        ...
```

**Contract Requirements**:
- Must validate all fields per AppConfig Pydantic model
- Must check environment variables referenced in api_key_env fields
- Must enforce 2-5 task agents constraint (FR-019)
- Must provide clear error messages for validation failures

**Used By**: UI settings page, application initialization

**Source**: FR-017, FR-018, FR-019, FR-020

---

### 2. Database Module (`src/database/`)

#### Interface: DatabaseConnection

```python
from typing import Protocol
import duckdb

class DatabaseConnection(Protocol):
    """Database connection management."""

    def connect(self, db_path: str) -> duckdb.DuckDBPyConnection:
        """Establish connection to DuckDB database.

        Args:
            db_path: Path to DuckDB file

        Returns:
            Active database connection

        Raises:
            duckdb.Error: Connection failed
        """
        ...

    def initialize_schema(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Create tables and indexes if they don't exist.

        Args:
            conn: Active database connection

        Raises:
            duckdb.Error: Schema creation failed
        """
        ...

    def close(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Close database connection.

        Args:
            conn: Connection to close
        """
        ...
```

#### Interface: TaskRepository

```python
from typing import Protocol
from datetime import datetime
from src.models.task import TaskSubmission, AgentExecution, EvaluationResult

class TaskRepository(Protocol):
    """Repository for task-related database operations."""

    def create_task(self, prompt: str) -> int:
        """Create new task submission.

        Args:
            prompt: Natural language task description

        Returns:
            Task ID

        Raises:
            ValueError: Invalid prompt (empty)
            duckdb.Error: Database error
        """
        ...

    def create_execution(
        self,
        task_id: int,
        model_provider: str,
        model_name: str
    ) -> int:
        """Create new agent execution record.

        Args:
            task_id: Parent task ID
            model_provider: AI provider name
            model_name: Model identifier

        Returns:
            Execution ID

        Raises:
            ValueError: Invalid task_id
            duckdb.Error: Database error
        """
        ...

    def update_execution_result(
        self,
        execution_id: int,
        status: str,
        all_messages_json: str,
        duration_seconds: float,
        token_count: int
    ) -> None:
        """Update execution with results.

        Args:
            execution_id: Execution ID to update
            status: Final status ("completed", "failed", "timeout")
            all_messages_json: Pydantic AI message history
            duration_seconds: Execution time
            token_count: Tokens consumed

        Raises:
            ValueError: Invalid status or execution_id
            duckdb.Error: Database error
        """
        ...

    def create_evaluation(
        self,
        execution_id: int,
        score: int,
        explanation: str
    ) -> int:
        """Create evaluation result.

        Args:
            execution_id: Agent execution ID
            score: Numeric score (0-100)
            explanation: Text evaluation

        Returns:
            Evaluation ID

        Raises:
            ValueError: Invalid score or execution_id
            duckdb.Error: Database error
        """
        ...

    def get_leaderboard(self, task_id: int) -> list[dict]:
        """Get leaderboard entries for a task.

        Args:
            task_id: Task ID

        Returns:
            List of dicts with keys:
                execution_id, model_name, score, evaluation_text,
                duration_seconds, token_count, all_messages

        Raises:
            duckdb.Error: Database error
        """
        ...

    def get_task_history(self, limit: int = 50) -> list[dict]:
        """Get historical task executions.

        Args:
            limit: Maximum number of tasks to return

        Returns:
            List of dicts with keys:
                task_id, prompt, submitted_at, agent_count, avg_score

        Raises:
            duckdb.Error: Database error
        """
        ...

    def get_performance_metrics(self, task_id: int) -> list[dict]:
        """Get performance metrics for charts.

        Args:
            task_id: Task ID

        Returns:
            List of dicts with keys:
                model_name, avg_duration, avg_tokens

        Raises:
            duckdb.Error: Database error
        """
        ...
```

**Contract Requirements**:
- All methods must handle database errors gracefully
- Write operations must be transactional
- Queries must use parameterized statements (SQL injection prevention)
- Results must match data model schema

**Used By**: Execution orchestrator, UI components

**Source**: FR-008, FR-022, SC-013, SC-014

---

### 3. Agent Execution Module (`src/execution/`)

#### Interface: TaskExecutor

```python
from typing import Protocol
from src.models.execution import ExecutionResult

class TaskExecutor(Protocol):
    """Orchestrates parallel agent execution."""

    async def execute_task(
        self,
        task_id: int,
        prompt: str,
        agents: list[Agent],
        timeout: int
    ) -> list[ExecutionResult]:
        """Execute task across multiple agents in parallel.

        Args:
            task_id: Database task ID
            prompt: Natural language task
            agents: List of configured Pydantic AI agents
            timeout: Timeout in seconds per agent

        Returns:
            List of ExecutionResult (one per agent)

        Raises:
            ValueError: Invalid parameters
        """
        ...

    async def execute_single_agent(
        self,
        agent: Agent,
        prompt: str,
        timeout: int
    ) -> ExecutionResult | None:
        """Execute single agent with timeout.

        Args:
            agent: Pydantic AI agent instance
            prompt: Task prompt
            timeout: Timeout in seconds

        Returns:
            ExecutionResult or None if timeout/failure

        Raises:
            Exception: Unexpected errors (logged, not raised)
        """
        ...
```

#### Interface: EvaluationExecutor

```python
from typing import Protocol

class EvaluationExecutor(Protocol):
    """Executes evaluation agent."""

    async def evaluate_execution(
        self,
        eval_agent: Agent,
        task_prompt: str,
        agent_result: str,
        all_messages_json: str
    ) -> tuple[int, str]:
        """Evaluate agent execution.

        Args:
            eval_agent: Evaluation agent instance
            task_prompt: Original task prompt
            agent_result: Agent's final output
            all_messages_json: Full execution history

        Returns:
            Tuple of (score, explanation)

        Raises:
            ValueError: Evaluation failed or returned invalid score
        """
        ...
```

**Contract Requirements**:
- Must enforce timeout per agent (FR-028)
- Must treat timeout as failure with status="timeout" (FR-029)
- Must handle individual agent failures without blocking others (FR-011)
- Must record complete execution history (FR-005)

**Used By**: UI main page, background task runner

**Source**: FR-002, FR-006, FR-011, FR-028, FR-029

---

### 4. Tool Module (`src/agents/tools.py`)

#### Interface: Tool Functions

```python
from datetime import datetime

@tool
def get_datetime() -> str:
    """Get current datetime in ISO 8601 format.

    Returns:
        Current datetime string (e.g., "2025-10-31T12:34:56")
    """
    ...

@tool
def check_prime(n: int) -> bool:
    """Check if a number is prime.

    Args:
        n: Integer to check

    Returns:
        True if n is prime, False otherwise

    Raises:
        ValueError: n < 2
    """
    ...

@tool
def check_palindrome(text: str) -> bool:
    """Check if text is a palindrome.

    Args:
        text: String to check (case-insensitive)

    Returns:
        True if palindrome, False otherwise
    """
    ...
```

**Contract Requirements**:
- All tools must be pure functions (no side effects)
- All tools must have complete docstrings
- All tools must handle invalid inputs with clear errors
- Tools must be compatible with Pydantic AI's @tool decorator

**Used By**: Task agents (dynamically called during execution)

**Source**: FR-003, FR-004

---

### 5. UI Module (`src/ui/`)

#### Interface: UI Components

```python
from nicegui import ui
from typing import Protocol, Callable

class InputForm(Protocol):
    """Task input form component."""

    def render(
        self,
        on_submit: Callable[[str], None]
    ) -> None:
        """Render multi-line text input and submit button.

        Args:
            on_submit: Callback when user clicks execute button
                       Receives prompt text as argument
        """
        ...

class StatusDisplay(Protocol):
    """Execution status display component."""

    def render(
        self,
        execution_state: dict[str, str]
    ) -> None:
        """Render real-time agent status.

        Args:
            execution_state: Dict mapping model_name -> status
                            Status: "running" | "completed" | "failed"
        """
        ...

    def update(
        self,
        model_name: str,
        status: str
    ) -> None:
        """Update status for specific agent.

        Args:
            model_name: Model identifier
            status: New status
        """
        ...

class LeaderboardTable(Protocol):
    """Leaderboard display component."""

    def render(
        self,
        entries: list[dict]
    ) -> None:
        """Render leaderboard table sorted by score.

        Args:
            entries: List of leaderboard entries from database
                    Each entry must have: model_name, score,
                    evaluation_text, duration_seconds, token_count
        """
        ...

class ToolCallTree(Protocol):
    """Hierarchical tool call tree component."""

    def render(
        self,
        tool_calls: list[dict]
    ) -> None:
        """Render tool call hierarchy using ui.tree().

        Args:
            tool_calls: Hierarchical tool call data
                       Format: [{'id': str, 'label': str, 'children': [...]}]
        """
        ...

class PerformanceCharts(Protocol):
    """Performance metrics chart component."""

    def render(
        self,
        metrics: list[dict]
    ) -> None:
        """Render Plotly charts for performance metrics.

        Args:
            metrics: List of dicts with keys:
                    model_name, avg_duration, avg_tokens
        """
        ...
```

**Contract Requirements**:
- All components must handle empty data gracefully
- All components must update reactively when data changes
- All components must follow NiceGUI best practices
- All callbacks must be async-safe

**Used By**: UI pages (main, history, performance)

**Source**: FR-001, FR-007, FR-009, FR-013, FR-014, FR-015, FR-023, FR-024, FR-025

---

## Data Flow Contract

### Workflow: Task Execution

```
User Input (UI)
    ↓ (prompt: str)
TaskRepository.create_task()
    ↓ (task_id: int)
TaskExecutor.execute_task()
    ↓ (parallel execution)
TaskRepository.create_execution() (per agent)
    ↓
TaskExecutor.execute_single_agent() (per agent, async)
    ↓ (result or None)
TaskRepository.update_execution_result() (per agent)
    ↓
EvaluationExecutor.evaluate_execution() (per agent)
    ↓ (score, explanation)
TaskRepository.create_evaluation() (per agent)
    ↓
TaskRepository.get_leaderboard()
    ↓ (entries: list[dict])
LeaderboardTable.render()
    ↓
User sees results (UI)
```

### Workflow: Historical View

```
User navigates to History (UI)
    ↓
TaskRepository.get_task_history()
    ↓ (history: list[dict])
UI renders history list
    ↓ (user selects task)
TaskRepository.get_leaderboard(selected_task_id)
    ↓ (entries: list[dict])
LeaderboardTable.render()
    ↓
User sees historical results
```

## Error Handling Contract

### Database Errors

```python
try:
    repo.create_task(prompt)
except ValueError as e:
    # Display user-friendly error in UI
    ui.notify(f"Invalid input: {e}", type='negative')
except duckdb.Error as e:
    # Log error, show generic message
    logger.error(f"Database error: {e}")
    ui.notify("Failed to save task. Please try again.", type='negative')
```

### Agent Execution Errors

```python
try:
    result = await executor.execute_single_agent(agent, prompt, timeout)
except asyncio.TimeoutError:
    # Treat as failure (FR-029)
    result = None
    status = "timeout"
except Exception as e:
    # Log unexpected errors, continue with other agents (FR-011)
    logger.error(f"Agent execution failed: {e}")
    result = None
    status = "failed"
```

### Configuration Errors

```python
try:
    config = ConfigLoader.load(config_path)
except FileNotFoundError:
    # Prompt user to create config or use defaults
    ui.notify("Configuration file not found. Using defaults.", type='warning')
    config = AppConfig()  # Use defaults
except ValueError as e:
    # Show validation errors clearly
    ui.notify(f"Invalid configuration: {e}", type='negative')
    sys.exit(1)
```

## Type Safety Contract

All public interfaces must:
1. Use type annotations for all parameters and return values
2. Avoid `Any` type (use specific types or Union)
3. Use Pydantic models for complex data structures
4. Use Protocol for interface definitions
5. Pass `mypy --strict` type checking

## Testing Contract

### Unit Test Requirements

- All repository methods must have unit tests with mocked database
- All executor methods must have unit tests with mocked agents
- All tools must have unit tests with edge cases
- All UI components must have unit tests with mocked data

### Integration Test Requirements

- Database operations must be tested with real DuckDB in-memory instance
- Agent execution must be tested with mocked API responses
- UI rendering must be tested with test client

### E2E Test Requirements

- Full workflow (submit → execute → evaluate → display) must be tested
- Use test configuration with fast timeout (5 seconds)
- Use mock AI providers to avoid external API calls

## Performance Contract

- Database queries must complete in <100ms (SC-014)
- UI updates must be visible within 500ms of state change
- Parallel agent execution must scale linearly (O(1) with proper async)
- Memory usage must remain <500MB for typical workloads

## Security Contract

- API keys must never be stored in code or TOML (FR-017)
- API keys must only be loaded from environment variables
- Database paths must be validated to prevent path traversal
- User input must be sanitized before database insertion
- No SQL injection vulnerabilities (use parameterized queries)

## Versioning Contract

- Internal APIs follow semantic versioning
- Breaking changes require major version bump
- Deprecation warnings required before removal
- Migration scripts for database schema changes

This internal API contract ensures type-safe, testable, and maintainable component integration throughout the system.
