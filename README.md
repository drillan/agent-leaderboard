---
title: Multi-Agent Competition System
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
---

# Multi-Agent Competition System

A comprehensive system for executing tasks across multiple AI models, evaluating their performance, and visualizing results in an interactive leaderboard.

> **Hugging Face Spaces**: This application is ready to deploy on Hugging Face Spaces. See [plans/huggingface-deployment.md](plans/huggingface-deployment.md) for deployment instructions.

## Features

- **Multi-Model Execution**: Run the same task across multiple AI models in parallel (OpenAI, Anthropic, Google Gemini)
- **Automated Evaluation**: AI-powered evaluation agent scores each execution on a 0-100 scale
- **Interactive Leaderboard**: Real-time leaderboard with rankings, scores, and performance metrics
- **Performance Analytics**: Visualize execution duration, token consumption, and throughput metrics
- **Execution History**: Browse past task executions and view historical leaderboards
- **Detailed Logging**: Explore chronological execution logs with tool calls and responses
- **Configuration UI**: Manage AI models and settings through a web interface
- **Tool Call Visualization**: Hierarchical tree view of tool calls and their results

## Quick Start

### Prerequisites

- Python 3.13 or higher
- `uv` package manager ([installation guide](https://github.com/astral-sh/uv))
- API keys for at least 2 AI providers (OpenAI, Anthropic, or Google)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd agent-leaderboard

# Install dependencies
uv sync

# Install development dependencies (optional)
uv sync --group dev
```

### Configuration

1. **Set up environment variables**:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Google (optional)
export GOOGLE_API_KEY="..."
```

2. **Create `config.toml`** in the project root:

```toml
[execution]
timeout_seconds = 60

[[task_agents.models]]
provider = "openai"
model = "gpt-4o"
api_key_env = "OPENAI_API_KEY"

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
Consider accuracy, completeness, and efficiency.
Provide a numeric score and detailed explanation.
"""

[database]
path = "agent_leaderboard.duckdb"
```

### Running the Application

```bash
# Start the web interface
uv run python src/main.py

# Or with custom config
uv run python src/main.py --config path/to/config.toml
```

The web interface will be available at `http://localhost:8080`.

## Usage

### Executing a Task

1. Navigate to the **Task Execution** tab
2. Enter your task prompt (e.g., "Check if 17 is a prime number")
3. Click **Execute**
4. Watch as agents execute in parallel and results appear in the leaderboard

### Viewing Performance Metrics

1. Navigate to the **Performance** tab
2. Select a task from the dropdown (or view all tasks)
3. Analyze charts showing:
   - Execution duration by model
   - Token consumption by model
   - Tokens per second (throughput)

### Browsing History

1. Navigate to the **History** tab
2. Click on any past task to view its historical leaderboard
3. Compare results across different executions

### Viewing Execution Details

1. In any leaderboard, click the 👁️ (eye) icon next to an agent
2. View the detailed execution log showing:
   - User prompts and assistant responses
   - Tool calls with arguments and results
   - Chronological event timeline

### Managing Configuration

1. Navigate to the **Settings** tab
2. Add, remove, or modify task agents (2-5 required)
3. Configure the evaluation agent and criteria
4. Adjust execution timeout
5. Click **Save** to persist changes

## Development

### Running Tests

```bash
# All tests
uv run pytest

# Unit tests only
uv run pytest tests/unit/

# Integration tests only
uv run pytest tests/integration/

# With coverage
uv run pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Run all quality checks
uv run ruff check . && uv run ruff format . && uv run mypy .

# Auto-fix linting issues
uv run ruff check . --fix

# Format code
uv run ruff format .
```

### Project Structure

```
src/
├── agents/         # Pydantic AI agents (task execution and evaluation)
├── config/         # Configuration loading and validation
├── database/       # DuckDB persistence layer
├── execution/      # Task orchestration and timeout handling
├── models/         # Domain models (Pydantic)
├── ui/             # NiceGUI web interface
│   ├── components/ # Reusable UI components
│   └── pages/      # Page layouts
└── main.py         # Application entry point

tests/
├── unit/           # Unit tests (fast, no external dependencies)
├── integration/    # Integration tests (mocked APIs)
└── e2e/            # End-to-end tests (full workflow)

specs/001-agent-leaderboard/
├── spec.md         # Feature specification
├── plan.md         # Implementation plan
├── data-model.md   # Data entities and schema
└── tasks.md        # Implementation tasks checklist
```

## Technology Stack

- **Runtime**: Python 3.13+
- **Package Manager**: uv
- **AI Framework**: Pydantic AI (with OpenAI, Anthropic, Google providers)
- **Web UI**: NiceGUI
- **Database**: DuckDB
- **Visualization**: Plotly
- **Testing**: pytest
- **Code Quality**: ruff, mypy

## Documentation

- **Quickstart Guide**: [specs/001-agent-leaderboard/quickstart.md](specs/001-agent-leaderboard/quickstart.md)
- **Feature Specification**: [specs/001-agent-leaderboard/spec.md](specs/001-agent-leaderboard/spec.md)
- **Implementation Plan**: [specs/001-agent-leaderboard/plan.md](specs/001-agent-leaderboard/plan.md)
- **Data Model**: [specs/001-agent-leaderboard/data-model.md](specs/001-agent-leaderboard/data-model.md)
- **Development Guidelines**: [CLAUDE.md](CLAUDE.md)

## Troubleshooting

### Common Issues

**"Environment variable not found"**
- Ensure all required API keys are exported or in `.env` file

**"Expected 2-5 task agents"**
- Configure at least 2 models in `config.toml` under `task_agents.models`

**"Database locked"**
- Only one application instance can run at a time
- Delete `agent_leaderboard.duckdb` to reset

**"Agent execution timeout"**
- Increase `execution.timeout_seconds` in config.toml
- Simplify the task prompt

**"Address already in use"**
- Change port with `--port 8081` flag or modify in src/main.py

## Contributing

This project follows Test-Driven Development (TDD):

1. Write tests first (Red phase)
2. Implement features (Green phase)
3. Refactor code (Refactor phase)
4. Run quality checks before committing

See [CLAUDE.md](CLAUDE.md) for detailed development principles.

## License

[Add your license here]

## Support

- **Issues**: Create an issue in the repository
- **Questions**: Refer to documentation in `specs/001-agent-leaderboard/`
- **Development**: See [CLAUDE.md](CLAUDE.md)

---

**Ready to start?** Run `uv run python src/main.py` and execute your first task!
