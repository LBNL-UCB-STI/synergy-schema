from __future__ import annotations

from pathlib import Path

import tomllib


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


def test_overview_and_proof_make_the_two_newcomer_actions_clear() -> None:
    overview = (DOCS / "index.md").read_text()
    assert overview.startswith("# Synergy Schema\n\nShare a scenario")
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
    assert "contract-at-a-glance.md" in script
    ci = (ROOT / ".github/workflows/ci.yml").read_text()
    assert (
        "UV_CACHE_DIR=/tmp/synergy-schema-uv-cache scripts/preview-schema-docs build"
        in ci
    )
