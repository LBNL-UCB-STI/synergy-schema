"""Tests for Deliverable 1 Graphviz ER diagram generation."""

from pathlib import Path
import tempfile
from synergy_schema.graphviz_diagram import (
    generate_graphviz_erd,
    generate_population_erd,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = (
    REPO_ROOT / "src" / "synergy_schema" / "schema" / "deliverable_1_static_schema.yaml"
)


def test_generate_graphviz_erd() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_base = Path(tmp_dir) / "test_erd"
        svg_path = generate_graphviz_erd(SCHEMA_PATH, out_base, rankdir="TB")
        png_path = Path(tmp_dir) / "test_erd.png"

        assert svg_path.exists()
        assert png_path.exists()

        svg_content = svg_path.read_text(encoding="utf-8")

        # Verify all 12 Deliverable 1 classes are present in the SVG
        expected_classes = [
            "UrbanSimBlockMarginals",
            "BlockToTazMapping",
            "UrbanSimZonalTotals",
            "DemosPolarisMappedHousehold",
            "DemosPolarisMappedPerson",
            "AtlasHouseholdFleetOutput",
            "AtlasVehicleFleetOutput",
            "PolarisDemandDatabaseHousehold",
            "PolarisDemandDatabasePerson",
            "PolarisDemandDatabaseVehicle",
            "InputNetworkSkims",
            "NextYearNetworkSkims",
        ]
        for cls_name in expected_classes:
            assert cls_name in svg_content, (
                f"Class {cls_name} missing from Graphviz SVG"
            )

        # Verify key markers and relationship labels
        assert "[PK]" in svg_content
        assert "[FK]" in svg_content
        assert "Marginal Control" in svg_content
        assert "1:1 Fleet Join" in svg_content
        assert "TAZ Location" in svg_content


def test_generate_population_erd() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_base = Path(tmp_dir) / "test_pop_erd"
        svg_path = generate_population_erd(SCHEMA_PATH, out_base, rankdir="LR")
        png_path = Path(tmp_dir) / "test_pop_erd.png"

        assert svg_path.exists()
        assert png_path.exists()

        svg_content = svg_path.read_text(encoding="utf-8")

        # Verify 7 core population and fleet classes are present
        expected_classes = [
            "DemosPolarisMappedHousehold",
            "DemosPolarisMappedPerson",
            "AtlasHouseholdFleetOutput",
            "AtlasVehicleFleetOutput",
            "PolarisDemandDatabaseHousehold",
            "PolarisDemandDatabasePerson",
            "PolarisDemandDatabaseVehicle",
        ]
        for cls_name in expected_classes:
            assert cls_name in svg_content, (
                f"Class {cls_name} missing from Population SVG"
            )

        assert "1:1 Fleet Join" in svg_content
        assert "Pop Recode Lineage" in svg_content
