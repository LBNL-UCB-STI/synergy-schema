"""Cross-document validators for trajectory exchange bundles."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

from .diagnostics import CheckResult, Diagnostic


def canonical_bundle_digest(bundle: Mapping[str, Any]) -> str:
    """Hash a trajectory manifest without its self-referential digest field."""
    projection = dict(bundle)
    projection.pop("manifest_content_digest", None)
    encoded = json.dumps(projection, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _artifact_digest(reference: object) -> str | None:
    if not isinstance(reference, Mapping):
        return None
    identity = reference.get("artifact_identity")
    if (
        not isinstance(identity, Mapping)
        or identity.get("digest_algorithm") != "sha256"
    ):
        return None
    digest = identity.get("content_digest")
    return str(digest) if digest else None


def _run_id(reference: object) -> str | None:
    return (
        str(reference["run_id"])
        if isinstance(reference, Mapping) and reference.get("run_id")
        else None
    )


def _years(trajectory: Mapping[str, Any]) -> tuple[set[int], set[int], set[int]]:
    requested = {int(year) for year in trajectory.get("requested_years", [])}
    snapshots = trajectory.get("snapshots", [])
    successful = {
        int(item["simulation_year"])
        for item in snapshots
        if isinstance(item, Mapping) and item.get("simulation_year") is not None
    }
    skipped = {
        int(item["year"])
        for item in trajectory.get("skipped_years", [])
        if isinstance(item, Mapping) and item.get("year") is not None
    }
    return requested, successful, skipped


def _diagnostic(code: str, message: str) -> Diagnostic:
    return Diagnostic(code, message, "error")


def validate_population_bundle(bundle: Mapping[str, Any]) -> CheckResult:
    """Validate one PILATES trajectory manifest against its embedded trajectory."""
    diagnostics: list[Diagnostic] = []
    trajectory = bundle.get("population_trajectory")
    if not isinstance(trajectory, Mapping):
        return CheckResult(
            (
                _diagnostic(
                    "BUNDLE_ROLE_CARDINALITY", "population trajectory is required"
                ),
            )
        )
    requested, successful, skipped = _years(trajectory)
    snapshot_bundles = bundle.get("population_snapshot_bundles", [])
    by_year: dict[int, list[Mapping[str, Any]]] = {}
    for snapshot_bundle in (
        snapshot_bundles if isinstance(snapshot_bundles, list) else []
    ):
        if isinstance(snapshot_bundle, Mapping) and isinstance(
            snapshot_bundle.get("population_snapshot"), Mapping
        ):
            snapshot = snapshot_bundle["population_snapshot"]
            if snapshot.get("simulation_year") is not None:
                by_year.setdefault(int(snapshot["simulation_year"]), []).append(
                    snapshot_bundle
                )
    if set(by_year) != successful or any(len(items) != 1 for items in by_year.values()):
        diagnostics.append(
            _diagnostic(
                "BUNDLE_ROLE_CARDINALITY",
                "one population bundle is required for every successful year",
            )
        )
    header = _run_id(
        (bundle.get("consist_trajectory_evidence") or {}).get("scenario_header_run")
    )
    children = {
        _run_id(item.get("child_run")): item
        for item in (bundle.get("consist_trajectory_evidence") or {}).get(
            "child_run_evidence", []
        )
        if isinstance(item, Mapping) and _run_id(item.get("child_run")) is not None
    }
    for year, snapshot_bundles_for_year in by_year.items():
        snapshot_bundle = snapshot_bundles_for_year[0]
        members = snapshot_bundle.get("members", [])
        roles = (
            [item.get("semantic_role") for item in members if isinstance(item, Mapping)]
            if isinstance(members, list)
            else []
        )
        if sorted(roles) != ["households", "persons", "vehicles"]:
            diagnostics.append(
                _diagnostic(
                    "BUNDLE_ROLE_CARDINALITY",
                    f"year {year} needs exactly households, persons, and vehicles",
                )
            )
        provenance = snapshot_bundle.get("consist_provenance", {})
        artifacts = (
            provenance.get("artifacts", []) if isinstance(provenance, Mapping) else []
        )
        artifact_by_id = {
            str(item.get("artifact_id")): item
            for item in artifacts
            if isinstance(item, Mapping) and item.get("artifact_id")
        }
        association_runs: dict[str, set[str | None]] = {}
        child_ids = set()
        runs = provenance.get("runs", []) if isinstance(provenance, Mapping) else []
        for run in runs if isinstance(runs, list) else []:
            if isinstance(run, Mapping) and _run_id(run):
                child_ids.add(_run_id(run))
                parent = _run_id(run.get("parent_run"))
                if header and parent is not None and parent != header:
                    diagnostics.append(
                        _diagnostic(
                            "CONSIST_PARENT_MISMATCH",
                            f"child run for {year} does not directly parent to scenario header",
                        )
                    )
        for association in (
            provenance.get("associations", [])
            if isinstance(provenance, Mapping)
            else []
        ):
            if (
                isinstance(association, Mapping)
                and association.get("direction") == "output"
            ):
                artifact = association.get("artifact")
                if isinstance(artifact, Mapping) and artifact.get("artifact_id"):
                    association_runs.setdefault(
                        str(artifact["artifact_id"]), set()
                    ).add(_run_id(association.get("run")))
        expected_child = next(
            (
                item
                for item in children.values()
                if int(item.get("simulation_year", -1)) == year
            ),
            None,
        )
        expected_child_run = (
            _run_id(expected_child.get("child_run"))
            if expected_child is not None
            else None
        )
        for member in members if isinstance(members, list) else []:
            member_digest = (
                _artifact_digest(member.get("artifact"))
                if isinstance(member, Mapping)
                else None
            )
            match = next(
                (
                    item
                    for item in artifact_by_id.values()
                    if isinstance(item.get("immutable_identity"), Mapping)
                    and item["immutable_identity"].get("digest") == member_digest
                ),
                None,
            )
            if member_digest is None or match is None:
                diagnostics.append(
                    _diagnostic(
                        "ARTIFACT_IDENTITY_MISMATCH",
                        f"year {year} member artifact is not the recorded Consist artifact",
                    )
                )
            elif expected_child_run not in association_runs.get(
                str(match.get("artifact_id")), set()
            ):
                diagnostics.append(
                    _diagnostic(
                        "CONSIST_PARENT_MISMATCH",
                        f"year {year} member output association uses a foreign run",
                    )
                )
        snapshot = snapshot_bundle.get("population_snapshot", {})
        if expected_child is None or (
            header and _run_id(expected_child.get("child_run")) not in child_ids
        ):
            diagnostics.append(
                _diagnostic(
                    "CONSIST_PARENT_MISMATCH",
                    f"year {year} has no matching Consist child evidence",
                )
            )
        elif expected_child.get("equilibrium_iteration") != snapshot.get(
            "equilibrium_iteration"
        ):
            diagnostics.append(
                _diagnostic(
                    "CONSIST_PARENT_MISMATCH",
                    f"year {year} child iteration differs from snapshot",
                )
            )
    statuses = (bundle.get("schedule_evidence") or {}).get("handoff_year_statuses", [])
    actual = (
        {
            int(item["simulation_year"]): item.get("status")
            for item in statuses
            if isinstance(item, Mapping) and item.get("simulation_year") is not None
        }
        if isinstance(statuses, list)
        else {}
    )
    expected = {year: "exported" for year in successful} | {
        year: "skipped" for year in skipped
    }
    if actual != expected or set(actual) != requested:
        diagnostics.append(
            _diagnostic(
                "SCHEDULE_EVIDENCE_MISMATCH",
                "schedule status records disagree with requested, successful, or skipped years",
            )
        )
    if bundle.get("manifest_content_digest_algorithm") != "sha256" or bundle.get(
        "manifest_content_digest"
    ) != canonical_bundle_digest(bundle):
        diagnostics.append(
            _diagnostic(
                "ARTIFACT_IDENTITY_MISMATCH",
                "trajectory manifest digest does not match canonical content",
            )
        )
    return CheckResult(tuple(diagnostics))


def _reference_equal(
    reference: object, expected: Mapping[str, Any], pairs: Sequence[tuple[str, str]]
) -> bool:
    return isinstance(reference, Mapping) and all(
        reference.get(actual) == expected.get(expected_key)
        for actual, expected_key in pairs
    )


_SCHEMA_IDENTITY_FIELDS = (
    "language",
    "schema_digest_algorithm",
    "schema_digest",
    "selected_root",
)


def _schema_identity_matches(receipt: object, expected: object) -> bool:
    return (
        isinstance(receipt, Mapping)
        and isinstance(expected, Mapping)
        and all(
            receipt.get(field) == expected.get(field) and receipt.get(field)
            for field in _SCHEMA_IDENTITY_FIELDS
        )
    )


def validate_polaris_bundle(
    bundle: Mapping[str, Any],
    population_bundle: Mapping[str, Any],
    contract: Mapping[str, Any],
    implementations: Sequence[Mapping[str, Any]],
    ownership: Mapping[str, Any],
    *,
    production: bool = False,
) -> CheckResult:
    """Validate a POLARIS receipt against source, mapping, and implementation facts."""
    diagnostics: list[Diagnostic] = list(
        validate_population_bundle(population_bundle).diagnostics
    )
    trajectory = population_bundle.get("population_trajectory", {})
    requested, successful, skipped = _years(
        trajectory if isinstance(trajectory, Mapping) else {}
    )
    source = bundle.get("source_trajectory_bundle")
    if (
        not _reference_equal(
            source,
            population_bundle,
            (
                ("population_trajectory_bundle_id", "id"),
                ("manifest_content_digest", "manifest_content_digest"),
            ),
        )
        or not isinstance(source, Mapping)
        or source.get("manifest_content_digest_algorithm") != "sha256"
    ):
        diagnostics.append(
            _diagnostic(
                "ARTIFACT_IDENTITY_MISMATCH",
                "source trajectory reference does not match its canonical manifest",
            )
        )
    if bundle.get("scenario_definition_ref") != trajectory.get(
        "scenario_definition_ref"
    ) or bundle.get("stochastic_realization_id") != trajectory.get(
        "stochastic_realization_id"
    ):
        diagnostics.append(
            _diagnostic(
                "ARTIFACT_IDENTITY_MISMATCH",
                "receipt scenario or realization differs from source trajectory",
            )
        )
    if (
        set(bundle.get("requested_years", [])) != requested
        or set(bundle.get("successful_years", [])) != successful
        or {
            int(item["year"])
            for item in bundle.get("skipped_years", [])
            if isinstance(item, Mapping)
        }
        != skipped
    ):
        diagnostics.append(
            _diagnostic(
                "SCHEDULE_EVIDENCE_MISMATCH",
                "receipt year declarations differ from source trajectory",
            )
        )
    members = bundle.get("members", [])
    by_year: dict[int, list[str]] = {}
    for member in members if isinstance(members, list) else []:
        if isinstance(member, Mapping) and member.get("simulation_year") is not None:
            by_year.setdefault(int(member["simulation_year"]), []).append(
                str(member.get("semantic_role"))
            )
    required_roles = [
        "households",
        "persons",
        "vehicle_class",
        "vehicle_type",
        "vehicles",
    ]
    for year in successful:
        if sorted(by_year.get(year, [])) != required_roles:
            diagnostics.append(
                _diagnostic(
                    "POLARIS_YEAR_ROLE_MISSING",
                    f"year {year} needs all five POLARIS artifact roles",
                )
            )
    unexpected_member_years = sorted(set(by_year) - successful)
    for year in unexpected_member_years:
        diagnostics.append(
            _diagnostic(
                "POLARIS_MEMBER_YEAR_INVALID",
                f"year {year} is not a successful source trajectory year",
            )
        )
    if bundle.get("completeness_status") != "complete":
        diagnostics.append(
            _diagnostic(
                "POLARIS_RECEIPT_INCOMPLETE",
                "POLARIS population translation receipts must declare complete",
            )
        )
    mapping_ref = bundle.get("population_translation_contract")
    mapping_ok = (
        _reference_equal(
            mapping_ref,
            contract,
            (
                ("population_translation_contract_id", "id"),
                ("revision", "revision"),
                ("semantic_content_digest", "semantic_content_digest"),
            ),
        )
        and isinstance(mapping_ref, Mapping)
        and mapping_ref.get("semantic_content_digest_algorithm")
        == contract.get("semantic_content_digest_algorithm")
    )
    binding = bundle.get("translation_implementation_binding")
    implementation = next(
        (
            item
            for item in implementations
            if isinstance(binding, Mapping)
            and item.get("id") == binding.get("translation_implementation_binding_id")
        ),
        None,
    )
    implementation_ok = (
        implementation is not None
        and isinstance(binding, Mapping)
        and binding.get("implemented_semantic_content_digest")
        == contract.get("semantic_content_digest")
        and binding.get("implementation_content_digest")
        == _artifact_digest(implementation.get("implementation_artifact"))
        and _artifact_digest(bundle.get("implementation_artifact"))
        == _artifact_digest(implementation.get("implementation_artifact"))
    )
    residue_ids = {
        item.get("id")
        for item in contract.get("residue_records", [])
        if isinstance(item, Mapping)
    }
    residues_ok = all(
        isinstance(item, Mapping)
        and item.get("residue_record_id") in residue_ids
        and item.get("semantic_content_digest")
        == contract.get("semantic_content_digest")
        for item in bundle.get("residue_observations", [])
    )
    if not mapping_ok or not implementation_ok or not residues_ok:
        diagnostics.append(
            _diagnostic(
                "ARTIFACT_IDENTITY_MISMATCH",
                "receipt mapping, implementation, or residue identity is not registered",
            )
        )
    for name in ("source_schema_contract", "target_schema_contract"):
        expected_contract = contract.get(name)
        if not _schema_identity_matches(bundle.get(name), expected_contract):
            diagnostics.append(
                _diagnostic(
                    "SCHEMA_CONTRACT_MISMATCH",
                    f"receipt {name} does not match the registered mapping release",
                )
            )
    lifecycle = (contract.get("governance") or {}).get("lifecycle_status")
    if lifecycle in {"superseded", "deprecated"}:
        diagnostics.append(
            _diagnostic(
                "PRODUCTION_RECEIPT_REQUIRED",
                "new receipts cannot use superseded or deprecated mappings",
            )
        )
    if implementation is not None and implementation.get("status") == "retired":
        diagnostics.append(
            _diagnostic(
                "PRODUCTION_RECEIPT_REQUIRED",
                "new receipts cannot use retired translation implementations",
            )
        )
    if production and (
        lifecycle != "approved"
        or implementation is None
        or implementation.get("status") != "conformance_checked"
        or bundle.get("receipt_generation_mode") != "automatic_adapter"
    ):
        diagnostics.append(
            _diagnostic(
                "PRODUCTION_RECEIPT_REQUIRED",
                "production receipt requires approved mapping, checked implementation, and automatic adapter",
            )
        )
    return CheckResult(tuple(diagnostics))
