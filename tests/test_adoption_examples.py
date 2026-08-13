from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import yaml

from synergy_schema.conformance.bundles import canonical_bundle_digest
from synergy_schema.conformance.cli import main
from synergy_schema.conformance.day_zero import validate_day_zero_manifest
from synergy_schema.conformance.documents import load_mapping


ROOT = Path(__file__).parents[1]


def test_day_zero_example_is_a_byte_accurate_discovery_receipt() -> None:
    example = ROOT / "examples/day_zero_exchange"
    manifest = yaml.safe_load(
        (example / "day-zero-manifest.yaml").read_text(encoding="utf-8")
    )
    assert (
        manifest["payload_artifact"]["artifact_identity"]["content_digest"]
        == sha256((example / "payload.csv").read_bytes()).hexdigest()
    )
    assert (
        manifest["producer_artifact"]["artifact_identity"]["content_digest"]
        == sha256((example / "producer.sql").read_bytes()).hexdigest()
    )
    assert manifest["native_scenario_namespace"] == "synthetic.atlas"
    assert manifest["native_scenario_label"] == "day-zero-demo"
    assert manifest["simulation_year"] == 2025
    assert manifest["generation_mode"] == "manual_discovery"
    assert [
        item.code
        for item in validate_day_zero_manifest(manifest, production=True).diagnostics
    ] == ["PRODUCTION_RECEIPT_REQUIRED"]


def test_one_year_handshake_is_an_honest_draft_with_canonical_bundle_identity(
    capsys: object,
) -> None:
    example = ROOT / "examples/one_year_mapping_handshake"
    assert (
        main(
            [
                "check-all",
                "--schema",
                "src/synergy_schema/schema/synergy_schema.yaml",
                "--dir",
                str(example),
            ]
        )
        == 0
    )
    assert "MAPPING_NOT_APPROVED" in capsys.readouterr().err
    polaris = load_mapping(example / "polaris-translation-bundle.yaml")
    population = load_mapping(example / "pilates-trajectory-bundle.yaml")
    assert polaris["source_trajectory_bundle"][
        "manifest_content_digest"
    ] == canonical_bundle_digest(population)
    contract = load_mapping(
        example
        / "mapping-release/revision-1/contract/population-translation-contract.yaml"
    )
    assert contract["governance"]["lifecycle_status"] == "draft"
    assert (
        contract["semantic_content_digest"]
        == polaris["population_translation_contract"]["semantic_content_digest"]
    )
    assert (ROOT / "mappings/releases/atlas-demos-to-polaris/OWNERS.yaml").exists()
