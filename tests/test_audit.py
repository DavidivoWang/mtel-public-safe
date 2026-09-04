import json
from pathlib import Path

from mtel_runtime import run_mtel
from mtel_runtime.audit import configure_logging

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source" / "core_public.mtel"
VALID_INPUT = {
    "request": {"kind": "external_fact"},
    "factual_claim": {"has_evidence": False},
}


def _events(capsys):
    return [json.loads(line) for line in capsys.readouterr().err.splitlines() if line.strip()]


def _assert_strict_flat(events):
    for event in events:
        assert all(not isinstance(value, (dict, list)) for value in event.values()), event


def _write_source(tmp_path: Path, expression: str) -> Path:
    source = tmp_path / "audit_error.mtel"
    source.write_text(
        "@spec MTEL/0.2\n"
        "rule audit_error\n"
        f"  when {expression}\n"
        "  -> PASS \"never\"\n"
        "end\n"
        "flow default\n"
        "  bind *\n"
        "  overlap hold\n"
        "end\n",
        encoding="utf-8",
    )
    return source


def test_logging_is_flat_json_and_has_minimum_event_chain(capsys):
    configure_logging("INFO")
    run_mtel(SOURCE, VALID_INPUT)
    events = _events(capsys)
    names = {event["event"] for event in events}
    assert {
        "parse_started",
        "parse_completed",
        "input_validated",
        "execution_started",
        "condition_evaluated",
        "rule_selected",
        "execution_completed",
    } <= names
    selected = next(event for event in events if event["event"] == "rule_selected")
    assert selected["rule"] == "block_unsupported_fact"
    _assert_strict_flat(events)


def test_condition_unsupported_event_is_strict_flat(capsys, tmp_path: Path):
    configure_logging("INFO")
    result = run_mtel(_write_source(tmp_path, "danger()"), VALID_INPUT)
    events = _events(capsys)
    unsupported = next(event for event in events if event["event"] == "condition_unsupported")
    assert result["status"] == "HOLD"
    assert unsupported["error_code"] == "UNSAFE_EXPRESSION"
    assert "error_message" in unsupported
    assert "error" not in unsupported
    _assert_strict_flat(events)


def test_condition_error_event_is_strict_flat(capsys, tmp_path: Path):
    configure_logging("INFO")
    result = run_mtel(_write_source(tmp_path, "missing.value == true"), VALID_INPUT)
    events = _events(capsys)
    condition_error = next(event for event in events if event["event"] == "condition_error")
    assert result["status"] == "HOLD"
    assert condition_error["error_code"] == "UNKNOWN_PATH"
    assert "error_message" in condition_error
    assert "error" not in condition_error
    _assert_strict_flat(events)
