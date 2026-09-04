import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_normal_malformed_output_has_no_traceback(tmp_path: Path):
    source = tmp_path / "bad.mtel"
    source.write_text('@spec MTEL/0.2\nrule bad\n  when true\nend\n', encoding="utf-8")
    result = subprocess.run([sys.executable, "-m", "mtel_runtime", "inspect", "--source", str(source)], text=True, capture_output=True)
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert json.loads(result.stdout)["error"]["code"] == "RULE_MISSING_ACTION"


def test_debug_mode_can_show_traceback(tmp_path: Path):
    missing = tmp_path / "missing.mtel"
    result = subprocess.run([sys.executable, "-m", "mtel_runtime", "--debug", "inspect", "--source", str(missing)], text=True, capture_output=True)
    assert result.returncode == 2
    assert "Traceback" in result.stderr
    assert json.loads(result.stdout)["error"]["code"] == "SOURCE_NOT_FOUND"
