"""Tool implementations for agent use.

This module provides utility tools that agents can call during task execution:
- get_datetime: Returns current date and time
- check_prime: Validates if a number is prime
- check_palindrome: Checks if text is a palindrome
"""

from datetime import datetime


def get_datetime() -> str:
    """Get the current date and time.

    Returns:
        Current datetime in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)

    Example:
        >>> result = get_datetime()
        >>> isinstance(result, str)
        True
        >>> "T" in result  # ISO format includes 'T' separator
        True
    """
    return datetime.now().isoformat()


def check_prime(n: int) -> dict[str, bool | str]:
    """Check if a number is prime.

    A prime number is a natural number greater than 1 that has no positive
    divisors other than 1 and itself.

    Args:
        n: The number to check (must be >= 2)

    Returns:
        Dictionary containing:
            - is_prime: Boolean indicating if the number is prime
            - reason: Explanation of the result

    Raises:
        ValueError: If n < 2

    Example:
        >>> check_prime(17)
        {'is_prime': True, 'reason': '17 is a prime number'}
        >>> check_prime(4)
        {'is_prime': False, 'reason': '4 is not prime (divisible by 2)'}
    """
    if n < 2:
        raise ValueError("Number must be >= 2 for prime checking")

    if n == 2:
        return {"is_prime": True, "reason": "2 is the only even prime number"}

    if n % 2 == 0:
        return {"is_prime": False, "reason": f"{n} is not prime (divisible by 2)"}

    # Check odd divisors up to sqrt(n)
    i = 3
    while i * i <= n:
        if n % i == 0:
            return {"is_prime": False, "reason": f"{n} is not prime (divisible by {i})"}
        i += 2

    return {"is_prime": True, "reason": f"{n} is a prime number"}


def check_palindrome(text: str) -> dict[str, bool | str]:
    """Check if text is a palindrome (case-insensitive).

    A palindrome is a word, phrase, or sequence that reads the same
    backward as forward when ignoring case and non-alphanumeric characters.

    Args:
        text: The text to check

    Returns:
        Dictionary containing:
            - is_palindrome: Boolean indicating if the text is a palindrome
            - cleaned_text: The normalized text used for comparison
            - reason: Explanation of the result

    Example:
        >>> check_palindrome("racecar")
        {'is_palindrome': True, 'cleaned_text': 'racecar', 'reason': 'Text is a palindrome'}
        >>> check_palindrome("A man a plan a canal Panama")
        {'is_palindrome': True, 'cleaned_text': 'amanaplanacanalpanama', 'reason': 'Text is a palindrome'}
        >>> check_palindrome("hello")
        {'is_palindrome': False, 'cleaned_text': 'hello', 'reason': 'Text is not a palindrome'}
    """
    # Remove non-alphanumeric characters and convert to lowercase
    cleaned = "".join(c.lower() for c in text if c.isalnum())

    if not cleaned:
        return {
            "is_palindrome": False,
            "cleaned_text": cleaned,
            "reason": "No alphanumeric characters found",
        }

    is_palindrome = cleaned == cleaned[::-1]

    return {
        "is_palindrome": is_palindrome,
        "cleaned_text": cleaned,
        "reason": "Text is a palindrome" if is_palindrome else "Text is not a palindrome",
    }
