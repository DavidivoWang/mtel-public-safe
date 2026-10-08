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


def test_missing_flow_is_attributed_to_execution_stage(tmp_path: Path):
    source = _write(tmp_path, '@spec MTEL/0.2\nrule allow priority 10\n  when true\n  -> PASS "ok"\nend\nflow default\n  bind *\n  overlap hold\nend\n')
    result = run_mtel(source, _input(), flow="missing")
    assert result["status"] == "ERROR"
    assert result["error"]["code"] == "FLOW_NOT_FOUND"
    assert result["trace"] == ["parse:PASS", "flow:missing:ERROR"]


def test_equal_priority_first_uses_definition_order_and_emits_selection(tmp_path: Path, monkeypatch):
    events = []
    monkeypatch.setattr("mtel_runtime.engine.emit", lambda event, **fields: events.append((event, fields)))
    rules = {
        "a": 'rule a priority 5\n  when true\n  -> PASS "a_target"\nend\n',
        "b": 'rule b priority 5\n  when true\n  -> ROUTE "b_target"\nend\n',
    }
    for first, second, action in (("a", "b", "PASS"), ("b", "a", "ROUTE")):
        events.clear()
        source = _write(
            tmp_path,
            '@spec MTEL/0.2\n'
            + rules[first] + rules[second]
            + 'flow default\n  bind *\n  overlap first\nend\n',
        )
        result = run_mtel(source, _input())

        assert result["status"] == action
        assert result["decision"] == {
            "action": action, "target": f"{first}_target",
            "rule": first, "priority": 5, "veto": False,
        }
        assert result["matched_rules"] == [first, second]
        assert result["trace"][-1] == f"selected:{first}"
        selected = [fields for event, fields in events if event == "rule_selected"]
        assert selected == [{
            "rule": first, "action": action, "target": f"{first}_target",
            "priority": 5, "veto": False,
        }]


def test_overlap_first_filters_veto_before_source_order(tmp_path: Path):
    source = _write(
        tmp_path,
        '@spec MTEL/0.2\n'
        'rule allow priority 10\n  when true\n  -> PASS "ok"\nend\n'
        'rule block priority 1 veto\n  when true\n  -> BLOCK "stop"\nend\n'
        'flow default\n  bind *\n  overlap first\nend\n',
    )
    result = run_mtel(source, _input())
    assert result["status"] == "BLOCK"
    assert result["decision"]["rule"] == "block"
    assert result["matched_rules"] == ["allow", "block"]
