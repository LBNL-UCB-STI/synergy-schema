from __future__ import annotations

from pathlib import Path

import tomllib

import docs_macros


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
        "Proof of concept",
        "Bring an existing mapping",
        "Design rationale",
        "Shared structure",
        "Workflow structures",
        "Cross-model mappings",
        "Schema reference",
    ]
    expected = {
        "A population that changes over three years",
        "What the checker catches",
        "Day-zero manifest",
        "One-year mapping handshake",
        "Contract at a glance",
        "Costs and exit",
        "Why LinkML",
        "Why not one big table?",
        "Are flat files enough?",
        "Schema organization",
        "Scenario definitions and trajectories",
        "Population snapshots and artifact identity",
        "Population trajectory realization identity",
        "Core schema UML",
        "Glossary",
        "PILATES post-ATLAS population",
        "POLARIS translated population",
        "Population identity",
        "Translation contract, residue, and lineage",
        "Scenario compatibility",
        "Complete generated reference",
    }
    leaves = _leaf_targets(nav)
    assert expected <= {label for label, _ in leaves}
    for _label, target in leaves:
        if target.startswith("schema/"):
            continue
        assert (DOCS / target).is_file()


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
        "### Workflow profile",
        "### Native record",
        "### Native contract",
        "### Native contract element reference",
        "### Artifact",
        "### Receipt",
        "### Translation contract",
        "### Mapping residue",
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
    assert "does not transfer semantic ownership" in glossary
    assert "not a Synergy-owned replacement for the" in glossary
    assert "model's schema" in glossary
    assert "catalog → element → binding" in glossary


def test_concept_heavy_guides_link_selected_first_uses_to_the_glossary() -> None:
    expected_links = {
        "shared-structure/scenario-definitions-and-trajectories.md": (
            "[scenario definition](glossary.md#scenario-definition)",
            "[population trajectory](glossary.md#population-trajectory)",
        ),
        "workflow-structures/index.md": (
            "[workflow profiles](../shared-structure/glossary.md#workflow-profile)",
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


def test_overview_and_proof_make_the_two_newcomer_actions_clear() -> None:
    overview = (DOCS / "index.md").read_text()
    assert overview.startswith("# Synergy Schema\n\nTransportation modeling studies")
    for heading in (
        "## Why this project exists",
        "## What Synergy adds",
        "## What it does not replace",
        "## What is in these docs",
        "## Where to start",
    ):
        assert heading in overview
    assert "PILATES modeling pipeline" in overview
    assert "and POLARIS" in overview
    assert "keep their own schemas" in overview
    assert "legitimately produce different" in overview
    assert "model-specific results" in overview
    assert "| Documentation area | What you will find |" in overview
    assert "Bring an existing mapping" in overview
    assert "three-year proof" in overview

    proof = (DOCS / "proof-of-concept/index.md").read_text()
    for reference in (
        "ScenarioDefinition",
        "PopulationTrajectory",
        "HouseholdState",
        "PersonState",
        "Vehicle",
        "ConsistProvenanceDocument",
    ):
        assert reference in proof
    commands = (DOCS / "proof-of-concept/check-the-showcase.md").read_text()
    assert "examples/evolving_population" in commands
    assert "exit 0" in commands
    assert "evolving_population_broken_scenario" in commands
    assert "evolving_population_broken_artifact_identity" in commands
    assert "exit 1" in commands
    assert "SCENARIO_DIGEST_MISMATCH" in commands
    assert "ARTIFACT_IDENTITY_MISMATCH" in commands


def test_checker_page_displays_tables_from_the_showcase_fixtures() -> None:
    page = (DOCS / "proof-of-concept/check-the-showcase.md").read_text()
    for tab in (
        '=== "Population evolution"',
        '=== "Scenario bindings"',
        '=== "Broken checks"',
    ):
        assert tab in page
    rendered = "\n".join(
        (
            docs_macros.showcase_snapshot_summary_table(),
            docs_macros.showcase_person_history_table(),
            docs_macros.showcase_household_lineage_table(),
            docs_macros.showcase_vehicle_history_table(),
            docs_macros.showcase_scenario_assumptions_table(),
            docs_macros.showcase_bindings_table(),
            docs_macros.showcase_broken_scenario_table(),
            docs_macros.showcase_broken_artifact_table(),
        )
    )
    for macro in (
        "{{ showcase_snapshot_summary_table(4) }}",
        "{{ showcase_person_history_table(4) }}",
        "{{ showcase_household_lineage_table(4) }}",
        "{{ showcase_vehicle_history_table(4) }}",
        "{{ showcase_scenario_assumptions_table(4) }}",
        "{{ showcase_bindings_table(4) }}",
        "{{ showcase_broken_scenario_table(4) }}",
        "{{ showcase_broken_artifact_table(4) }}",
    ):
        assert macro in page
    for value in (
        "person:new-2030",
        "household:family-a-2",
        "compatible_with_gaps",
        "zev_policy",
        "SCENARIO_DIGEST_MISMATCH",
        "ARTIFACT_IDENTITY_MISMATCH",
    ):
        assert value in rendered
    assert "core-population-evolution.yaml" in page
    assert "zev-model-bindings.yaml" in page
    assert "Every person record in this synthetic fixture is shown" in page
    assert "does not declare person-to-household membership" in page
    assert "Household state records" in rendered
    assert "Not declared in this fixture" in rendered
    assert "Every assumption binding declared" in page
    assert "synthetic fixture is shown as well" in page
    assert (
        "All digest values below come directly from the valid and broken fixtures"
        in page
    )
    assert "Shared value" in rendered
    assert "Valid declaration" in rendered
    assert "Broken declaration" in rendered
    assert "broken-scenario-definition.yaml" in page
    assert "broken-polaris-bundle.yaml" in page


def test_adoption_guides_are_honest_about_scope_cost_and_exit() -> None:
    adoption = "\n".join(
        path.read_text() for path in (DOCS / "bring-an-existing-mapping").glob("*.md")
    )
    for heading in ("What we ask", "What we do not ask", "What you get", "Timeline"):
        assert heading in adoption
    assert "contract-at-a-glance" in adoption
    assert "discovery-only" in adoption
    assert "automatic-emission" in adoption
    assert "kill criterion" in adoption
    assert "minutes, not hours" in adoption
    assert "five business days" in adoption
    assert "payloads, readable tables, and inert manifests" in adoption
    assert "historical incidents" in adoption
    assert "flat files plus a README can be enough" in adoption


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
    assert "| Situation | Decision |" in compatibility


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
    assert "Core classes hold shared assertions" in page
    assert "allowed to be absent but not" in page
    assert "contradictory when two implementations" in page
    assert "does not make disagreement impossible" in page
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
    assert "pinned source and target catalogs" in handshake
    assert "This approval concerns what the translation means" in handshake
    lineage = (DOCS / "cross-model-mappings/mapping-lineage.md").read_text()
    assert "| Document | Question it answers |" in lineage
    assert "approved rules, wrong script" in lineage
