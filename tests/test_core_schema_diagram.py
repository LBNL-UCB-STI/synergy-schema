from pathlib import Path

from synergy_schema.core_schema_diagram import render_core_schema_uml


ROOT = Path(__file__).parents[1]
CORE = ROOT / "src" / "synergy_schema" / "schema" / "core"


def test_core_schema_uml_contains_every_core_class_and_key_relationships() -> None:
    rendered = render_core_schema_uml(CORE)

    expected_classes = {
        "ScenarioDefinitionReference",
        "ScenarioAssumption",
        "ScenarioDefinition",
        "ScenarioAssumptionBinding",
        "ModelScenarioBinding",
        "PopulationSnapshot",
        "HouseholdState",
        "PersonState",
        "HouseholdMembership",
        "VehicleState",
        "HouseholdVehicleAssignment",
        "SkippedPopulationYear",
        "PopulationTrajectory",
        "ProducingRunReference",
        "ImmutableArtifactIdentity",
        "PhysicalArtifactReference",
        "SchemaContractReference",
        "HandoffBundleMember",
        "HandoffBundle",
        "NativeContractCatalogReference",
        "NativeContractElementReference",
    }
    for class_name in expected_classes:
        assert f"class {class_name}" in rendered
    assert rendered.count("classDiagram") == 7
    assert rendered.count("```mermaid") == 8
    assert "flowchart LR" in rendered
    for heading in (
        "## Scenario definitions and bindings",
        "## Population snapshots and relationships",
        "## Population trajectories",
        "## Handoff and artifact references",
        "## References into model-owned interfaces",
    ):
        assert heading in rendered
    assert "PopulationTrajectory" in rendered and "PopulationSnapshot" in rendered
    assert "HouseholdMembership" in rendered and "PersonState" in rendered
    assert "HouseholdMembership" in rendered and "HouseholdState" in rendered
    assert "HandoffBundle" in rendered and "HandoffBundleMember" in rendered
    assert (
        "ModelScenarioBinding" in rendered and "ScenarioDefinitionReference" in rendered
    )
    assert "document nesting, not team ownership" in rendered
    assert "Catalog → element → binding" in rendered
    assert "does not copy the model's runtime schema" in rendered
    assert "ScenarioAssumptionBinding --> NativeContractElementReference" in rendered
    assert "### Population relationship overview" in rendered
    assert "HouseholdMembership --> PersonState : person_state_ref" in rendered
    assert "HouseholdMembership --> HouseholdState : household_state_ref" in rendered
    assert "HouseholdVehicleAssignment --> VehicleState : vehicle_state_ref" in rendered
    assert (
        "HouseholdVehicleAssignment --> HouseholdState : household_state_ref"
        in rendered
    )


def test_core_schema_uml_is_deterministic() -> None:
    assert render_core_schema_uml(CORE) == render_core_schema_uml(CORE)
