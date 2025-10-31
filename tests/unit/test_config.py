"""Unit tests for configuration management.

Tests for configuration models, loader, and validation.
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.config.loader import ConfigLoader
from src.config.models import (
    AppConfig,
    DatabaseConfig,
    EvaluationConfig,
    ExecutionConfig,
    ModelConfig,
)


class TestModelConfig:
    """Tests for ModelConfig validation."""

    def test_valid_model_config(self) -> None:
        """Test valid model configuration."""
        os.environ["TEST_API_KEY"] = "test-key-123"
        config = ModelConfig(provider="openai", model="gpt-4o", api_key_env="TEST_API_KEY")
        assert config.provider == "openai"
        assert config.model == "gpt-4o"
        assert config.api_key_env == "TEST_API_KEY"
        del os.environ["TEST_API_KEY"]

    def test_missing_api_key_env(self) -> None:
        """Test that missing environment variable raises error."""
        if "NONEXISTENT_KEY" in os.environ:
            del os.environ["NONEXISTENT_KEY"]

        with pytest.raises(ValueError, match="not found"):
            ModelConfig(provider="openai", model="gpt-4o", api_key_env="NONEXISTENT_KEY")

    def test_empty_api_key(self) -> None:
        """Test that empty API key raises error."""
        os.environ["EMPTY_KEY"] = ""
        with pytest.raises(ValueError, match="is empty"):
            ModelConfig(provider="openai", model="gpt-4o", api_key_env="EMPTY_KEY")
        del os.environ["EMPTY_KEY"]

    def test_invalid_provider(self) -> None:
        """Test that invalid provider is rejected."""
        os.environ["TEST_KEY"] = "test"
        with pytest.raises(ValueError):
            ModelConfig(provider="invalid", model="gpt-4o", api_key_env="TEST_KEY")
        del os.environ["TEST_KEY"]


class TestExecutionConfig:
    """Tests for ExecutionConfig validation."""

    def test_default_timeout(self) -> None:
        """Test default timeout value."""
        config = ExecutionConfig()
        assert config.timeout_seconds == 60

    def test_custom_timeout(self) -> None:
        """Test custom timeout value."""
        config = ExecutionConfig(timeout_seconds=120)
        assert config.timeout_seconds == 120

    def test_timeout_below_minimum(self) -> None:
        """Test that timeout below 1 is rejected."""
        with pytest.raises(ValueError):
            ExecutionConfig(timeout_seconds=0)

    def test_timeout_above_maximum(self) -> None:
        """Test that timeout above 600 is rejected."""
        with pytest.raises(ValueError):
            ExecutionConfig(timeout_seconds=601)


class TestEvaluationConfig:
    """Tests for EvaluationConfig validation."""

    def test_valid_evaluation_config(self) -> None:
        """Test valid evaluation configuration."""
        os.environ["EVAL_KEY"] = "eval-key-123"
        config = EvaluationConfig(
            provider="openai",
            model="gpt-4o",
            api_key_env="EVAL_KEY",
            prompt="Test prompt with {task_prompt} and {agent_response}",
        )
        assert config.provider == "openai"
        assert "{task_prompt}" in config.prompt
        del os.environ["EVAL_KEY"]


class TestDatabaseConfig:
    """Tests for DatabaseConfig."""

    def test_default_path(self) -> None:
        """Test default database path."""
        config = DatabaseConfig()
        assert config.path == "agent_leaderboard.duckdb"

    def test_custom_path(self) -> None:
        """Test custom database path."""
        config = DatabaseConfig(path="custom.duckdb")
        assert config.path == "custom.duckdb"


class TestAppConfig:
    """Tests for AppConfig validation."""

    def test_valid_app_config(self) -> None:
        """Test valid application configuration with 2 task agents."""
        os.environ["KEY1"] = "key1"
        os.environ["KEY2"] = "key2"
        os.environ["EVAL_KEY"] = "eval"

        config = AppConfig(
            execution=ExecutionConfig(timeout_seconds=60),
            task_agents=[
                ModelConfig(provider="openai", model="gpt-4o", api_key_env="KEY1"),
                ModelConfig(provider="anthropic", model="claude-sonnet-4", api_key_env="KEY2"),
            ],
            evaluation_agent=EvaluationConfig(
                provider="openai",
                model="gpt-4o",
                api_key_env="EVAL_KEY",
                prompt="Evaluate: {task_prompt} -> {agent_response}",
            ),
            database=DatabaseConfig(),
        )

        assert len(config.task_agents) == 2
        assert config.execution.timeout_seconds == 60

        del os.environ["KEY1"]
        del os.environ["KEY2"]
        del os.environ["EVAL_KEY"]

    def test_too_few_task_agents(self) -> None:
        """Test that fewer than 2 task agents is rejected."""
        os.environ["KEY1"] = "key1"
        os.environ["EVAL_KEY"] = "eval"

        with pytest.raises(ValueError):
            AppConfig(
                execution=ExecutionConfig(),
                task_agents=[ModelConfig(provider="openai", model="gpt-4o", api_key_env="KEY1")],
                evaluation_agent=EvaluationConfig(
                    provider="openai",
                    model="gpt-4o",
                    api_key_env="EVAL_KEY",
                    prompt="Test",
                ),
                database=DatabaseConfig(),
            )

        del os.environ["KEY1"]
        del os.environ["EVAL_KEY"]

    def test_duplicate_models(self) -> None:
        """Test that duplicate models are rejected."""
        os.environ["KEY1"] = "key1"
        os.environ["EVAL_KEY"] = "eval"

        with pytest.raises(ValueError, match="Duplicate models"):
            AppConfig(
                execution=ExecutionConfig(),
                task_agents=[
                    ModelConfig(provider="openai", model="gpt-4o", api_key_env="KEY1"),
                    ModelConfig(provider="openai", model="gpt-4o", api_key_env="KEY1"),
                ],
                evaluation_agent=EvaluationConfig(
                    provider="openai",
                    model="gpt-4o",
                    api_key_env="EVAL_KEY",
                    prompt="Test",
                ),
                database=DatabaseConfig(),
            )

        del os.environ["KEY1"]
        del os.environ["EVAL_KEY"]


class TestConfigLoader:
    """Tests for ConfigLoader."""

    def test_load_valid_config(self) -> None:
        """Test loading a valid TOML configuration file."""
        os.environ["KEY1"] = "key1"
        os.environ["KEY2"] = "key2"
        os.environ["EVAL_KEY"] = "eval"

        toml_content = """
[execution]
timeout_seconds = 90

[[task_agents]]
provider = "openai"
model = "gpt-4o"
api_key_env = "KEY1"

[[task_agents]]
provider = "anthropic"
model = "claude-sonnet-4"
api_key_env = "KEY2"

[evaluation_agent]
provider = "openai"
model = "gpt-4o"
api_key_env = "EVAL_KEY"
prompt = "Evaluate: {task_prompt} -> {agent_response}"

[database]
path = "test.duckdb"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            temp_path = f.name

        try:
            config = ConfigLoader.load(temp_path)
            assert config.execution.timeout_seconds == 90
            assert len(config.task_agents) == 2
            assert config.database.path == "test.duckdb"
        finally:
            Path(temp_path).unlink()
            del os.environ["KEY1"]
            del os.environ["KEY2"]
            del os.environ["EVAL_KEY"]

    def test_load_nonexistent_file(self) -> None:
        """Test that loading nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load("/nonexistent/config.toml")

    def test_load_invalid_toml(self) -> None:
        """Test that invalid TOML raises error."""
        invalid_toml = "invalid {{{ toml"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(invalid_toml)
            temp_path = f.name

        try:
            with pytest.raises(Exception):  # TOMLDecodeError
                ConfigLoader.load(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_validate_dict(self) -> None:
        """Test validating a configuration dictionary."""
        os.environ["KEY1"] = "key1"
        os.environ["KEY2"] = "key2"
        os.environ["EVAL_KEY"] = "eval"

        config_dict = {
            "execution": {"timeout_seconds": 60},
            "task_agents": [
                {"provider": "openai", "model": "gpt-4o", "api_key_env": "KEY1"},
                {
                    "provider": "anthropic",
                    "model": "claude-sonnet-4",
                    "api_key_env": "KEY2",
                },
            ],
            "evaluation_agent": {
                "provider": "openai",
                "model": "gpt-4o",
                "api_key_env": "EVAL_KEY",
                "prompt": "Test",
            },
            "database": {"path": "test.duckdb"},
        }

        config = ConfigLoader.validate_dict(config_dict)
        assert isinstance(config, AppConfig)

        del os.environ["KEY1"]
        del os.environ["KEY2"]
        del os.environ["EVAL_KEY"]
