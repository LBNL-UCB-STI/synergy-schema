"""Render a collaborator-facing Mermaid map from population identity mappings."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml


class DiagramInputError(ValueError):
    """Raised when a population mapping cannot be rendered faithfully."""


def _mapping_value(mapping: Mapping[str, object], name: str, context: str) -> str:
    value = mapping.get(name)
    if not isinstance(value, str) or not value:
        raise DiagramInputError(f"{context}: {name} must be a non-empty string")
    return value


def _field_paths(mapping: Mapping[str, object], name: str, context: str) -> list[str]:
    value = mapping.get(name)
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(path, str) and path for path in value)
    ):
        raise DiagramInputError(f"{context}: {name} must be a list of field paths")
    return value


def _mermaid_text(value: str) -> str:
    return value.replace('"', "'")


def _render_mermaid(
    legs: list[tuple[str, str, str]],
    constructions: list[tuple[str, list[str], str, str]] | None = None,
) -> list[str]:
    node_ids: dict[str, str] = {}
    lines = ["```mermaid", "flowchart LR"]

    def node_id(path: str) -> str:
        if path not in node_ids:
            node_ids[path] = f"field_{len(node_ids) + 1}"
            lines.append(f'  {node_ids[path]}["{_mermaid_text(path)}"]')
        return node_ids[path]

    for source_path, target_path, edge_label in legs:
        lines.append(
            f'  {node_id(source_path)} -->|"{edge_label}"| {node_id(target_path)}'
        )
    for construction_id, source_paths, target_path, edge_label in constructions or []:
        construction_node = f"construction_{len(lines)}"
        lines.append(f'  {construction_node}["{_mermaid_text(construction_id)}"]')
        for source_path in source_paths:
            lines.append(f'  {node_id(source_path)} -->|"input"| {construction_node}')
        lines.append(
            f'  {construction_node} -->|"{edge_label}"| {node_id(target_path)}'
        )
    lines.extend(["```", ""])
    return lines


def render_cross_model_identity_map(mappings: Mapping[str, object]) -> str:
    """Render one deterministic Mermaid page from paired population mapping legs."""
    stable_identity_legs: list[tuple[str, str, str]] = []
    derived_and_scoped_legs: list[tuple[str, str, str]] = []
    identity_constructions: list[tuple[str, list[str], str, str]] = []

    for representation_name in sorted(mappings):
        representation = mappings[representation_name]
        context = f"mapping {representation_name}"
        if not isinstance(representation, Mapping):
            raise DiagramInputError(f"{context} must be a mapping")
        slot_mappings = representation.get("slot_mappings")
        if not isinstance(slot_mappings, list):
            raise DiagramInputError(f"{context}: slot_mappings must be a list")

        for index, slot_mapping in enumerate(slot_mappings, start=1):
            slot_context = f"{context} slot mapping {index}"
            if not isinstance(slot_mapping, Mapping):
                raise DiagramInputError(f"{slot_context} must be a mapping")
            source_paths = _field_paths(slot_mapping, "source_paths", slot_context)
            target_paths = _field_paths(slot_mapping, "target_paths", slot_context)
            if len(source_paths) != len(target_paths):
                raise DiagramInputError(
                    f"{slot_context} requires aligned source_paths and target_paths"
                )
            mapping_status = _mapping_value(
                slot_mapping, "mapping_status", slot_context
            )
            identity_role = _mapping_value(slot_mapping, "identity_role", slot_context)
            cardinality = _mapping_value(
                slot_mapping, "relationship_cardinality", slot_context
            )
            value_stability = _mapping_value(
                slot_mapping, "value_stability", slot_context
            )
            edge_label = _mermaid_text(
                f"{mapping_status} | {identity_role} | {cardinality}"
            )
            destination = (
                stable_identity_legs
                if value_stability == "preserved"
                and identity_role in {"entity_identifier", "relationship_foreign_key"}
                else derived_and_scoped_legs
            )

            for source_path, target_path in zip(
                source_paths, target_paths, strict=True
            ):
                destination.append((source_path, target_path, edge_label))

        constructions = representation.get("identity_constructions", [])
        if not isinstance(constructions, list):
            raise DiagramInputError(f"{context}: identity_constructions must be a list")
        for index, construction in enumerate(constructions, start=1):
            construction_context = f"{context} identity construction {index}"
            if not isinstance(construction, Mapping):
                raise DiagramInputError(f"{construction_context} must be a mapping")
            source_paths = _field_paths(
                construction, "source_paths", construction_context
            )
            if len(source_paths) < 2:
                raise DiagramInputError(
                    f"{construction_context} requires at least two source_paths"
                )
            target_path = _mapping_value(
                construction, "target_path", construction_context
            )
            construction_id = _mapping_value(construction, "id", construction_context)
            mapping_status = _mapping_value(
                construction, "mapping_status", construction_context
            )
            identity_role = _mapping_value(
                construction, "identity_role", construction_context
            )
            cardinality = _mapping_value(
                construction, "relationship_cardinality", construction_context
            )
            edge_label = _mermaid_text(
                f"{mapping_status} | {identity_role} | {cardinality}"
            )
            identity_constructions.append(
                (construction_id, source_paths, target_path, edge_label)
            )

    lines = [
        "# Cross-model population identity map",
        "",
        "This generated map shows semantic relationships declared in the population "
        "identity mapping manifest. Each edge label is `mapping status | identity "
        "role | cardinality`; it complements native LinkML reference edges rather "
        "than treating same-named fields as foreign keys.",
        "",
        "## Stable identity and household membership",
        "",
        "Preserved entity identifiers and person-to-household foreign keys form "
        "the cross-model population continuity chain.",
        "",
    ]
    lines.extend(_render_mermaid(stable_identity_legs))
    lines.extend(
        [
            "## Derived, renamed, and artifact-scoped mappings",
            "",
            "Derived values, local ordinals, aliases, geographic lookups, and "
            "artifact-scoped identities provide supporting context without crowding "
            "the stable population chain.",
            "",
        ]
    )
    lines.extend(_render_mermaid(derived_and_scoped_legs, identity_constructions))
    lines.extend(
        [
            "The mapping manifest remains the authoritative record for transformation "
            "details and implementation evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def write_cross_model_identity_map(
    mappings: Mapping[str, object], output_path: Path
) -> None:
    """Write the rendered diagram page, creating its parent directory when needed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_cross_model_identity_map(mappings), encoding="utf-8")


def main() -> None:
    """Render a population identity Mermaid page from a YAML mapping manifest."""
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("input_path", type=Path)
    parser.add_argument("output_path", type=Path)
    args = parser.parse_args()

    loaded: Any = yaml.safe_load(args.input_path.read_text(encoding="utf-8"))
    if not isinstance(loaded, Mapping):
        raise DiagramInputError("mapping document must be a mapping")
    write_cross_model_identity_map(loaded, args.output_path)


if __name__ == "__main__":
    main()
