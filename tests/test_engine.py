from pathlib import Path

from mtel_runtime import run_mtel


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "rules.mtel"
    path.write_text(body, encoding="utf-8")
    return path


def _input() -> dict:
    return {"request": {"kind": "external_fact"}, "factual_claim": {"has_evidence": True}}


def test_veto_wins(tmp_path: Path):
    source = _write(tmp_path, '@spec MTEL/0.2\nrule allow priority 10\n  when true\n  -> PASS "ok"\nend\nrule block priority 1 veto\n  when true\n  -> BLOCK "stop"\nend\nflow default\n  bind *\n  overlap hold\nend\n')
    result = run_mtel(source, _input())
    assert result["status"] == "BLOCK"
    assert result["decision"]["rule"] == "block"


def test_equal_priority_conflict_holds(tmp_path: Path):
    source = _write(tmp_path, '@spec MTEL/0.2\nrule a priority 5\n  when true\n  -> PASS "a"\nend\nrule b priority 5\n  when true\n  -> ROUTE "b"\nend\nflow default\n  bind *\n  overlap hold\nend\n')
    result = run_mtel(source, _input())
    assert result["status"] == "HOLD"
    assert result["decision"]["target"] == "rule_conflict"
