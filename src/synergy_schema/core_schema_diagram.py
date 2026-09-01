"""Render a UML-style Mermaid diagram from every Synergy core class."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml


class CoreDiagramInputError(ValueError):
    """Raised when a core schema document cannot be rendered faithfully."""


def _core_documents(core_dir: Path) -> list[tuple[str, Mapping[str, object]]]:
    documents: list[tuple[str, Mapping[str, object]]] = []
    for path in sorted(core_dir.glob("*.yaml")):
        loaded: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, Mapping):
            raise CoreDiagramInputError(f"{path}: schema must be a mapping")
        documents.append((path.stem, loaded))
    if not documents:
        raise CoreDiagramInputError(f"{core_dir}: no core YAML schemas found")
    return documents


def _classes(document: Mapping[str, object], context: str) -> Mapping[str, object]:
    classes = document.get("classes")
    if not isinstance(classes, Mapping):
        raise CoreDiagramInputError(f"{context}: classes must be a mapping")
    return classes


def _attributes(class_definition: object, context: str) -> Mapping[str, object]:
    if not isinstance(class_definition, Mapping):
        raise CoreDiagramInputError(f"{context}: class definition must be a mapping")
    attributes = class_definition.get("attributes", {})
    if not isinstance(attributes, Mapping):
        raise CoreDiagramInputError(f"{context}: attributes must be a mapping")
    return attributes


def _attribute_definition(attribute: object, context: str) -> Mapping[str, object]:
    if not isinstance(attribute, Mapping):
        raise CoreDiagramInputError(f"{context}: attribute must be a mapping")
    return attribute


def _scalar_label(name: str, definition: Mapping[str, object]) -> str:
    range_name = str(definition.get("range", "string"))
    if definition.get("multivalued") is True:
        range_name += "[]"
    if definition.get("required") is not True:
        range_name += "?"
    return f"+{range_name} {name}"


def _target_multiplicity(definition: Mapping[str, object]) -> str:
    if definition.get("multivalued") is True:
        return "1..*" if definition.get("required") is True else "0..*"
    return "1" if definition.get("required") is True else "0..1"


MODULES = {
    "scenario_definition": (
        "Scenario definitions and bindings",
        "Shared assumptions and the declarations connecting them to native model settings.",
    ),
    "population_snapshot": (
        "Population snapshots and relationships",
        "Snapshot-scoped identities, household membership, and vehicle relationships.",
    ),
    "population_trajectory": (
        "Population trajectories",
        "Ordered snapshots and explicit records for requested years that were skipped.",
    ),
    "handoff_bundle": (
        "Handoff and artifact references",
        "Provider-neutral bundles, physical artifacts, schema contracts, and producing runs.",
    ),
    "native_contract": (
        "References into model-owned interfaces",
        "Pinned references to inventories of model-owned paths, keys, and columns.",
    ),
}


def _render_module_diagram(
    module_name: str,
    document: Mapping[str, object],
    all_classes: set[str],
) -> list[str]:
    lines = ["```mermaid", "classDiagram", "direction LR"]
    relationships: list[str] = []
    for class_name, class_definition in _classes(document, module_name).items():
        attributes = _attributes(class_definition, f"{module_name}.{class_name}")
        lines.append(f"  class {class_name} {{")
        for attribute_name, raw_definition in attributes.items():
            definition = _attribute_definition(
                raw_definition, f"{module_name}.{class_name}.{attribute_name}"
            )
            range_name = str(definition.get("range", "string"))
            if range_name in all_classes:
                arrow = (
                    "*--"
                    if definition.get("inlined") is True
                    or definition.get("inlined_as_list") is True
                    else "-->"
                )
                relationships.append(
                    f'  {class_name} "1" {arrow} "{_target_multiplicity(definition)}" '
                    f"{range_name} : {attribute_name}"
                )
            else:
                lines.append(f"    {_scalar_label(str(attribute_name), definition)}")
        lines.append("  }")
    lines.extend(sorted(relationships))
    lines.extend(["```", ""])
    return lines


def render_core_schema_uml(core_dir: Path) -> str:
    """Render a deterministic page containing every class in ``core_dir``."""
    loaded_documents = dict(_core_documents(core_dir))
    missing_modules = set(MODULES) - set(loaded_documents)
    if missing_modules:
        names = ", ".join(sorted(missing_modules))
        raise CoreDiagramInputError(f"missing core schema modules: {names}")
    all_classes: set[str] = set()
    for module_name, document in loaded_documents.items():
        all_classes.update(_classes(document, module_name))

    lines = [
        "# Core schema UML",
        "",
        "This generated page contains every class declared in the five core schema",
        "modules. The overview shows how the modules depend on one another; the",
        "smaller UML diagrams below show the complete scalar fields and typed",
        "relationships for one module at a time.",
        "",
        "## Module overview",
        "",
        "```mermaid",
        "flowchart LR",
        '  scenario["Scenario definitions"] --> native["Model-owned interface references"]',
        '  snapshot["Population snapshots"] --> scenario',
        '  trajectory["Population trajectories"] --> snapshot',
        '  trajectory --> handoff["Handoff and artifacts"]',
        "  native --> handoff",
        "```",
        "",
        "Each detailed diagram includes every class defined by that module. A",
        "referenced class from another module may appear as a name-only box; its",
        "fields are shown in its home module below.",
        "",
    ]
    for module_name, (title, description) in MODULES.items():
        lines.extend(
            [
                f"## {title}",
                "",
                description,
                "",
            ]
        )
        if module_name == "population_snapshot":
            lines.extend(
                [
                    "### Population relationship overview",
                    "",
                    "Households, persons, and vehicles are snapshot-scoped state",
                    "occurrences. Membership and vehicle assignment are explicit",
                    "relationship records; the schema does not infer a direct",
                    "person-to-household or vehicle-to-household link.",
                    "",
                    "```mermaid",
                    "classDiagram",
                    "direction LR",
                    "  HouseholdMembership --> PersonState : person_state_ref",
                    "  HouseholdMembership --> HouseholdState : household_state_ref",
                    "  HouseholdMembership --> PopulationSnapshot : population_snapshot_ref",
                    "  HouseholdVehicleAssignment --> VehicleState : vehicle_state_ref",
                    "  HouseholdVehicleAssignment --> HouseholdState : household_state_ref",
                    "  HouseholdVehicleAssignment --> PopulationSnapshot : population_snapshot_ref",
                    "  PersonState --> PopulationSnapshot : population_snapshot_ref",
                    "  HouseholdState --> PopulationSnapshot : population_snapshot_ref",
                    "  VehicleState --> PopulationSnapshot : population_snapshot_ref",
                    "  HouseholdState --> HouseholdState : predecessor_state_refs",
                    "```",
                    "",
                    "A state identifier names one occurrence in one snapshot. Optional",
                    "longitudinal references connect identity across snapshots; they do",
                    "not turn the occurrence record into a timeless master entity.",
                    "",
                    "### Complete fields and references",
                    "",
                ]
            )
        if module_name == "native_contract":
            lines.extend(
                [
                    "This module does not copy the model's runtime schema. It gives",
                    "shared documents a stable way to point into a model-owned",
                    "interface inventory without taking ownership of that interface.",
                    "",
                    "**Catalog → element → binding:**",
                    "",
                    "1. `NativeContractCatalogReference` pins one inventory revision",
                    "   and digest.",
                    "2. `NativeContractElementReference` names one typed path, key, or",
                    "   column inside that pinned inventory.",
                    "3. `ScenarioAssumptionBinding` or another mapping class explains",
                    "   how that native element relates to shared meaning.",
                    "",
                    "```mermaid",
                    "classDiagram",
                    "direction LR",
                    "  class ScenarioAssumptionBinding",
                    "  class NativeContractElementReference",
                    "  class NativeContractCatalogReference",
                    "  ScenarioAssumptionBinding --> NativeContractElementReference : native_element",
                    "  NativeContractElementReference *-- NativeContractCatalogReference : catalog",
                    "```",
                    "",
                    "See the [plain-language glossary](../shared-structure/glossary.md#native-contract)",
                    "for a concrete example and the ownership boundary.",
                    "",
                ]
            )
        lines.extend(
            _render_module_diagram(
                module_name, loaded_documents[module_name], all_classes
            )
        )
    lines.extend(
        [
            "",
            "A filled diamond means LinkML document nesting, not team ownership. A",
            "plain arrow means a typed reference whose target may require",
            "cross-document conformance checks. Multiplicities describe the field",
            "on the source class.",
            "",
            "The diagram is an orientation aid. The generated class pages remain",
            "authoritative for descriptions, annotations, validation boundaries, and",
            "enum values.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    """Write the generated core UML page."""
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("core_dir", type=Path)
    parser.add_argument("output_path", type=Path)
    args = parser.parse_args()
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(render_core_schema_uml(args.core_dir), encoding="utf-8")


if __name__ == "__main__":
    main()
