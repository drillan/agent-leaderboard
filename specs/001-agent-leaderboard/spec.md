# Feature Specification: Multi-Agent Competition System

**Feature Branch**: `001-agent-leaderboard`
**Created**: 2025-10-31
**Status**: Draft
**Input**: User description: "次の複数コンペ型のエージェントを定義してください

要件:

- 複数(2-5程度)の、異なるモデルで、同じタスクを遂行するエージェント(タスクエージェント)が並行に実行される
- 各エージェントはタスクの実行結果を評価エージェント(LLMモデルによる評価)され、0-100のスコアと、文章による評価がされる
- タスクエージェントはユーザから与えられたプロンプトに応じてツール(https://ai.pydantic.dev/tools/)を呼び出す
- タスクエージェントと呼び出されたツールなどの全ての履歴が保存される
- 最終結果はリーダーボードに表示され、履歴からタスクの実行結果、評価結果、スコア、呼び出されたツールがスコア順(降順)に表示される

ツール:
- 現在日時を返す
- 素数を判定する
- 回文を判定する

技術スタック:
- 全てのエージェントは Pydantic AI(https://ai.pydantic.dev/) で実装する
- リーダーボードのUIはNiceGUI(https://nicegui.io/) で実装する"

## Clarifications

### Session 2025-10-31

- Q: What specific information should be displayed in the leaderboard? → A: Leaderboard must include task agent results, evaluation scores with text feedback, and hierarchical display of tool calls
- Q: What performance metrics should be tracked and visualized? → A: Track and visualize execution duration, token consumption, and other agent resource usage metrics in chart format
- Q: What happens when an agent fails or times out during execution? → A: Failed agents are displayed on the leaderboard with score 0 and evaluation text indicating "Execution Failed"
- Q: Where should performance metrics charts be displayed in relation to the leaderboard? → A: Performance metrics charts are displayed in a separate tab/section from the leaderboard as an independent dashboard
- Q: Which AI models should the task agents use? → A: Support multiple providers (OpenAI, Anthropic, Gemini, etc.) configurable via TOML file and NiceGUI settings UI
- Q: Which AI model should the evaluation agent use? → A: Evaluation agent model is independently configurable via TOML file and changeable through the settings UI
- Q: How should execution history and results be persisted? → A: Use DuckDB to store Pydantic AI's all_messages_json with native JSON column support for efficient SQL queries and analysis
- Q: What UI form should be used for task prompt input? → A: Single multi-line text input field with an execution button (simple, one task at a time)
- Q: What should be displayed during task execution? → A: Loading indicator with execution status for each agent (running/completed/failed)
- Q: Should the leaderboard show only the latest execution or historical results? → A: Display latest execution results by default, with ability to browse past execution history organized by task
- Q: What timeout should be applied to agent execution? → A: Configurable timeout via TOML settings, default 60 seconds
- Q: What evaluation criteria should the evaluation agent use? → A: Evaluation prompt configurable via TOML settings with a default general-purpose prompt provided

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Execute Multi-Agent Competition (Priority: P1)

A user submits a natural language task prompt to the system and receives results from multiple competing agents executing the same task in parallel, each using different AI models.

**Why this priority**: This is the core value proposition - enabling users to compare how different AI models perform on the same task. Without this, the system has no purpose.

**Independent Test**: Can be fully tested by submitting a simple task prompt (e.g., "Check if 17 is prime") and verifying that multiple agents execute the task and return results. Delivers immediate value by showing AI model comparison.

**Acceptance Scenarios**:

1. **Given** a user opens the application, **When** they view the main interface, **Then** they see a multi-line text input field for entering task prompts and an execution button
2. **Given** a user has configured 2-5 AI models via TOML file or settings UI, **When** they enter a task prompt in the text field and click the execution button, **Then** the system launches one agent per configured model in parallel to execute the task
3. **Given** agents are executing a task, **When** the user views the interface, **Then** they see a loading indicator and the execution status (running/completed/failed) for each agent
4. **Given** agents are executing a task, **When** an agent needs information, **Then** the agent can call available tools (datetime, prime checker, palindrome checker) to gather information
5. **Given** an agent completes execution, **When** the status updates, **Then** the UI shows that specific agent as "completed" while other agents may still be running
6. **Given** an agent exceeds the configured timeout (default 60 seconds), **When** the timeout is reached, **Then** the agent is terminated and marked as "failed" in the status display
7. **Given** all agents have completed execution (successfully or via timeout), **When** results are ready, **Then** each agent's output is captured and stored for evaluation

---

### User Story 2 - View Evaluation Results and Rankings (Priority: P1)

A user views the leaderboard showing evaluation scores and rankings for all agents that competed on a task, with detailed feedback explaining each score, task results, and hierarchical tool usage.

**Why this priority**: Scores and rankings are essential for understanding which models performed best. Seeing tool usage hierarchy helps understand problem-solving approaches. Without evaluation, the comparison has no meaning.

**Independent Test**: Can be fully tested by checking the leaderboard after task execution completes. The leaderboard should display all agents sorted by score (highest first) with numeric scores (0-100), text explanations, task results, and hierarchical tree of tool calls. Delivers clear value by answering "which model is best for this task?"

**Acceptance Scenarios**:

1. **Given** multiple agents have completed a task, **When** the configured evaluation agent (independently specified in settings) reviews each agent's performance, **Then** each agent receives a score from 0-100 and a text explanation of the score
2. **Given** evaluation is complete, **When** the system updates the display, **Then** the leaderboard automatically shows the latest execution results in descending order by score (highest score first)
3. **Given** a user has submitted a task, **When** execution and evaluation complete, **Then** the leaderboard view automatically refreshes to display the new results without requiring manual page reload
4. **Given** the leaderboard is displayed, **When** the user examines a result, **Then** they can see the agent's score, evaluation text, final task output, and hierarchical structure of tool calls
5. **Given** an agent has called tools during execution, **When** the user views the leaderboard entry, **Then** tool calls are displayed in a hierarchical tree structure showing the sequence and nesting of tool invocations
6. **Given** an agent fails or times out during execution, **When** the user views the leaderboard, **Then** the failed agent is displayed with score 0 and evaluation text "Execution Failed"
7. **Given** past executions exist in DuckDB, **When** the user accesses the history view, **Then** they can browse previous task execution results organized by task with timestamps

---

### User Story 3 - Analyze Performance Metrics (Priority: P2)

A user views performance metrics for all competing agents, including execution duration and token consumption, displayed in visual charts in a separate dashboard tab/section to compare efficiency across different models.

**Why this priority**: Performance comparison (speed, resource usage) helps users choose not just the most accurate model but also the most efficient one. This is valuable for production deployment decisions but secondary to correctness evaluation.

**Independent Test**: Can be fully tested by viewing the performance dashboard tab/section after task completion. Charts should display execution time and token usage for each agent, enabling quick visual comparison. Delivers value by answering "which model is most efficient?"

**Acceptance Scenarios**:

1. **Given** agents have completed execution, **When** the system collects performance data, **Then** execution duration and token consumption are recorded for each agent
2. **Given** performance metrics are collected, **When** the user navigates to the performance dashboard tab/section, **Then** they can see visual charts comparing execution duration across all agents
3. **Given** performance metrics are collected, **When** the user navigates to the performance dashboard tab/section, **Then** they can see visual charts comparing token consumption across all agents
4. **Given** the charts are displayed, **When** the user examines a metric, **Then** they can identify which agent was fastest or most resource-efficient
5. **Given** the user is viewing results, **When** they want to switch between leaderboard and performance views, **Then** they can navigate between the leaderboard tab and performance dashboard tab

---

### User Story 4 - Configure AI Models (Priority: P2)

A user configures which AI models (and how many) will compete on tasks, either by editing a TOML configuration file or through the NiceGUI settings interface, supporting multiple providers like OpenAI, Anthropic, and Gemini.

**Why this priority**: Model configuration flexibility is essential for comparing different providers and adjusting based on cost, availability, or performance requirements. This enables the core value proposition but is secondary to executing and viewing results.

**Independent Test**: Can be fully tested by modifying the TOML file or using the settings UI to select 2-5 models from different providers, then verifying that subsequent task executions use the configured models. Delivers value by enabling users to customize their comparison setup.

**Acceptance Scenarios**:

1. **Given** a user wants to customize competing models, **When** they edit the TOML configuration file with model specifications (provider, model name, API key), **Then** the system loads and validates the configuration on startup
2. **Given** a user prefers UI-based configuration, **When** they access the settings interface in NiceGUI, **Then** they can select 2-5 models from available providers (OpenAI, Anthropic, Gemini) and save the configuration
3. **Given** a user wants to configure the evaluation agent, **When** they access the settings interface or edit the TOML file, **Then** they can select a specific model (provider and model name) to use for evaluation independently from task agent models
4. **Given** a user wants to customize evaluation criteria, **When** they edit the TOML configuration file, **Then** they can define a custom evaluation prompt (with a default general-purpose prompt provided)
5. **Given** a user wants to adjust execution timeout, **When** they edit the TOML configuration file or access settings UI, **Then** they can set a custom timeout value in seconds (default 60 seconds)
6. **Given** a user has configured models via UI, **When** the configuration is saved, **Then** the TOML file is updated to persist both task agent models and evaluation agent model settings
7. **Given** invalid configuration exists (e.g., fewer than 2 models or missing API keys), **When** the system starts or validates settings, **Then** a clear error message is displayed indicating what needs to be corrected

---

### User Story 5 - Browse Past Task Execution History (Priority: P3)

A user browses past task execution results to compare how different models performed on previous tasks or to review historical test results.

**Why this priority**: Historical comparison helps identify consistent model performance patterns and track improvements over time. This is valuable for analysis but secondary to viewing current results.

**Independent Test**: Can be fully tested by executing multiple tasks, then accessing the history view to verify all past executions are listed with timestamps and can be selected to view their leaderboards. Delivers value by enabling trend analysis.

**Acceptance Scenarios**:

1. **Given** multiple task executions have been completed and stored in DuckDB, **When** the user navigates to the history view, **Then** they see a list of past task executions organized by task prompt with timestamps
2. **Given** the history list is displayed, **When** the user selects a past execution, **Then** the leaderboard displays the results from that historical execution
3. **Given** a user is viewing a historical execution, **When** they want to return to the latest results, **Then** they can navigate back to the default latest execution view

---

### User Story 6 - Explore Execution History and Tool Usage (Priority: P3)

A user explores detailed execution history for each agent, including which tools were called, when they were called, and what results they returned.

**Why this priority**: Understanding HOW each agent solved the task (which tools it used and in what order) provides insight into different problem-solving approaches. This is valuable but secondary to seeing the final results and performance metrics.

**Independent Test**: Can be fully tested by selecting an agent from the leaderboard and viewing its execution history. The history should show a timeline of actions, tool calls, and results. Delivers value by helping users understand why certain models scored higher.

**Acceptance Scenarios**:

1. **Given** an agent has executed a task, **When** the agent calls any tool during execution, **Then** the tool name, input parameters, and output result are recorded in Pydantic AI's all_messages_json format
2. **Given** agent execution completes, **When** the system persists results, **Then** all_messages_json is stored in DuckDB's JSON column for efficient querying
3. **Given** execution history exists in DuckDB, **When** a user selects an agent from the leaderboard, **Then** they can view a complete chronological log of all actions taken by that agent retrieved from the database
4. **Given** the execution history is displayed, **When** a user examines a tool call, **Then** they can see what tool was called, what inputs were provided, and what output was returned

---

### Edge Cases

- **Agent failure or timeout**: Failed agents (including those exceeding the configurable timeout, default 60 seconds) are displayed on the leaderboard with score 0 and evaluation text "Execution Failed". Other agents continue execution without interruption.
- **Invalid model configuration**: System displays clear error message at startup or during settings validation indicating missing or invalid configuration (e.g., fewer than 2 task models, missing API keys, evaluation agent not configured).
- **Database initialization**: On first run, system creates DuckDB database file and required tables automatically.
- **Database write failure**: If DuckDB write fails during execution, system logs the error and displays a warning to the user but continues showing in-memory results for the current session.
- What happens when no tools are needed to complete the task?
- How does the system handle when all agents produce identical results?
- What happens when the evaluation agent cannot determine a clear score?
- How does the system handle tasks that require tools not currently available?
- What happens when a user submits an empty or malformed prompt?
- What happens when an API key becomes invalid during execution?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept natural language task prompts from users via a multi-line text input field in the NiceGUI interface
- **FR-023**: System MUST provide an execution button that triggers parallel agent execution when clicked
- **FR-002**: System MUST execute the same task using 2-5 different agents in parallel, with each agent using a different AI model as configured
- **FR-025**: System MUST display a loading indicator during task execution showing the execution status (running/completed/failed) for each agent in real-time
- **FR-028**: System MUST enforce a configurable timeout for agent execution (default 60 seconds, configurable via TOML)
- **FR-029**: System MUST treat agents that exceed the timeout as failed and display them with score 0 and evaluation text "Execution Failed"
- **FR-017**: System MUST support configuration of AI models via TOML file, including provider (OpenAI, Anthropic, Gemini, etc.), model name, and API credentials
- **FR-018**: System MUST provide a settings UI in NiceGUI for selecting and configuring 2-5 AI models from multiple providers
- **FR-019**: System MUST validate model configuration at startup and during settings changes, ensuring at least 2 models are configured with valid credentials
- **FR-020**: Changes made in the settings UI MUST be persisted to the TOML configuration file
- **FR-003**: System MUST provide three utility tools: current datetime retrieval, prime number validation, and palindrome validation
- **FR-004**: Agents MUST be able to call available tools dynamically based on task requirements
- **FR-005**: System MUST record complete execution history including all tool calls and their results for each agent using Pydantic AI's all_messages_json
- **FR-006**: System MUST evaluate each agent's performance using an evaluation agent (independently configurable via TOML and settings UI) that produces a numeric score (0-100) and text explanation
- **FR-021**: System MUST allow configuration of the evaluation agent model independently from task agent models via TOML file and settings UI
- **FR-030**: System MUST allow configuration of the evaluation prompt via TOML file to define custom evaluation criteria
- **FR-031**: System MUST provide a default general-purpose evaluation prompt that assesses accuracy, completeness, and efficiency if no custom prompt is configured
- **FR-007**: System MUST display the latest execution results by default in a leaderboard interface sorted by score in descending order (highest first)
- **FR-024**: System MUST automatically update the leaderboard display when new execution results are available, without requiring manual page reload
- **FR-026**: System MUST provide a history view where users can browse past task executions organized by task prompt with timestamps
- **FR-027**: System MUST allow users to select and view the leaderboard for any past execution from the history view
- **FR-008**: System MUST persist all execution history, evaluation results, and scores to DuckDB with JSON column support for efficient storage and querying
- **FR-022**: System MUST store Pydantic AI's all_messages_json output in DuckDB's native JSON column format for each agent execution
- **FR-009**: Leaderboard MUST display agent identifier, score, evaluation text, task output, and hierarchical tool call tree for each competing agent
- **FR-010**: Users MUST be able to view detailed execution history for each agent, including chronological tool calls and results
- **FR-011**: System MUST handle agent failures gracefully without blocking other agents or the overall evaluation; failed agents MUST be displayed on the leaderboard with score 0 and evaluation text "Execution Failed"
- **FR-012**: System MUST collect performance metrics for each agent execution, including execution duration and token consumption
- **FR-013**: System MUST display performance metrics in visual chart format in a separate dashboard tab/section, enabling comparison of execution duration across agents
- **FR-014**: System MUST display performance metrics in visual chart format in a separate dashboard tab/section, enabling comparison of token consumption across agents
- **FR-016**: Users MUST be able to navigate between the leaderboard view and the performance metrics dashboard view
- **FR-015**: Tool calls MUST be organized and displayed in a hierarchical structure that reflects the sequence and nesting of invocations

### Key Entities

- **Model Configuration**: Represents an AI model configuration entry, including provider name (OpenAI, Anthropic, Gemini, etc.), model identifier, API credentials, role (task agent or evaluation agent), and enabled status. Stored in TOML format and manageable via settings UI.
- **Task Submission**: Represents a user's natural language prompt requesting task execution, including the prompt text and submission timestamp. Persisted to DuckDB.
- **Agent Execution**: Represents a single agent's attempt to complete a task, including the agent identifier, model identifier (referencing Model Configuration), execution status, completion timestamp, and all_messages_json (Pydantic AI output stored in DuckDB JSON column). Persisted to DuckDB.
- **Tool Call**: Represents a single invocation of a utility tool by an agent, including tool name, input parameters, output result, timestamp, and hierarchical position (parent-child relationships for nested calls). Extracted from all_messages_json for display purposes.
- **Evaluation Result**: Represents the evaluation agent's assessment of an agent execution, including numeric score (0-100), text explanation, and evaluation timestamp. Persisted to DuckDB.
- **Performance Metrics**: Represents resource consumption data for an agent execution, including execution duration (time from start to completion) and token consumption (total tokens used by the agent). Persisted to DuckDB and used for chart generation via SQL aggregation queries.
- **Leaderboard Entry**: Represents a single row in the results display, aggregating agent execution, evaluation result, performance metrics, and hierarchical tool usage for ranking and comparison

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can submit a task prompt and see competing results from multiple agents within 30 seconds of execution completion
- **SC-002**: 100% of task executions produce a leaderboard with at least 2 competing agents ranked by evaluation score
- **SC-015**: Users can see real-time execution status updates for each agent during task execution, providing clear feedback on progress
- **SC-011**: Users can configure 2-5 task agent AI models and 1 evaluation agent model from multiple providers via TOML file or settings UI, with configuration persisted correctly
- **SC-012**: Invalid model configurations (missing task agents, missing evaluation agent, invalid credentials) are detected and reported with clear error messages before task execution
- **SC-003**: Users can view complete execution history showing all tool calls and results for any agent
- **SC-004**: Evaluation scores accurately reflect task completion quality based on configured evaluation criteria, with text explanations providing actionable feedback
- **SC-018**: Users can customize evaluation criteria via TOML configuration to align with specific task requirements
- **SC-005**: System successfully handles parallel execution of 2-5 agents without race conditions or data corruption
- **SC-017**: Agents that exceed the configured timeout (default 60 seconds) are automatically terminated and marked as failed in 100% of cases
- **SC-006**: Leaderboard displays results sorted correctly with highest scores appearing first in 100% of cases
- **SC-007**: Tool calls are displayed in hierarchical tree format showing parent-child relationships for 100% of agents that invoked tools
- **SC-008**: Performance metrics (duration and token consumption) are collected and displayed for 100% of agent executions
- **SC-009**: Visual charts enable users to identify the fastest agent and most token-efficient agent at a glance
- **SC-010**: Leaderboard shows complete information (task result, score, evaluation text, tool hierarchy, performance metrics) for each agent in a single view
- **SC-013**: All execution history, including all_messages_json, evaluation results, and performance metrics, are successfully persisted to DuckDB for 100% of task executions
- **SC-014**: Historical execution data can be queried and retrieved from DuckDB efficiently for leaderboard display and performance chart generation
- **SC-016**: Users can access and view past task execution results from the history view, enabling comparison across multiple execution sessions

## Quality Gates *(mandatory per constitution)*

### Code Quality Requirements
- [ ] All code passes `ruff check .` with zero violations
- [ ] All code passes `ruff format .` (formatting applied)
- [ ] All code passes `mypy .` with zero type errors
- [ ] All public functions/classes have Google-style docstrings
- [ ] All functions/methods/variables have type annotations

### Test-Driven Development Requirements
- [ ] Tests written BEFORE implementation
- [ ] Tests approved by user BEFORE implementation
- [ ] Red-Green-Refactor cycle followed
- [ ] Test file naming matches feature (e.g., `test_feature.py` for `feature.py`)

### Data Accuracy Requirements
- [ ] No magic numbers (all constants named)
- [ ] No hard-coded configuration values
- [ ] No credentials in code
- [ ] Configuration centrally managed
- [ ] Explicit error handling (no silent failures)

## Technology Stack *(mandatory)*

### Core Technologies

- **Agent Framework**: Pydantic AI (https://ai.pydantic.dev/) - All task agents and evaluation agent implemented using Pydantic AI
- **UI Framework**: NiceGUI (https://nicegui.io/) - Web interface for task submission, leaderboard display, and settings management
- **Database**: DuckDB - Local database for persisting execution history (all_messages_json), evaluation results, and performance metrics with native JSON column support
- **Configuration**: TOML - Configuration file format for AI model settings (providers, model names, API credentials)
- **Visualization**: Plotly (via NiceGUI integration) - Performance metrics charts (duration, token consumption)
- **Tree Display**: NiceGUI Tree component (https://nicegui.io/documentation/tree) - Hierarchical display of tool call sequences

### AI Model Providers (Configurable)

- **OpenAI**: Support for GPT-4, GPT-3.5, and other OpenAI models
- **Anthropic**: Support for Claude Sonnet, Haiku, Opus models
- **Google**: Support for Gemini models
- **Extensible**: Architecture allows adding additional providers as needed

### Development Tools

- **Linting**: ruff
- **Type Checking**: mypy
- **Testing**: pytest (per project standards)
