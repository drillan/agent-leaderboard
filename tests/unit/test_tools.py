"""Unit tests for agent tools.

Tests for the three utility tools: get_datetime, check_prime, check_palindrome.
"""

import re
from datetime import datetime

import pytest

from src.agents.tools import check_palindrome, check_prime, get_datetime


class TestGetDatetime:
    """Tests for get_datetime tool."""

    def test_returns_string(self) -> None:
        """Test that get_datetime returns a string."""
        result = get_datetime()
        assert isinstance(result, str)

    def test_iso_format(self) -> None:
        """Test that result is in ISO 8601 format."""
        result = get_datetime()
        # ISO format: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DDTHH:MM:SS.ffffff
        iso_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
        assert re.match(iso_pattern, result), f"Result '{result}' is not in ISO format"

    def test_recent_timestamp(self) -> None:
        """Test that returned datetime is recent (within last second)."""
        before = datetime.now()
        result = get_datetime()
        after = datetime.now()

        result_dt = datetime.fromisoformat(result)
        assert before <= result_dt <= after


class TestCheckPrime:
    """Tests for check_prime tool."""

    def test_prime_number_2(self) -> None:
        """Test that 2 is correctly identified as prime."""
        result = check_prime(2)
        assert result["is_prime"] is True
        assert "2" in result["reason"]

    def test_prime_number_17(self) -> None:
        """Test that 17 is correctly identified as prime."""
        result = check_prime(17)
        assert result["is_prime"] is True
        assert "17" in result["reason"]

    def test_prime_number_large(self) -> None:
        """Test a larger prime number (97)."""
        result = check_prime(97)
        assert result["is_prime"] is True

    def test_not_prime_4(self) -> None:
        """Test that 4 is correctly identified as not prime."""
        result = check_prime(4)
        assert result["is_prime"] is False
        assert "4" in result["reason"]

    def test_not_prime_100(self) -> None:
        """Test that 100 is correctly identified as not prime."""
        result = check_prime(100)
        assert result["is_prime"] is False

    def test_invalid_input_negative(self) -> None:
        """Test that negative numbers raise ValueError."""
        with pytest.raises(ValueError, match="must be >= 2"):
            check_prime(-5)

    def test_invalid_input_zero(self) -> None:
        """Test that zero raises ValueError."""
        with pytest.raises(ValueError, match="must be >= 2"):
            check_prime(0)

    def test_invalid_input_one(self) -> None:
        """Test that one raises ValueError."""
        with pytest.raises(ValueError, match="must be >= 2"):
            check_prime(1)

    def test_result_structure(self) -> None:
        """Test that result has expected structure."""
        result = check_prime(17)
        assert "is_prime" in result
        assert "reason" in result
        assert isinstance(result["is_prime"], bool)
        assert isinstance(result["reason"], str)


class TestCheckPalindrome:
    """Tests for check_palindrome tool."""

    def test_simple_palindrome(self) -> None:
        """Test a simple palindrome: racecar."""
        result = check_palindrome("racecar")
        assert result["is_palindrome"] is True
        assert result["cleaned_text"] == "racecar"

    def test_case_insensitive(self) -> None:
        """Test that check is case-insensitive: Racecar."""
        result = check_palindrome("Racecar")
        assert result["is_palindrome"] is True
        assert result["cleaned_text"] == "racecar"

    def test_phrase_with_spaces(self) -> None:
        """Test phrase with spaces: A man a plan a canal Panama."""
        result = check_palindrome("A man a plan a canal Panama")
        assert result["is_palindrome"] is True
        assert result["cleaned_text"] == "amanaplanacanalpanama"

    def test_with_punctuation(self) -> None:
        """Test palindrome with punctuation: A man, a plan, a canal: Panama!"""
        result = check_palindrome("A man, a plan, a canal: Panama!")
        assert result["is_palindrome"] is True

    def test_not_palindrome(self) -> None:
        """Test a non-palindrome: hello."""
        result = check_palindrome("hello")
        assert result["is_palindrome"] is False
        assert result["cleaned_text"] == "hello"

    def test_single_character(self) -> None:
        """Test single character (always palindrome): a."""
        result = check_palindrome("a")
        assert result["is_palindrome"] is True

    def test_empty_string(self) -> None:
        """Test empty string (not a palindrome)."""
        result = check_palindrome("")
        assert result["is_palindrome"] is False
        assert "No alphanumeric characters" in result["reason"]

    def test_only_punctuation(self) -> None:
        """Test string with only punctuation."""
        result = check_palindrome("!@#$%")
        assert result["is_palindrome"] is False
        assert "No alphanumeric characters" in result["reason"]

    def test_result_structure(self) -> None:
        """Test that result has expected structure."""
        result = check_palindrome("test")
        assert "is_palindrome" in result
        assert "cleaned_text" in result
        assert "reason" in result
        assert isinstance(result["is_palindrome"], bool)
        assert isinstance(result["cleaned_text"], str)
        assert isinstance(result["reason"], str)
