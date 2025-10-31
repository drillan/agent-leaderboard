# Tasks: Multi-Agent Competition System

**Input**: Design documents from `/specs/001-agent-leaderboard/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Per constitutional principle I (Test-Driven Development), tests are MANDATORY and MUST be written BEFORE implementation. Tests MUST be approved by the user before implementation begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Single project structure: `src/`, `tests/` at repository root
- Paths below assume single project as per plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure per plan.md (src/, tests/, config.toml, pyproject.toml)
- [X] T002 Initialize Python project with uv and add pydantic-ai-slim[openai,anthropic,google] dependency
- [X] T003 [P] Add NiceGUI dependency to pyproject.toml
- [X] T004 [P] Add duckdb dependency to pyproject.toml
- [X] T005 [P] Configure ruff for linting and formatting in pyproject.toml
- [X] T006 [P] Configure mypy for type checking in pyproject.toml
- [X] T007 [P] Configure pytest for testing in pyproject.toml
- [X] T008 Create default config.toml with sample configuration (2 task agents, 1 eval agent)
- [X] T009 Create .env.example file documenting required environment variables (API keys)
- [X] T010 Add .gitignore for Python, venv, DuckDB files, .env

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Configuration Management

- [X] T011 [P] Create configuration Pydantic models in src/config/models.py (ModelConfig, ExecutionConfig, EvaluationConfig, AppConfig)
- [X] T012 [P] Implement TOML configuration loader in src/config/loader.py with validation
- [X] T013 [P] Create default configuration values in src/config/defaults.py (default eval prompt, timeout)

### Database Foundation

- [X] T014 [P] Implement DuckDB connection management in src/database/connection.py
- [X] T015 [P] Define database schema (tables, indexes, views) in src/database/schema.py per data-model.md
- [X] T016 Implement database initialization logic (create tables, schema metadata) in src/database/connection.py

### Domain Models

- [X] T017 [P] Create TaskSubmission model in src/models/task.py with Pydantic validation
- [X] T018 [P] Create AgentExecution model in src/models/execution.py with status enum
- [X] T019 [P] Create EvaluationResult model in src/models/evaluation.py with score validation (0-100)
- [X] T020 [P] Create PerformanceMetrics model in src/models/metrics.py

### Tools Implementation

- [X] T021 [P] Implement get_datetime tool in src/agents/tools.py with @tool decorator
- [X] T022 [P] Implement check_prime tool in src/agents/tools.py with validation (n >= 2)
- [X] T023 [P] Implement check_palindrome tool in src/agents/tools.py (case-insensitive)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute Multi-Agent Competition (Priority: P1) 🎯 MVP

**Goal**: Enable users to submit a task prompt and see multiple agents execute it in parallel with real-time status updates

**Independent Test**: Submit "Check if 17 is prime" and verify 2+ agents execute in parallel, showing real-time status (running/completed/failed), and results are stored

### Tests for User Story 1 (MANDATORY - TDD Principle) ⚠️

> **CONSTITUTIONAL REQUIREMENT: Write these tests FIRST, get USER APPROVAL, ensure they FAIL (Red phase), then implement (Green phase)**

- [X] T024 [P] [US1] Unit test for tool implementations in tests/unit/test_tools.py (all 3 tools)
- [X] T025 [P] [US1] Unit test for configuration loading in tests/unit/test_config.py (valid/invalid cases)
- [X] T026 [P] [US1] Unit test for domain models validation in tests/unit/test_models.py
- [X] T027 [P] [US1] Integration test for task execution workflow in tests/integration/test_agent_execution.py (mock API calls)
- [X] T028 [US1] End-to-end test for full workflow in tests/e2e/test_full_workflow.py (submit → execute → store)

### Implementation for User Story 1

**Task Agents Creation**

- [X] T029 [US1] Implement task agent factory in src/agents/task_agent.py (creates Agent with tools per model config)

**Execution Orchestration**

- [X] T030 [US1] Implement timeout wrapper in src/execution/timeout.py using asyncio.wait_for()
- [X] T031 [US1] Create execution state tracker in src/execution/state.py (dataclass with agent statuses dict)
- [X] T032 [US1] Implement single agent executor in src/execution/executor.py with timeout handling (returns AgentRunResult | None)
- [X] T033 [US1] Implement parallel multi-agent executor in src/execution/executor.py using asyncio.gather()

**Database Persistence**

- [X] T034 [US1] Implement TaskRepository.create_task() in src/database/repositories.py
- [X] T035 [US1] Implement TaskRepository.create_execution() in src/database/repositories.py
- [X] T036 [US1] Implement TaskRepository.update_execution_result() in src/database/repositories.py (stores all_messages_json)

**UI Components**

- [X] T037 [P] [US1] Create task input form component in src/ui/components/input_form.py (multi-line textarea + button)
- [X] T038 [P] [US1] Create execution status display component in src/ui/components/status_display.py (reactive labels)
- [X] T039 [US1] Implement main task execution page in src/ui/pages/main.py (integrates form + status + execution logic)

**Application Entry Point**

- [X] T040 [US1] Create main application entry point in src/main.py (load config, initialize DB, launch NiceGUI)

**Checkpoint**: User Story 1 fully functional - can submit tasks, see parallel execution with real-time status, results stored in DuckDB

---

## Phase 4: User Story 2 - View Evaluation Results and Rankings (Priority: P1)

**Goal**: Display leaderboard with evaluation scores, rankings, and hierarchical tool usage after task execution completes

**Independent Test**: After task execution, verify leaderboard shows agents sorted by score (highest first), with scores (0-100), evaluation text, and hierarchical tool call tree

### Tests for User Story 2 (MANDATORY - TDD Principle) ⚠️

> **CONSTITUTIONAL REQUIREMENT: Write these tests FIRST, get USER APPROVAL, ensure they FAIL (Red phase), then implement (Green phase)**

- [ ] T041 [P] [US2] Unit test for evaluation agent in tests/unit/test_agents.py (score extraction, validation)
- [ ] T042 [P] [US2] Unit test for tool hierarchy extraction in tests/unit/test_execution.py (parse all_messages_json)
- [ ] T043 [US2] Integration test for evaluation workflow in tests/integration/test_agent_execution.py (execute → evaluate → store)

### Implementation for User Story 2

**Evaluation Agent**

- [ ] T044 [US2] Implement evaluation agent factory in src/agents/eval_agent.py (uses configurable eval prompt)
- [ ] T045 [US2] Implement evaluation executor in src/execution/executor.py (runs eval agent, parses score & explanation)

**Tool Hierarchy Extraction**

- [ ] T046 [US2] Implement tool call hierarchy extractor in src/execution/executor.py (parse all_messages_json → tree structure)

**Database Queries**

- [ ] T047 [P] [US2] Implement TaskRepository.create_evaluation() in src/database/repositories.py
- [ ] T048 [P] [US2] Implement TaskRepository.get_leaderboard() in src/database/repositories.py (joins executions + evaluations, sorts by score DESC)

**UI Components**

- [ ] T049 [P] [US2] Create leaderboard table component in src/ui/components/leaderboard.py (NiceGUI table sorted by score)
- [ ] T050 [P] [US2] Create tool call tree component in src/ui/components/tool_tree.py (ui.tree() with hierarchical data)
- [ ] T051 [US2] Integrate leaderboard + tool tree into main page in src/ui/pages/main.py (auto-refresh after execution)

**Checkpoint**: User Stories 1 AND 2 functional - complete workflow from task submission to evaluated, ranked leaderboard display

---

## Phase 5: User Story 3 - Analyze Performance Metrics (Priority: P2)

**Goal**: Enable users to view performance metrics (duration, token usage) in visual charts in a separate dashboard tab

**Independent Test**: After task execution, navigate to performance dashboard tab and verify charts display execution duration and token consumption for all agents

### Tests for User Story 3 (MANDATORY - TDD Principle) ⚠️

> **CONSTITUTIONAL REQUIREMENT: Write these tests FIRST, get USER APPROVAL, ensure they FAIL (Red phase), then implement (Green phase)**

- [ ] T052 [P] [US3] Unit test for performance metrics calculation in tests/unit/test_models.py (duration, token count)
- [ ] T053 [US3] Integration test for performance metrics query in tests/integration/test_database_persistence.py (aggregate query)

### Implementation for User Story 3

**Database Queries**

- [ ] T054 [US3] Implement TaskRepository.get_performance_metrics() in src/database/repositories.py (aggregate query for charts)

**UI Components**

- [ ] T055 [P] [US3] Create performance charts component in src/ui/components/charts.py (Plotly bar charts via ui.plotly())
- [ ] T056 [US3] Create performance dashboard page in src/ui/pages/performance.py (duration chart + token chart)

**UI Integration**

- [ ] T057 [US3] Add tab navigation to main app in src/ui/app.py (main tab + performance tab)
- [ ] T058 [US3] Integrate performance page into app in src/ui/app.py

**Checkpoint**: User Stories 1, 2, AND 3 functional - complete system with task execution, evaluation, and performance analysis

---

## Phase 6: User Story 4 - Configure AI Models (Priority: P2)

**Goal**: Allow users to configure AI models (2-5 task agents + 1 eval agent) via TOML file and settings UI

**Independent Test**: Edit config.toml to change models, restart app, verify new models are used. Use settings UI to change models, verify TOML file is updated and subsequent executions use new models

### Tests for User Story 4 (MANDATORY - TDD Principle) ⚠️

> **CONSTITUTIONAL REQUIREMENT: Write these tests FIRST, get USER APPROVAL, ensure they FAIL (Red phase), then implement (Green phase)**

- [ ] T059 [P] [US4] Unit test for configuration validation in tests/unit/test_config.py (2-5 agents, valid providers, env vars exist)
- [ ] T060 [US4] Integration test for settings UI persistence in tests/integration/test_ui_integration.py (UI save → TOML update)

### Implementation for User Story 4

**Configuration Persistence**

- [ ] T061 [US4] Implement ConfigLoader.save() in src/config/loader.py (write AppConfig to TOML)

**UI Components**

- [ ] T062 [P] [US4] Create settings form component in src/ui/components/settings.py (model selection dropdowns, provider selection)
- [ ] T063 [US4] Create settings page in src/ui/pages/settings.py (load config, save to TOML on submit)

**UI Integration**

- [ ] T064 [US4] Add settings tab to main app in src/ui/app.py
- [ ] T065 [US4] Integrate settings page into app in src/ui/app.py

**Configuration Validation**

- [ ] T066 [US4] Add startup validation in src/main.py (validate config, display clear errors for invalid config)

**Checkpoint**: User Stories 1-4 functional - full system with configurable AI models

---

## Phase 7: User Story 5 - Browse Past Task Execution History (Priority: P3)

**Goal**: Enable users to browse past task executions and view their historical leaderboards

**Independent Test**: Execute multiple tasks, navigate to history view, verify all past executions listed with timestamps, select one, verify historical leaderboard displays correctly

### Tests for User Story 5 (MANDATORY - TDD Principle) ⚠️

> **CONSTITUTIONAL REQUIREMENT: Write these tests FIRST, get USER APPROVAL, ensure they FAIL (Red phase), then implement (Green phase)**

- [ ] T067 [P] [US5] Integration test for historical executions query in tests/integration/test_database_persistence.py (multiple tasks, correct ordering)
- [ ] T068 [US5] Integration test for historical leaderboard display in tests/integration/test_ui_integration.py (select past task → show results)

### Implementation for User Story 5

**Database Queries**

- [ ] T069 [US5] Implement TaskRepository.get_task_history() in src/database/repositories.py (list past tasks with metadata)

**UI Components**

- [ ] T070 [P] [US5] Create history list component in src/ui/components/history_list.py (table of past tasks)
- [ ] T071 [US5] Create history page in src/ui/pages/history.py (list + selection → show historical leaderboard)

**UI Integration**

- [ ] T072 [US5] Add history tab to main app in src/ui/app.py
- [ ] T073 [US5] Integrate history page into app in src/ui/app.py

**Checkpoint**: User Stories 1-5 functional - complete system with historical browsing

---

## Phase 8: User Story 6 - Explore Execution History and Tool Usage (Priority: P3)

**Goal**: Enable users to view detailed execution history for each agent, showing chronological tool calls and results

**Independent Test**: Select an agent from leaderboard, verify detailed execution log displays with tool calls, inputs, outputs, and timestamps

### Tests for User Story 6 (MANDATORY - TDD Principle) ⚠️

> **CONSTITUTIONAL REQUIREMENT: Write these tests FIRST, get USER APPROVAL, ensure they FAIL (Red phase), then implement (Green phase)**

- [ ] T074 [P] [US6] Unit test for execution log parsing in tests/unit/test_execution.py (extract chronological tool calls from all_messages_json)
- [ ] T075 [US6] Integration test for execution history display in tests/integration/test_ui_integration.py (select agent → show log)

### Implementation for User Story 6

**Execution Log Parsing**

- [ ] T076 [US6] Implement execution log parser in src/execution/executor.py (extract tool calls with timestamps from all_messages_json)

**UI Components**

- [ ] T077 [P] [US6] Create execution log display component in src/ui/components/execution_log.py (chronological list of tool calls)
- [ ] T078 [US6] Add execution log modal/panel to leaderboard in src/ui/components/leaderboard.py (click agent → show log)

**Checkpoint**: All 6 user stories functional - complete multi-agent competition system

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T079 [P] Add comprehensive docstrings to all public functions/classes (Google-style format)
- [ ] T080 [P] Add logging for key operations (task submission, agent execution, evaluation, errors)
- [ ] T081 [P] Error handling improvements across all modules (explicit exceptions, user-friendly messages)
- [ ] T082 [P] Performance optimization: Add connection pooling for DuckDB in src/database/connection.py
- [ ] T083 [P] Performance optimization: Lazy loading for history queries in src/database/repositories.py
- [ ] T084 [P] Security hardening: Validate database paths to prevent path traversal in src/database/connection.py
- [ ] T085 [P] Add input sanitization for task prompts in src/ui/components/input_form.py
- [ ] T086 Create README.md with setup instructions per quickstart.md
- [ ] T087 [P] Verify quickstart.md against implemented system (test all examples)
- [ ] T088 Refactor duplicate code if found (per DRY principle)
- [ ] T089 Final code cleanup (remove debug code, unused imports)

---

## Constitutional Compliance Checklist (Before Final Commit)

**GATE: All items MUST pass before committing**

- [ ] `ruff check .` passes with zero violations
- [ ] `ruff format .` applied to all files
- [ ] `mypy .` passes with zero type errors
- [ ] All tests passing (`pytest`)
- [ ] No magic numbers or hard-coded values (all constants named)
- [ ] No credentials or API keys in code (only in environment variables)
- [ ] All public APIs have Google-style docstrings
- [ ] Type annotations on all functions/methods/variables
- [ ] No `Any` types (or documented justifications)
- [ ] No duplicate code (DRY principle verified)
- [ ] No versioned classes (V2, V3) created
- [ ] Documentation (README.md) complete and accurate
- [ ] quickstart.md validated against implemented system

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order: US1 (P1) → US2 (P1) → US3 (P2) → US4 (P2) → US5 (P3) → US6 (P3)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational - Integrates with US1 but independently testable
- **User Story 3 (P2)**: Can start after Foundational - Uses data from US1/US2 but independently testable
- **User Story 4 (P2)**: Can start after Foundational - No dependencies on other stories
- **User Story 5 (P3)**: Can start after Foundational - Uses data from US1/US2 but independently testable
- **User Story 6 (P3)**: Can start after Foundational - Uses data from US1/US2 but independently testable

### Within Each User Story

- Tests MUST be written and approved, then FAIL before implementation
- Models before services
- Services before endpoints/UI
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
- T003, T004, T005, T006, T007 can run in parallel (different files)

**Phase 2 (Foundational)**:
- Configuration: T011, T012, T013 can run in parallel
- Database: T014, T015 can run in parallel (T016 depends on both)
- Domain Models: T017, T018, T019, T020 can run in parallel
- Tools: T021, T022, T023 can run in parallel

**Phase 3 (US1)**:
- Tests: T024, T025, T026, T027 can run in parallel
- UI Components: T037, T038 can run in parallel
- Database: T034, T035 can run in parallel (T036 sequential)

**Phase 4 (US2)**:
- Tests: T041, T042 can run in parallel
- Database: T047, T048 can run in parallel
- UI Components: T049, T050 can run in parallel

**Phase 5 (US3)**:
- Tests: T052 and T053 can run in parallel
- UI Components: T055 can run parallel with database work

**Phase 6 (US4)**:
- Tests: T059 can run in parallel with implementation if mocks available
- UI Components: T062 can prepare while backend is being finalized

**Phase 7 (US5)**:
- Tests: T067, T068 can run in parallel
- UI Components: T070 can run in parallel with backend work

**Phase 8 (US6)**:
- Tests: T074, T075 can run in parallel
- UI Components: T077 can run in parallel with backend work

**Phase 9 (Polish)**:
- T079, T080, T081, T082, T083, T084, T085, T087 can all run in parallel

**User Stories (after Foundational)**:
- If team has capacity, US1, US2, US3, US4, US5, US6 can all be worked on in parallel by different developers

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for tool implementations in tests/unit/test_tools.py"
Task: "Unit test for configuration loading in tests/unit/test_config.py"
Task: "Unit test for domain models validation in tests/unit/test_models.py"
Task: "Integration test for task execution workflow in tests/integration/test_agent_execution.py"

# Launch all parallel models/components:
Task: "Create task input form component in src/ui/components/input_form.py"
Task: "Create execution status display component in src/ui/components/status_display.py"
Task: "Implement TaskRepository.create_task() in src/database/repositories.py"
Task: "Implement TaskRepository.create_execution() in src/database/repositories.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (execute multi-agent tasks)
4. Complete Phase 4: User Story 2 (view evaluated leaderboard)
5. **STOP and VALIDATE**: Test end-to-end workflow independently
6. Deploy/demo MVP - core value delivered

**Rationale**: US1 + US2 together provide complete value - submit tasks, get evaluated results. This is the minimum viable product.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 + 2 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 3 (performance charts) → Test independently → Deploy/Demo
4. Add User Story 4 (model configuration UI) → Test independently → Deploy/Demo
5. Add User Story 5 (historical browsing) → Test independently → Deploy/Demo
6. Add User Story 6 (detailed execution logs) → Test independently → Deploy/Demo
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers after Foundational phase completes:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (core execution)
   - Developer B: User Story 2 (evaluation & leaderboard)
   - Developer C: User Story 3 (performance charts)
   - Developer D: User Story 4 (configuration UI)
3. Stories complete and integrate independently
4. Lower priority stories (US5, US6) added after core is stable

---

## Task Count Summary

- **Phase 1 (Setup)**: 10 tasks
- **Phase 2 (Foundational)**: 13 tasks
- **Phase 3 (US1 - Execute)**: 17 tasks (5 tests + 12 implementation)
- **Phase 4 (US2 - Evaluate)**: 11 tasks (3 tests + 8 implementation)
- **Phase 5 (US3 - Performance)**: 7 tasks (2 tests + 5 implementation)
- **Phase 6 (US4 - Configure)**: 8 tasks (2 tests + 6 implementation)
- **Phase 7 (US5 - History)**: 7 tasks (2 tests + 5 implementation)
- **Phase 8 (US6 - Logs)**: 5 tasks (2 tests + 3 implementation)
- **Phase 9 (Polish)**: 11 tasks
- **Total**: 89 tasks

**MVP Scope (US1 + US2)**: 51 tasks (Setup + Foundational + US1 + US2)

**Parallel Tasks**: 47 tasks marked [P] for parallel execution opportunities

---

## Notes

- [P] tasks = different files, no dependencies on incomplete work
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Tests MUST fail (Red phase) before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- MVP (US1 + US2) delivers core value: submit tasks → get evaluated results
- Foundational phase is CRITICAL blocker - must complete first
