"""Unit tests for provider mapping functionality.

Tests for get_pydantic_ai_provider function with all supported providers.
"""

import pytest

from src.config.models import get_pydantic_ai_provider


class TestProviderMapping:
    """Tests for get_pydantic_ai_provider function."""

    def test_openai_provider_mapping(self) -> None:
        """Test OpenAI provider maps to correct Pydantic AI format."""
        assert get_pydantic_ai_provider("openai") == "openai"

    def test_anthropic_provider_mapping(self) -> None:
        """Test Anthropic provider maps to correct Pydantic AI format."""
        assert get_pydantic_ai_provider("anthropic") == "anthropic"

    def test_gemini_provider_mapping(self) -> None:
        """Test Gemini provider maps to correct Pydantic AI format."""
        assert get_pydantic_ai_provider("gemini") == "google-gla:"

    def test_groq_provider_mapping(self) -> None:
        """Test Groq provider maps to correct Pydantic AI format."""
        assert get_pydantic_ai_provider("groq") == "groq:"

    def test_huggingface_provider_mapping(self) -> None:
        """Test Hugging Face provider maps to correct Pydantic AI format."""
        assert get_pydantic_ai_provider("huggingface") == "huggingface:"

    def test_unknown_provider_raises_error(self) -> None:
        """Test unknown provider raises ValueError."""
        with pytest.raises(ValueError, match="Unknown provider"):
            get_pydantic_ai_provider("unknown_provider")

    def test_error_message_includes_valid_providers(self) -> None:
        """Test error message lists all valid providers."""
        with pytest.raises(ValueError) as exc_info:
            get_pydantic_ai_provider("invalid")

        error_message = str(exc_info.value)
        assert "openai" in error_message
        assert "anthropic" in error_message
        assert "gemini" in error_message
        assert "groq" in error_message
        assert "huggingface" in error_message
