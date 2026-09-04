from __future__ import annotations

from pathlib import Path
from typing import Any

from .audit import emit
from .engine import execute
from .errors import MTELRuntimeError
from .evaluator import compile_expression
from .parser import parse_program
from .schema import validate_input


def _rethrow_or_payload(exc: Exception, debug: bool, trace: list[str]) -> dict[str, Any]:
    if debug:
        raise exc
    if isinstance(exc, MTELRuntimeError):
        error = exc.to_dict()
    else:
        error = {"code": "INTERNAL_ERROR", "message": "unexpected internal error"}
    return {"status": "ERROR", "error": error, "trace": trace}


def inspect_mtel(source_path: str | Path, *, debug: bool = False) -> dict[str, Any]:
    source = str(source_path)
    emit("parse_started", mode="inspect", source=source)
    try:
        program = parse_program(source_path)
        emit("parse_completed", mode="inspect", source_files=len(program.source_files))
        for rule in program.rules:
            try:
                compile_expression(rule.expression)
            except MTELRuntimeError as exc:
                raise MTELRuntimeError(
                    exc.code,
                    f"rule {rule.name}: {exc.message}",
                    rule.source,
                    rule.line,
                ) from exc
        return {
            "status": "PASS",
            "spec": program.spec,
            "rules": [
                {
                    "name": rule.name,
                    "priority": rule.priority,
                    "veto": rule.veto,
                    "action": rule.action,
                    "target": rule.target,
                }
                for rule in program.rules
            ],
            "flows": [
                {
                    "name": flow.name,
                    "bindings": list(flow.bindings),
                    "overlap": flow.overlap,
                }
                for flow in program.flows
            ],
            "source_files": list(program.source_files),
        }
    except Exception as exc:
        emit("parse_failed", mode="inspect", error=getattr(exc, "code", "INTERNAL_ERROR"))
        return _rethrow_or_payload(exc, debug, ["inspect:ERROR"])


def run_mtel(
    source_path: str | Path,
    input_data: dict[str, Any],
    flow: str = "default",
    *,
    debug: bool = False,
) -> dict[str, Any]:
    source = str(source_path)
    emit("parse_started", mode="run", source=source)
    try:
        if not isinstance(input_data, dict):
            raise MTELRuntimeError("INPUT_TYPE", "input_data must be an object")
        program = parse_program(source_path)
        emit("parse_completed", mode="run", source_files=len(program.source_files))
        validate_input(input_data)
        emit("input_validated", schema="when_input_v0_2")
        return execute(program, input_data, flow)
    except Exception as exc:
        code = getattr(exc, "code", "INTERNAL_ERROR")
        if code.startswith("SCHEMA_"):
            emit("input_validation_failed", error=code)
            trace = ["parse:PASS", "schema:ERROR"]
        else:
            emit("parse_failed", mode="run", error=code)
            trace = ["parse:ERROR"]
        return _rethrow_or_payload(exc, debug, trace)
