"""Population ledger checks, packaged as a LinkML validation plugin.

These cover rules that span records within one PopulationLedger document and
that standard LinkML validation cannot express. They check declared metadata
only; nothing here reads parquet or recomputes digests.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any, Mapping

from linkml.validator import Validator
from linkml.validator.plugins import JsonschemaValidationPlugin, ValidationPlugin
from linkml.validator.report import Severity, ValidationResult
from linkml.validator.validation_context import ValidationContext

from .diagnostics import CheckResult, Diagnostic


def _facets(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {e.get("facet"): e for e in snapshot.get("core_state", {}).get("facets", [])}


def _ancestors(sid: str, snapshots: dict[str, dict[str, Any]]) -> set[str]:
    seen: set[str] = set()
    stack = [sid]
    while stack:
        current = stack.pop()
        if current in seen or current not in snapshots:
            continue
        seen.add(current)
        stack.extend(snapshots[current].get("parent_snapshots", []))
    return seen


def _merge_parents(
    parent_ids: list[str],
    snapshots: dict[str, dict[str, Any]],
    order: dict[str, int],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Combine parent states into the one state a child builds on.

    With one parent this is that parent's state. With several, each facet
    takes the entry of the parent that changed it since the latest common
    ancestor; a facet changed by more than one parent is a conflict.
    """
    if len(parent_ids) <= 1:
        return (_facets(snapshots[parent_ids[0]]) if parent_ids else {}), []
    common = set.intersection(*(_ancestors(pid, snapshots) for pid in parent_ids))
    base = _facets(snapshots[max(common, key=order.__getitem__)]) if common else {}
    merged = dict(base)
    changed_by: dict[str, int] = {}
    for pid in parent_ids:
        for facet, entry in _facets(snapshots[pid]).items():
            if entry != base.get(facet):
                changed_by[facet] = changed_by.get(facet, 0) + 1
                merged[facet] = entry
    return merged, sorted(f for f, n in changed_by.items() if n > 1)


def catalog_problems(catalog: dict[str, Any]) -> list[str]:
    """Return one message per violated rule in a mapping catalog."""
    problems: list[str] = []
    seen: set[str] = set()
    for mapping in catalog.get("mappings", []):
        mapping_id = mapping.get("mapping_id")
        if mapping_id in seen:
            problems.append(f"duplicate mapping_id {mapping_id}")
        seen.add(mapping_id)
        declared_kinds = set(mapping.get("input_view_kinds", []))
        for binding in mapping.get("field_bindings", []):
            if binding.get("view_kind") not in declared_kinds:
                problems.append(
                    f"{mapping_id}: binding view_kind {binding.get('view_kind')} "
                    "is not declared in input_view_kinds"
                )
    return problems


def ledger_problems(
    ledger: dict[str, Any], catalog: dict[str, Any] | None = None
) -> list[str]:
    """Return one message per violated ledger rule, in document order.

    Derivation mappings are checked only when the ledger's mapping catalog is
    supplied.
    """
    problems: list[str] = []
    mappings: dict[str, dict[str, Any]] | None = None
    if catalog is not None:
        if catalog.get("catalog_id") != ledger.get("mapping_catalog"):
            problems.append(
                f"mapping catalog {catalog.get('catalog_id')} is not the ledger's "
                f"{ledger.get('mapping_catalog')}"
            )
        problems.extend(catalog_problems(catalog))
        mappings = {m.get("mapping_id"): m for m in catalog.get("mappings", [])}

    snapshots: dict[str, dict[str, Any]] = {}
    order: dict[str, int] = {}
    view_ids: set[str] = set()
    # Facets whose content was last produced by a mapping with input_facets.
    delta_built: dict[str, set[str]] = {}

    for index, snapshot in enumerate(ledger.get("snapshots", [])):
        sid = snapshot.get("snapshot_id")
        if sid in snapshots:
            problems.append(f"duplicate snapshot_id {sid}")
        step = snapshot.get("step", {})
        reads = set(step.get("reads", []))
        output_kinds = {
            v.get("view_id"): v.get("view_kind") for v in step.get("output_views", [])
        }
        for view in [*step.get("input_views", []), *step.get("output_views", [])]:
            view_id = view.get("view_id")
            if view_id in view_ids:
                problems.append(f"duplicate view_id {view_id}")
            view_ids.add(view_id)
        entries = snapshot.get("core_state", {}).get("facets", [])
        own = {e.get("facet"): e for e in entries}

        parent_snapshot_ids = snapshot.get("parent_snapshots", [])
        if index == 0 and parent_snapshot_ids:
            problems.append(f"{sid}: the first snapshot must not have a parent")
        elif index > 0 and not parent_snapshot_ids:
            problems.append(f"{sid}: every later snapshot must have a parent")
        known_parents = [pid for pid in parent_snapshot_ids if pid in snapshots]
        for pid in parent_snapshot_ids:
            if pid not in snapshots:
                problems.append(f"{sid}: parent {pid} is not an earlier snapshot")
                continue
            child_year = snapshot.get("simulation_year")
            parent_year = snapshots[pid].get("simulation_year")
            if (
                isinstance(child_year, int)
                and isinstance(parent_year, int)
                and child_year < parent_year
            ):
                problems.append(f"{sid}: simulation_year precedes parent {pid}")
        parents, conflicts = _merge_parents(known_parents, snapshots, order)
        for facet in conflicts:
            problems.append(
                f"{sid}: more than one parent changed {facet} since their common "
                "ancestor; joined parents must not change the same facet"
            )

        parent_states = {
            snapshots[pid].get("core_state", {}).get("state_digest")
            for pid in known_parents
        }
        for view in step.get("input_views", []):
            prepared = view.get("prepared_from_state")
            if prepared is None:
                problems.append(
                    f"{sid}: input {view.get('view_id')} has no prepared_from_state"
                )
            elif prepared not in parent_states:
                problems.append(
                    f"{sid}: input {view.get('view_id')} was prepared from a state "
                    "no parent has"
                )

        if len(own) != len(entries):
            problems.append(f"{sid}: a facet appears more than once")
        for facet in reads - parents.keys():
            problems.append(f"{sid}: reads {facet}, which no parent has established")
        for facet in parents.keys() - own.keys():
            problems.append(f"{sid}: drops {facet}, which a parent established")

        derived: dict[str, dict[str, Any]] = {}
        for derivation in step.get("derivations", []):
            facet = derivation.get("facet")
            if facet in derived:
                problems.append(f"{sid}: {facet} is derived more than once")
            derived[facet] = derivation
            if facet not in own:
                problems.append(
                    f"{sid}: derives {facet}, which is missing from core_state"
                )
            for view in derivation.get("views", []):
                if view not in output_kinds:
                    problems.append(
                        f"{sid}: {facet} cites {view}, which is not an output of this step"
                    )
            if mappings is None:
                continue
            mapping = mappings.get(derivation.get("mapping"))
            if mapping is None:
                problems.append(
                    f"{sid}: {facet} uses unknown mapping {derivation.get('mapping')}"
                )
                continue
            if mapping.get("facet") != facet:
                problems.append(
                    f"{sid}: {facet} uses a mapping for {mapping.get('facet')}"
                )
            allowed = set(mapping.get("input_view_kinds", []))
            for view in derivation.get("views", []):
                if view in output_kinds and output_kinds[view] not in allowed:
                    problems.append(
                        f"{sid}: {facet} cites {view}, whose view_kind is not declared "
                        "by its mapping"
                    )
            for input_facet in mapping.get("input_facets", []):
                if input_facet not in parents:
                    problems.append(
                        f"{sid}: {facet} mapping needs parent {input_facet}, which no "
                        "parent has established"
                    )

        for facet, entry in own.items():
            if facet not in derived and entry.get("digest") != (
                parents.get(facet) or {}
            ).get("digest"):
                problems.append(
                    f"{sid}: {facet} changed but this step has no derivation for it"
                )

        built = {
            facet
            for pid in known_parents
            for facet in delta_built.get(pid, set())
            if facet not in derived
        }
        if mappings is not None:
            built |= {
                facet
                for facet, derivation in derived.items()
                if mappings.get(derivation.get("mapping"), {}).get("input_facets")
            }

        if sid not in snapshots:
            snapshots[sid] = snapshot
            order[sid] = index
            delta_built[sid] = built

    years: list[int] = []
    for checkpoint in ledger.get("checkpoints", []):
        year = checkpoint.get("simulation_year")
        target_id = checkpoint.get("snapshot")
        target = snapshots.get(target_id)
        if target is None:
            problems.append(f"checkpoint {year}: unknown snapshot {target_id}")
            continue
        if target.get("simulation_year") != year:
            problems.append(f"checkpoint {year}: snapshot belongs to another year")
        for entry in target.get("core_state", {}).get("facets", []):
            if (
                entry.get("facet") in delta_built[target_id]
                and "stored_object" not in entry
            ):
                problems.append(
                    f"checkpoint {year}: {entry.get('facet')} is derived from parent "
                    "facets but has no stored_object"
                )
        years.append(year)
    if years != sorted(set(years)):
        problems.append("checkpoint years must be unique and increasing")
    return problems


class LedgerConformancePlugin(ValidationPlugin):
    """Run ledger_problems alongside LinkML's shape validation.

    Pass the ledger's mapping catalog to also check derivation mappings.
    """

    def __init__(self, catalog: dict[str, Any] | None = None) -> None:
        self.catalog = catalog

    def process(
        self, instance: dict, context: ValidationContext
    ) -> Iterator[ValidationResult]:
        for message in ledger_problems(instance, self.catalog):
            yield ValidationResult(
                type="ledger-conformance",
                severity=Severity.ERROR,
                instance=instance,
                instantiates=context.target_class,
                message=message,
            )


def validate_ledger(
    ledger: Mapping[str, Any],
    catalog: Mapping[str, Any] | None = None,
    schema_path: str | Path | None = None,
) -> CheckResult:
    """Validate a PopulationLedger against LinkML schema rules and ledger invariants."""
    if schema_path is None:
        schema_path = (
            Path(__file__).parents[1] / "schema" / "core" / "population_ledger.yaml"
        )
    plugins = [
        JsonschemaValidationPlugin(closed=True),
        LedgerConformancePlugin(dict(catalog) if catalog is not None else None),
    ]
    report = Validator(str(schema_path), validation_plugins=plugins).validate(
        dict(ledger), "PopulationLedger"
    )
    diagnostics = []
    for result in report.results:
        code = (
            "LEDGER_CONFORMANCE_INVALID"
            if result.type == "ledger-conformance"
            else "LEDGER_SHAPE_INVALID"
        )
        diagnostics.append(Diagnostic(code, str(result.message), "error"))
    return CheckResult(tuple(diagnostics))
