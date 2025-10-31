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

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Execute Multi-Agent Competition (Priority: P1)

A user submits a natural language task prompt to the system and receives results from multiple competing agents executing the same task in parallel, each using different AI models.

**Why this priority**: This is the core value proposition - enabling users to compare how different AI models perform on the same task. Without this, the system has no purpose.

**Independent Test**: Can be fully tested by submitting a simple task prompt (e.g., "Check if 17 is prime") and verifying that multiple agents execute the task and return results. Delivers immediate value by showing AI model comparison.

**Acceptance Scenarios**:

1. **Given** a user has a task to complete, **When** they submit a task prompt through the interface, **Then** the system launches 2-5 different agents in parallel to execute the task
2. **Given** agents are executing a task, **When** an agent needs information, **Then** the agent can call available tools (datetime, prime checker, palindrome checker) to gather information
3. **Given** all agents have completed execution, **When** results are ready, **Then** each agent's output is captured and stored for evaluation

---

### User Story 2 - View Evaluation Results and Rankings (Priority: P1)

A user views the leaderboard showing evaluation scores and rankings for all agents that competed on a task, with detailed feedback explaining each score.

**Why this priority**: Scores and rankings are essential for understanding which models performed best. Without evaluation, the comparison has no meaning.

**Independent Test**: Can be fully tested by checking the leaderboard after task execution completes. The leaderboard should display all agents sorted by score (highest first) with both numeric scores (0-100) and text explanations. Delivers clear value by answering "which model is best for this task?"

**Acceptance Scenarios**:

1. **Given** multiple agents have completed a task, **When** an evaluation agent reviews each agent's performance, **Then** each agent receives a score from 0-100 and a text explanation of the score
2. **Given** evaluation is complete, **When** the user views the leaderboard, **Then** agents are displayed in descending order by score (highest score first)
3. **Given** the leaderboard is displayed, **When** the user examines a result, **Then** they can see the agent's score, evaluation text, and final output

---

### User Story 3 - Explore Execution History and Tool Usage (Priority: P2)

A user explores detailed execution history for each agent, including which tools were called, when they were called, and what results they returned.

**Why this priority**: Understanding HOW each agent solved the task (which tools it used and in what order) provides insight into different problem-solving approaches. This is valuable but secondary to seeing the final results.

**Independent Test**: Can be fully tested by selecting an agent from the leaderboard and viewing its execution history. The history should show a timeline of actions, tool calls, and results. Delivers value by helping users understand why certain models scored higher.

**Acceptance Scenarios**:

1. **Given** an agent has executed a task, **When** the agent calls any tool during execution, **Then** the tool name, input parameters, and output result are recorded
2. **Given** execution history exists, **When** a user selects an agent from the leaderboard, **Then** they can view a complete chronological log of all actions taken by that agent
3. **Given** the execution history is displayed, **When** a user examines a tool call, **Then** they can see what tool was called, what inputs were provided, and what output was returned

---

### Edge Cases

- What happens when an agent fails or times out during execution?
- What happens when no tools are needed to complete the task?
- How does the system handle when all agents produce identical results?
- What happens when the evaluation agent cannot determine a clear score?
- How does the system handle tasks that require tools not currently available?
- What happens when a user submits an empty or malformed prompt?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept natural language task prompts from users
- **FR-002**: System MUST execute the same task using 2-5 different agents in parallel
- **FR-003**: System MUST provide three utility tools: current datetime retrieval, prime number validation, and palindrome validation
- **FR-004**: Agents MUST be able to call available tools dynamically based on task requirements
- **FR-005**: System MUST record complete execution history including all tool calls and their results for each agent
- **FR-006**: System MUST evaluate each agent's performance using an evaluation agent that produces a numeric score (0-100) and text explanation
- **FR-007**: System MUST display results in a leaderboard interface sorted by score in descending order (highest first)
- **FR-008**: System MUST persist all execution history, evaluation results, and scores for later review
- **FR-009**: Leaderboard MUST display agent identifier, score, evaluation text, and task output for each competing agent
- **FR-010**: Users MUST be able to view detailed execution history for each agent, including chronological tool calls and results
- **FR-011**: System MUST handle agent failures gracefully without blocking other agents or the overall evaluation

### Key Entities

- **Task Submission**: Represents a user's natural language prompt requesting task execution, including the prompt text and submission timestamp
- **Agent Execution**: Represents a single agent's attempt to complete a task, including the agent identifier, model identifier, execution status, and completion timestamp
- **Tool Call**: Represents a single invocation of a utility tool by an agent, including tool name, input parameters, output result, and timestamp
- **Evaluation Result**: Represents the evaluation agent's assessment of an agent execution, including numeric score (0-100), text explanation, and evaluation timestamp
- **Leaderboard Entry**: Represents a single row in the results display, aggregating agent execution, evaluation result, and key metrics for ranking

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can submit a task prompt and see competing results from multiple agents within 30 seconds of execution completion
- **SC-002**: 100% of task executions produce a leaderboard with at least 2 competing agents ranked by evaluation score
- **SC-003**: Users can view complete execution history showing all tool calls and results for any agent
- **SC-004**: Evaluation scores accurately reflect task completion quality, with text explanations providing actionable feedback
- **SC-005**: System successfully handles parallel execution of 2-5 agents without race conditions or data corruption
- **SC-006**: Leaderboard displays results sorted correctly with highest scores appearing first in 100% of cases

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
