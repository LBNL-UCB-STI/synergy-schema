"""Cross-document validators for trajectory exchange bundles."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .diagnostics import CheckResult, Diagnostic
from .shapes import validate_bundle_shape


def canonical_bundle_digest(bundle: Mapping[str, Any]) -> str:
    """Return the legacy logical full-bundle digest, excluding only itself.

    This digest hashes the parsed mapping, not the original serialized document
    bytes.  It is retained for existing manifests and is neither a realization
    identity nor a registry identity.
    """
    projection = dict(bundle)
    projection.pop("manifest_content_digest", None)
    encoded = json.dumps(projection, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


_REALIZATION_KIND = "synergy:scenario-realization:population-trajectory-v1"
_REALIZATION_VERSION = "1"
_REQUIRED_POPULATION_ROLES = ("households", "persons", "vehicles")
_SHA256_HEX_LENGTH = 64
_MAX_SAFE_JCS_INTEGER = 2**53 - 1


def _is_sha256_digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == _SHA256_HEX_LENGTH
        and all(character in "0123456789abcdef" for character in value)
    )


def _required_string(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _realization_diagnostic(message: str) -> Diagnostic:
    return _diagnostic("REALIZATION_PROJECTION_INVALID", message)


def _is_v1_realization_bundle(bundle: Mapping[str, Any]) -> bool:
    """Identify bundles that opt into identity verification without breaking migration."""
    return "realization_identity" in bundle or "realization_receipt" in bundle


def _snapshot_parent_id(value: object) -> str | None:
    if isinstance(value, str) and value:
        return value
    if isinstance(value, Mapping) and _required_string(value.get("id")):
        return str(value["id"])
    return None


def _validate_realization_projection(bundle: Mapping[str, Any]) -> list[Diagnostic]:
    """Return v1 projection diagnostics without inspecting the supplied result."""
    diagnostics: list[Diagnostic] = []
    trajectory = bundle.get("population_trajectory")
    if not isinstance(trajectory, Mapping):
        return [_realization_diagnostic("population trajectory is required")]

    root_version = bundle.get("manifest_version")
    if not _required_string(root_version):
        diagnostics.append(_realization_diagnostic("root manifest_version is required"))
    root_status = bundle.get("completeness_status")
    if root_status not in {"complete", "incomplete"}:
        diagnostics.append(
            _realization_diagnostic("root completeness_status is invalid")
        )
    trajectory_status = trajectory.get("completeness_status")
    if trajectory_status not in {"complete", "incomplete"}:
        diagnostics.append(
            _realization_diagnostic("trajectory completeness_status is invalid")
        )
    elif root_status != trajectory_status:
        diagnostics.append(
            _realization_diagnostic(
                "root and trajectory completeness_status must agree"
            )
        )

    scenario = trajectory.get("scenario_definition_ref")
    if (
        not isinstance(scenario, Mapping)
        or not all(
            _required_string(scenario.get(field))
            for field in ("scenario_definition_id", "revision")
        )
        or not _is_sha256_digest(scenario.get("content_digest"))
    ):
        diagnostics.append(_realization_diagnostic("scenario definition is invalid"))
    if not _required_string(trajectory.get("id")):
        diagnostics.append(_realization_diagnostic("trajectory id is required"))
    if not _required_string(trajectory.get("stochastic_realization_id")):
        diagnostics.append(
            _realization_diagnostic("stochastic_realization_id is required")
        )

    requested_raw = trajectory.get("requested_years")
    requested = requested_raw if isinstance(requested_raw, list) else []
    if (
        not requested
        or any(
            isinstance(year, bool) or not isinstance(year, int) for year in requested
        )
        or requested != sorted(set(requested))
    ):
        diagnostics.append(
            _realization_diagnostic("requested_years must be unique ascending integers")
        )

    skipped_raw = trajectory.get("skipped_years", [])
    skipped_records = skipped_raw if isinstance(skipped_raw, list) else []
    skipped: list[int] = []
    for item in skipped_records:
        year = item.get("year") if isinstance(item, Mapping) else None
        if isinstance(year, bool) or not isinstance(year, int):
            diagnostics.append(_realization_diagnostic("skipped year is invalid"))
            continue
        skipped.append(year)
    if (
        not isinstance(skipped_raw, list)
        or skipped != sorted(set(skipped))
        or any(year not in requested for year in skipped)
    ):
        diagnostics.append(
            _realization_diagnostic(
                "skipped_years must be unique ascending requested years"
            )
        )

    snapshots_raw = trajectory.get("snapshots")
    snapshots = snapshots_raw if isinstance(snapshots_raw, list) else []
    if not snapshots:
        diagnostics.append(_realization_diagnostic("at least one snapshot is required"))
    snapshot_ids: set[str] = set()
    snapshot_years: list[int] = []
    snapshot_by_id: dict[str, Mapping[str, Any]] = {}
    for snapshot in snapshots:
        if not isinstance(snapshot, Mapping):
            diagnostics.append(_realization_diagnostic("snapshot is invalid"))
            continue
        snapshot_id = snapshot.get("id")
        year = snapshot.get("simulation_year")
        if not _required_string(snapshot_id) or (
            isinstance(year, bool) or not isinstance(year, int)
        ):
            diagnostics.append(
                _realization_diagnostic("snapshot id and simulation_year are required")
            )
            continue
        if snapshot_id in snapshot_ids:
            diagnostics.append(_realization_diagnostic("snapshot ids must be unique"))
        snapshot_ids.add(snapshot_id)
        snapshot_by_id[snapshot_id] = snapshot
        snapshot_years.append(year)
        if snapshot.get("scenario_definition_ref") != scenario:
            diagnostics.append(
                _realization_diagnostic(
                    "snapshot scenario reference differs from trajectory"
                )
            )
        if snapshot.get("stochastic_realization_id") != trajectory.get(
            "stochastic_realization_id"
        ):
            diagnostics.append(
                _realization_diagnostic(
                    "snapshot stochastic realization differs from trajectory"
                )
            )
        if "equilibrium_iteration" in snapshot and (
            snapshot["equilibrium_iteration"] is None
            or isinstance(snapshot["equilibrium_iteration"], bool)
            or not isinstance(snapshot["equilibrium_iteration"], int)
        ):
            diagnostics.append(
                _realization_diagnostic(
                    "equilibrium_iteration must be an integer when present"
                )
            )
    if snapshot_years != sorted(snapshot_years) or len(snapshot_years) != len(
        set(snapshot_years)
    ):
        diagnostics.append(
            _realization_diagnostic("snapshot years must be strictly increasing")
        )
    successful = set(snapshot_years)
    if successful.intersection(skipped) or successful.union(skipped) != set(requested):
        diagnostics.append(
            _realization_diagnostic(
                "requested, successful, and skipped years must form one closure"
            )
        )
    expected_status = (
        "complete" if not skipped and successful == set(requested) else "incomplete"
    )
    if (
        trajectory_status in {"complete", "incomplete"}
        and trajectory_status != expected_status
    ):
        diagnostics.append(
            _realization_diagnostic("trajectory completeness_status is inconsistent")
        )
    for snapshot_id, snapshot in snapshot_by_id.items():
        if "parent_snapshot_ref" not in snapshot:
            continue
        parent = snapshot["parent_snapshot_ref"]
        parent_id = _snapshot_parent_id(parent)
        if parent_id is None or parent_id not in snapshot_by_id:
            diagnostics.append(
                _realization_diagnostic("parent snapshot must be in this trajectory")
            )
        elif snapshot_by_id[parent_id].get("simulation_year") >= snapshot.get(
            "simulation_year"
        ):
            diagnostics.append(
                _realization_diagnostic("parent snapshot must precede its child")
            )

    bundles_raw = bundle.get("population_snapshot_bundles")
    snapshot_bundles = bundles_raw if isinstance(bundles_raw, list) else []
    by_snapshot_id: dict[str, list[Mapping[str, Any]]] = {}
    for snapshot_bundle in snapshot_bundles:
        snapshot = (
            snapshot_bundle.get("population_snapshot")
            if isinstance(snapshot_bundle, Mapping)
            else None
        )
        snapshot_id = snapshot.get("id") if isinstance(snapshot, Mapping) else None
        if _required_string(snapshot_id):
            by_snapshot_id.setdefault(snapshot_id, []).append(snapshot_bundle)
        else:
            diagnostics.append(
                _realization_diagnostic("snapshot bundle must name a snapshot")
            )
    if set(by_snapshot_id) != snapshot_ids or any(
        len(items) != 1 for items in by_snapshot_id.values()
    ):
        diagnostics.append(
            _realization_diagnostic(
                "one snapshot bundle is required for every trajectory snapshot"
            )
        )

    for snapshot_id, snapshot in snapshot_by_id.items():
        matches = by_snapshot_id.get(snapshot_id, [])
        if len(matches) != 1:
            continue
        snapshot_bundle = matches[0]
        if snapshot_bundle.get("population_snapshot") != snapshot:
            diagnostics.append(
                _realization_diagnostic(
                    "snapshot bundle context differs from trajectory"
                )
            )
        if not _required_string(snapshot_bundle.get("manifest_version")):
            diagnostics.append(
                _realization_diagnostic("snapshot manifest_version is required")
            )
        if snapshot_bundle.get("completeness_status") != "complete":
            diagnostics.append(
                _realization_diagnostic("successful snapshot bundles must be complete")
            )
        members_raw = snapshot_bundle.get("members")
        members = members_raw if isinstance(members_raw, list) else []
        roles = [
            member.get("semantic_role") if isinstance(member, Mapping) else None
            for member in members
        ]
        if sorted(roles, key=lambda value: str(value)) != list(
            _REQUIRED_POPULATION_ROLES
        ):
            diagnostics.append(
                _realization_diagnostic(
                    f"snapshot {snapshot_id} needs each required semantic role once"
                )
            )
        for member in members:
            if not isinstance(member, Mapping):
                continue
            artifact = member.get("artifact")
            identity = (
                artifact.get("artifact_identity")
                if isinstance(artifact, Mapping)
                else None
            )
            if (
                not isinstance(identity, Mapping)
                or identity.get("digest_algorithm") != "sha256"
                or not _is_sha256_digest(identity.get("content_digest"))
            ):
                diagnostics.append(
                    _realization_diagnostic("member artifact digest is invalid")
                )
            contract = member.get("schema_contract")
            if (
                not isinstance(contract, Mapping)
                or not _required_string(contract.get("language"))
                or contract.get("schema_digest_algorithm") != "sha256"
                or not _is_sha256_digest(contract.get("schema_digest"))
                or not _required_string(contract.get("selected_root"))
            ):
                diagnostics.append(
                    _realization_diagnostic("member schema contract is invalid")
                )
    return diagnostics


def _jcs_json_bytes(value: object) -> bytes:
    """Encode the v1 restricted JSON value set with RFC 8785 key ordering."""

    def encode(item: object) -> str:
        if item is None:
            raise ValueError("REALIZATION_PROJECTION_INVALID: null is not permitted")
        if isinstance(item, bool):
            return "true" if item else "false"
        if isinstance(item, int):
            if abs(item) > _MAX_SAFE_JCS_INTEGER:
                raise ValueError(
                    "REALIZATION_PROJECTION_INVALID: integer is outside JCS range"
                )
            return str(item)
        if isinstance(item, str):
            if any(0xD800 <= ord(character) <= 0xDFFF for character in item):
                raise ValueError(
                    "REALIZATION_PROJECTION_INVALID: strings cannot contain surrogates"
                )
            return json.dumps(item, ensure_ascii=False, separators=(",", ":"))
        if isinstance(item, list):
            return "[" + ",".join(encode(child) for child in item) + "]"
        if isinstance(item, Mapping):
            if not all(isinstance(key, str) for key in item):
                raise ValueError(
                    "REALIZATION_PROJECTION_INVALID: object keys must be strings"
                )
            ordered_keys = sorted(item, key=lambda key: key.encode("utf-16be"))
            return (
                "{"
                + ",".join(f"{encode(key)}:{encode(item[key])}" for key in ordered_keys)
                + "}"
            )
        raise ValueError(
            "REALIZATION_PROJECTION_INVALID: only objects, arrays, strings, integers, and booleans are permitted"
        )

    return encode(value).encode("utf-8")


def _realization_projection_unchecked(bundle: Mapping[str, Any]) -> dict[str, Any]:
    trajectory = bundle["population_trajectory"]
    assert isinstance(trajectory, Mapping)
    scenario = trajectory["scenario_definition_ref"]
    assert isinstance(scenario, Mapping)
    bundles_by_snapshot = {
        item["population_snapshot"]["id"]: item
        for item in bundle["population_snapshot_bundles"]
        if isinstance(item, Mapping)
        and isinstance(item.get("population_snapshot"), Mapping)
    }
    snapshots: list[dict[str, Any]] = []
    for snapshot in trajectory["snapshots"]:
        assert isinstance(snapshot, Mapping)
        snapshot_bundle = bundles_by_snapshot[snapshot["id"]]
        members: list[dict[str, Any]] = []
        for member in sorted(
            snapshot_bundle["members"], key=lambda candidate: candidate["semantic_role"]
        ):
            assert isinstance(member, Mapping)
            artifact = member["artifact"]
            contract = member["schema_contract"]
            assert isinstance(artifact, Mapping) and isinstance(contract, Mapping)
            identity = artifact["artifact_identity"]
            assert isinstance(identity, Mapping)
            members.append(
                {
                    "semantic_role": member["semantic_role"],
                    "artifact_identity": {
                        "digest_algorithm": identity["digest_algorithm"],
                        "content_digest": identity["content_digest"],
                    },
                    "schema_contract": {
                        "language": contract["language"],
                        "schema_digest_algorithm": contract["schema_digest_algorithm"],
                        "schema_digest": contract["schema_digest"],
                        "selected_root": contract["selected_root"],
                    },
                }
            )
        result: dict[str, Any] = {
            "snapshot_id": snapshot["id"],
            "manifest_version": snapshot_bundle["manifest_version"],
            "simulation_year": snapshot["simulation_year"],
            "completeness_status": snapshot_bundle["completeness_status"],
            "members": members,
        }
        if "equilibrium_iteration" in snapshot:
            result["equilibrium_iteration"] = snapshot["equilibrium_iteration"]
        if "parent_snapshot_ref" in snapshot:
            result["parent_snapshot_ref"] = _snapshot_parent_id(
                snapshot["parent_snapshot_ref"]
            )
        snapshots.append(result)
    return {
        "kind": _REALIZATION_KIND,
        "projection_version": _REALIZATION_VERSION,
        "digest_algorithm": "sha256",
        "manifest_version": bundle["manifest_version"],
        "scenario_definition": {
            "scenario_definition_id": scenario["scenario_definition_id"],
            "revision": scenario["revision"],
            "digest_algorithm": "sha256",
            "content_digest": scenario["content_digest"],
        },
        "stochastic_realization_id": trajectory["stochastic_realization_id"],
        "trajectory": {
            "trajectory_id": trajectory["id"],
            "requested_years": trajectory["requested_years"],
            "skipped_years": [item["year"] for item in trajectory["skipped_years"]],
            "completeness_status": trajectory["completeness_status"],
            "membership_rule": {
                "profile": "pilates-population-snapshot-v1",
                "required_roles": list(_REQUIRED_POPULATION_ROLES),
                "optional_roles": [],
            },
            "snapshots": snapshots,
        },
    }


def _validate_supplied_realization_identity(
    bundle: Mapping[str, Any], diagnostics: list[Diagnostic]
) -> None:
    """Validate top-level and receipt identities only after a valid envelope."""
    if diagnostics:
        return
    supplied: list[tuple[str, object]] = []
    if "realization_identity" in bundle:
        supplied.append(("realization identity", bundle["realization_identity"]))
    if "realization_receipt" in bundle:
        receipt = bundle["realization_receipt"]
        if not isinstance(receipt, Mapping) or receipt.get("receipt_version") != "1":
            diagnostics.append(
                _diagnostic(
                    "REALIZATION_IDENTITY_MISMATCH", "realization receipt is invalid"
                )
            )
            return
        supplied.append(
            ("receipt realization identity", receipt.get("realization_identity"))
        )
    if not supplied:
        return
    expected = sha256(
        _jcs_json_bytes(_realization_projection_unchecked(bundle))
    ).hexdigest()
    canonical_identity = {
        "kind": _REALIZATION_KIND,
        "projection_version": _REALIZATION_VERSION,
        "digest_algorithm": "sha256",
        "content_digest": expected,
    }
    for label, identity in supplied:
        if identity != canonical_identity:
            diagnostics.append(
                _diagnostic(
                    "REALIZATION_IDENTITY_MISMATCH",
                    f"{label} does not match the v1 projection",
                )
            )


def canonical_realization_projection(bundle: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate and return the closed population-trajectory v1 projection."""
    schema_path = Path(__file__).parents[1] / "schema" / "synergy_schema.yaml"
    diagnostics = list(
        validate_bundle_shape(
            schema_path, bundle, "PopulationTrajectoryBundle"
        ).diagnostics
    )
    if diagnostics:
        raise ValueError(
            "; ".join(f"{item.code}: {item.message}" for item in diagnostics)
        )
    diagnostics = list(validate_population_bundle(bundle).diagnostics)
    if not _is_v1_realization_bundle(bundle):
        diagnostics.extend(_validate_realization_projection(bundle))
    if diagnostics:
        raise ValueError(
            "; ".join(f"{item.code}: {item.message}" for item in diagnostics)
        )
    return _realization_projection_unchecked(bundle)


def canonical_realization_digest(bundle: Mapping[str, Any]) -> str:
    """Return SHA-256 of the RFC 8785 population-trajectory v1 projection."""
    return sha256(_jcs_json_bytes(canonical_realization_projection(bundle))).hexdigest()


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


def _integer(value: object) -> int | None:
    """Return an already-typed integer without coercing malformed input."""
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _years(trajectory: Mapping[str, Any]) -> tuple[set[int], set[int], set[int]]:
    requested_values = trajectory.get("requested_years", [])
    requested = {
        year
        for value in requested_values
        if isinstance(requested_values, list)
        if (year := _integer(value)) is not None
    }
    snapshots = trajectory.get("snapshots", [])
    successful = {
        year
        for item in snapshots
        if isinstance(item, Mapping)
        and (year := _integer(item.get("simulation_year"))) is not None
    }
    skipped_values = trajectory.get("skipped_years", [])
    skipped = {
        year
        for item in skipped_values
        if isinstance(skipped_values, list)
        if isinstance(item, Mapping)
        and (year := _integer(item.get("year"))) is not None
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
            year = _integer(snapshot.get("simulation_year"))
            if year is not None:
                by_year.setdefault(year, []).append(snapshot_bundle)
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
                if _integer(item.get("simulation_year")) == year
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
    actual = {
        year: item.get("status")
        for item in statuses
        if isinstance(statuses, list)
        if isinstance(item, Mapping)
        and (year := _integer(item.get("simulation_year"))) is not None
    }
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
    if _is_v1_realization_bundle(bundle):
        diagnostics.extend(_validate_realization_projection(bundle))
        _validate_supplied_realization_identity(bundle, diagnostics)
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
