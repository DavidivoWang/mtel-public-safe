import hashlib
import json
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


def test_public_inventory_and_manifest_are_current():
    root = Path(__file__).resolve().parents[1]
    inventory_path = root / "PUBLIC_FILE_INVENTORY.json"
    manifest_path = root / "PUBLIC_RELEASE_MANIFEST.yaml"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert inventory["file_count"] == len(inventory["files"])
    for entry in inventory["files"]:
        payload = (root / entry["path"]).read_bytes()
        assert len(payload) == entry["bytes"]
        assert hashlib.sha256(payload).hexdigest() == entry["sha256"]

    inventory_sha = hashlib.sha256(inventory_path.read_bytes()).hexdigest()
    assert manifest["payload_inventory_sha256"] == inventory_sha

    manifest_files = {entry["path"]: entry for entry in manifest["files"]}
    assert manifest_files["PUBLIC_FILE_INVENTORY.json"]["sha256"] == inventory_sha
    assert set(manifest_files) == {
        "PUBLIC_RELEASE_MANIFEST.yaml",
        "PUBLIC_FILE_INVENTORY.json",
        *(entry["path"] for entry in inventory["files"]),
    }
    for entry in inventory["files"]:
        assert manifest_files[entry["path"]]["sha256"] == entry["sha256"]
