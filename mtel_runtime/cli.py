from __future__ import annotations

import argparse
import json
import traceback
from pathlib import Path
from typing import Any

from .api import inspect_mtel, run_mtel
from .audit import configure_logging
from .errors import MTELRuntimeError


def _load_input(path: str | None, inline: str | None) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8")) if path else json.loads(inline) if inline else {}
    if not isinstance(value, dict):
        raise ValueError("input JSON must be an object")
    return value


def _print(payload: dict[str, Any], pretty: bool) -> None:
    print(json.dumps(payload, indent=2 if pretty else None, sort_keys=True))


def _exception_payload(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, MTELRuntimeError):
        return {"status": "ERROR", "error": exc.to_dict()}
    if isinstance(exc, (OSError, ValueError, json.JSONDecodeError)):
        return {"status": "ERROR", "error": {"code": "INPUT_ERROR", "message": str(exc)}}
    return {"status": "ERROR", "error": {"code": "INTERNAL_ERROR", "message": "unexpected internal error"}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mtel-runtime")
    parser.add_argument("--log-level", default="WARNING")
    parser.add_argument("--debug", action="store_true", help="show Python traceback for diagnostic use")
    sub = parser.add_subparsers(dest="command", required=True)
    inspect_parser = sub.add_parser("inspect")
    inspect_parser.add_argument("--source", required=True)
    inspect_parser.add_argument("--pretty", action="store_true")
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--source", required=True)
    run_parser.add_argument("--input")
    run_parser.add_argument("--data")
    run_parser.add_argument("--flow", default="default")
    run_parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    configure_logging(args.log_level)
    try:
        if args.command == "inspect":
            payload = inspect_mtel(args.source, debug=args.debug)
            _print(payload, args.pretty)
            return 0 if payload["status"] == "PASS" else 2
        payload = run_mtel(
            args.source,
            _load_input(args.input, args.data),
            args.flow,
            debug=args.debug,
        )
        _print(payload, args.pretty)
        return 0 if payload["status"] != "ERROR" else 2
    except Exception as exc:
        if args.debug:
            traceback.print_exc()
        _print(_exception_payload(exc), True)
        return 2
