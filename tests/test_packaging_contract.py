from pathlib import Path

import mtel_runtime


def test_package_has_no_path_injection_or_legacy_import():
    root = Path(mtel_runtime.__file__).resolve().parent
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    assert "sys.path.insert" not in text
    assert "from runtime" not in text
    assert "import runtime" not in text


def test_two_public_library_functions_are_explicit():
    assert mtel_runtime.__all__ == ["run_mtel", "inspect_mtel"]
