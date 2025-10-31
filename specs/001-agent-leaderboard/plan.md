# Implementation Plan: Multi-Agent Competition System

**Branch**: `001-agent-leaderboard` | **Date**: 2025-10-31 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-agent-leaderboard/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This system enables users to compare multiple AI models by executing the same task across 2-5 different agents in parallel, evaluating their performance, and displaying results in an interactive leaderboard. The system uses Pydantic AI for agent implementation, NiceGUI for the web interface, DuckDB for persistence, and supports configurable AI models from multiple providers (OpenAI, Anthropic, Gemini). Results include evaluation scores (0-100), text feedback, hierarchical tool usage visualization, and performance metrics charts.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**:
- Pydantic AI with extras: `pydantic-ai-slim[openai,anthropic,google]` (agent framework with AI provider support)
- NiceGUI (web UI framework)
- DuckDB (embedded database with JSON column support)
- Plotly (visualization via NiceGUI integration)

**Storage**: DuckDB (local file-based database for execution history, evaluation results, and performance metrics)
**Testing**: pytest (unit, integration, and E2E tests)
**Target Platform**: Linux/macOS/Windows desktop (local web server via NiceGUI)
**Project Type**: Single web application (NiceGUI-based local web interface)
**Performance Goals**:
- Task execution completion within 30 seconds (SC-001)
- Real-time UI updates during agent execution (FR-025)
- Parallel execution of 2-5 agents without race conditions (SC-005)

**Constraints**:
- Configurable agent execution timeout (default 60 seconds, FR-028)
- Support 2-5 concurrent task agents minimum (FR-002)
- All execution history must persist to DuckDB (FR-008)

**Scale/Scope**:
- 2-5 concurrent agents per task execution
- Unlimited historical task executions (limited by DuckDB storage)
- 3 predefined tools (datetime, prime checker, palindrome checker)
- Multiple AI provider support (OpenAI, Anthropic, Gemini)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The following constitutional principles MUST be verified:

### I. Test-Driven Development (NON-NEGOTIABLE)
- [x] Tests MUST be written before implementation - **COMMITTED**: All tasks will follow TDD workflow
- [x] Tests MUST be approved by user before implementation - **COMMITTED**: User approval required per spec
- [x] Red-Green-Refactor cycle MUST be followed - **COMMITTED**: Standard TDD cycle
- [x] One feature = one test file mapping confirmed - **COMMITTED**: Feature-based test organization

### II. Code-Specification Consistency
- [x] Specifications reviewed and unambiguous - **PASS**: Specification fully clarified via /speckit.clarify
- [x] Documentation changes approved by user - **COMMITTED**: All spec updates approved
- [x] No implementation until specifications complete - **PASS**: Spec complete, moving to implementation plan

### III. Code Quality Standards
- [x] `ruff check .` passes with zero violations - **COMMITTED**: Pre-commit quality gate per constitution
- [x] `ruff format .` applied - **COMMITTED**: Pre-commit formatting per constitution
- [x] `mypy .` passes with zero errors - **COMMITTED**: Type checking gate per constitution
- [x] All functions/methods/variables have type annotations - **COMMITTED**: FR requirement + constitution
- [x] No `Any` types used (or justified exceptions documented) - **COMMITTED**: Specific types preferred per constitution

### IV. Data Accuracy
- [x] No magic numbers or hard-coded strings - **COMMITTED**: All values as named constants (FR-030, FR-031)
- [x] No environment-dependent values embedded - **COMMITTED**: TOML configuration for all settings
- [x] No credentials or API keys in code - **COMMITTED**: TOML-based credential management (FR-017)
- [x] All fixed values defined as named constants - **COMMITTED**: Constitution principle IV
- [x] Configuration centrally managed - **COMMITTED**: TOML + settings UI (FR-017, FR-018, FR-020)
- [x] Errors handled explicitly (exceptions raised) - **COMMITTED**: Explicit error handling per constitution

### V. DRY (Don't Repeat Yourself)
- [x] Existing implementations searched (Glob/Grep) - **N/A**: New feature, no existing implementation
- [x] No duplicate code patterns (3+ repetitions) - **COMMITTED**: Will extract reusable components during implementation
- [x] Reusable components identified - **PENDING**: Will identify during Phase 1 design

### VI. Refactoring Policy
- [x] No versioned classes (V2, V3) created - **N/A**: New feature
- [x] Existing code modified directly - **N/A**: New feature
- [x] Impact analysis completed (dependencies, tests, docs) - **PENDING**: Will complete during Phase 1

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── config/                  # Configuration management
│   ├── __init__.py
│   ├── models.py           # Configuration data models (Pydantic)
│   ├── loader.py           # TOML configuration loader
│   └── defaults.py         # Default configuration values
├── database/               # DuckDB persistence layer
│   ├── __init__.py
│   ├── connection.py       # DuckDB connection management
│   ├── schema.py           # Database schema definitions
│   └── repositories.py     # Data access layer
├── agents/                 # Pydantic AI agent implementations
│   ├── __init__.py
│   ├── task_agent.py       # Task execution agent
│   ├── eval_agent.py       # Evaluation agent
│   └── tools.py            # Tool implementations (datetime, prime, palindrome)
├── execution/              # Task execution orchestration
│   ├── __init__.py
│   ├── executor.py         # Parallel agent execution
│   ├── timeout.py          # Timeout management
│   └── state.py            # Execution state tracking
├── ui/                     # NiceGUI interface
│   ├── __init__.py
│   ├── app.py              # Main NiceGUI application
│   ├── components/         # Reusable UI components
│   │   ├── __init__.py
│   │   ├── input_form.py   # Task input form
│   │   ├── status_display.py # Execution status display
│   │   ├── leaderboard.py  # Leaderboard table
│   │   ├── tool_tree.py    # Hierarchical tool call tree
│   │   ├── charts.py       # Plotly performance charts
│   │   └── settings.py     # Settings UI
│   └── pages/              # Main UI pages/views
│       ├── __init__.py
│       ├── main.py         # Main task execution page
│       ├── history.py      # Historical executions view
│       └── performance.py  # Performance metrics dashboard
├── models/                 # Domain models
│   ├── __init__.py
│   ├── task.py             # Task submission model
│   ├── execution.py        # Agent execution model
│   ├── evaluation.py       # Evaluation result model
│   └── metrics.py          # Performance metrics model
└── main.py                 # Application entry point

tests/
├── unit/                   # Unit tests
│   ├── test_config.py
│   ├── test_database.py
│   ├── test_agents.py
│   ├── test_tools.py
│   ├── test_execution.py
│   └── test_models.py
├── integration/            # Integration tests
│   ├── test_agent_execution.py
│   ├── test_database_persistence.py
│   └── test_ui_integration.py
└── e2e/                    # End-to-end tests
    └── test_full_workflow.py

config.toml                 # Default configuration file
pyproject.toml              # Project dependencies and tool configuration
```

**Structure Decision**: Single project structure selected. This is a self-contained web application using NiceGUI as the UI framework. The structure separates concerns into:
- **config/**: Configuration management (TOML loading, validation)
- **database/**: DuckDB persistence layer
- **agents/**: Pydantic AI agent implementations
- **execution/**: Task orchestration and parallel execution
- **ui/**: NiceGUI interface (components and pages)
- **models/**: Domain models for entities

This structure follows the single project pattern as this is a local web application without separate frontend/backend deployments.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitutional violations detected. All checks passed or committed to compliance.
