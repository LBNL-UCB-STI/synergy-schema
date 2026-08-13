from __future__ import annotations

from copy import deepcopy

from synergy_schema.conformance.bundles import (
    canonical_bundle_digest,
    validate_polaris_bundle,
    validate_population_bundle,
)


def _scenario_ref() -> dict[str, str]:
    return {
        "scenario_definition_id": "scenario:synthetic",
        "revision": "r1",
        "content_digest": "s" * 64,
    }


def _trajectory() -> dict[str, object]:
    return {
        "id": "trajectory:synthetic",
        "scenario_definition_ref": _scenario_ref(),
        "stochastic_realization_id": "realization:1",
        "requested_years": [2025],
        "skipped_years": [],
        "snapshots": [
            {
                "id": "snapshot:2025",
                "scenario_definition_ref": _scenario_ref(),
                "stochastic_realization_id": "realization:1",
                "simulation_year": 2025,
                "equilibrium_iteration": 2,
            }
        ],
    }


def _artifact(digest: str) -> dict[str, object]:
    return {
        "artifact_identity": {"digest_algorithm": "sha256", "content_digest": digest},
        "locator": f"synthetic/{digest}.parquet",
    }


def _population_bundle() -> dict[str, object]:
    artifacts = {role: _artifact(role * 64) for role in ("a", "b", "c")}
    bundle: dict[str, object] = {
        "id": "bundle:population",
        "manifest_content_digest_algorithm": "sha256",
        "population_trajectory": _trajectory(),
        "population_snapshot_bundles": [
            {
                "population_snapshot": _trajectory()["snapshots"][0],
                "members": [
                    {"semantic_role": role, "artifact": artifact}
                    for role, artifact in zip(
                        ("households", "persons", "vehicles"),
                        artifacts.values(),
                        strict=True,
                    )
                ],
                "consist_provenance": {
                    "runs": [
                        {"run_id": "child:2025", "parent_run": {"run_id": "header:1"}}
                    ],
                    "artifacts": [
                        {
                            "artifact_id": f"id:{role}",
                            "immutable_identity": {
                                "algorithm": "sha256",
                                "kind": "file",
                                "digest": artifact["artifact_identity"][
                                    "content_digest"
                                ],
                            },
                        }
                        for role, artifact in artifacts.items()
                    ],
                    "associations": [
                        {
                            "run": {"run_id": "child:2025"},
                            "artifact": {"artifact_id": f"id:{role}"},
                            "direction": "output",
                        }
                        for role in artifacts
                    ],
                },
            }
        ],
        "schedule_evidence": {
            "handoff_year_statuses": [{"simulation_year": 2025, "status": "exported"}]
        },
        "consist_trajectory_evidence": {
            "scenario_header_run": {"run_id": "header:1"},
            "child_run_evidence": [
                {
                    "child_run": {"run_id": "child:2025"},
                    "simulation_year": 2025,
                    "equilibrium_iteration": 2,
                }
            ],
        },
    }
    bundle["manifest_content_digest"] = canonical_bundle_digest(bundle)
    return bundle


def _mapping_release() -> tuple[
    dict[str, object], list[dict[str, object]], dict[str, object]
]:
    contract = {
        "id": "mapping:synthetic",
        "revision": "r1",
        "semantic_content_digest_algorithm": "sha256",
        "semantic_content_digest": "m" * 64,
        "governance": {"lifecycle_status": "approved"},
        "residue_records": [{"id": "residue:one"}],
    }
    implementation = {
        "id": "implementation:synthetic",
        "implemented_semantic_content_digest_algorithm": "sha256",
        "implemented_semantic_content_digest": "m" * 64,
        "implementation_artifact": _artifact("i" * 64),
        "status": "conformance_checked",
    }
    return (
        contract,
        [implementation],
        {"source_owner": "ATLAS", "target_owner": "POLARIS"},
    )


def _polaris_bundle(population: dict[str, object]) -> dict[str, object]:
    contract, implementations, _ = _mapping_release()
    return {
        "source_trajectory_bundle": {
            "population_trajectory_bundle_id": population["id"],
            "manifest_content_digest_algorithm": "sha256",
            "manifest_content_digest": population["manifest_content_digest"],
        },
        "scenario_definition_ref": _scenario_ref(),
        "stochastic_realization_id": "realization:1",
        "population_translation_contract": {
            "population_translation_contract_id": contract["id"],
            "revision": contract["revision"],
            "semantic_content_digest_algorithm": "sha256",
            "semantic_content_digest": contract["semantic_content_digest"],
        },
        "translation_implementation_binding": {
            "translation_implementation_binding_id": implementations[0]["id"],
            "implemented_semantic_content_digest_algorithm": "sha256",
            "implemented_semantic_content_digest": contract["semantic_content_digest"],
            "implementation_content_digest_algorithm": "sha256",
            "implementation_content_digest": "i" * 64,
        },
        "implementation_artifact": _artifact("i" * 64),
        "requested_years": [2025],
        "successful_years": [2025],
        "skipped_years": [],
        "receipt_generation_mode": "automatic_adapter",
        "members": [
            {
                "semantic_role": role,
                "simulation_year": 2025,
                "artifact": _artifact(role * 64),
            }
            for role in (
                "households",
                "persons",
                "vehicles",
                "vehicle_class",
                "vehicle_type",
            )
        ],
        "residue_observations": [
            {
                "residue_record_id": "residue:one",
                "semantic_content_digest_algorithm": "sha256",
                "semantic_content_digest": "m" * 64,
            }
        ],
    }


def test_population_bundle_validates_roles_schedule_and_consist_identity() -> None:
    bundle = _population_bundle()
    assert validate_population_bundle(bundle).diagnostics == ()

    broken = deepcopy(bundle)
    broken["population_snapshot_bundles"][0]["members"].pop()
    broken["schedule_evidence"]["handoff_year_statuses"] = []
    broken["population_snapshot_bundles"][0]["consist_provenance"]["artifacts"][0][
        "immutable_identity"
    ]["digest"] = "x" * 64
    assert {item.code for item in validate_population_bundle(broken).diagnostics} == {
        "ARTIFACT_IDENTITY_MISMATCH",
        "BUNDLE_ROLE_CARDINALITY",
        "SCHEDULE_EVIDENCE_MISMATCH",
    }


def test_polaris_bundle_requires_all_yearly_roles_and_production_evidence() -> None:
    population = _population_bundle()
    polaris = _polaris_bundle(population)
    release = _mapping_release()
    assert (
        validate_polaris_bundle(
            polaris, population, *release, production=True
        ).diagnostics
        == ()
    )

    broken = deepcopy(polaris)
    broken["members"].pop()
    broken["receipt_generation_mode"] = "manual_discovery"
    assert {
        item.code
        for item in validate_polaris_bundle(
            broken, population, *release, production=True
        ).diagnostics
    } == {
        "POLARIS_YEAR_ROLE_MISSING",
        "PRODUCTION_RECEIPT_REQUIRED",
    }
