# Quickstart Guide: Multi-Agent Competition System

**Feature**: Multi-Agent Competition System
**Date**: 2025-10-31
**Purpose**: Guide developers through setup, configuration, and first task execution

## Prerequisites

- Python 3.11 or higher
- `uv` package manager installed
- API keys for at least 2 AI providers (OpenAI, Anthropic, or Gemini)

## Installation

### 1. Clone Repository and Install Dependencies

```bash
# Navigate to project root
cd agent-leaderboard

# Install all dependencies using uv
# Note: Pydantic AI will be installed with extras for OpenAI, Anthropic, and Google providers
uv sync

# Install development dependencies
uv sync --group dev
```

**Note on Pydantic AI**: The project uses `pydantic-ai-slim[openai,anthropic,google]` which includes provider-specific SDKs as extras. You don't need to install OpenAI SDK, Anthropic SDK, or Google Generative AI SDK separately.

### 2. Set Up Environment Variables

Create a `.env` file in the project root or export environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Google (if using Gemini)
export GOOGLE_API_KEY="..."
```

**Important**: Never commit API keys to version control. The `.env` file should be in `.gitignore`.

### 3. Configure Application

Create or edit `config.toml` in the project root:

```toml
[execution]
timeout_seconds = 60  # Agent execution timeout

# Task agents (2-5 required)
[[task_agents.models]]
provider = "openai"
model = "gpt-4o"
api_key_env = "OPENAI_API_KEY"

[[task_agents.models]]
provider = "anthropic"
model = "claude-sonnet-4"
api_key_env = "ANTHROPIC_API_KEY"

[[task_agents.models]]
provider = "gemini"
model = "gemini-1.5-pro"
api_key_env = "GOOGLE_API_KEY"

# Evaluation agent
[evaluation_agent]
provider = "openai"
model = "gpt-4"
api_key_env = "OPENAI_API_KEY"
prompt = """
Evaluate the agent's performance on a scale of 0-100.
Consider:
- Accuracy: Did the agent produce the correct result?
- Completeness: Did the agent address all aspects of the task?
- Efficiency: Did the agent use tools effectively?

Provide a numeric score (0-100) and a detailed explanation.
"""

# Database
[database]
path = "agent_leaderboard.duckdb"
```

## Running the Application

### Start the Web Interface

```bash
# From project root
uv run python src/main.py
```

The NiceGUI interface will open in your default web browser at `http://localhost:8080`.

### First Task Execution

1. **Enter a task prompt** in the multi-line text input field:
   ```
   Check if 17 is a prime number
   ```

2. **Click the "Execute" button**

3. **Watch real-time status** as agents execute in parallel:
   - `gpt-4o: running`
   - `claude-sonnet-4: running`
   - `gemini-1.5-pro: completed`

4. **View results** in the leaderboard table:
   - Agents sorted by evaluation score (highest first)
   - Scores (0-100)
   - Evaluation explanations
   - Execution duration and token usage
   - Hierarchical tool call tree

## Running Tests

### All Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Unit Tests Only

```bash
uv run pytest tests/unit/
```

### Integration Tests Only

```bash
uv run pytest tests/integration/
```

### End-to-End Tests

```bash
# E2E tests use mock APIs (no real API calls)
uv run pytest tests/e2e/
```

## Development Workflow

### Before Writing Code

1. **Read the specification**: `specs/001-agent-leaderboard/spec.md`
2. **Review the data model**: `specs/001-agent-leaderboard/data-model.md`
3. **Check API contracts**: `specs/001-agent-leaderboard/contracts/internal-api.md`

### Test-Driven Development (TDD)

Per constitution principle I, tests MUST be written before implementation:

```bash
# 1. Create test file
touch tests/unit/test_<feature>.py

# 2. Write failing test (Red phase)
uv run pytest tests/unit/test_<feature>.py  # Should fail

# 3. Implement feature (Green phase)
# ... write code in src/ ...

# 4. Run test again
uv run pytest tests/unit/test_<feature>.py  # Should pass

# 5. Refactor (if needed)
# ... improve code quality ...

# 6. Run full test suite
uv run pytest
```

### Code Quality Checks

**Pre-commit checks** (constitution principle III):

```bash
# Run all quality checks
ruff check . && ruff format . && mypy .

# Or individually:
ruff check .      # Linting
ruff format .     # Formatting
mypy .            # Type checking
```

**Fix common issues**:

```bash
# Auto-fix linting issues
ruff check . --fix

# Auto-format code
ruff format .
```

## Project Structure Quick Reference

```
src/
├── config/         # Configuration loading and validation
├── database/       # DuckDB persistence layer
├── agents/         # Pydantic AI agents and tools
├── execution/      # Task orchestration
├── ui/             # NiceGUI interface components
├── models/         # Domain models (Pydantic)
└── main.py         # Application entry point

tests/
├── unit/           # Unit tests (fast, no external deps)
├── integration/    # Integration tests (mocked APIs)
└── e2e/            # End-to-end tests (full workflow)

specs/001-agent-leaderboard/
├── spec.md         # Feature specification
├── plan.md         # Implementation plan
├── research.md     # Technology research
├── data-model.md   # Data entities and schema
├── contracts/      # API contracts
└── tasks.md        # Implementation tasks (generated later)
```

## Common Tasks

### Add a New Tool

1. Define tool in `src/agents/tools.py`:

```python
from pydantic_ai.tools import tool

@tool
def my_new_tool(param: str) -> str:
    """Tool description for AI.

    Args:
        param: Parameter description

    Returns:
        Result description
    """
    # Implementation
    return result
```

2. Register tool with task agents in `src/agents/task_agent.py`:

```python
task_agent = Agent(
    model=model_config,
    tools=[get_datetime, check_prime, check_palindrome, my_new_tool]
)
```

3. Write tests in `tests/unit/test_tools.py`:

```python
def test_my_new_tool():
    result = my_new_tool("test")
    assert result == expected
```

### Add a New AI Provider

1. Update configuration schema in `src/config/models.py`:

```python
class ModelConfig(BaseModel):
    provider: Literal["openai", "anthropic", "gemini", "new_provider"]
    ...
```

2. Add provider initialization logic in agent creation

3. Update `config.toml` with new provider entry

4. Test with new provider API key

### Customize Evaluation Criteria

Edit the `evaluation_agent.prompt` field in `config.toml`:

```toml
[evaluation_agent]
provider = "openai"
model = "gpt-4"
api_key_env = "OPENAI_API_KEY"
prompt = """
Your custom evaluation criteria here.
Focus on: [specific aspects]
Score range: 0-100
"""
```

## Troubleshooting

### Configuration Errors

**Error**: `Environment variable OPENAI_API_KEY not found`

**Solution**: Export the environment variable or add to `.env` file:
```bash
export OPENAI_API_KEY="sk-..."
```

**Error**: `Expected 2-5 task agents, found 1`

**Solution**: Add at least 2 models to `task_agents.models` in `config.toml`

### Database Errors

**Error**: `Database locked`

**Solution**: Ensure only one instance of the application is running

**Solution**: Delete `agent_leaderboard.duckdb` and restart (clears history)

### Agent Execution Errors

**Error**: `Agent execution timeout after 60 seconds`

**Solution**: Increase `execution.timeout_seconds` in `config.toml`

**Solution**: Simplify the task prompt

### UI Not Loading

**Error**: `Address already in use`

**Solution**: Another process is using port 8080. Change port in `src/main.py`:
```python
ui.run(port=8081)
```

## Next Steps

1. **Execute sample tasks** to familiarize yourself with the UI
2. **Explore historical executions** in the History tab
3. **Analyze performance metrics** in the Performance tab
4. **Review the test suite** to understand testing patterns
5. **Read the implementation plan** (`specs/001-agent-leaderboard/plan.md`)
6. **Start implementing features** following TDD workflow

## Resources

- **Pydantic AI Documentation**: https://ai.pydantic.dev/
- **NiceGUI Documentation**: https://nicegui.io/documentation
- **DuckDB Python API**: https://duckdb.org/docs/api/python/overview
- **Constitution** (Development Principles): `.specify/memory/constitution.md`

## Support

- For bugs or issues: Create an issue in the repository
- For questions: Refer to specification documents in `specs/001-agent-leaderboard/`
- For development guidance: See `CLAUDE.md` in project root

---

**Ready to start?** Run `uv run python src/main.py` and submit your first task!
