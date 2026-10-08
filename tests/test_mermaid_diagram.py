"""Tests for LinkML-driven Mermaid ER diagram generator."""

from pathlib import Path
from synergy_schema.mermaid_diagram import (
    generate_mermaid_erd,
    POPULATION_CLASSES,
    REGIONAL_CLASSES,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = (
    REPO_ROOT / "src" / "synergy_schema" / "schema" / "deliverable_1_static_schema.yaml"
)


def test_generate_mermaid_population_erd() -> None:
    mermaid_str = generate_mermaid_erd(SCHEMA_PATH, POPULATION_CLASSES)

    assert mermaid_str.startswith("erDiagram")

    # Verify all 7 core population classes are declared
    for cls_name in POPULATION_CLASSES:
        assert cls_name in mermaid_str, f"Missing {cls_name} in Mermaid ERD"

    # Verify key relationships
    assert (
        'DemosPolarisMappedHousehold ||--|{ DemosPolarisMappedPerson : "contains"'
        in mermaid_str
    )
    assert (
        'AtlasHouseholdFleetOutput ||--|{ AtlasVehicleFleetOutput : "owns"'
        in mermaid_str
    )
    assert (
        'PolarisDemandDatabaseHousehold ||--|{ PolarisDemandDatabasePerson : "contains"'
        in mermaid_str
    )
    assert (
        'PolarisDemandDatabaseHousehold ||--|{ PolarisDemandDatabaseVehicle : "owns"'
        in mermaid_str
    )
    assert (
        'DemosPolarisMappedHousehold ||--|| AtlasHouseholdFleetOutput : "1:1 fleet join"'
        in mermaid_str
    )
    assert (
        'DemosPolarisMappedHousehold ||--|| PolarisDemandDatabaseHousehold : "pop recode lineage"'
        in mermaid_str
    )
    assert (
        'AtlasVehicleFleetOutput ||--|| PolarisDemandDatabaseVehicle : "vehicle recode"'
        in mermaid_str
    )

    # Verify PK/FK tags
    assert "household PK" in mermaid_str
    assert "household FK" in mermaid_str
    assert "houseid PK" in mermaid_str
    assert "houseid FK" in mermaid_str


def test_generate_mermaid_regional_erd() -> None:
    mermaid_str = generate_mermaid_erd(SCHEMA_PATH, REGIONAL_CLASSES)

    assert mermaid_str.startswith("erDiagram")

    # Verify all 12 Deliverable 1 classes are declared
    for cls_name in REGIONAL_CLASSES:
        assert cls_name in mermaid_str, f"Missing {cls_name} in Regional Mermaid ERD"

    # Verify cross-model spatial links
    assert (
        'UrbanSimBlockMarginals ||--o{ DemosPolarisMappedHousehold : "marginal control"'
        in mermaid_str
    )
    assert (
        'UrbanSimZonalTotals ||--o{ PolarisDemandDatabaseHousehold : "TAZ location"'
        in mermaid_str
    )
    assert (
        'UrbanSimZonalTotals ||--o{ InputNetworkSkims : "TAZ dimension"' in mermaid_str
    )
    assert (
        'UrbanSimZonalTotals ||--o{ NextYearNetworkSkims : "TAZ dimension"'
        in mermaid_str
    )
    assert (
        'UrbanSimZonalTotals ||--o{ BeamHouseholdRecord : "TAZ location"' in mermaid_str
    )
    assert (
        'UrbanSimZonalTotals ||--o{ BeamNetworkSkims : "TAZ dimension"' in mermaid_str
    )


def test_render_database_erd_markdown() -> None:
    from synergy_schema.interactive_diagram import render_database_erd_markdown

    rendered = render_database_erd_markdown(SCHEMA_PATH)

    assert "# Database Schema & Entity-Relationship Diagrams" in rendered
    assert "## 1. Core Population & Vehicle Fleet ERD" in rendered
    assert "## 2. Complete Multi-Model Regional Architecture ERD" in rendered
    assert "## 3. Foreign Key & Pipeline Linkage Reference Table" in rendered

    # Verify Mermaid erDiagrams are embedded directly without tabs or graphviz
    assert rendered.count("```mermaid\nerDiagram") == 2
    assert "Graphviz" not in rendered
    assert "schema-explorer" not in rendered
    assert "Interactive Schema Inspector" not in rendered
