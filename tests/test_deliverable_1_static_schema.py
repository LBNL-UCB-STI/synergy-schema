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
    assert "DemosPolarisMappedHousehold" in classes
    assert "DemosPolarisMappedPerson" in classes

    # ATLAS
    assert "AtlasHouseholdFleetOutput" in classes
    assert "AtlasVehicleFleetOutput" in classes

    # POLARIS Demand & Skims
    assert "PolarisDemandDatabaseHousehold" in classes
    assert "PolarisDemandDatabasePerson" in classes
    assert "PolarisDemandDatabaseVehicle" in classes
    assert "PolarisDemandDatabaseVehicleClass" in classes
    assert "PolarisDemandDatabaseVehicleType" in classes
    assert "PolarisHouseholdStateOutput" in classes
    assert "PolarisPersonStateOutput" in classes
    assert "InputNetworkSkims" in classes
    assert "NextYearNetworkSkims" in classes

    # ActivitySim
    assert "ActivitySimHouseholdInputRecord" in classes
    assert "ActivitySimPersonInputRecord" in classes
    assert "ActivitySimNetworkSkims" in classes

    # BEAM
    assert "BeamHouseholdRecord" in classes
    assert "BeamPersonRecord" in classes
    assert "BeamVehicleRecord" in classes
    assert "BeamPlanRecord" in classes
    assert "BeamPlanOutputRecord" in classes
    assert "BeamNetworkSkims" in classes
    assert "BeamODSkimsRecord" in classes

    # SynthFirm
    assert "SynthFirmEstablishmentRecord" in classes
    assert "SynthFirmCarrierRecord" in classes
    assert "SynthFirmB2BShipmentRecord" in classes
    assert "SynthFirmInternationalFreightRecord" in classes

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
    assert "SynthFirmModeChoiceEnum" in enums
    assert "SynthFirmPowertrainEnum" in enums
    assert "SynthFirmPortTypeEnum" in enums
    assert "HandoffChannelType" in enums
    assert "FieldTransformationMode" in enums
    assert "ResidueKind" in enums
