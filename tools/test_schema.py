"""
test_schema.py - Tests for tools/schema.py (JSON-Schema-style validation).
Run: pytest tools/test_schema.py -v
"""

from __future__ import annotations

import pytest

from tools.exceptions import ValidationError
from tools.schema import is_valid, load_schema, validate


class TestSchemaLoading:
    def test_load_requirements_schema(self) -> None:
        s = load_schema("requirements")
        assert s["title"] == "Requirements"

    def test_load_missing_schema_raises(self) -> None:
        with pytest.raises(ValidationError):
            load_schema("does-not-exist")


class TestValidation:
    def test_valid_object(self) -> None:
        s = load_schema("requirements")
        validate({"object": "x", "language": "English", "analysis_type": "combined"}, s)

    def test_missing_required(self) -> None:
        s = load_schema("requirements")
        with pytest.raises(ValidationError):
            validate({"object": "x"}, s)

    def test_enum_violation(self) -> None:
        s = load_schema("requirements")
        with pytest.raises(ValidationError):
            validate({"object": "x", "language": "French", "analysis_type": "combined"}, s)

    def test_type_mismatch(self) -> None:
        s = {"type": "object", "properties": {"n": {"type": "integer"}}}
        with pytest.raises(ValidationError):
            validate({"n": "not int"}, s)

    def test_number_bounds(self) -> None:
        s = {"type": "object", "properties": {"n": {"type": "number", "minimum": 0, "maximum": 1}}}
        validate({"n": 0.5}, s)
        with pytest.raises(ValidationError):
            validate({"n": 2}, s)

    def test_array_items(self) -> None:
        s = {"type": "array", "items": {"type": "integer"}, "minItems": 1}
        validate([1, 2, 3], s)
        with pytest.raises(ValidationError):
            validate([], s)
        with pytest.raises(ValidationError):
            validate([1, "x"], s)

    def test_pattern(self) -> None:
        s = load_schema("final-report")
        validate({"date": "2026-07-20"}, {"type": "object", "properties": {"date": s["properties"]["date"]}})
        with pytest.raises(ValidationError):
            validate({"date": "20-07-2026"}, {"type": "object", "properties": {"date": s["properties"]["date"]}})

    def test_additional_properties_false(self) -> None:
        s = load_schema("tool-risk-matrix")
        validate({"probability": 2, "impact": 3}, s)
        with pytest.raises(ValidationError):
            validate({"probability": 2, "impact": 3, "extra": 1}, s)

    def test_is_valid_non_raising(self) -> None:
        s = load_schema("requirements")
        assert is_valid({"object": "x", "language": "English", "analysis_type": "combined"}, s)
        assert not is_valid({"object": "x"}, s)

    def test_one_of(self) -> None:
        s = {"oneOf": [{"type": "string"}, {"type": "integer"}]}
        validate("hi", s)
        validate(5, s)
        with pytest.raises(ValidationError):
            validate([], s)

    def test_const(self) -> None:
        s = {"const": "OK"}
        validate("OK", s)
        with pytest.raises(ValidationError):
            validate("NO", s)
