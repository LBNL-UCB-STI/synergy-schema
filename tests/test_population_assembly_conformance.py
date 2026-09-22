from synergy_schema.conformance.assembly import (
    population_assembly_digest,
    validate_population_assembly,
)


SNAPSHOT = {
    "id": "snapshot:2030",
    "scenario_definition_ref": {"id": "scenario:synthetic"},
    "stochastic_realization_id": "realization:r1",
    "simulation_year": 2030,
}


def _contribution(identifier: str, *, overlapping: bool = False) -> dict[str, object]:
    classifications = [
        {
            "id": f"{identifier}:household-id",
            "native_element": {"path": "household_id"},
            "classification": "core_assertion",
            "target": {"facet": "households", "field": "household_id"},
        }
    ]
    if overlapping:
        classifications.append(
            {
                "id": f"{identifier}:household-id-2",
                "native_element": {"path": "household_id_copy"},
                "classification": "core_assertion",
                "target": {"facet": "households", "field": "household_id"},
            }
        )
    return {
        "id": identifier,
        "manifest_version": "1",
        "completeness_status": "complete",
        "producing_run": {"provider": "synthetic", "run_id": f"run:{identifier}"},
        "members": [
            {
                "semantic_role": "households",
                "artifact": {
                    "locator": f"{identifier}.parquet",
                    "artifact_identity": {
                        "digest_algorithm": "sha256",
                        "content_digest": "a" * 64,
                    },
                },
            }
        ],
        "contribution_revision": 1,
        "target_snapshot": SNAPSHOT,
        "producing_model": "synthetic",
        "producing_component": identifier,
        "semantic_identity": {
            "kind": "synthetic",
            "projection_version": "1",
            "digest_algorithm": "sha256",
            "content_digest": "b" * 64,
        },
        "supplied_bindings": [],
        "column_classifications": classifications,
        "relationship_bindings": [],
        "mapping_reference": "mapping:synthetic",
        "completeness_declaration": "households",
    }


def _assembly(contributions: list[dict[str, object]]) -> dict[str, object]:
    refs = [
        {
            "contribution_id": c["id"],
            "revision": 1,
            "semantic_identity": c["semantic_identity"],
        }
        for c in contributions
    ]
    assembly: dict[str, object] = {
        "id": "assembly:2030",
        "assembly_revision": 1,
        "target_snapshot": SNAPSHOT,
        "contributions": refs,
        "supplied_facets": [],
        "field_resolutions": [],
        "resolved_facet_index": [
            {
                "id": "index:households",
                "target": {"facet": "households"},
                "contribution": refs[0],
                "artifact_member_role": "households",
                "schema_contract": {
                    "language": "LinkML",
                    "schema_digest": "c" * 64,
                    "schema_digest_algorithm": "sha256",
                    "selected_root": "Households",
                },
                "native_to_core_binding": {
                    "id": "binding:households",
                    "artifact_member_role": "households",
                    "native_element": {"path": "household_id"},
                    "core_target": {"facet": "households", "field": "household_id"},
                    "assertion_authority": "core_assertion",
                },
            }
        ],
        "semantic_identity": {
            "kind": "synthetic",
            "projection_version": "1",
            "digest_algorithm": "sha256",
            "content_digest": "0" * 64,
        },
        "status": "partial",
    }
    assembly["semantic_identity"]["content_digest"] = population_assembly_digest(
        assembly
    )
    return assembly


def test_canonical_assembly_passes_with_separate_contribution_manifests() -> None:
    contribution = _contribution("contribution:demos")
    result = validate_population_assembly(_assembly([contribution]), [contribution])
    assert result.exit_code == 0, result.diagnostics


def test_overlapping_core_assertions_require_resolution() -> None:
    first = _contribution("contribution:demos", overlapping=True)
    second = _contribution("contribution:atlas")
    result = validate_population_assembly(_assembly([first, second]), [first, second])
    assert any(
        item.code == "CORE_FIELD_OVERLAP_UNRESOLVED" for item in result.diagnostics
    )


def test_unknown_authority_and_digest_are_rejected() -> None:
    contribution = _contribution("contribution:demos")
    contribution["column_classifications"][0]["classification"] = "unclassified"
    contribution["members"][0]["artifact"]["artifact_identity"]["content_digest"] = (
        "not-a-digest"
    )
    result = validate_population_assembly(_assembly([contribution]), [contribution])
    assert {item.code for item in result.diagnostics} >= {
        "ASSEMBLY_COLUMN_AUTHORITY_INVALID",
        "ASSEMBLY_ARTIFACT_DIGEST_INVALID",
    }
