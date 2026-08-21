from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import yaml

from synergy_schema.conformance.bundles import canonical_bundle_digest
from synergy_schema.conformance.cli import main
from synergy_schema.conformance.day_zero import validate_day_zero_manifest
from synergy_schema.conformance.documents import load_mapping
from synergy_schema.conformance.mappings import mapping_digest


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
    encoding_source = contract["encoding_source"]
    encoding_path = example / encoding_source["locator"]
    assert (
        encoding_source["artifact_identity"]["content_digest"]
        == sha256(encoding_path.read_bytes()).hexdigest()
    )
    assert contract["semantic_content_digest"] == (
        "02ae76d67869ec8cee8ca138288e44907cd86ba31db81b66fa6d2e845e798663"
    )
    assert mapping_digest(contract) == contract["semantic_content_digest"]
    assert (
        contract["semantic_content_digest"]
        == polaris["population_translation_contract"]["semantic_content_digest"]
    )
    assert {item["id"] for item in contract["residue_records"]} == {
        "household-type-lookup",
        "out-of-region-households-filtered",
        "unsupported-source-tenure",
        "vehicle-year-context-dropped",
    }
    assert {item["residue_kind"] for item in contract["residue_records"]} == {
        "lookup_or_crosswalk",
        "filtered_rows",
        "unmapped_source",
        "dropped_context",
    }
    assert {item["residue_record_id"] for item in polaris["residue_observations"]} == {
        item["id"] for item in contract["residue_records"]
    }
    assert (ROOT / "mappings/releases/atlas-demos-to-polaris/OWNERS.yaml").exists()


def test_published_zev_trajectory_carries_a_realization_identity_and_contracts() -> (
    None
):
    """The public multi-year example pins its selection separately from receipts."""
    bundle = load_mapping(
        ROOT / "examples/evolving_population/zev-pilates-trajectory-bundle.yaml"
    )

    identity = bundle["realization_identity"]
    assert identity["kind"] == "synergy:scenario-realization:population-trajectory-v1"
    assert identity["projection_version"] == "1"
    assert identity["digest_algorithm"] == "sha256"
    assert len(identity["content_digest"]) == 64
    assert identity["content_digest"].islower()

    receipt = bundle["realization_receipt"]
    assert receipt["receipt_version"] == "1"
    assert receipt["realization_identity"] == identity

    snapshots = bundle["population_snapshot_bundles"]
    assert len(snapshots) >= 2
    for snapshot_bundle in snapshots:
        for member in snapshot_bundle["members"]:
            contract = member["schema_contract"]
            assert contract["language"] == "LinkML"
            assert contract["schema_digest_algorithm"] == "sha256"
            assert len(contract["schema_digest"]) == 64
            assert contract["selected_root"] in {
                "AtlasHouseholdInput",
                "AtlasPersonInput",
                "AtlasVehicleOutput",
            }
