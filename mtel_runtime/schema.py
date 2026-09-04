from __future__ import annotations

from typing import Any

from .errors import MTELRuntimeError

REQUEST_KINDS = {"external_fact", "document_fact", "numeric_replay"}
TOP_LEVEL_KEYS = {"request", "factual_claim", "document", "numeric_replay", "repo", "execution", "context"}


def _object(data: dict[str, Any], key: str, *, required: bool = False) -> dict[str, Any] | None:
    if key not in data:
        if required:
            raise MTELRuntimeError("SCHEMA_REQUIRED", f"$: '{key}' is a required property")
        return None
    value = data[key]
    if not isinstance(value, dict):
        raise MTELRuntimeError("SCHEMA_TYPE", f"{key}: expected object")
    return value


def _reject_extra(obj: dict[str, Any], allowed: set[str], path: str) -> None:
    extras = sorted(set(obj) - allowed)
    if extras:
        raise MTELRuntimeError("SCHEMA_ADDITIONAL_PROPERTY", f"{path}: unexpected property '{extras[0]}'")


def _required_bool(obj: dict[str, Any], key: str, path: str) -> None:
    if key not in obj:
        raise MTELRuntimeError("SCHEMA_REQUIRED", f"{path}: '{key}' is a required property")
    if not isinstance(obj[key], bool):
        raise MTELRuntimeError("SCHEMA_TYPE", f"{path}.{key}: expected boolean")


def validate_input(data: dict[str, Any]) -> None:
    _reject_extra(data, TOP_LEVEL_KEYS, "$")
    request = _object(data, "request", required=True)
    assert request is not None
    _reject_extra(request, {"kind", "output_contract"}, "request")
    if "kind" not in request:
        raise MTELRuntimeError("SCHEMA_REQUIRED", "request: 'kind' is a required property")
    kind = request["kind"]
    if not isinstance(kind, str):
        raise MTELRuntimeError("SCHEMA_TYPE", "request.kind: expected string")
    if kind not in REQUEST_KINDS:
        raise MTELRuntimeError("SCHEMA_ENUM", f"request.kind: unsupported value '{kind}'")
    if "output_contract" in request and not isinstance(request["output_contract"], str):
        raise MTELRuntimeError("SCHEMA_TYPE", "request.output_contract: expected string")

    for name, allowed in (
        ("factual_claim", {"has_evidence"}),
        ("document", {"available"}),
        ("numeric_replay", {"inputs_complete"}),
    ):
        obj = _object(data, name)
        if obj is not None:
            _reject_extra(obj, allowed, name)
    for name in ("repo", "execution", "context"):
        _object(data, name)

    if kind == "external_fact":
        obj = _object(data, "factual_claim", required=True)
        assert obj is not None
        _required_bool(obj, "has_evidence", "factual_claim")
    elif kind == "document_fact":
        obj = _object(data, "document", required=True)
        assert obj is not None
        _required_bool(obj, "available", "document")
    else:
        obj = _object(data, "numeric_replay", required=True)
        assert obj is not None
        _required_bool(obj, "inputs_complete", "numeric_replay")
