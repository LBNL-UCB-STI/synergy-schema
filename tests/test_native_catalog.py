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


def test_committed_pilates_catalog_preserves_static_legacy_spellings() -> None:
    catalog = load_catalog(
        ROOT / "catalogs/pilates/3877652b77990949c0b4cbbc982899b280a2ba38/catalog.yaml"
    )
    assert catalog.resolve("config_path", "shared.database.shapshot_path")


def test_refresh_uses_only_a_miniature_checkout(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    (checkout / "pilates/config").mkdir(parents=True)
    (checkout / "pilates/workflows").mkdir(parents=True)
    (checkout / "pilates/config/models.py").write_text(
        "from pydantic import BaseModel\n"
        "class RunConfig(BaseModel):\n    region: str\n"
        "class ChildConfig(BaseModel):\n    enabled: bool\n"
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


def test_refresh_traverses_quoted_forward_references(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    (checkout / "pilates/config").mkdir(parents=True)
    (checkout / "pilates/workflows").mkdir(parents=True)
    (checkout / "pilates/config/models.py").write_text(
        "from typing import Optional\n"
        "from pydantic import BaseModel\n"
        "class ChildConfig(BaseModel):\n    enabled: bool\n"
        'class PilatesConfig(BaseModel):\n    child: Optional["ChildConfig"]\n',
        encoding="utf-8",
    )
    (checkout / "pilates/workflows/artifact_keys.py").write_text("", encoding="utf-8")
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
    assert load_catalog(output / "catalog.yaml").resolve("config_path", "child.enabled")


def test_polaris_refresh_inventories_explicit_output_columns(tmp_path: Path) -> None:
    source = tmp_path / "translation_sql"
    source.mkdir()
    (source / "10_households.sql").write_text(
        "create or replace temp view polaris_households as\n"
        "select cast(h.id as bigint) as household, 0 as workers\n"
        "from input_households h;\n",
        encoding="utf-8",
    )
    output = tmp_path / "out"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/refresh-native-contract-catalog"),
            "--kind",
            "polaris",
            "--checkout",
            str(source),
            "--out",
            str(output),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    catalog = load_catalog(output / "catalog.yaml")
    assert catalog.resolve("sql_column", "polaris_households.household")
    assert catalog.resolve("sql_column", "polaris_households.workers")
    assert not catalog.resolve("sql_column", "polaris_households.bigint")
    assert not catalog.resolve("sql_column", "polaris_households.integer")
