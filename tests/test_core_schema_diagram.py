from pathlib import Path

from synergy_schema.core_schema_diagram import render_core_schema_uml


ROOT = Path(__file__).parents[1]
CORE = ROOT / "src" / "synergy_schema" / "schema" / "core"


def test_core_schema_uml_contains_every_core_class_and_key_relationships() -> None:
    rendered = render_core_schema_uml(CORE)

    expected_classes = {
        # scenario_definition
        "ScenarioDefinitionReference",
        "ScenarioAssumption",
        "ScenarioDefinition",
        "ScenarioAssumptionBinding",
        "ModelScenarioBinding",
        # core_tables
        "CoreHousehold",
        "CorePerson",
        "CoreHouseholdMembership",
        "CoreVehicle",
        "CoreHouseholdLocation",
        "CorePersonDemographics",
        "CoreHouseholdDwelling",
        "CorePersonSchooling",
        "CorePersonEmployment",
        # facet_mappings
        "ModelView",
        "CoreFacetMapping",
        "CoreFieldFromView",
        "FacetDerivation",
        "CoreFacetMappingCatalog",
        # population_ledger
        "CoreFacetEntry",
        "CoreState",
        "ModelStep",
        "PopulationSnapshot",
        "PopulationCheckpoint",
        "PopulationLedger",
        # handoff_bundle
        "ProducingRunReference",
        "ImmutableArtifactIdentity",
        "PhysicalArtifactReference",
        "SchemaContractReference",
        "HandoffBundleMember",
        "HandoffBundle",
        # native_contract
        "NativeContractCatalogReference",
        "NativeContractElementReference",
    }
    for class_name in expected_classes:
        assert f"class {class_name}" in rendered
    assert "flowchart LR" in rendered
    for heading in (
        "## Scenario definitions and bindings",
        "## Core entity tables",
        "## Facet mappings and derivations",
        "## Population ledger and state snapshots",
        "## Handoff and artifact references",
        "## References into model-owned interfaces",
    ):
        assert heading in rendered

    assert "CoreHouseholdMembership --> CorePerson : person_id" in rendered
    assert "CoreHouseholdMembership --> CoreHousehold : household_id" in rendered
    assert "CoreVehicle --> CoreHousehold : household_id" in rendered
    assert "PopulationLedger *-- PopulationCheckpoint : checkpoints" in rendered
    assert "PopulationSnapshot *-- CoreState : state" in rendered


def test_core_schema_uml_is_deterministic() -> None:
    assert render_core_schema_uml(CORE) == render_core_schema_uml(CORE)
