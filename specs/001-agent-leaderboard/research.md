# Research: Multi-Agent Competition System

**Feature**: Multi-Agent Competition System
**Date**: 2025-10-31
**Purpose**: Consolidate technology research and design decisions for implementation

## Overview

This document consolidates research findings and design decisions for the multi-agent competition system. All technical unknowns from the planning phase have been resolved through analysis of best practices, SDK documentation, and architectural patterns.

**Python Version**: Python 3.13+ is required for modern async/await patterns and improved performance.

## Technology Stack Research

### 1. Pydantic AI Integration

**Decision**: Use Pydantic AI's Agent class with tool decorators for task agents and evaluation agent

**Rationale**:
- Pydantic AI provides unified interface for multiple AI providers through extras installation
- Install with `pydantic-ai-slim[openai,anthropic,google]` to include all needed provider SDKs
- `AgentRunResult.all_messages_json()` provides complete execution history in JSON format
- Tool system allows declarative tool definition with type safety
- Built-in async support for parallel agent execution

**Implementation Pattern**:
```python
from pydantic_ai import Agent
from pydantic_ai.tools import tool

# Task agent with tools
task_agent = Agent(
    model=model_config,  # Configurable per spec
    tools=[get_datetime, check_prime, check_palindrome]
)

# Tool definition
@tool
def get_datetime() -> str:
    """Returns current datetime in ISO format."""
    return datetime.now().isoformat()
```

**Key API References**:
- Agent creation: `Agent(model, tools=[], system_prompt=...)`
- Execution: `await agent.run(prompt)` → `AgentRunResult`
- History extraction: `result.all_messages_json()` → JSON string

**Alternatives Considered**:
- LangChain: Rejected due to heavier framework weight and less direct multi-provider support
- Direct SDK usage: Rejected due to manual tool orchestration complexity

### 2. NiceGUI UI Framework

**Decision**: Use NiceGUI's component-based architecture with reactive UI elements

**Rationale**:
- Built-in components for forms, tables, and trees
- Native Plotly integration for charts (via `ui.plotly()`)
- Reactive binding for real-time updates during agent execution
- Simple tab-based navigation for leaderboard/history/performance views

**Implementation Pattern**:
```python
from nicegui import ui

# Main page with tabs
with ui.tabs() as tabs:
    main_tab = ui.tab('Task Execution')
    history_tab = ui.tab('History')
    perf_tab = ui.tab('Performance')

# Reactive status updates
status = ui.label('')
status.bind_text_from(execution_state, 'current_status')

# Tree for tool calls (FR-015)
tree = ui.tree([
    {'id': 'tool1', 'label': 'check_prime(17)', 'children': []}
])
```

**Key Components Used**:
- `ui.textarea()`: Multi-line task input (FR-001)
- `ui.button()`: Execution button (FR-023)
- `ui.table()`: Leaderboard display (FR-007)
- `ui.tree()`: Hierarchical tool call display (FR-015)
- `ui.plotly()`: Performance charts (FR-013, FR-014)
- `ui.spinner()`: Loading indicator (FR-025)

**Alternatives Considered**:
- Streamlit: Rejected due to page reload-based model (conflicts with real-time updates FR-025)
- Gradio: Rejected due to less flexible layout control for complex leaderboard UI

### 3. DuckDB for Persistence

**Decision**: Use DuckDB with JSON columns for storing `all_messages_json` and relational tables for metadata

**Rationale**:
- Native JSON column support allows efficient storage of Pydantic AI's `all_messages_json`
- SQL queries enable efficient filtering and aggregation for performance charts
- Embedded database (no server setup required)
- Python driver (`duckdb-python`) is lightweight and well-maintained

**Schema Design**:
```sql
CREATE TABLE task_submissions (
    id INTEGER PRIMARY KEY,
    prompt TEXT NOT NULL,
    submitted_at TIMESTAMP NOT NULL
);

CREATE TABLE agent_executions (
    id INTEGER PRIMARY KEY,
    task_id INTEGER REFERENCES task_submissions(id),
    model_provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    status TEXT NOT NULL,  -- 'completed', 'failed', 'timeout'
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds REAL,
    token_count INTEGER,
    all_messages JSON  -- Pydantic AI's all_messages_json
);

CREATE TABLE evaluations (
    id INTEGER PRIMARY KEY,
    execution_id INTEGER REFERENCES agent_executions(id),
    score INTEGER NOT NULL CHECK(score >= 0 AND score <= 100),
    explanation TEXT NOT NULL,
    evaluated_at TIMESTAMP NOT NULL
);
```

**JSON Query Pattern** (for tool call extraction):
```python
# Extract tool calls from all_messages JSON
cursor.execute("""
    SELECT
        execution_id,
        json_extract(all_messages, '$.tool_calls') as tools
    FROM agent_executions
    WHERE execution_id = ?
""", [exec_id])
```

**Alternatives Considered**:
- SQLite: Rejected due to weaker JSON support (no native JSON type until 3.38+)
- PostgreSQL: Rejected due to server setup complexity for local desktop app
- JSON files: Rejected due to lack of efficient querying for charts (FR-013, FR-014)

### 4. Configuration Management (TOML)

**Decision**: Use `tomli` (Python 3.11+) for reading TOML, Pydantic models for validation

**Rationale**:
- `tomli` is standard library for Python 3.11+
- Pydantic validation ensures type safety and error reporting
- TOML is human-readable for manual editing (FR-017)

**Configuration Structure**:
```toml
[execution]
timeout_seconds = 60  # FR-028

[task_agents]
[[task_agents.models]]
provider = "openai"
model = "gpt-4o"
api_key_env = "OPENAI_API_KEY"  # Not stored in TOML

[[task_agents.models]]
provider = "anthropic"
model = "claude-sonnet-4"
api_key_env = "ANTHROPIC_API_KEY"

[evaluation_agent]
provider = "openai"
model = "gpt-4"
api_key_env = "OPENAI_API_KEY"
prompt = """
Evaluate the agent's performance on a scale of 0-100.
Consider: accuracy, completeness, efficiency.
Provide a score and detailed text explanation.
"""  # FR-030, FR-031

[database]
path = "agent_leaderboard.duckdb"
```

**Validation Pattern**:
```python
from pydantic import BaseModel, Field

class ModelConfig(BaseModel):
    provider: str
    model: str
    api_key_env: str

class Config(BaseModel):
    timeout_seconds: int = Field(default=60, ge=1)
    task_agents: list[ModelConfig] = Field(min_length=2, max_length=5)
    evaluation_agent: ModelConfig
    evaluation_prompt: str
```

**Alternatives Considered**:
- YAML: Rejected due to ambiguous type parsing (e.g., Norway problem)
- JSON: Rejected due to lack of comments for user guidance

### 5. Parallel Execution with Asyncio

**Decision**: Use `asyncio.gather()` with timeout wrapper for parallel agent execution

**Rationale**:
- Pydantic AI agents support async execution natively
- `asyncio.gather()` allows true parallel execution (FR-002)
- `asyncio.wait_for()` provides timeout enforcement (FR-028)
- Exception handling allows graceful failure of individual agents (FR-011)

**Implementation Pattern**:
```python
import asyncio
from typing import List

async def execute_agent_with_timeout(
    agent: Agent,
    prompt: str,
    timeout: int
) -> AgentRunResult | None:
    try:
        return await asyncio.wait_for(
            agent.run(prompt),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        return None  # Handle as failed (FR-029)
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        return None

async def execute_all_agents(
    agents: List[Agent],
    prompt: str,
    timeout: int
) -> List[AgentRunResult | None]:
    tasks = [
        execute_agent_with_timeout(agent, prompt, timeout)
        for agent in agents
    ]
    return await asyncio.gather(*tasks)
```

**Alternatives Considered**:
- Threading: Rejected due to GIL limitations and complexity with async I/O
- Multiprocessing: Rejected due to overhead and complexity for 2-5 agents

### 6. Real-Time UI Updates

**Decision**: Use NiceGUI's reactive binding and async task updates

**Rationale**:
- NiceGUI supports binding UI elements to Python objects
- Updates propagate automatically when bound state changes
- Compatible with asyncio execution model

**Implementation Pattern**:
```python
from dataclasses import dataclass
from nicegui import ui

@dataclass
class ExecutionState:
    agent_statuses: dict[str, str]  # model_name -> "running"|"completed"|"failed"

state = ExecutionState(agent_statuses={})

# UI binding
for model_name in config.task_agents:
    label = ui.label()
    label.bind_text_from(
        state.agent_statuses,
        model_name,
        backward=lambda s: f"{model_name}: {s}"
    )

# Update during execution
async def run_task(prompt):
    for model_name in config.task_agents:
        state.agent_statuses[model_name] = "running"

    # ... execute agents ...

    state.agent_statuses[model_name] = "completed"  # Triggers UI update
```

### 7. Tool Call Hierarchy Extraction

**Decision**: Parse Pydantic AI's `all_messages_json` to build tree structure for `ui.tree()`

**Rationale**:
- Pydantic AI records all tool calls in message history
- JSON structure allows traversal to build parent-child relationships
- NiceGUI's `ui.tree()` component accepts hierarchical data

**Implementation Pattern**:
```python
def extract_tool_hierarchy(all_messages_json: str) -> list[dict]:
    """Extract tool calls from Pydantic AI messages into tree structure."""
    messages = json.loads(all_messages_json)

    tree_nodes = []
    for msg in messages:
        if msg.get('role') == 'tool':
            tree_nodes.append({
                'id': msg['tool_call_id'],
                'label': f"{msg['name']}({msg['arguments']})",
                'children': []  # Nesting handled by call order
            })

    return tree_nodes
```

**Note**: Exact JSON structure will be determined during implementation based on Pydantic AI version.

## Best Practices Applied

### Error Handling
- All API calls wrapped in try-except with explicit error messages
- Database write failures logged and reported to user (Edge Case: Database write failure)
- Agent failures handled gracefully without blocking others (FR-011)

### Configuration Validation
- Pydantic models validate all configuration on startup (FR-019)
- Clear error messages for invalid config (e.g., "Expected 2-5 task agents, found 1")
- API keys loaded from environment variables, never stored in TOML (FR-017)

### Testing Strategy
- Unit tests for pure functions (tools, data models, config validation)
- Integration tests for agent execution and database persistence
- E2E test for full workflow (submit task → execute → evaluate → display)
- Mocks for external API calls in unit/integration tests

### Performance Optimization
- DuckDB connection pooling for concurrent access
- Lazy loading of historical executions (paginated queries)
- Chart data aggregated in SQL (not Python) for efficiency

## Open Questions Resolved

1. **How to handle Pydantic AI's all_messages_json structure?**
   - Store as JSON column in DuckDB
   - Parse on-demand for UI display
   - Use JSON functions for querying

2. **How to update UI during parallel execution?**
   - NiceGUI reactive binding to execution state dataclass
   - Async task updates state, UI auto-reflects changes

3. **How to structure TOML for multi-model configuration?**
   - Array of tables for task agents
   - Separate table for evaluation agent
   - Environment variable references for API keys

4. **How to enforce timeout per agent?**
   - `asyncio.wait_for()` wrapper per agent
   - Timeout exception caught and treated as failure (FR-029)

5. **How to display tool call hierarchy?**
   - Extract from all_messages_json
   - Build tree data structure
   - Render with `ui.tree()`

## Implementation Readiness

All technical unknowns have been resolved. The implementation can proceed with confidence in:
- Pydantic AI integration patterns
- NiceGUI UI architecture
- DuckDB schema and JSON handling
- Configuration management approach
- Parallel execution with timeout
- Real-time UI updates

No further research blockers identified.
