from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from synergy_schema.native_catalog import (
    CatalogValidationError,
    catalog_digest,
    load_catalog,
    write_catalog,
)


ROOT = Path(__file__).parents[1]


def _catalog() -> dict[str, object]:
    return {
        "catalog_id": "pilates-config",
        "catalog_kind": "pilates",
        "revision": "abc123",
        "upstream": {
            "source_paths": ["pilates/config/models.py"],
            "revision": "abc123",
        },
        "digest_algorithm": "sha256",
        "content_digest": "",
        "elements": [
            {"kind": "config_path", "path": "run.region"},
            {"kind": "artifact_key", "path": "atlas_vehicles2_output"},
            {"kind": "sql_column", "path": "household"},
        ],
    }


def test_catalog_digest_and_resolution_are_offline(tmp_path: Path) -> None:
    path = tmp_path / "catalog.yaml"
    write_catalog(_catalog(), path)

    catalog = load_catalog(path)

    assert catalog.resolve("config_path", "run.region")
    assert catalog.resolve("artifact_key", "atlas_vehicles2_output")
    assert catalog.resolve("sql_column", "household")
    assert catalog.document["content_digest"] == catalog_digest(catalog.document)


def test_catalog_rejects_duplicate_or_bad_digest(tmp_path: Path) -> None:
    duplicate = _catalog()
    duplicate["elements"] = [
        {"kind": "config_path", "path": "run.region"},
        {"kind": "config_path", "path": "run.region"},
    ]
    path = tmp_path / "duplicate.yaml"
    path.write_text(yaml.safe_dump(duplicate), encoding="utf-8")
    with pytest.raises(CatalogValidationError, match="duplicate"):
        load_catalog(path)

    invalid = _catalog()
    invalid["content_digest"] = "0" * 64
    path.write_text(yaml.safe_dump(invalid), encoding="utf-8")
    with pytest.raises(CatalogValidationError, match="digest"):
        load_catalog(path)


def test_committed_catalogs_are_checksummed_and_resolvable() -> None:
    catalogs = sorted((ROOT / "catalogs").glob("*/*/catalog.yaml"))
    assert {path.parent.parent.name for path in catalogs} == {"pilates", "polaris"}
    for path in catalogs:
        catalog = load_catalog(path)
        assert catalog.document["content_digest"] == catalog_digest(catalog.document)
        assert (path.parent / "source.json").exists()


def test_refresh_uses_only_a_miniature_checkout(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    (checkout / "pilates/config").mkdir(parents=True)
    (checkout / "pilates/workflows").mkdir(parents=True)
    (checkout / "pilates/config/models.py").write_text(
        "from pydantic import BaseModel\n"
        "class RunConfig(BaseModel):\n    region: str\n"
        "class PilatesConfig(BaseModel):\n    run: RunConfig\n",
        encoding="utf-8",
    )
    (checkout / "pilates/workflows/artifact_keys.py").write_text(
        'OUTPUT = "post_atlas_population"\n', encoding="utf-8"
    )
    output = tmp_path / "out"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/refresh-native-contract-catalog"),
            "--kind",
            "pilates",
            "--checkout",
            str(checkout),
            "--out",
            str(output),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    catalog = load_catalog(output / "catalog.yaml")
    assert catalog.resolve("config_path", "run.region")
    assert catalog.resolve("artifact_key", "post_atlas_population")
    assert json.loads((output / "source.json").read_text())["source_paths"]
