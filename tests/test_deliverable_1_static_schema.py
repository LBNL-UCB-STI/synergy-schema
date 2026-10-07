"""Contract tests for Deliverable 1 static schema bundle."""

from pathlib import Path
from linkml_runtime.utils.schemaview import SchemaView

SCHEMA_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "synergy_schema"
    / "schema"
    / "deliverable_1_static_schema.yaml"
)


def test_deliverable_1_schema_contains_all_models_and_channels() -> None:
    view = SchemaView(str(SCHEMA_PATH))
    classes = set(view.all_classes())

    # UrbanSim
    assert "UrbanSimBlockMarginals" in classes
    assert "BlockToTazMapping" in classes
    assert "UrbanSimZonalTotals" in classes

    # DEMOS
    assert "DemosPolarisMappedHouseholdExampleV1" in classes
    assert "DemosPolarisMappedPersonExampleV1" in classes

    # ATLAS
    assert "AtlasHouseholdFleetOutputExampleV1" in classes
    assert "AtlasVehicleFleetOutputExampleV1" in classes

    # POLARIS Demand & Skims
    assert "PolarisDemandDatabaseV1Household" in classes
    assert "PolarisDemandDatabaseV1Person" in classes
    assert "PolarisDemandDatabaseV1Vehicle" in classes
    assert "InputNetworkSkims" in classes
    assert "NextYearNetworkSkims" in classes

    # Handoff contracts
    assert "SingleYearModelHandoffPackage" in classes
    assert "ModelHandoffChannel" in classes
    assert "CategoricalCrosswalkRule" in classes


def test_deliverable_1_enums() -> None:
    view = SchemaView(str(SCHEMA_PATH))
    enums = set(view.all_enums())

    assert "AtlasPowertrainEnum" in enums
    assert "AtlasBodyTypeEnum" in enums
    assert "AtlasVintageCategoryEnum" in enums
    assert "HandoffChannelType" in enums
    assert "FieldTransformationMode" in enums
    assert "ResidueKind" in enums
