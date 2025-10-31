"""Default configuration values for the agent leaderboard system.

This module provides default values used when configuration is not
fully specified or for fallback scenarios.
"""

DEFAULT_EVALUATION_PROMPT = """You are evaluating the performance of an AI agent that \
completed a task.

Task: {task_prompt}

Agent's Response: {agent_response}

Please evaluate the agent's response on the following criteria:
1. Correctness: Did the agent correctly complete the task?
2. Efficiency: Did the agent use tools appropriately?
3. Completeness: Did the agent provide a complete answer?

Provide:
1. A score from 0-100 (where 100 is perfect)
2. A brief explanation of your evaluation

Response format:
Score: [number]
Explanation: [your explanation]"""

DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_DATABASE_PATH = "agent_leaderboard.duckdb"
