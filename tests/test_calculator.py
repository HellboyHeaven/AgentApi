import pytest

from app.tools.base import ToolError
from app.tools.calculator import calculate


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("2 + 2", "4"),
        ("17 * 23", "391"),
        ("391 / 4", "97.75"),
        ("7 // 2", "3"),
        ("7 % 3", "1"),
        ("2 ** 10", "1024"),
        ("-3 + 5", "2"),
        ("(1 + 2) * (3 + 4)", "21"),
        ("sqrt(16)", "4"),
        ("round(sqrt(2), 5)", "1.41421"),
        ("0.1 + 0.2", "0.3"),
        ("1 / 3", "0.333333333333"),
        ("pi * 2", "6.28318530718"),
        ("floor(2.7) + ceil(2.1)", "5"),
        ("1_000 * 3", "3000"),
        ("  2 + 2  ", "4"),
    ],
)
def test_valid_expressions(expression, expected):
    assert calculate(expression) == expected


def test_big_but_allowed_power():
    assert len(calculate("2 ** 1000")) == 302


@pytest.mark.parametrize(
    "expression, message",
    [
        ("", "empty"),
        ("   ", "empty"),
        ("x * 2", "Unknown name"),
        ("__import__('os').system('ls')", "Unknown function"),
        ("open('/etc/passwd')", "Unknown function"),
        ("().__class__", "Unsupported syntax"),
        ("[1, 2, 3]", "Unsupported syntax"),
        ("1,5 + 2", "Unsupported syntax"),
        ("lambda: 1", "Unsupported syntax"),
        ("'a' * 3", "Only plain numbers"),
        ("True + 1", "Only plain numbers"),
        ("1j * 2", "Only plain numbers"),
        ("2 ^ 3", "exponentiation"),
        ("1 / 0", "Division by zero"),
        ("0 ** -1", "Division by zero"),
        ("sqrt(-1)", "Math error"),
        ("round(1.5, 2.5)", "Math error"),
        ("sqrt(1, 2, 3)", "at most two"),
        ("9 ** 9 ** 9", "too large"),
        ("999 ** 999", "too large"),
        ("(-8) ** 0.5", "not a real number"),
        ("1 +", "Could not parse"),
        ("x" * 201, "longer than"),
    ],
)
def test_rejected_expressions(expression, message):
    with pytest.raises(ToolError, match=message):
        calculate(expression)


def test_null_byte_is_rejected_not_crashed():
    with pytest.raises(ToolError):
        calculate("1\x00 + 1")