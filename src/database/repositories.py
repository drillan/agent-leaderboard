"""Database repositories for task and execution management.

This module provides repository pattern implementation for
database operations on tasks, executions, and evaluations.
"""

from src.database.connection import DatabaseConnection
from src.models.evaluation import EvaluationResult
from src.models.execution import AgentExecution
from src.models.task import TaskSubmission


class TaskRepository:
    """Repository for task and execution management.

    Handles CRUD operations for TaskSubmission, AgentExecution,
    and EvaluationResult entities.
    """

    def __init__(self, db: DatabaseConnection):
        """Initialize repository with database connection.

        Args:
            db: DatabaseConnection instance
        """
        self.db = db

    def create_task(self, task: TaskSubmission) -> int:
        """Create a new task submission in the database.

        Args:
            task: TaskSubmission instance to persist

        Returns:
            Database ID of the created task

        Raises:
            Exception: If database operation fails
        """
        conn = self.db.connect()

        cursor = conn.execute(
            "INSERT INTO task_submissions (prompt, submitted_at) VALUES (?, ?) RETURNING id",
            [task.prompt, task.submitted_at],
        )

        result = cursor.fetchone()
        if result is None:
            raise RuntimeError("Failed to create task: no ID returned")

        task_id: int = result[0]
        conn.commit()

        return task_id

    def create_execution(self, execution: AgentExecution) -> int:
        """Create a new agent execution record in the database.

        Args:
            execution: AgentExecution instance to persist

        Returns:
            Database ID of the created execution

        Raises:
            Exception: If database operation fails
        """
        conn = self.db.connect()

        cursor = conn.execute(
            """
            INSERT INTO agent_executions
            (task_id, model_provider, model_name, status, started_at,
             completed_at, duration_seconds, token_count, all_messages)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id
            """,
            [
                execution.task_id,
                execution.model_provider,
                execution.model_name,
                execution.status.value,
                execution.started_at,
                execution.completed_at,
                execution.duration_seconds,
                execution.token_count,
                execution.all_messages_json,
            ],
        )

        result = cursor.fetchone()
        if result is None:
            raise RuntimeError("Failed to create execution: no ID returned")

        execution_id: int = result[0]
        conn.commit()

        return execution_id

    def update_execution_result(self, execution: AgentExecution) -> None:
        """Update an existing execution with results.

        Args:
            execution: AgentExecution instance with updated fields (must have id)

        Raises:
            ValueError: If execution.id is None
            Exception: If database operation fails
        """
        if execution.id is None:
            raise ValueError("Execution must have an ID to be updated")

        conn = self.db.connect()

        conn.execute(
            """
            UPDATE agent_executions
            SET status = ?,
                completed_at = ?,
                duration_seconds = ?,
                token_count = ?,
                all_messages = ?
            WHERE id = ?
            """,
            [
                execution.status.value,
                execution.completed_at,
                execution.duration_seconds,
                execution.token_count,
                execution.all_messages_json,
                execution.id,
            ],
        )

        conn.commit()

    def get_task(self, task_id: int) -> TaskSubmission | None:
        """Retrieve a task by ID.

        Args:
            task_id: Database ID of the task

        Returns:
            TaskSubmission instance if found, None otherwise
        """
        conn = self.db.connect()

        result = conn.execute(
            "SELECT id, prompt, submitted_at FROM task_submissions WHERE id = ?",
            [task_id],
        ).fetchone()

        if not result:
            return None

        return TaskSubmission(id=result[0], prompt=result[1], submitted_at=result[2])

    def get_execution(self, execution_id: int) -> AgentExecution | None:
        """Retrieve an execution by ID.

        Args:
            execution_id: Database ID of the execution

        Returns:
            AgentExecution instance if found, None otherwise
        """
        conn = self.db.connect()

        result = conn.execute(
            """
            SELECT id, task_id, model_provider, model_name, status,
                   started_at, completed_at, duration_seconds, token_count, all_messages
            FROM agent_executions WHERE id = ?
            """,
            [execution_id],
        ).fetchone()

        if not result:
            return None

        return AgentExecution(
            id=result[0],
            task_id=result[1],
            model_provider=result[2],
            model_name=result[3],
            status=result[4],
            started_at=result[5],
            completed_at=result[6],
            duration_seconds=result[7],
            token_count=result[8],
            all_messages_json=result[9],
        )

    def get_executions_for_task(self, task_id: int) -> list[AgentExecution]:
        """Retrieve all executions for a specific task.

        Args:
            task_id: Database ID of the task

        Returns:
            List of AgentExecution instances (may be empty)
        """
        conn = self.db.connect()

        results = conn.execute(
            """
            SELECT id, task_id, model_provider, model_name, status,
                   started_at, completed_at, duration_seconds, token_count, all_messages
            FROM agent_executions
            WHERE task_id = ?
            ORDER BY started_at ASC
            """,
            [task_id],
        ).fetchall()

        executions = []
        for row in results:
            executions.append(
                AgentExecution(
                    id=row[0],
                    task_id=row[1],
                    model_provider=row[2],
                    model_name=row[3],
                    status=row[4],
                    started_at=row[5],
                    completed_at=row[6],
                    duration_seconds=row[7],
                    token_count=row[8],
                    all_messages_json=row[9],
                )
            )

        return executions

    def create_evaluation(self, evaluation: EvaluationResult) -> int:
        """Create a new evaluation record in the database.

        Args:
            evaluation: EvaluationResult instance to persist

        Returns:
            Database ID of the created evaluation

        Raises:
            Exception: If database operation fails
        """
        conn = self.db.connect()

        cursor = conn.execute(
            """
            INSERT INTO evaluations
            (execution_id, score, explanation, evaluated_at)
            VALUES (?, ?, ?, ?)
            RETURNING id
            """,
            [
                evaluation.execution_id,
                evaluation.score,
                evaluation.explanation,
                evaluation.evaluated_at,
            ],
        )

        result = cursor.fetchone()
        if result is None:
            raise RuntimeError("Failed to create evaluation: no ID returned")

        evaluation_id: int = result[0]
        conn.commit()

        return evaluation_id

    def get_leaderboard(self, task_id: int) -> list[dict[str, object]]:
        """Get leaderboard entries for a specific task.

        Args:
            task_id: Database ID of the task

        Returns:
            List of dictionaries with leaderboard data, sorted by score DESC, duration ASC
        """
        conn = self.db.connect()

        results = conn.execute(
            """
            SELECT
                execution_id,
                model_provider,
                model_name,
                status,
                duration_seconds,
                token_count,
                score,
                evaluation_text,
                prompt
            FROM leaderboard_entries
            WHERE task_id = ?
            ORDER BY score DESC, duration_seconds ASC
            """,
            [task_id],
        ).fetchall()

        leaderboard = []
        for row in results:
            leaderboard.append(
                {
                    "execution_id": row[0],
                    "model_provider": row[1],
                    "model_name": row[2],
                    "status": row[3],
                    "duration_seconds": row[4],
                    "token_count": row[5],
                    "score": row[6],
                    "evaluation_text": row[7],
                    "prompt": row[8],
                }
            )

        return leaderboard
