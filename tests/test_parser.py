from pathlib import Path

from mtel_runtime.api import inspect_mtel
from mtel_runtime.parser import parse_program


def test_include_and_flow(tmp_path: Path):
    module = tmp_path / "module.mtel"
    module.write_text('@spec MTEL/0.2\nrule r priority 1\n  when true\n  -> PASS "ok"\nend\n', encoding="utf-8")
    root = tmp_path / "root.mtel"
    root.write_text('@spec MTEL/0.2\ninclude "module.mtel"\nflow default\n  bind *\n  overlap hold\nend\n', encoding="utf-8")
    program = parse_program(root)
    assert [rule.name for rule in program.rules] == ["r"]


def test_malformed_rule_and_traversal_are_structured(tmp_path: Path):
    bad = tmp_path / "bad.mtel"
    bad.write_text('@spec MTEL/0.2\nrule bad\n  when true\nend\n', encoding="utf-8")
    result = inspect_mtel(bad)
    assert result["error"]["code"] == "RULE_MISSING_ACTION"
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    source = source_dir / "root.mtel"
    source.write_text('@spec MTEL/0.2\ninclude "../outside.mtel"\n', encoding="utf-8")
    assert inspect_mtel(source)["error"]["code"] == "INCLUDE_TRAVERSAL"


def test_duplicate_flow_is_rejected(tmp_path: Path):
    source = tmp_path / "dup.mtel"
    source.write_text(
        '@spec MTEL/0.2\nrule a\n  when true\n  -> PASS "a"\nend\n'
        'flow default\n  bind a\nend\nflow default\n  bind a\nend\n',
        encoding="utf-8",
    )
    result = inspect_mtel(source)
    assert result["status"] == "ERROR"
    assert result["error"]["code"] == "FLOW_DUPLICATE_NAME"


def test_inspect_rejects_unsafe_expression(tmp_path: Path):
    source = tmp_path / "unsafe.mtel"
    source.write_text('@spec MTEL/0.2\nrule bad\n  when danger()\n  -> PASS "x"\nend\n', encoding="utf-8")
    result = inspect_mtel(source)
    assert result["status"] == "ERROR"
    assert result["error"]["code"] == "UNSAFE_EXPRESSION"
