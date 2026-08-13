"""Semantic mapping-release projections and validation."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from linkml_runtime.utils.schemaview import SchemaView

from synergy_schema.native_catalog import (
    CatalogValidationError,
    catalog_identity,
    resolve_catalog_reference,
)

from .diagnostics import CheckResult, Diagnostic, InputError
from .documents import load_mapping_release


def _catalog_identity(reference: Mapping[str, Any]) -> dict[str, Any]:
    return catalog_identity(reference)


def _element_projection(element: Mapping[str, Any]) -> dict[str, str]:
    return {"kind": str(element["kind"]), "path": str(element["path"])}


_SCHEMA_IDENTITY_FIELDS = (
    "language",
    "schema_digest_algorithm",
    "schema_digest",
    "selected_root",
)


def _schema_contract_identity(contract: Mapping[str, Any], name: str) -> dict[str, str]:
    value = contract.get(name)
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    identity = {
        field: str(value.get(field, "")).strip() for field in _SCHEMA_IDENTITY_FIELDS
    }
    missing = [field for field, item in identity.items() if not item]
    if missing:
        raise ValueError(
            f"{name} is missing required identity fields: {', '.join(missing)}"
        )
    return identity


def semantic_mapping_projection(contract: Mapping[str, Any]) -> dict[str, Any]:
    """The release content that model-owner approvals attest to."""
    mappings = [
        {
            "id": str(item["id"]),
            "source_element": _element_projection(item["source_element"]),
            "target_element": _element_projection(item["target_element"]),
            "transformation_mode": str(item["transformation_mode"]),
            "rule": str(item["rule"]),
        }
        for item in contract.get("field_mappings", [])
    ]
    residues = [
        {
            "id": str(item["id"]),
            "residue_kind": str(item["residue_kind"]),
            "affected_elements": sorted(
                [
                    _element_projection(element)
                    for element in item.get("affected_elements", [])
                ],
                key=lambda element: (element["kind"], element["path"]),
            ),
            "deterministic_rule": item.get("deterministic_rule"),
            "rationale": str(item["rationale"]),
            "disposition": str(item["disposition"]),
        }
        for item in contract.get("residue_records", [])
    ]
    projection = {
        "source_catalog": _catalog_identity(contract["source_catalog"]),
        "target_catalog": _catalog_identity(contract["target_catalog"]),
        "field_mappings": sorted(mappings, key=lambda item: item["id"]),
        "residue_records": sorted(residues, key=lambda item: item["id"]),
    }
    for name in ("source_schema_contract", "target_schema_contract"):
        projection[name] = _schema_contract_identity(contract, name)
    return projection


def mapping_digest(contract: Mapping[str, Any]) -> str:
    projection = semantic_mapping_projection(contract)
    rendered = json.dumps(projection, sort_keys=True, separators=(",", ":"))
    return sha256(rendered.encode("utf-8")).hexdigest()


def _catalog_for(reference: Mapping[str, Any], catalog_root: Path | str | None):
    return resolve_catalog_reference(reference, catalog_root)


def _validate_elements(
    contract: Mapping[str, Any], catalog_root: Path | str | None
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    try:
        source_catalog = _catalog_for(contract["source_catalog"], catalog_root)
        target_catalog = _catalog_for(contract["target_catalog"], catalog_root)
    except (CatalogValidationError, KeyError) as error:
        return [Diagnostic("NATIVE_ELEMENT_UNRESOLVED", str(error), "error")]

    source_primary: dict[tuple[str, str], int] = {}
    target_primary: dict[tuple[str, str], int] = {}

    def add(mapping: dict[tuple[str, str], int], element: Mapping[str, Any]) -> None:
        identity = (str(element.get("kind")), str(element.get("path")))
        mapping[identity] = mapping.get(identity, 0) + 1

    def resolved_element(
        element: object, expected_catalog: object
    ) -> tuple[bool, Mapping[str, Any]]:
        if not isinstance(element, Mapping):
            return False, {}
        catalog_ref = element.get("catalog")
        if not isinstance(catalog_ref, Mapping):
            return False, element
        try:
            nested_catalog = resolve_catalog_reference(catalog_ref, catalog_root)
        except CatalogValidationError:
            return False, element
        return (
            nested_catalog.identity == expected_catalog.identity
            and nested_catalog.resolve(
                str(element.get("kind", "")), str(element.get("path", ""))
            ),
            element,
        )

    for field in contract.get("field_mappings", []):
        source, target = (
            field.get("source_element", {}),
            field.get("target_element", {}),
        )
        source_ok, source_element = resolved_element(source, source_catalog)
        target_ok, target_element = resolved_element(target, target_catalog)
        if not source_ok or not target_ok:
            diagnostics.append(
                Diagnostic(
                    "NATIVE_ELEMENT_UNRESOLVED",
                    f"field mapping {field.get('id')} references an unknown catalog element",
                    "error",
                )
            )
        add(source_primary, source_element)
        add(target_primary, target_element)
    primary_kinds = {"unmapped_source", "dropped_context", "required_target_default"}
    primary_elements: set[tuple[str, str]] = set()
    for residue in contract.get("residue_records", []):
        kind = residue.get("residue_kind")
        for element in residue.get("affected_elements", []):
            expected_catalog = (
                source_catalog
                if kind in {"unmapped_source", "dropped_context"}
                else target_catalog
            )
            element_ok, resolved = resolved_element(element, expected_catalog)
            identity = (str(resolved.get("kind")), str(resolved.get("path")))
            if not element_ok:
                diagnostics.append(
                    Diagnostic(
                        "NATIVE_ELEMENT_UNRESOLVED",
                        f"residue {residue.get('id')} references an unknown catalog element",
                        "error",
                    )
                )
            if kind in primary_kinds:
                primary_elements.add(identity)
                if kind in {"unmapped_source", "dropped_context"}:
                    source_primary[identity] = source_primary.get(identity, 0) + 1
                elif kind == "required_target_default":
                    target_primary[identity] = target_primary.get(identity, 0) + 1
            elif identity not in set(source_primary) | set(target_primary):
                diagnostics.append(
                    Diagnostic(
                        "MAPPING_COVERAGE_MISSING",
                        f"supplementary residue {residue.get('id')} lacks a primary disposition",
                        "error",
                    )
                )
    source_columns = {
        ("sql_column", str(element["path"]))
        for element in source_catalog.document["elements"]
        if element["kind"] == "sql_column"
    }
    target_columns = {
        ("sql_column", str(element["path"]))
        for element in target_catalog.document["elements"]
        if element["kind"] == "sql_column"
    }
    missing = [
        element
        for element in source_columns | target_columns
        if (source_primary if element in source_columns else target_primary).get(
            element, 0
        )
        != 1
    ]
    if missing:
        diagnostics.append(
            Diagnostic(
                "MAPPING_COVERAGE_MISSING",
                "each source and required target column needs exactly one primary disposition",
                "error",
            )
        )
    return diagnostics


def _validate_approval(
    contract: Mapping[str, Any], ownership: Mapping[str, Any], require_approved: bool
) -> list[Diagnostic]:
    governance = contract.get("governance", {})
    lifecycle = governance.get("lifecycle_status")
    digest = contract.get("semantic_content_digest")
    algorithm = contract.get("semantic_content_digest_algorithm")
    reviews = governance.get("review_records", [])
    accepted_roles = {
        review.get("reviewer_role")
        for review in reviews
        if review.get("decision") == "accept"
        and review.get("assessed_semantic_content_digest") == digest
        and review.get("assessed_semantic_content_digest_algorithm") == algorithm
        and review.get("reviewing_team") == ownership.get(review.get("reviewer_role"))
    }
    if (
        lifecycle == "approved"
        and not {"source_owner", "target_owner"} <= accepted_roles
    ):
        return [
            Diagnostic(
                "MAPPING_FALSE_APPROVAL",
                "approved mapping lacks current source and target owner acceptance",
                "error",
            )
        ]
    if lifecycle != "approved":
        severity = "error" if require_approved else "warning"
        return [
            Diagnostic(
                "MAPPING_NOT_APPROVED", "mapping release is not approved", severity
            )
        ]
    return []


def _validate_implementations(
    contract: Mapping[str, Any], implementations: list[Mapping[str, Any]], strict: bool
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    digest = contract.get("semantic_content_digest")
    algorithm = contract.get("semantic_content_digest_algorithm")
    for implementation in implementations:
        if (
            implementation.get("implemented_semantic_content_digest") != digest
            or implementation.get("implemented_semantic_content_digest_algorithm")
            != algorithm
        ):
            diagnostics.append(
                Diagnostic(
                    "MAPPING_IMPLEMENTATION_UNREGISTERED",
                    f"implementation {implementation.get('id')} does not implement this semantic digest",
                    "error",
                )
            )
        elif implementation.get("status") != "conformance_checked":
            diagnostics.append(
                Diagnostic(
                    "MAPPING_IMPLEMENTATION_NOT_CHECKED",
                    f"implementation {implementation.get('id')} is not conformance checked",
                    "error" if strict else "warning",
                )
            )
    return diagnostics


def validate_mapping_release(
    release: Path | str,
    *,
    require_approved: bool = False,
    new_receipt: bool = False,
    schema_path: Path | str | None = None,
    catalog_root: Path | str | None = None,
) -> CheckResult:
    """Check an immutable mapping release and separate implementation registrations."""
    if schema_path is not None:
        try:
            schema = SchemaView(str(schema_path))
            if schema.get_class("PopulationTranslationContract") is None:
                raise InputError("schema does not define PopulationTranslationContract")
        except Exception as error:
            raise InputError(f"cannot load mapping schema: {error}") from error
    contract, implementations, ownership = load_mapping_release(release)
    diagnostics: list[Diagnostic] = []
    try:
        expected = mapping_digest(contract)
    except (KeyError, TypeError, ValueError) as error:
        diagnostics.append(Diagnostic("MAPPING_DOCUMENT_INVALID", str(error), "error"))
        return CheckResult(tuple(diagnostics))
    except CatalogValidationError as error:
        diagnostics.append(Diagnostic("MAPPING_DIGEST_MISMATCH", str(error), "error"))
        return CheckResult(tuple(diagnostics))
    if (
        contract.get("semantic_content_digest_algorithm") != "sha256"
        or contract.get("semantic_content_digest") != expected
    ):
        diagnostics.append(
            Diagnostic(
                "MAPPING_DIGEST_MISMATCH",
                "mapping semantic digest does not match canonical content",
                "error",
            )
        )
    diagnostics.extend(_validate_elements(contract, catalog_root))
    diagnostics.extend(_validate_approval(contract, ownership, require_approved))
    diagnostics.extend(
        _validate_implementations(contract, implementations, require_approved)
    )
    lifecycle = contract.get("governance", {}).get("lifecycle_status")
    if new_receipt and lifecycle in {"superseded", "deprecated"}:
        diagnostics.append(
            Diagnostic(
                "MAPPING_NOT_RECEIPT_ELIGIBLE",
                "superseded or deprecated mappings cannot authorize new receipts",
                "error",
            )
        )
    return CheckResult(tuple(diagnostics))
