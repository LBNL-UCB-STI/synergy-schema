"""Semantic checks for canonical core-population assembly manifests."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence

from .diagnostics import CheckResult, Diagnostic

_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_AUTHORITY_KINDS = {
    "core_assertion",
    "model_view",
    "carried_through",
    "unclassified_native_field",
}


def _map(value: object) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _items(value: object) -> list[Mapping[str, Any]]:
    return (
        [item for item in value if isinstance(item, Mapping)]
        if isinstance(value, list)
        else []
    )


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _snapshot(value: object) -> tuple[object, ...] | None:
    item = _map(value)
    if item is None:
        return None
    scenario = _map(item.get("scenario_definition_ref"))
    scenario_key = (
        tuple(sorted((str(k), str(v)) for k, v in scenario.items()))
        if scenario
        else _text(item.get("scenario_definition_ref"))
    )
    return (
        item.get("id"),
        scenario_key,
        item.get("stochastic_realization_id"),
        item.get("simulation_year"),
    )


def _target(entry: Mapping[str, Any]) -> Mapping[str, Any] | None:
    return _map(entry.get("target"))


def _facet(target: Mapping[str, Any] | None) -> str:
    return _text((target or {}).get("facet"))


def _field(target: Mapping[str, Any] | None) -> str:
    return _text((target or {}).get("field"))


def _contribution_id(ref: Mapping[str, Any]) -> str:
    return _text(ref.get("contribution_id"))


def _identity_digest(identity: Mapping[str, Any] | None) -> tuple[str, str]:
    identity = identity or {}
    return _text(identity.get("digest_algorithm")), _text(
        identity.get("content_digest")
    )


def canonical_population_assembly_projection(
    assembly: Mapping[str, Any],
) -> dict[str, Any]:
    projection = {
        str(k): v for k, v in sorted(assembly.items(), key=lambda pair: str(pair[0]))
    }
    identity = projection.get("semantic_identity")
    if isinstance(identity, Mapping):
        identity = deepcopy(dict(identity))
        identity.pop("content_digest", None)
        projection["semantic_identity"] = identity
    return projection


def population_assembly_digest(assembly: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        canonical_population_assembly_projection(assembly),
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _diag(code: str, message: str) -> Diagnostic:
    return Diagnostic(code, message, "error")


def validate_population_assembly(
    assembly: Mapping[str, Any], contributions: Sequence[Mapping[str, Any]] = ()
) -> CheckResult:
    diagnostics: list[Diagnostic] = []
    target_key = _snapshot(assembly.get("target_snapshot"))
    if target_key is None:
        diagnostics.append(
            _diag("ASSEMBLY_SNAPSHOT_INVALID", "assembly target_snapshot is required")
        )
    refs = _items(assembly.get("contributions"))
    if not refs:
        diagnostics.append(
            _diag(
                "ASSEMBLY_CONTRIBUTION_INVALID",
                "at least one contribution reference is required",
            )
        )
    by_id: dict[str, Mapping[str, Any]] = {}
    for ref in refs:
        identifier = _contribution_id(ref)
        if not identifier or identifier in by_id:
            diagnostics.append(
                _diag(
                    "ASSEMBLY_CONTRIBUTION_ROLE_CONFLICT",
                    "contribution references must have distinct contribution_id values",
                )
            )
        elif identifier:
            by_id[identifier] = ref
    docs = {_text(doc.get("id")): doc for doc in contributions if _text(doc.get("id"))}
    if len(docs) != len(contributions):
        diagnostics.append(
            _diag(
                "ASSEMBLY_CONTRIBUTION_INVALID",
                "each contribution manifest must declare an id",
            )
        )
    for identifier, ref in by_id.items():
        doc = docs.get(identifier)
        if doc is None:
            diagnostics.append(
                _diag(
                    "ASSEMBLY_CONTRIBUTION_MISSING",
                    f"no contribution manifest supplied for {identifier}",
                )
            )
            continue
        if ref.get("revision") != doc.get("contribution_revision"):
            diagnostics.append(
                _diag(
                    "ASSEMBLY_CONTRIBUTION_REVISION_MISMATCH",
                    f"contribution {identifier} revision does not match its manifest",
                )
            )
        if _snapshot(doc.get("target_snapshot")) != target_key:
            diagnostics.append(
                _diag(
                    "ASSEMBLY_SNAPSHOT_MISMATCH",
                    f"contribution {identifier} targets a different snapshot",
                )
            )
        if _map(ref.get("semantic_identity")) != _map(doc.get("semantic_identity")):
            diagnostics.append(
                _diag(
                    "ASSEMBLY_CONTRIBUTION_IDENTITY_MISMATCH",
                    f"contribution {identifier} semantic identity differs from its reference",
                )
            )

    assertions: dict[tuple[str, str], list[str]] = {}
    supplied_roles: set[str] = set()
    for supplied in _items(assembly.get("supplied_facets")):
        role = _facet(_target(supplied))
        if not role or role in supplied_roles:
            diagnostics.append(
                _diag(
                    "ASSEMBLY_CONTRIBUTION_ROLE_CONFLICT",
                    "supplied_facets must declare distinct facet roles",
                )
            )
        supplied_roles.add(role)
    for identifier in by_id:
        doc = docs.get(identifier)
        if doc is None:
            continue
        binding_roles: set[tuple[str, str]] = set()
        for entry in _items(doc.get("column_classifications")):
            kind = _text(entry.get("classification"))
            if kind not in _AUTHORITY_KINDS:
                diagnostics.append(
                    _diag(
                        "ASSEMBLY_COLUMN_AUTHORITY_INVALID",
                        f"unknown column authority classification {kind or '<missing>'}",
                    )
                )
            if _map(entry.get("native_element")) is None:
                diagnostics.append(
                    _diag(
                        "ASSEMBLY_COLUMN_AUTHORITY_INVALID",
                        f"classified column in {identifier} must name native_element",
                    )
                )
            target = _target(entry)
            role = (_facet(target), _field(target))
            if role in binding_roles and role != ("", ""):
                diagnostics.append(
                    _diag(
                        "ASSEMBLY_CONTRIBUTION_ROLE_CONFLICT",
                        f"contribution {identifier} repeats a target role",
                    )
                )
            binding_roles.add(role)
            if kind == "core_assertion":
                if not _facet(target) or not _field(target):
                    diagnostics.append(
                        _diag(
                            "ASSEMBLY_COLUMN_AUTHORITY_INVALID",
                            "core assertion must name target facet and field",
                        )
                    )
                else:
                    assertions.setdefault((_facet(target), _field(target)), []).append(
                        identifier
                    )
            if (
                kind == "carried_through"
                and _map(entry.get("upstream_assertion")) is None
            ):
                diagnostics.append(
                    _diag(
                        "CARRIED_THROUGH_UPSTREAM_ASSERTION_REQUIRED",
                        "carried-through field must name upstream_assertion",
                    )
                )

    resolved: set[tuple[str, str]] = set()
    for resolution in _items(assembly.get("field_resolutions")):
        target = _target(resolution)
        selected = _map(resolution.get("selected_assertion"))
        candidates = _items(resolution.get("candidate_assertions"))
        key = (_facet(target), _field(target))
        if not key[0] or not key[1] or selected is None:
            diagnostics.append(
                _diag(
                    "ASSEMBLY_RESOLUTION_INVALID",
                    "field resolution needs target and selected_assertion",
                )
            )
            continue
        selected_ref = _map(selected.get("contribution")) or selected
        selected_id = _contribution_id(selected_ref)
        candidate_ids = {
            _contribution_id(_map(item.get("contribution")) or item)
            for item in candidates
        }
        if selected_id not in candidate_ids:
            diagnostics.append(
                _diag(
                    "ASSEMBLY_RESOLUTION_INVALID",
                    f"selected assertion for {key[0]}/{key[1]} is not a candidate",
                )
            )
        resolved.add(key)
    for key, owners in assertions.items():
        if len(set(owners)) > 1 and key not in resolved:
            diagnostics.append(
                _diag(
                    "CORE_FIELD_OVERLAP_UNRESOLVED",
                    f"overlapping core assertion for {key[0]}/{key[1]} lacks an approved resolution",
                )
            )

    for identifier in by_id:
        doc = docs.get(identifier)
        if doc is None:
            continue
        for relation in _items(doc.get("relationship_bindings")):
            source = _map(relation.get("source_contribution")) or {}
            target_ref = _map(relation.get("target_contribution")) or {}
            source_id = _contribution_id(source)
            target_id = _contribution_id(target_ref)
            if (
                source_id not in by_id
                or target_id not in by_id
                or not _items(relation.get("source_key_fields"))
                or not _items(relation.get("target_key_fields"))
            ):
                diagnostics.append(
                    _diag(
                        "ASSEMBLY_RELATIONSHIP_INVALID",
                        "relationship must reference known contributions and key fields",
                    )
                )
            if "vehicle" in _text(relation.get("relationship_kind")).lower() and _facet(
                _map(relation.get("target_core"))
            ) not in {"households", "household"}:
                diagnostics.append(
                    _diag(
                        "ASSEMBLY_RELATIONSHIP_INVALID",
                        "vehicle relationship must target households",
                    )
                )

    indexed = set()
    for entry in _items(assembly.get("resolved_facet_index")):
        target = _target(entry)
        contribution = _map(entry.get("contribution")) or {}
        contribution_id = _contribution_id(contribution)
        if contribution_id not in by_id or not _facet(target):
            diagnostics.append(
                _diag(
                    "ASSEMBLY_RESOLVED_INDEX_MISMATCH",
                    "resolved facet index selects an undeclared contribution or facet",
                )
            )
        indexed.add((_facet(target), contribution_id))
    if not indexed and refs:
        diagnostics.append(
            _diag(
                "ASSEMBLY_RESOLVED_INDEX_MISMATCH",
                "resolved_facet_index must contain declared selections",
            )
        )

    seen: dict[str, str] = {}
    for identifier in by_id:
        doc = docs.get(identifier)
        if doc is None:
            continue
        for member in _items(doc.get("members")):
            artifact = _map(member.get("artifact")) or {}
            algorithm, digest = _identity_digest(
                _map(artifact.get("artifact_identity"))
            )
            if algorithm != "sha256" or not _DIGEST.fullmatch(digest):
                diagnostics.append(
                    _diag(
                        "ASSEMBLY_ARTIFACT_DIGEST_INVALID",
                        f"artifact in {identifier} lacks a valid sha256 identity",
                    )
                )
            locator = _text(artifact.get("locator"))
            if locator and locator in seen and seen[locator] != digest:
                diagnostics.append(
                    _diag(
                        "ASSEMBLY_ARTIFACT_DIGEST_MISMATCH",
                        f"artifact locator {locator} has inconsistent digests",
                    )
                )
            if locator:
                seen[locator] = digest

    algorithm, declared = _identity_digest(_map(assembly.get("semantic_identity")))
    if algorithm != "sha256" or not _DIGEST.fullmatch(declared):
        diagnostics.append(
            _diag(
                "ASSEMBLY_DIGEST_INVALID",
                "assembly semantic_identity must declare a lowercase sha256 content_digest",
            )
        )
    elif declared != population_assembly_digest(assembly):
        diagnostics.append(
            _diag(
                "ASSEMBLY_DIGEST_MISMATCH",
                "assembly semantic digest does not match its declared content",
            )
        )
    return CheckResult(tuple(diagnostics))
