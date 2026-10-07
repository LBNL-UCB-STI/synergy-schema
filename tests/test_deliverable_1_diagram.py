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

    # Diagram blocks
    assert rendered.count("classDiagram") == 4
    assert rendered.count("flowchart TD") == 1
    assert rendered.count("```mermaid") == 5

    # Crosswalk annotations
    assert "Crosswalk X-P1" in rendered
    assert "Crosswalk X-P2" in rendered
    assert "Crosswalk X-V1" in rendered
    assert "Crosswalk X-V2" in rendered


def test_deliverable_1_uml_deterministic() -> None:
    assert render_deliverable_1_uml() == render_deliverable_1_uml()
