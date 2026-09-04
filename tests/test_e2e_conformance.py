import json
from pathlib import Path

from mtel_runtime import run_mtel

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source" / "core_public.mtel"


def test_external_fact_without_evidence_blocks():
    data = json.loads((ROOT / "examples" / "input_external_fact.json").read_text(encoding="utf-8"))
    result = run_mtel(SOURCE, data)
    assert result["status"] == "BLOCK"
    assert result["decision"]["target"] == "evidence_required"


def test_external_fact_with_evidence_routes():
    result = run_mtel(SOURCE, {"request": {"kind": "external_fact"}, "factual_claim": {"has_evidence": True}})
    assert result["status"] == "ROUTE"
    assert result["decision"]["target"] == "evidence_bounded_answer"


def test_document_route():
    data = {"request": {"kind": "document_fact"}, "document": {"available": True}}
    assert run_mtel(SOURCE, data)["decision"]["target"] == "document_bounded_answer"


def test_numeric_replay_route():
    data = {"request": {"kind": "numeric_replay"}, "numeric_replay": {"inputs_complete": True}}
    assert run_mtel(SOURCE, data)["decision"]["target"] == "deterministic_numeric_replay"
