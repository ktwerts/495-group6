"""Tests for the shared input helpers every module uses."""

import pytest

from app.errors import ValidationError
from app.validation import (
    parse_date,
    parse_int,
    parse_positive_number,
    parse_qualifications,
    parse_time,
    require_fields,
    require_json,
)


def test_parse_date():
    assert parse_date("2026-11-16").isoformat() == "2026-11-16"
    with pytest.raises(ValidationError):
        parse_date("16/11/2026")


def test_parse_time_normalizes():
    assert parse_time("9:05") == "09:05"
    with pytest.raises(ValidationError):
        parse_time("9am")


def test_parse_int_bounds():
    assert parse_int("3", "n", 1, 5) == 3
    with pytest.raises(ValidationError, match="at least 1"):
        parse_int(0, "n", minimum=1)
    with pytest.raises(ValidationError, match="at most 5"):
        parse_int(9, "n", maximum=5)
    with pytest.raises(ValidationError):
        parse_int("x", "n")


def test_parse_positive_number():
    assert parse_positive_number("40", "hours", maximum=80) == 40.0
    with pytest.raises(ValidationError):
        parse_positive_number(0, "hours")
    with pytest.raises(ValidationError):
        parse_positive_number(100, "hours", maximum=80)
    with pytest.raises(ValidationError):
        parse_positive_number("abc", "hours")


def test_parse_qualifications():
    assert parse_qualifications(" Cook, cashier,cook ") == ["cashier", "cook"]
    assert parse_qualifications(["A", "b"]) == ["a", "b"]
    assert parse_qualifications(None) == []
    with pytest.raises(ValidationError):
        parse_qualifications(5)


def test_require_fields_and_json():
    require_fields({"a": 1, "b": 0}, "a", "b")
    with pytest.raises(ValidationError, match="b"):
        require_fields({"a": 1, "b": ""}, "a", "b")
    with pytest.raises(ValidationError):
        require_json(["not", "a", "dict"])
