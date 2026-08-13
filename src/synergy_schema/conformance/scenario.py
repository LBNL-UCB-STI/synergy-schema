"""Canonical scenario projections and cross-document conformance checks."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from synergy_schema.native_catalog import CatalogValidationError, load_catalog

from .diagnostics import CheckResult, Diagnostic


def normalize_scalar(value: object, value_type: str) -> object:
    """Normalize declared scalar values without guessing native conventions."""
    text = str(value)
    if value_type == "integer":
        return int(text)
    if value_type == "number":
        decimal = Decimal(text)
        if not decimal.is_finite():
            raise ValueError("number must be finite")
        return format(decimal.normalize(), "f")
    if value_type == "boolean":
        if text in {"true", "1"}:
            return True
        if text in {"false", "0"}:
            return False
        raise ValueError("boolean must be one of true, false, 1, or 0")
    if value_type in {"string", "code", "reference"}:
        return text
    raise ValueError(f"unsupported scalar value_type: {value_type}")


def canonical_scenario_projection(definition: Mapping[str, Any]) -> dict[str, Any]:
    """Return the semantic scenario document used for its immutable identity."""
    assumptions = definition.get("assumptions", [])
    if not isinstance(assumptions, list):
        raise ValueError("assumptions must be a list")
    projected_assumptions = []
    for assumption in assumptions:
        if not isinstance(assumption, Mapping):
            raise ValueError("assumptions must contain mappings")
        value_type = str(assumption["value_type"])
        projected_assumptions.append(
            {
                "assumption_key": str(assumption["assumption_key"]),
                "value": normalize_scalar(assumption["value"], value_type),
                "value_type": value_type,
                "unit": assumption.get("unit"),
                "authority": str(assumption["authority"]),
            }
        )
    result: dict[str, Any] = {
        "id": str(definition["id"]),
        "revision": str(definition["revision"]),
        "region_ref": str(definition["region_ref"]),
        "start_year": int(definition["start_year"]),
        "end_year": int(definition["end_year"]),
        "assumptions": sorted(
            projected_assumptions, key=lambda item: item["assumption_key"]
        ),
    }
    if definition.get("parent_definition_ref") is not None:
        result["parent_definition_ref"] = definition["parent_definition_ref"]
    return result


def canonical_scenario_json(definition: Mapping[str, Any]) -> str:
    return json.dumps(
        canonical_scenario_projection(definition), sort_keys=True, separators=(",", ":")
    )


def scenario_digest(definition: Mapping[str, Any]) -> str:
    return sha256(canonical_scenario_json(definition).encode("utf-8")).hexdigest()


def _reference_matches(reference: object, definition: Mapping[str, Any]) -> bool:
    return isinstance(reference, Mapping) and (
        reference.get("scenario_definition_id") == definition.get("id")
        and reference.get("revision") == definition.get("revision")
        and reference.get("content_digest") == definition.get("content_digest")
    )


def _catalog_for(binding: Mapping[str, Any]):
    catalog_ref = binding.get("native_contract_catalog")
    if not isinstance(catalog_ref, Mapping):
        raise CatalogValidationError(
            "binding native_contract_catalog must be a mapping"
        )
    path = catalog_ref.get("catalog_path")
    if path is None:
        raise CatalogValidationError("binding must identify a catalog_path")
    return load_catalog(Path(str(path)))


def _validate_bindings(
    definition: Mapping[str, Any], bindings: Sequence[Mapping[str, Any]]
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    assumptions = {
        str(item["assumption_key"]): item for item in definition.get("assumptions", [])
    }
    for binding in bindings:
        if not _reference_matches(binding.get("scenario_definition_ref"), definition):
            diagnostics.append(
                Diagnostic(
                    "SCENARIO_BINDING_CONFLICT",
                    "binding selects a different scenario definition",
                    "error",
                )
            )
        try:
            catalog = _catalog_for(binding)
        except CatalogValidationError as error:
            diagnostics.append(
                Diagnostic("NATIVE_ELEMENT_UNRESOLVED", str(error), "error")
            )
            continue
        for item in binding.get("assumption_bindings", []):
            if not isinstance(item, Mapping):
                diagnostics.append(
                    Diagnostic(
                        "SCENARIO_BINDING_CONFLICT",
                        "assumption binding must be a mapping",
                        "error",
                    )
                )
                continue
            key = str(item.get("assumption_key", ""))
            assumption = assumptions.get(key)
            if assumption is None:
                diagnostics.append(
                    Diagnostic(
                        "SCENARIO_BINDING_CONFLICT",
                        f"unknown assumption {key}",
                        "error",
                    )
                )
                continue
            native = item.get("native_element")
            if not isinstance(native, Mapping) or not catalog.resolve(
                str(native.get("kind", "")), str(native.get("path", ""))
            ):
                diagnostics.append(
                    Diagnostic(
                        "NATIVE_ELEMENT_UNRESOLVED",
                        f"native element for {key} is not cataloged",
                        "error",
                    )
                )
            mode = item.get("binding_mode")
            state = item.get("compatibility_state")
            if mode == "unsupported":
                if item.get("resolved_native_value") is not None:
                    diagnostics.append(
                        Diagnostic(
                            "SCENARIO_BINDING_CONFLICT",
                            f"unsupported {key} carries a native value",
                            "error",
                        )
                    )
                if state == "compatible_with_gaps":
                    diagnostics.append(
                        Diagnostic(
                            "SCENARIO_COMPATIBILITY_GAP",
                            f"{key} is unsupported",
                            "warning",
                        )
                    )
                continue
            if (
                mode == "transformed"
                and not str(item.get("transformation_description", "")).strip()
            ):
                diagnostics.append(
                    Diagnostic(
                        "SCENARIO_BINDING_CONFLICT",
                        f"transformed {key} lacks a description",
                        "error",
                    )
                )
            if (
                mode == "override"
                and not str(item.get("override_rationale", "")).strip()
            ):
                diagnostics.append(
                    Diagnostic(
                        "SCENARIO_BINDING_CONFLICT",
                        f"override {key} lacks a rationale",
                        "error",
                    )
                )
            if mode == "override" or state in {"incompatible", "pending_review"}:
                diagnostics.append(
                    Diagnostic(
                        "SCENARIO_BINDING_CONFLICT", f"{key} is not compatible", "error"
                    )
                )
                continue
            if mode in {"direct", "alias"}:
                try:
                    expected = normalize_scalar(
                        assumption["value"], str(assumption["value_type"])
                    )
                    actual = normalize_scalar(
                        item.get("resolved_native_value", ""),
                        str(assumption["value_type"]),
                    )
                except (ValueError, InvalidOperation):
                    diagnostics.append(
                        Diagnostic(
                            "SCENARIO_BINDING_CONFLICT",
                            f"{key} has an invalid scalar",
                            "error",
                        )
                    )
                else:
                    if actual != expected:
                        diagnostics.append(
                            Diagnostic(
                                "SCENARIO_BINDING_CONFLICT",
                                f"{key} conflicts with the scenario",
                                "error",
                            )
                        )
            if state == "compatible_with_gaps":
                diagnostics.append(
                    Diagnostic(
                        "SCENARIO_COMPATIBILITY_GAP",
                        f"{key} has a compatibility gap",
                        "warning",
                    )
                )
    return diagnostics


def _validate_trajectory(
    definition: Mapping[str, Any], trajectory: Mapping[str, Any]
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if not _reference_matches(trajectory.get("scenario_definition_ref"), definition):
        diagnostics.append(
            Diagnostic(
                "SCENARIO_BINDING_CONFLICT",
                "trajectory selects a different scenario definition",
                "error",
            )
        )
    snapshots = trajectory.get("snapshots", [])
    years: list[int] = []
    known_ids: set[str] = set()
    realization = trajectory.get("stochastic_realization_id")
    for snapshot in snapshots if isinstance(snapshots, list) else []:
        year = int(snapshot.get("simulation_year"))
        years.append(year)
        parent = snapshot.get("parent_snapshot_ref")
        if parent is not None and str(parent) not in known_ids:
            diagnostics.append(
                Diagnostic(
                    "TRAJECTORY_PARENT_INVALID",
                    f"parent for {snapshot.get('id')} is not earlier",
                    "error",
                )
            )
        known_ids.add(str(snapshot.get("id")))
        if (
            not _reference_matches(snapshot.get("scenario_definition_ref"), definition)
            or snapshot.get("stochastic_realization_id") != realization
        ):
            diagnostics.append(
                Diagnostic(
                    "TRAJECTORY_MEMBER_MISMATCH",
                    f"snapshot {snapshot.get('id')} differs from trajectory",
                    "error",
                )
            )
    if years != sorted(years) or len(years) != len(set(years)):
        diagnostics.append(
            Diagnostic(
                "TRAJECTORY_YEAR_ORDER",
                "snapshot years must be ordered and unique",
                "error",
            )
        )
    requested = set(trajectory.get("requested_years", []))
    skipped = trajectory.get("skipped_years", [])
    skipped_years = {item.get("year") for item in skipped if isinstance(item, Mapping)}
    if requested != set(years) | skipped_years or set(years) & skipped_years:
        diagnostics.append(
            Diagnostic(
                "TRAJECTORY_COMPLETENESS_MISMATCH",
                "requested, successful, and skipped years disagree",
                "error",
            )
        )
    return diagnostics


def validate_scenario(
    definition: Mapping[str, Any],
    bindings: Sequence[Mapping[str, Any]],
    trajectory: Mapping[str, Any],
) -> CheckResult:
    diagnostics: list[Diagnostic] = []
    try:
        digest = scenario_digest(definition)
    except (KeyError, TypeError, ValueError, InvalidOperation) as error:
        return CheckResult(
            (Diagnostic("SCENARIO_DOCUMENT_INVALID", str(error), "error"),)
        )
    if definition.get("content_digest") != digest:
        diagnostics.append(
            Diagnostic(
                "SCENARIO_DIGEST_MISMATCH",
                "scenario content digest does not match canonical content",
                "error",
            )
        )
        return CheckResult(tuple(diagnostics))
    diagnostics.extend(_validate_bindings(definition, bindings))
    diagnostics.extend(_validate_trajectory(definition, trajectory))
    return CheckResult(tuple(diagnostics))
