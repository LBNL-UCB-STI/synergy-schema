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
    assert "Crosswalk X-P2" in rendered
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


def test_deliverable_1_uml_deterministic() -> None:
    assert render_deliverable_1_uml() == render_deliverable_1_uml()
