import pytest

from mtel_runtime.errors import MTELRuntimeError
from mtel_runtime.evaluator import compile_expression, evaluate_expression


def test_match_no_match_and_unknown_path():
    data = {"request": {"kind": "external_fact"}, "factual_claim": {"has_evidence": True}}
    assert evaluate_expression('request.kind == "external_fact" and factual_claim.has_evidence == true', data)["state"] == "MATCH"
    assert evaluate_expression('request.kind == "document_fact"', data)["state"] == "NO_MATCH"
    result = evaluate_expression("missing.value == true", {})
    assert result["state"] == "ERROR"
    assert result["error"]["code"] == "UNKNOWN_PATH"


def test_unsafe_syntax_is_rejected_at_compile_and_runtime():
    with pytest.raises(MTELRuntimeError, match="unsupported expression node"):
        compile_expression("danger()")
    assert evaluate_expression("danger()", {})["error"]["code"] == "UNSAFE_EXPRESSION"
    assert evaluate_expression('request["kind"] == "external_fact"', {"request": {"kind": "external_fact"}})["error"]["code"] == "UNSAFE_EXPRESSION"
