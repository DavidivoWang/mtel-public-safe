from pathlib import Path

from mtel_runtime import run_mtel
from mtel_runtime.schema import validate_input

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source" / "core_public.mtel"


def test_supported_nested_contracts_validate():
    validate_input({"request": {"kind": "external_fact"}, "factual_claim": {"has_evidence": False}})
    validate_input({"request": {"kind": "document_fact"}, "document": {"available": True}})
    validate_input({"request": {"kind": "numeric_replay"}, "numeric_replay": {"inputs_complete": True}})


def test_wrong_shape_fails_before_evaluation():
    result = run_mtel(SOURCE, {"request": {"kind": "external_fact"}, "factual_claim": {"has_evidence": "yes"}})
    assert result["status"] == "ERROR"
    assert result["error"]["code"] == "SCHEMA_TYPE"
    assert result["trace"] == ["parse:PASS", "schema:ERROR"]


def test_unknown_request_kind_is_rejected():
    result = run_mtel(SOURCE, {"request": {"kind": "other"}})
    assert result["error"]["code"] == "SCHEMA_ENUM"
