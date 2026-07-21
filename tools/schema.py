"""
schema.py - Lightweight JSON-Schema-style validation for water-puppetry-staging-design.

Provides dependency-free validation of structured inputs/outputs exchanged
between the main agent, sub-agents, hooks, and tools. Supports the subset of
JSON Schema used by this project's asset schemas (type, required, properties,
enum, minimum, maximum, minItems, maxItems, items, additionalProperties,
oneOf, pattern). Designed for production runtime, not a full draft-2020 impl.

Usage:
    from tools.schema import validate, ValidationError as SchemaError
    validate({"object": "x"}, load_schema("requirements"))
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tools.exceptions import ValidationError

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "schemas"

_TYPE_MAP: dict[str, type | tuple[type, ...]] = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "null": type(None),
}


def load_schema(name: str, assets_dir: Path | None = None) -> dict[str, Any]:
    """Load a JSON schema from assets/schemas/<name>.schema.json."""
    base = assets_dir or ASSETS_DIR
    path = base / f"{name}.schema.json"
    if not path.exists():
        raise ValidationError(f"Schema file not found: {path}", gate="schema")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as ex:
        raise ValidationError(f"Invalid JSON in schema {name}: {ex}", gate="schema") from ex


def validate(instance: Any, schema: dict[str, Any], *, path: str = "$") -> None:
    """Validate ``instance`` against ``schema``. Raises ValidationError on failure."""
    if not isinstance(schema, dict):
        raise ValidationError(f"Schema at {path} must be an object", gate="schema")

    if "oneOf" in schema:
        matched = False
        last_err: str | None = None
        for sub in schema["oneOf"]:
            try:
                validate(instance, sub, path=path)
                matched = True
                break
            except ValidationError as ex:
                last_err = str(ex)
        if not matched:
            raise ValidationError(f"{path}: value does not match any oneOf branch ({last_err})", gate="schema")
        return

    if "type" in schema:
        expected = schema["type"]
        types = expected if isinstance(expected, list) else [expected]
        if not any(_check_type(instance, t) for t in types):
            raise ValidationError(
                f"{path}: expected type {expected}, got {type(instance).__name__}",
                gate="schema",
            )

    if "enum" in schema and instance not in schema["enum"]:
        raise ValidationError(f"{path}: value {instance!r} not in enum {schema['enum']}", gate="schema")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            raise ValidationError(f"{path}: string shorter than minLength", gate="schema")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            raise ValidationError(f"{path}: string longer than maxLength", gate="schema")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            raise ValidationError(
                f"{path}: string {instance!r} does not match pattern {schema['pattern']!r}",
                gate="schema",
            )

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            raise ValidationError(f"{path}: {instance} < minimum {schema['minimum']}", gate="schema")
        if "maximum" in schema and instance > schema["maximum"]:
            raise ValidationError(f"{path}: {instance} > maximum {schema['maximum']}", gate="schema")
        if "exclusiveMinimum" in schema and instance <= schema["exclusiveMinimum"]:
            raise ValidationError(f"{path}: {instance} <= exclusiveMinimum {schema['exclusiveMinimum']}", gate="schema")
        if "exclusiveMaximum" in schema and instance >= schema["exclusiveMaximum"]:
            raise ValidationError(f"{path}: {instance} >= exclusiveMaximum {schema['exclusiveMaximum']}", gate="schema")

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            raise ValidationError(f"{path}: fewer than minItems {schema['minItems']}", gate="schema")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            raise ValidationError(f"{path}: more than maxItems {schema['maxItems']}", gate="schema")
        item_schema = schema.get("items")
        if item_schema is not None:
            for idx, item in enumerate(instance):
                validate(item, item_schema, path=f"{path}[{idx}]")

    if isinstance(instance, dict):
        required = schema.get("required", [])
        missing = [k for k in required if k not in instance]
        if missing:
            raise ValidationError(f"{path}: missing required keys {missing}", gate="schema")
        props = schema.get("properties", {})
        for key, value in instance.items():
            if key in props:
                validate(value, props[key], path=f"{path}.{key}")
            elif schema.get("additionalProperties") is False:
                raise ValidationError(f"{path}: additional property {key!r} not allowed", gate="schema")
            else:
                ap = schema.get("additionalProperties")
                if isinstance(ap, dict):
                    validate(value, ap, path=f"{path}.{key}")

    if "const" in schema and instance != schema["const"]:
        raise ValidationError(f"{path}: value {instance!r} != const {schema['const']!r}", gate="schema")


def _check_type(instance: Any, type_name: str) -> bool:
    py_type = _TYPE_MAP.get(type_name)
    if py_type is None:
        return True
    if type_name == "integer" and isinstance(instance, bool):
        return False
    if type_name == "number" and isinstance(instance, bool):
        return False
    return isinstance(instance, py_type)


def is_valid(instance: Any, schema: dict[str, Any]) -> bool:
    """Return True if valid, False otherwise (non-raising convenience)."""
    try:
        validate(instance, schema)
        return True
    except ValidationError:
        return False
