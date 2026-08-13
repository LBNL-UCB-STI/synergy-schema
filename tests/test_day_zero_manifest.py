from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import yaml

from synergy_schema.conformance.day_zero import (
    create_day_zero_manifest,
    validate_day_zero_manifest,
)


def test_day_zero_manifest_hashes_only_explicit_artifacts_and_is_discovery_only(
    tmp_path: Path,
) -> None:
    payload = tmp_path / "payload.csv"
    producer = tmp_path / "producer.sql"
    adjacent = tmp_path / "unrelated.csv"
    payload.write_bytes(b"synthetic,payload\n")
    producer.write_bytes(b"select 1;\n")
    adjacent.write_bytes(b"must not be read")
    manifest = create_day_zero_manifest(payload, producer, "atlas", "demo", 2025)
    assert manifest == create_day_zero_manifest(
        payload, producer, "atlas", "demo", 2025
    )
    assert (
        manifest["payload_artifact"]["artifact_identity"]["content_digest"]
        == sha256(payload.read_bytes()).hexdigest()
    )
    assert (
        manifest["producer_artifact"]["artifact_identity"]["content_digest"]
        == sha256(producer.read_bytes()).hexdigest()
    )
    assert manifest["generation_mode"] == "manual_discovery"
    assert validate_day_zero_manifest(manifest).diagnostics == ()
    assert [
        item.code
        for item in validate_day_zero_manifest(manifest, production=True).diagnostics
    ] == ["PRODUCTION_RECEIPT_REQUIRED"]


def test_day_zero_manifest_raises_input_error_for_missing_explicit_artifact(
    tmp_path: Path,
) -> None:
    from synergy_schema.conformance.diagnostics import InputError

    producer = tmp_path / "producer.sql"
    producer.write_text("select 1;", encoding="utf-8")
    try:
        create_day_zero_manifest(
            tmp_path / "missing.csv", producer, "atlas", "demo", 2025
        )
    except InputError as error:
        assert "cannot read explicit artifact" in str(error)
    else:
        raise AssertionError("missing artifact must be rejected")


def test_day_zero_yaml_is_deterministic(tmp_path: Path) -> None:
    payload = tmp_path / "payload.csv"
    producer = tmp_path / "producer.sql"
    payload.write_text("x\n", encoding="utf-8")
    producer.write_text("select 1;\n", encoding="utf-8")
    one = yaml.safe_dump(
        create_day_zero_manifest(payload, producer, "atlas", "demo", 2025),
        sort_keys=True,
    )
    two = yaml.safe_dump(
        create_day_zero_manifest(payload, producer, "atlas", "demo", 2025),
        sort_keys=True,
    )
    assert one == two
