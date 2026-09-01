from __future__ import annotations

import re
from pathlib import Path

import tomllib

import docs_macros
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


def test_navigation_has_the_approved_eight_sections_and_existing_leaves() -> None:
    nav = _nav()
    assert [next(iter(item)) for item in nav] == [
        "Overview",
        "Shared structure",
        "Proof of concept",
        "Cross-model mappings",
        "Workflow structures",
        "Bring an existing mapping",
        "Design rationale",
        "Schema reference",
    ]
    expected = {
        "A population that changes over three years",
        "Following the proof from claim to file",
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
        "Population trajectory realization identity",
        "Core schema UML",
        "Glossary",
        "PILATES post-ATLAS population",
        "POLARIS translated population",
        "Population identity",
        "Mapping meaning, implementation, and lineage",
        "Scenario compatibility",
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
        "## Why the difficult records matter",
        "## How Synergy organizes the answer",
        "## Scope and limits",
        "## How the documentation builds",
    ):
        assert heading in overview
    assert "same shared universe" in overview
    assert "Interface descriptions" in overview
    assert "Review records" in overview
    assert "Evidence" in overview
    assert "this claim checkable" in overview
    assert "PILATES modeling pipeline" in overview
    assert "and POLARIS" in overview
    assert "keep their own schemas" in overview
    assert "legitimately produce different" in overview
    assert "model-specific results" in overview
    assert "| Documentation area | Question it answers |" in overview
    assert "Bring an existing mapping" in overview
    assert "Three-year proof" in overview


def test_public_guides_avoid_second_person_and_attestation_language() -> None:
    maintained_pages = {
        target
        for _label, target in _leaf_targets(_nav())
        if not target.startswith("schema/")
    }
    maintained_pages.add("pilates/post-atlas-population-bundle.md")
    second_person = re.compile(r"\b(?:you|your|yours|yourself)\b", re.IGNORECASE)
    attestation = re.compile(r"\battest\w*\b", re.IGNORECASE)

    for relative_path in maintained_pages:
        page = (DOCS / relative_path).read_text()
        assert second_person.search(page) is None, relative_path
        assert attestation.search(page) is None, relative_path


def test_proof_uses_the_executable_showcase_and_preserves_scope() -> None:
    proof = (DOCS / "proof-of-concept/index.md").read_text()
    normalized_proof = " ".join(proof.split())
    for reference in (
        "ScenarioDefinition",
        "PopulationTrajectory",
        "HouseholdState",
        "PersonState",
        "Vehicle",
        "ConsistProvenanceDocument",
    ):
        assert reference in proof
    for idea in (
        "same shared universe",
        "Evidence",
        "interfaces",
        "review records",
        "not a deployed PILATES or POLARIS runtime",
    ):
        assert idea in normalized_proof
    commands = (DOCS / "proof-of-concept/check-the-showcase.md").read_text()
    assert "examples/evolving_population/baseline" in commands
    assert "examples/evolving_population/zev" in commands
    assert "exit 0" in commands
    assert "evolving_population_broken_scenario" in commands
    assert "evolving_population_broken_artifact_identity" in commands
    assert "exit 1" in commands
    assert "SCENARIO_DIGEST_MISMATCH" in commands
    assert "ARTIFACT_IDENTITY_MISMATCH" in commands


def test_checker_page_displays_tables_from_the_showcase_fixtures() -> None:
    page = (DOCS / "proof-of-concept/check-the-showcase.md").read_text()
    for heading in (
        "## The population over time",
        "## Shared identity and model-owned results",
        "## From a shared assumption to an exact file",
        "## What the proof establishes",
        "## Deliberately broken exchanges",
    ):
        assert heading in page
    rendered = "\n".join(
        (
            docs_macros.showcase_population_timeline_table(),
            docs_macros.showcase_branch_comparison_table(),
            docs_macros.showcase_scenario_assumptions_table(),
            docs_macros.showcase_bindings_table(),
            docs_macros.showcase_evidence_trace_table(),
            docs_macros.showcase_status_ladder_table(),
            docs_macros.showcase_broken_scenario_table(),
            docs_macros.showcase_broken_artifact_table(),
        )
    )
    for macro in (
        "{{ showcase_population_timeline_table() }}",
        "{{ showcase_branch_comparison_table() }}",
        "{{ showcase_scenario_assumptions_table(4) }}",
        "{{ showcase_bindings_table(4) }}",
        "{{ showcase_evidence_trace_table() }}",
        "{{ showcase_status_ladder_table() }}",
        "{{ showcase_broken_scenario_table(4) }}",
        "{{ showcase_broken_artifact_table(4) }}",
    ):
        assert macro in page
    for value in (
        "person:synthetic-evolving:new-2030",
        "household-state:synthetic-evolving-2030:family-a-2",
        "compatible_with_gaps",
        "zev_policy",
        "SCENARIO_DIGEST_MISMATCH",
        "ARTIFACT_IDENTITY_MISMATCH",
    ):
        assert value in rendered
    assert "core-population-evolution.yaml" in page
    assert "zev-model-bindings.yaml" in page
    assert "Every person state has an explicit household membership" in page
    assert "does not declare person-to-household membership" not in page
    assert "Not declared in this fixture" not in rendered
    assert "review records" in page
    assert "Evidence" in page
    assert (
        "All digest values below come directly from the valid and broken fixtures"
        in page
    )
    assert "Shared value" in rendered
    assert "Valid declaration" in rendered
    assert "Broken declaration" in rendered
    assert "broken-scenario-definition.yaml" in page
    assert "broken-polaris-bundle.yaml" in page
    assert "blob/expand-schema" not in page
    assert "blob/main" in page


def test_evolving_population_views_are_registered_and_fixture_backed() -> None:
    registered: dict[str, object] = {}

    class Environment:
        def macro(self, function: object) -> None:
            registered[function.__name__] = function  # type: ignore[attr-defined]

    docs_macros.define_env(Environment())
    names = {
        "showcase_population_timeline_table",
        "showcase_branch_comparison_table",
        "showcase_evidence_trace_table",
        "showcase_status_ladder_table",
    }
    assert names <= registered.keys()
    rendered = "\n".join(
        registered[name]()
        for name in sorted(names)  # type: ignore[operator]
    )
    for value in (
        "person:synthetic-evolving:alex",
        "battery_electric",
        "vehicle_adoption.zev_policy",
        "manual_discovery",
        "Schema-valid structure",
        "6 collections",
        "Cross-document checker boundary",
        "complete / complete",
        "Draft mapping review",
        "review_records=0",
        "Compatibility gap",
        "Production evidence not claimed",
    ):
        assert value in rendered


def test_adoption_guides_are_honest_about_scope_cost_and_exit() -> None:
    adoption = "\n".join(
        path.read_text() for path in (DOCS / "bring-an-existing-mapping").glob("*.md")
    )
    for heading in ("Inputs", "What stays unchanged", "Outputs", "Typical timing"):
        assert heading in adoption
    assert "contract-at-a-glance" in adoption
    assert "discovery evidence" in adoption
    assert "Automatic receipt emission" in adoption
    assert "Work stops" in adoption
    assert "minutes, not hours" in adoption
    assert "five business days" in adoption
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
    assert "cross_model_identity_diagram" in script
    assert "core_schema_diagram" in script
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
    assert "#population-relationship-overview" in snapshot_page


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
