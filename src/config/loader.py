"""TOML configuration file loader with validation.

This module provides functionality to load and save application
configuration from/to TOML files with Pydantic validation.
"""

import tomllib
from pathlib import Path
from typing import Any

from .models import AppConfig


class ConfigLoader:
    """Loader for TOML configuration files with validation."""

    @staticmethod
    def load(config_path: str | Path) -> AppConfig:
        """Load and validate configuration from a TOML file.

        Args:
            config_path: Path to the TOML configuration file

        Returns:
            Validated application configuration

        Raises:
            FileNotFoundError: If the configuration file does not exist
            ValueError: If the configuration is invalid
            tomllib.TOMLDecodeError: If the TOML file is malformed
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with config_path.open("rb") as f:
            config_dict = tomllib.load(f)

        try:
            return AppConfig(**config_dict)
        except Exception as e:
            raise ValueError(f"Invalid configuration: {e}") from e

    @staticmethod
    def save(config: AppConfig, config_path: str | Path) -> None:
        """Save configuration to a TOML file.

        Args:
            config: Application configuration to save
            config_path: Path to the TOML configuration file

        Raises:
            OSError: If the file cannot be written
        """
        import tomli_w

        config_path = Path(config_path)
        config_dict = config.model_dump()

        with config_path.open("wb") as f:
            tomli_w.dump(config_dict, f)

    @staticmethod
    def validate_dict(config_dict: dict[str, Any]) -> AppConfig:
        """Validate a configuration dictionary without loading from file.

        Args:
            config_dict: Configuration dictionary to validate

        Returns:
            Validated application configuration

        Raises:
            ValueError: If the configuration is invalid
        """
        try:
            return AppConfig(**config_dict)
        except Exception as e:
            raise ValueError(f"Invalid configuration: {e}") from e
