from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

import synergy_schema.conformance.bundles as bundle_checks
from synergy_schema.conformance.bundles import (
    canonical_bundle_digest,
    canonical_realization_digest,
    canonical_realization_projection,
    _jcs_json_bytes,
    validate_polaris_bundle,
    validate_population_bundle,
)


def _scenario_ref() -> dict[str, str]:
    return {
        "scenario_definition_id": "scenario:synthetic",
        "revision": "r1",
        "content_digest": "a" * 64,
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


def _schema_contract(role: str) -> dict[str, str]:
    digest = {"households": "1", "persons": "2", "vehicles": "3"}[role]
    return {
        "language": "linkml",
        "schema_digest_algorithm": "sha256",
        "schema_digest": digest * 64,
        "selected_root": f"Atlas{role.title()}Input",
    }


def _realization_bundle() -> dict[str, object]:
    """A two-year complete bundle with all v1 identity-bearing facts."""
    scenario = _scenario_ref()
    snapshots = [
        {
            "id": "snapshot:2025",
            "scenario_definition_ref": scenario,
            "stochastic_realization_id": "realization:1",
            "simulation_year": 2025,
            "equilibrium_iteration": 2,
        },
        {
            "id": "snapshot:2030",
            "scenario_definition_ref": scenario,
            "stochastic_realization_id": "realization:1",
            "simulation_year": 2030,
            "parent_snapshot_ref": "snapshot:2025",
        },
    ]
    trajectory = {
        "id": "trajectory:synthetic",
        "scenario_definition_ref": scenario,
        "stochastic_realization_id": "realization:1",
        "requested_years": [2025, 2030],
        "skipped_years": [],
        "completeness_status": "complete",
        "snapshots": snapshots,
    }
    snapshot_bundles = []
    for snapshot in snapshots:
        year = snapshot["simulation_year"]
        members = [
            {
                "semantic_role": role,
                "artifact": _artifact(digest * 64),
                "schema_contract": _schema_contract(role),
            }
            for role, digest in (
                ("households", "a" if year == 2025 else "d"),
                ("persons", "b" if year == 2025 else "e"),
                ("vehicles", "c" if year == 2025 else "f"),
            )
        ]
        artifact_ids = {
            member["semantic_role"]: (
                f"00000000-0000-5000-8000-{year % 10000:04d}{index:08d}"
            )
            for index, member in enumerate(members, start=1)
        }
        snapshot_bundles.append(
            {
                "id": f"bundle:{year}",
                "manifest_version": "1",
                "completeness_status": "complete",
                "producing_run": {"provider": "PILATES", "run_id": f"child:{year}"},
                "population_snapshot": snapshot,
                "members": members,
                "consist_provenance": {
                    "runs": [
                        {
                            "run_id": f"child:{year}",
                            "parent_run": {"run_id": "header:1"},
                        }
                    ],
                    "artifacts": [
                        {
                            "artifact_id": artifact_ids[member["semantic_role"]],
                            "immutable_identity": {
                                "algorithm": "sha256",
                                "kind": "file",
                                "digest": member["artifact"]["artifact_identity"][
                                    "content_digest"
                                ],
                            },
                        }
                        for member in members
                    ],
                    "associations": [
                        {
                            "run": {"run_id": f"child:{year}"},
                            "artifact": {
                                "artifact_id": artifact_ids[member["semantic_role"]]
                            },
                            "direction": "output",
                        }
                        for member in members
                    ],
                    "provenance_context": {
                        "namespace": "urn:consist:test",
                        "locator": "test/consist.duckdb",
                    },
                },
            }
        )
    bundle: dict[str, object] = {
        "id": "bundle:population",
        "manifest_version": "1",
        "completeness_status": "complete",
        "producing_run": {"provider": "PILATES", "run_id": "header:1"},
        "members": [
            {"semantic_role": "trajectory_manifest", "artifact": _artifact("0" * 64)}
        ],
        "manifest_content_digest_algorithm": "sha256",
        "population_trajectory": trajectory,
        "population_snapshot_bundles": snapshot_bundles,
        "schedule_evidence": {
            "planned_execution_boundaries": [2025, 2030],
            "handoff_year_statuses": [
                {"simulation_year": 2025, "status": "exported"},
                {"simulation_year": 2030, "status": "exported"},
            ],
            "config_catalog": _artifact("1" * 64),
            "scheduler_implementation": _artifact("2" * 64),
        },
        "consist_trajectory_evidence": {
            "scenario_header_run": {"run_id": "header:1"},
            "child_run_evidence": [
                {
                    "child_run": {"run_id": f"child:{snapshot['simulation_year']}"},
                    "simulation_year": snapshot["simulation_year"],
                    **(
                        {"equilibrium_iteration": snapshot["equilibrium_iteration"]}
                        if "equilibrium_iteration" in snapshot
                        else {}
                    ),
                }
                for snapshot in snapshots
            ],
        },
    }
    bundle["manifest_content_digest"] = canonical_bundle_digest(bundle)
    return bundle


def _swap_first_member_artifacts(bundle: dict[str, object]) -> None:
    members = bundle["population_snapshot_bundles"][0]["members"]
    members[0]["artifact"], members[1]["artifact"] = (
        members[1]["artifact"],
        members[0]["artifact"],
    )


def _add_skipped_year(bundle: dict[str, object]) -> None:
    trajectory = bundle["population_trajectory"]
    trajectory["requested_years"].append(2035)
    trajectory["skipped_years"].append({"year": 2035, "reason": "policy skip"})
    trajectory["completeness_status"] = "incomplete"
    bundle["completeness_status"] = "incomplete"
    bundle["schedule_evidence"]["handoff_year_statuses"].append(
        {"simulation_year": 2035, "status": "skipped"}
    )


def test_realization_projection_is_closed_and_uses_the_v1_test_vector() -> None:
    """Changing receipt data cannot enter the portable realization identity."""
    bundle = _realization_bundle()

    projection = canonical_realization_projection(bundle)

    assert projection == {
        "kind": "synergy:scenario-realization:population-trajectory-v1",
        "projection_version": "1",
        "digest_algorithm": "sha256",
        "manifest_version": "1",
        "scenario_definition": {
            "scenario_definition_id": "scenario:synthetic",
            "revision": "r1",
            "digest_algorithm": "sha256",
            "content_digest": "a" * 64,
        },
        "stochastic_realization_id": "realization:1",
        "trajectory": {
            "trajectory_id": "trajectory:synthetic",
            "requested_years": [2025, 2030],
            "skipped_years": [],
            "completeness_status": "complete",
            "membership_rule": {
                "profile": "pilates-population-snapshot-v1",
                "required_roles": ["households", "persons", "vehicles"],
                "optional_roles": [],
            },
            "snapshots": [
                {
                    "snapshot_id": "snapshot:2025",
                    "manifest_version": "1",
                    "simulation_year": 2025,
                    "equilibrium_iteration": 2,
                    "completeness_status": "complete",
                    "members": [
                        {
                            "semantic_role": role,
                            "artifact_identity": {
                                "digest_algorithm": "sha256",
                                "content_digest": digest * 64,
                            },
                            "schema_contract": _schema_contract(role),
                        }
                        for role, digest in (
                            ("households", "a"),
                            ("persons", "b"),
                            ("vehicles", "c"),
                        )
                    ],
                },
                {
                    "snapshot_id": "snapshot:2030",
                    "manifest_version": "1",
                    "simulation_year": 2030,
                    "parent_snapshot_ref": "snapshot:2025",
                    "completeness_status": "complete",
                    "members": [
                        {
                            "semantic_role": role,
                            "artifact_identity": {
                                "digest_algorithm": "sha256",
                                "content_digest": digest * 64,
                            },
                            "schema_contract": _schema_contract(role),
                        }
                        for role, digest in (
                            ("households", "d"),
                            ("persons", "e"),
                            ("vehicles", "f"),
                        )
                    ],
                },
            ],
        },
    }
    vector = (
        (Path(__file__).parent / "fixtures" / "population_trajectory_v1.jcs.json")
        .read_bytes()
        .rstrip(b"\n")
    )
    assert _jcs_json_bytes(projection) == vector
    assert (
        canonical_realization_digest(bundle)
        == (Path(__file__).parent / "fixtures" / "population_trajectory_v1.sha256")
        .read_text(encoding="utf-8")
        .strip()
    )

    receipt_only_change = deepcopy(bundle)
    receipt_only_change["population_snapshot_bundles"][0]["members"][0]["artifact"][
        "locator"
    ] = "moved/households.parquet"
    receipt_only_change["population_snapshot_bundles"][0]["members"][0]["row_count"] = (
        99
    )
    receipt_only_change["manifest_content_digest"] = canonical_bundle_digest(
        receipt_only_change
    )
    assert canonical_realization_digest(
        receipt_only_change
    ) == canonical_realization_digest(bundle)


def test_realization_projection_rejects_ambiguous_roles_and_wrong_identity() -> None:
    """An invalid selection never receives a digest, including self-claims."""
    valid_identity = _realization_bundle()
    expected_digest = canonical_realization_digest(valid_identity)
    valid_identity["realization_identity"] = {
        "kind": "synergy:scenario-realization:population-trajectory-v1",
        "projection_version": "1",
        "digest_algorithm": "sha256",
        "content_digest": expected_digest,
    }
    valid_identity["manifest_content_digest"] = canonical_bundle_digest(valid_identity)
    assert validate_population_bundle(valid_identity).diagnostics == ()
    assert canonical_realization_projection(
        valid_identity
    ) == canonical_realization_projection(_realization_bundle())

    duplicate_role = _realization_bundle()
    duplicate_role["population_snapshot_bundles"][0]["members"][2]["semantic_role"] = (
        "persons"
    )
    duplicate_role["manifest_content_digest"] = canonical_bundle_digest(duplicate_role)
    with pytest.raises(ValueError, match="REALIZATION_PROJECTION_INVALID"):
        canonical_realization_digest(duplicate_role)

    wrong_identity = _realization_bundle()
    wrong_identity["realization_identity"] = {
        "kind": "wrong",
        "projection_version": "1",
        "digest_algorithm": "sha256",
        "content_digest": "0" * 64,
    }
    wrong_identity["manifest_content_digest"] = canonical_bundle_digest(wrong_identity)
    assert "REALIZATION_IDENTITY_MISMATCH" in {
        item.code for item in validate_population_bundle(wrong_identity).diagnostics
    }


def test_realization_digest_excludes_receipts_but_changes_with_selected_bytes() -> None:
    """Moving a member is not a new realization; changing its bytes is."""
    bundle = _realization_bundle()
    full_digest = canonical_bundle_digest(bundle)
    realization_digest = canonical_realization_digest(bundle)

    reordered = deepcopy(bundle)
    reordered["population_snapshot_bundles"][0]["members"].reverse()
    reordered["manifest_content_digest"] = canonical_bundle_digest(reordered)
    assert canonical_bundle_digest(reordered) != full_digest
    assert canonical_realization_digest(reordered) == realization_digest

    changed_member = deepcopy(bundle)
    changed_member["population_snapshot_bundles"][0]["members"][0]["artifact"][
        "artifact_identity"
    ]["content_digest"] = "0" * 64
    changed_member["population_snapshot_bundles"][0]["consist_provenance"]["artifacts"][
        0
    ]["immutable_identity"]["digest"] = "0" * 64
    changed_member["manifest_content_digest"] = canonical_bundle_digest(changed_member)
    assert canonical_bundle_digest(changed_member) != full_digest
    assert canonical_realization_digest(changed_member) != realization_digest


@pytest.mark.parametrize(
    ("name", "mutate", "realization_changes"),
    [
        (
            "producing-run locator",
            lambda bundle: bundle.__setitem__(
                "producing_run", {**bundle["producing_run"], "run_locator": "moved/run"}
            ),
            False,
        ),
        (
            "producing-run id",
            lambda bundle: bundle["producing_run"].__setitem__(
                "run_id", "header:relocated"
            ),
            False,
        ),
        (
            "Consist child id",
            lambda bundle: (
                bundle["population_snapshot_bundles"][0]["consist_provenance"]["runs"][
                    0
                ].__setitem__("run_id", "child:relocated"),
                bundle["population_snapshot_bundles"][0]["consist_provenance"][
                    "associations"
                ][0]["run"].__setitem__("run_id", "child:relocated"),
                bundle["population_snapshot_bundles"][0]["consist_provenance"][
                    "associations"
                ][1]["run"].__setitem__("run_id", "child:relocated"),
                bundle["population_snapshot_bundles"][0]["consist_provenance"][
                    "associations"
                ][2]["run"].__setitem__("run_id", "child:relocated"),
                bundle["consist_trajectory_evidence"]["child_run_evidence"][0][
                    "child_run"
                ].__setitem__("run_id", "child:relocated"),
            ),
            False,
        ),
        (
            "schema discovery metadata",
            lambda bundle: bundle["population_snapshot_bundles"][0]["members"][0][
                "schema_contract"
            ].update(
                {"schema_uri": "https://example.invalid/schema", "schema_version": "v2"}
            ),
            False,
        ),
        (
            "selected contract root",
            lambda bundle: bundle["population_snapshot_bundles"][0]["members"][0][
                "schema_contract"
            ].__setitem__("selected_root", "DifferentRoot"),
            True,
        ),
        (
            "trajectory semantic id",
            lambda bundle: bundle["population_trajectory"].__setitem__(
                "id", "trajectory:changed"
            ),
            True,
        ),
        ("semantic role byte swap", _swap_first_member_artifacts, True),
        ("membership and completeness", _add_skipped_year, True),
    ],
)
def test_realization_mutation_matrix(
    name: str, mutate: object, realization_changes: bool
) -> None:
    """Receipt and discovery mutations stay out; declared meaning stays in."""
    bundle = _realization_bundle()
    original_full = canonical_bundle_digest(bundle)
    original_realization = canonical_realization_digest(bundle)
    changed = deepcopy(bundle)
    assert callable(mutate), name
    mutate(changed)
    changed["manifest_content_digest"] = canonical_bundle_digest(changed)

    assert canonical_bundle_digest(changed) != original_full
    assert (
        canonical_realization_digest(changed) != original_realization
    ) is realization_changes


def test_realization_digest_ignores_source_key_order_but_rejects_unknown_fields() -> (
    None
):
    """Canonical object ordering is stable, while the public profile stays closed."""
    bundle = _realization_bundle()
    reordered = dict(reversed(tuple(bundle.items())))
    assert canonical_bundle_digest(reordered) == canonical_bundle_digest(bundle)
    assert canonical_realization_digest(reordered) == canonical_realization_digest(
        bundle
    )

    unknown = deepcopy(bundle)
    unknown["future_unrecognized_field"] = "not projected"
    unknown["manifest_content_digest"] = canonical_bundle_digest(unknown)
    with pytest.raises(ValueError, match="BUNDLE_SHAPE_INVALID"):
        canonical_realization_projection(unknown)


def test_realization_projection_rejects_null_optionals_and_missing_contract() -> None:
    """Optional projection fields are omitted, never encoded as null."""
    null_optional = _realization_bundle()
    null_optional["population_trajectory"]["snapshots"][0]["equilibrium_iteration"] = (
        None
    )
    null_optional["population_snapshot_bundles"][0]["population_snapshot"][
        "equilibrium_iteration"
    ] = None
    null_optional["manifest_content_digest"] = canonical_bundle_digest(null_optional)
    with pytest.raises(ValueError, match="REALIZATION_PROJECTION_INVALID"):
        canonical_realization_projection(null_optional)

    missing_contract = _realization_bundle()
    missing_contract["population_snapshot_bundles"][1]["members"][0].pop(
        "schema_contract"
    )
    missing_contract["manifest_content_digest"] = canonical_bundle_digest(
        missing_contract
    )
    with pytest.raises(ValueError, match="REALIZATION_PROJECTION_INVALID"):
        canonical_realization_projection(missing_contract)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda bundle: bundle["population_snapshot_bundles"][0]["members"][0][
            "artifact"
        ]["artifact_identity"].__setitem__("content_digest", "not-a-digest"),
        lambda bundle: bundle["population_trajectory"]["snapshots"][1].__setitem__(
            "parent_snapshot_ref", "snapshot:missing"
        ),
        lambda bundle: bundle["population_trajectory"]["snapshots"].reverse(),
    ],
)
def test_realization_projection_rejects_malformed_identity_inputs(
    mutate: object,
) -> None:
    """Bad byte identities and trajectory structure fail before hashing."""
    bundle = _realization_bundle()
    assert callable(mutate)
    mutate(bundle)
    bundle["manifest_content_digest"] = canonical_bundle_digest(bundle)

    with pytest.raises(ValueError, match="REALIZATION_PROJECTION_INVALID"):
        canonical_realization_digest(bundle)


@pytest.mark.parametrize("invalid_year", [None, "2025"])
def test_realization_projection_reports_invalid_year_types(
    invalid_year: object,
) -> None:
    """Malformed year values are diagnostics, never incidental conversion errors."""
    bundle = _realization_bundle()
    bundle["population_trajectory"]["requested_years"] = [invalid_year, 2030]
    bundle["manifest_content_digest"] = canonical_bundle_digest(bundle)

    with pytest.raises(ValueError, match="BUNDLE_SHAPE_INVALID"):
        canonical_realization_projection(bundle)
    bundle["realization_identity"] = {
        "kind": "synergy:scenario-realization:population-trajectory-v1",
        "projection_version": "1",
        "digest_algorithm": "sha256",
        "content_digest": "0" * 64,
    }
    bundle["manifest_content_digest"] = canonical_bundle_digest(bundle)
    assert "REALIZATION_PROJECTION_INVALID" in {
        item.code for item in validate_population_bundle(bundle).diagnostics
    }


def test_population_validation_skips_identity_hash_after_envelope_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed envelope must not be promoted to a realization calculation."""
    bundle = _realization_bundle()
    identity_digest = canonical_realization_digest(bundle)
    bundle["realization_identity"] = {
        "kind": "synergy:scenario-realization:population-trajectory-v1",
        "projection_version": "1",
        "digest_algorithm": "sha256",
        "content_digest": identity_digest,
    }
    bundle["schedule_evidence"]["handoff_year_statuses"] = []
    bundle["manifest_content_digest"] = canonical_bundle_digest(bundle)
    monkeypatch.setattr(
        bundle_checks,
        "_jcs_json_bytes",
        lambda value: (_ for _ in ()).throw(AssertionError("must not hash")),
    )

    diagnostics = validate_population_bundle(bundle).diagnostics

    assert {item.code for item in diagnostics} == {"SCHEDULE_EVIDENCE_MISMATCH"}


def test_realization_public_api_runs_shape_validation_and_checks_receipt_identity() -> (
    None
):
    """Closed profile fields and both identity placements bind the same projection."""
    unknown_field = _realization_bundle()
    unknown_field["unrecognized_field"] = True
    unknown_field["manifest_content_digest"] = canonical_bundle_digest(unknown_field)
    with pytest.raises(ValueError, match="BUNDLE_SHAPE_INVALID"):
        canonical_realization_projection(unknown_field)

    bundle = _realization_bundle()
    digest = canonical_realization_digest(bundle)
    identity = {
        "kind": "synergy:scenario-realization:population-trajectory-v1",
        "projection_version": "1",
        "digest_algorithm": "sha256",
        "content_digest": digest,
    }
    bundle["realization_identity"] = identity
    bundle["realization_receipt"] = {
        "receipt_version": "1",
        "realization_identity": {**identity, "content_digest": "0" * 64},
    }
    bundle["manifest_content_digest"] = canonical_bundle_digest(bundle)
    assert "REALIZATION_IDENTITY_MISMATCH" in {
        item.code for item in validate_population_bundle(bundle).diagnostics
    }


@pytest.mark.parametrize("value", [-(2**53 - 1), 2**53 - 1])
def test_jcs_accepts_interoperable_integer_boundaries(value: int) -> None:
    """The portable subset includes both endpoints of the JCS-safe range."""
    assert _jcs_json_bytes({"value": value}) == f'{{"value":{value}}}'.encode()


@pytest.mark.parametrize("value", [-(2**53), 2**53])
def test_jcs_rejects_integers_outside_interoperable_range(value: int) -> None:
    """Values beyond exact IEEE-754 integer range cannot enter v1 bytes."""
    with pytest.raises(ValueError, match="integer is outside JCS range"):
        _jcs_json_bytes({"value": value})


def test_jcs_orders_object_keys_as_rfc8785_utf16_code_units() -> None:
    """Non-ASCII keys retain JCS rather than Python's code-point ordering."""
    assert _jcs_json_bytes({"\U0001f600": 1, "\ufffd": 2}) == (
        b'{"\xf0\x9f\x98\x80":1,"\xef\xbf\xbd":2}'
    )


def test_jcs_rejects_unicode_surrogates() -> None:
    """A surrogate is not a Unicode scalar value and cannot be serialized."""
    with pytest.raises(ValueError, match="strings cannot contain surrogates"):
        _jcs_json_bytes({"value": "\ud800"})


def test_realization_projection_rejects_duplicate_snapshot_ids() -> None:
    """Snapshot IDs and their role sets form an unambiguous trajectory selection."""
    bundle = _realization_bundle()
    bundle["population_trajectory"]["snapshots"][1]["id"] = "snapshot:2025"
    bundle["manifest_content_digest"] = canonical_bundle_digest(bundle)

    with pytest.raises(ValueError, match="snapshot ids must be unique"):
        canonical_realization_digest(bundle)


def _mapping_release() -> tuple[
    dict[str, object], list[dict[str, object]], dict[str, object]
]:
    contract = {
        "id": "mapping:synthetic",
        "revision": "r1",
        "semantic_content_digest_algorithm": "sha256",
        "semantic_content_digest": "m" * 64,
        "governance": {"lifecycle_status": "approved"},
        "source_schema_contract": {
            "language": "linkml",
            "schema_digest_algorithm": "sha256",
            "schema_digest": "q" * 64,
            "selected_root": "AtlasHouseholdInput",
        },
        "target_schema_contract": {
            "language": "linkml",
            "schema_digest_algorithm": "sha256",
            "schema_digest": "r" * 64,
            "selected_root": "PolarisHouseholdRecord",
        },
        "residue_records": [{"id": "residue:one"}],
    }
    implementation = {
        "id": "implementation:synthetic",
        "implemented_semantic_content_digest_algorithm": "sha256",
        "implemented_semantic_content_digest": "m" * 64,
        "implementation_artifact": _artifact("i" * 64),
        "source_schema_contract": contract["source_schema_contract"],
        "target_schema_contract": contract["target_schema_contract"],
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
        "id": "bundle:polaris",
        "manifest_version": "0.1",
        "completeness_status": "complete",
        "producing_run": {"provider": "synthetic", "run_id": "polaris:2025"},
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
        "source_schema_contract": contract["source_schema_contract"],
        "target_schema_contract": contract["target_schema_contract"],
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


def test_population_bundle_rejects_duplicate_year_and_foreign_output_run() -> None:
    bundle = _population_bundle()
    duplicate = deepcopy(bundle)
    duplicate["population_snapshot_bundles"].append(
        deepcopy(duplicate["population_snapshot_bundles"][0])
    )
    foreign_run = deepcopy(bundle)
    foreign_run["population_snapshot_bundles"][0]["consist_provenance"]["associations"][
        0
    ]["run"]["run_id"] = "run:unrelated"
    assert "BUNDLE_ROLE_CARDINALITY" in {
        item.code for item in validate_population_bundle(duplicate).diagnostics
    }
    assert "CONSIST_PARENT_MISMATCH" in {
        item.code for item in validate_population_bundle(foreign_run).diagnostics
    }


def test_polaris_bundle_requires_registered_source_and_target_schema_contracts() -> (
    None
):
    population = _population_bundle()
    polaris = _polaris_bundle(population)
    release = _mapping_release()
    missing = deepcopy(polaris)
    missing.pop("source_schema_contract")
    mismatch = deepcopy(polaris)
    mismatch["target_schema_contract"]["selected_root"] = "WrongRoot"
    assert "SCHEMA_CONTRACT_MISMATCH" in {
        item.code
        for item in validate_polaris_bundle(missing, population, *release).diagnostics
    }
    assert "SCHEMA_CONTRACT_MISMATCH" in {
        item.code
        for item in validate_polaris_bundle(mismatch, population, *release).diagnostics
    }


def test_polaris_schema_contract_comparison_ignores_discovery_locators() -> None:
    population = _population_bundle()
    polaris = _polaris_bundle(population)
    polaris["source_schema_contract"]["schema_uri"] = "https://example.invalid/schema"
    polaris["target_schema_contract"]["schema_version"] = "discovery-only"
    assert (
        validate_polaris_bundle(polaris, population, *_mapping_release()).diagnostics
        == ()
    )


def test_polaris_bundle_rejects_a_forged_source_manifest_digest() -> None:
    """A receipt cannot trust a source self-reported digest after source drift."""
    population = _population_bundle()
    polaris = _polaris_bundle(population)
    forged = deepcopy(population)
    forged["population_trajectory"]["snapshots"][0]["equilibrium_iteration"] = 99

    assert "ARTIFACT_IDENTITY_MISMATCH" in {
        item.code
        for item in validate_polaris_bundle(
            polaris, forged, *_mapping_release()
        ).diagnostics
    }


def test_polaris_bundle_rejects_retired_implementation_for_every_receipt() -> None:
    """Retired bindings cannot authorize discovery or production receipts."""
    population = _population_bundle()
    polaris = _polaris_bundle(population)
    contract, implementations, ownership = _mapping_release()
    implementations[0]["status"] = "retired"

    assert "PRODUCTION_RECEIPT_REQUIRED" in {
        item.code
        for item in validate_polaris_bundle(
            polaris, population, contract, implementations, ownership
        ).diagnostics
    }


def test_polaris_bundle_requires_complete_receipts_and_successful_member_years() -> (
    None
):
    """A receipt is complete only for source-successful years, with no extras."""
    population = _population_bundle()
    polaris = _polaris_bundle(population)
    incomplete = deepcopy(polaris)
    incomplete["completeness_status"] = "incomplete"
    outside_schedule = deepcopy(polaris)
    outside_schedule["members"].append(
        {
            "semantic_role": "households",
            "simulation_year": 2030,
            "artifact": _artifact("z" * 64),
        }
    )

    assert "POLARIS_RECEIPT_INCOMPLETE" in {
        item.code
        for item in validate_polaris_bundle(
            incomplete, population, *_mapping_release()
        ).diagnostics
    }
    assert "POLARIS_MEMBER_YEAR_INVALID" in {
        item.code
        for item in validate_polaris_bundle(
            outside_schedule, population, *_mapping_release()
        ).diagnostics
    }
