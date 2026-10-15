"""Tests for Deliverable 1 UML diagram rendering."""

from synergy_schema.deliverable_1_diagram import render_deliverable_1_uml


def test_deliverable_1_uml_contains_all_models_and_diagrams() -> None:
    rendered = render_deliverable_1_uml()

    # Model classes present
    assert "UrbanSimBlockMarginals" in rendered
    assert "BlockToTazMapping" in rendered
    assert "UrbanSimZonalTotals" in rendered
    assert "DemosPolarisMappedHousehold" in rendered
    assert "DemosPolarisMappedPerson" in rendered
    assert "AtlasHouseholdFleetOutput" in rendered
    assert "AtlasVehicleFleetOutput" in rendered
    assert "PolarisDemandDatabaseHousehold" in rendered
    assert "PolarisDemandDatabasePerson" in rendered
    assert "PolarisDemandDatabaseVehicle" in rendered
    assert "InputNetworkSkims" in rendered
    assert "NextYearNetworkSkims" in rendered
    assert "ActivitySimHouseholdInputRecord" in rendered
    assert "ActivitySimPersonInputRecord" in rendered
    assert "BeamHouseholdRecord" in rendered
    assert "BeamPersonRecord" in rendered
    assert "BeamVehicleRecord" in rendered
    assert "BeamPlanRecord" in rendered
    assert "BeamNetworkSkims" in rendered
    assert "SynthFirmEstablishmentRecord" in rendered
    assert "SynthFirmCarrierRecord" in rendered
    assert "SynthFirmB2BShipmentRecord" in rendered
    assert "SynthFirmInternationalFreightRecord" in rendered

    # Workflow tabs
    assert '=== "Primary Workflow: POLARIS Dynamic Traffic Assignment"' in rendered
    assert (
        '=== "LBL Counterpart Workflow: ActivitySim Demand & BEAM Dynamic Simulation"'
        in rendered
    )
    assert (
        '=== "Freight & Commercial Demand Pipeline: SynthFirm to POLARIS & BEAM"'
        in rendered
    )

    # Diagram blocks
    assert rendered.count("classDiagram") == 7
    assert rendered.count("flowchart TD") == 3
    assert rendered.count("```mermaid") == 10

    # ATLAS updating ActivitySim cars
    assert "ATLAS_HH_B ==>|Updates cars per household| AS_Pop" in rendered
    assert (
        'AtlasHouseholdFleetOutput "1" ..> "1" ActivitySimHouseholdInputRecord : updates cars'
        in rendered
    )

    # Crosswalk annotations
    assert "Crosswalk X-P1" in rendered
    assert "Crosswalk X-P1, X-P2" in rendered
    assert "Crosswalk X-P1, X-P6" in rendered
    assert "Crosswalk X-P1 / D-P3a" in rendered
    assert "Crosswalk X-V1" in rendered
    assert "Crosswalk X-V2" in rendered

    # Clickable LinkML schema links
    assert 'click SF_Firm "../schema/SynthFirmEstablishmentRecord/"' in rendered
    assert 'click DEMOS_HH "../schema/DemosPolarisMappedHousehold/"' in rendered
    assert (
        'link SynthFirmEstablishmentRecord "../schema/SynthFirmEstablishmentRecord/"'
        in rendered
    )
    assert (
        'link PolarisDemandDatabaseHousehold "../schema/PolarisDemandDatabaseHousehold/"'
        in rendered
    )
    assert (
        "[`SynthFirmEstablishmentRecord`](../schema/SynthFirmEstablishmentRecord.md)"
        in rendered
    )
    assert 'click BEAM_Skims "../schema/BeamNetworkSkims/"' in rendered
    assert 'click POL_StateOut "../schema/PolarisPersonStateOutput/"' in rendered
    assert "PolarisHouseholdStateOutput" in rendered
    assert "PolarisPersonStateOutput" in rendered
    assert "+float_2D sov_time_am [origin_zone, destination_zone]" in rendered
    assert (
        "+float_3D transit_in_vehicle_time [time_period, origin_zone, destination_zone]"
        in rendered
    )
    assert "ActivitySimNetworkSkims" in rendered
    assert "+float_2D DIST [origin_zone, destination_zone]" in rendered
    assert "+float_3D SOV_TIME [time_period, origin_zone, destination_zone]" in rendered
    assert (
        "+float_3D WLK_TRN_WLK_IVT [time_period, origin_zone, destination_zone]"
        in rendered
    )
    assert "class PolarisDemandDatabaseVehicleClass {" in rendered
    assert "class PolarisDemandDatabaseVehicleType {" in rendered
    assert "+int housing_unit_type [Crosswalk D-H1]" in rendered
    assert "+int autonomous_vehicles" in rendered
    assert "+int relate" not in rendered
    assert "+int housing_type" not in rendered
    assert "+int odometer" not in rendered


def test_deliverable_1_uml_deterministic() -> None:
    assert render_deliverable_1_uml() == render_deliverable_1_uml()


def test_deliverable_1_uml_schema_prefix() -> None:
    rendered = render_deliverable_1_uml(schema_prefix="schema")
    assert (
        "[`SynthFirmEstablishmentRecord`](schema/SynthFirmEstablishmentRecord.md)"
        in rendered
    )
    # Mermaid links should still use ../schema/
    assert 'click SF_Firm "../schema/SynthFirmEstablishmentRecord/"' in rendered
