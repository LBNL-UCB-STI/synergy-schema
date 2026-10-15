from __future__ import annotations

import re
from pathlib import Path

import tomllib

from zensical.config import parse_config


ROOT = Path(__file__).parents[1]
DOCS = ROOT / "docs"


def _nav() -> list[dict[str, object]]:
    return tomllib.loads((ROOT / "zensical.toml").read_text())["project"]["nav"]


def _leaf_targets(items: list[dict[str, object]]) -> list[tuple[str, str]]:
    leaves: list[tuple[str, str]] = []
    for item in items:
        label, value = next(iter(item.items()))
        if isinstance(value, list):
            leaves.extend(_leaf_targets(value))
        else:
            leaves.append((label, value))
    return leaves


def test_navigation_has_approved_sections_and_existing_leaves() -> None:
    nav = _nav()
    assert [next(iter(item)) for item in nav] == [
        "Overview",
        "Shared structure",
        "Cross-model mappings",
        "Workflow structures",
        "Design rationale",
        "Model contract review",
        "Schema reference",
    ]
    expected = {
        "Three-step pilot",
        "Day-zero manifest",
        "One-year mapping handshake",
        "Mapping at a glance",
        "Costs and exit",
        "Why LinkML",
        "Why not one big table?",
        "Are flat files enough?",
        "How Synergy is organized",
        "Scenario definitions and trajectories",
        "Population snapshots and artifact identity",
        "Canonical tabular content digests",
        "Population trajectory realization identity",
        "Core schema UML",
        "Glossary",
        "PILATES post-ATLAS population",
        "POLARIS translated population",
        "Contract at a Glance",
        "Architecture & UML",
        "Database ER Diagrams",
        "Population identity",
        "Mapping meaning, implementation, and lineage",
        "Scenario compatibility",
        "Model contract review",
        "ATLAS",
        "ActivitySim",
        "UrbanSim",
        "POLARIS",
        "DEMOS",
        "Complete generated reference",
    }
    leaves = _leaf_targets(nav)
    assert expected <= {label for label, _ in leaves}
    for _label, target in leaves:
        if target.startswith("schema/"):
            continue
        assert (DOCS / target).is_file()


def test_docs_configuration_parses_markdown_inside_linkml_html_wrappers() -> None:
    """Generated LinkML reference pages use ``<div markdown=\"1\">`` wrappers."""
    config = parse_config(str(ROOT / "zensical.toml"))

    assert "md_in_html" in config["markdown_extensions"]


def test_realization_identity_contract_is_public_and_release_ready() -> None:
    """Downstream consumers have a stable, non-internal contract to cite."""
    contract = (DOCS / "shared-structure/realization-identity.md").read_text()
    for text in (
        "synergy:scenario-realization:population-trajectory-v1",
        "RFC 8785 JSON Canonicalization Scheme (JCS)",
        "population_trajectory_v1.jcs.json",
        "4651ff4cb5471f36c9632df1e3d3ec37a9ff81352cc2d1990cac6a3b2fd919b5",
        "independently supplied expected identity",
        "2**53 - 1",
        "Unicode scalar values",
    ):
        assert text in contract


def test_glossary_explains_core_terms_and_common_distinctions() -> None:
    overview = (DOCS / "index.md").read_text()
    organization = (DOCS / "shared-structure/index.md").read_text()
    assert "[Glossary](shared-structure/glossary.md)" in overview
    assert "[Glossary](glossary.md)" in organization

    glossary = (DOCS / "shared-structure/glossary.md").read_text()
    for heading in (
        "## Shared scenarios and changing populations",
        "## Schemas, contracts, profiles, and native records",
        "## Files, bundles, manifests, receipts, and provenance",
        "## Mappings, implementations, and residue",
        "## Ownership and authority",
        "## Digests, review states, and compatibility",
    ):
        assert heading in glossary
    for term in (
        "### Scenario definition",
        "### Population trajectory",
        "### Population snapshot",
        "### Interface",
        "### Workflow profile",
        "### Native record",
        "### Native contract",
        "### Native contract element reference",
        "### Artifact",
        "### Evidence",
        "### Receipt",
        "### Translation contract",
        "### Mapping residue",
        "### Review record",
        "### Semantic digest",
        "### Compatible with gaps",
    ):
        assert term in glossary
    assert "| Often confused | How they differ |" in glossary
    assert "## What a binding means here" in glossary
    assert (
        "| Binding or relationship | Connects | Maintained by | What it establishes |"
        in glossary
    )
    assert "| Responsibility | Decision authority |" in glossary
    assert "does not transfer authority over meaning" in glossary
    assert "not a Synergy-owned replacement for the" in glossary
    assert "model's schema" in glossary
    assert "catalog → element → binding" in glossary
    assert "supports a bounded claim" in glossary
    assert "source_owner" in glossary
    assert "target_owner" in glossary
    assert "semantic_content_digest" in glossary
    assert "`semantic_owner`" not in glossary


def test_concept_heavy_guides_link_selected_first_uses_to_the_glossary() -> None:
    expected_links = {
        "shared-structure/scenario-definitions-and-trajectories.md": (
            "[scenario definition](glossary.md#scenario-definition)",
            "[population trajectory](glossary.md#population-trajectory)",
        ),
        "workflow-structures/index.md": (
            "[workflow profile](../shared-structure/glossary.md#workflow-profile)",
            "[model-native records](../shared-structure/glossary.md#native-record)",
        ),
        "cross-model-mappings/mapping-lineage.md": (
            "[translation contract](../shared-structure/glossary.md#translation-contract)",
            "[mapping residue](../shared-structure/glossary.md#mapping-residue)",
        ),
        "bring-an-existing-mapping/one-year-mapping-handshake.md": (
            "[receipt](../shared-structure/glossary.md#receipt)",
            "[draft](../shared-structure/glossary.md#draft)",
        ),
    }
    for relative_path, links in expected_links.items():
        page = (DOCS / relative_path).read_text()
        for link in links:
            assert link in page


def test_overview_explains_the_shared_universe_and_why_records_matter() -> None:
    overview = (DOCS / "index.md").read_text()
    assert overview.startswith("# Synergy Schema\n\nA transportation modeling workflow")
    for heading in (
        "## The coordination problem",
        "## One shared universe, several modeling systems",
        "## What Synergy records, and why",
        "## Scope and limits",
        "## How the documentation builds",
    ):
        assert heading in overview
    assert "declared consistency" in overview
    assert "Interface descriptions" in overview
    assert "Review records" in overview
    assert "Evidence" in overview
    assert "evidence from the" in overview
    assert "PILATES modeling pipeline" in overview
    assert "and POLARIS" in overview
    assert "keep their own schemas" in overview
    assert "legitimately produce different" in overview
    assert "model-specific results" in overview
    assert "| Documentation area | Question it answers |" in overview
    assert "Bring an existing mapping" in overview
    assert "one-year mapping handshake" in overview


def test_public_guides_avoid_second_person_and_attestation_language() -> None:
    maintained_pages = {
        target
        for _label, target in _leaf_targets(_nav())
        if not target.startswith("schema/")
    }
    second_person = re.compile(r"\b(?:you|your|yours|yourself)\b", re.IGNORECASE)
    attestation = re.compile(r"\battest\w*\b", re.IGNORECASE)

    for relative_path in maintained_pages:
        page = (DOCS / relative_path).read_text()
        assert second_person.search(page) is None, relative_path
        assert attestation.search(page) is None, relative_path


def test_adoption_guides_are_honest_about_scope_cost_and_exit() -> None:
    adoption = "\n".join(
        path.read_text() for path in (DOCS / "bring-an-existing-mapping").glob("*.md")
    )
    for heading in ("Inputs", "What stays unchanged", "First useful result"):
        assert heading in adoption
    assert "contract-at-a-glance" in adoption
    assert "discovery evidence" in adoption
    assert "Automatic receipt emission" in adoption
    assert "Work stops" in adoption
    assert "consumer's existing import or dry-run path" in adoption
    assert "For repeated exchanges or material mapping changes" in adoption
    assert "five business days" not in adoption
    assert "payloads, readable review tables, and" in adoption
    assert "historical incidents" in adoption
    assert "Flat files plus a README can be enough" in adoption


def test_workflow_and_compatibility_guides_state_boundaries_and_decisions() -> None:
    pilates = (DOCS / "workflow-structures/pilates.md").read_text()
    polaris = (DOCS / "workflow-structures/polaris.md").read_text()
    for page in (pilates, polaris):
        for heading in ("## Current", "## Proposed", "## Out of scope"):
            assert heading in page
    assert "native records are partial" in polaris
    assert "runtime adapter enforcement is future work" in polaris
    compatibility = (
        DOCS / "cross-model-mappings/scenario-compatibility.md"
    ).read_text()
    for term in ("No conflict", "Gap", "Override", "Conflict"):
        assert term in compatibility
    assert "| Situation | Recorded decision | Consequence |" in compatibility


def test_docs_build_generates_identity_diagram_and_contract_review_copy() -> None:
    script = (ROOT / "scripts/preview-schema-docs").read_text()
    assert "core_schema_diagram" in script
    assert "deliverable_1_diagram" in script
    assert "mermaid_diagram" in script
    assert "interactive_diagram" in script
    assert "contract-at-a-glance.md" in script
    ci = (ROOT / ".github/workflows/ci.yml").read_text()
    assert (
        "UV_CACHE_DIR=/tmp/synergy-schema-uv-cache scripts/preview-schema-docs build"
        in ci
    )


def test_shared_structure_explains_core_agreement_boundary() -> None:
    page = (DOCS / "shared-structure/index.md").read_text()
    assert "## The agreement boundary" in page
    assert "claim may be" in page
    assert "two authoritative claims cannot" in page
    assert "does not prevent disagreement" in page
    assert "core-schema-uml.md" in page
    snapshot_page = (
        DOCS / "shared-structure/population-snapshots-and-artifact-identity.md"
    ).read_text()
    assert "#core-entity-tables" in snapshot_page


def test_maintained_surfaces_avoid_ambiguous_release_jargon() -> None:
    forbidden = "semantic" + " release"
    roots = (DOCS, ROOT / "src", ROOT / "examples")
    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file() or "superpowers" in path.parts:
                continue
            if path.is_relative_to(DOCS / "schema"):
                continue
            assert forbidden not in path.read_text(errors="ignore").lower(), path

    handshake = (
        DOCS / "bring-an-existing-mapping/one-year-mapping-handshake.md"
    ).read_text()
    assert "exact same mapping content" in handshake
    assert "pinned source and target interface catalogs" in handshake
    assert "Review of the mapping meaning" in handshake
    lineage = (DOCS / "cross-model-mappings/mapping-lineage.md").read_text()
    assert "| Record | Question it answers |" in lineage
    assert "approved rules, wrong script" in lineage
