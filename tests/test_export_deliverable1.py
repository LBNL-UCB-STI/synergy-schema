"""Tests for the Deliverable 1 export pipeline and standalone distribution isolation."""

import os
from pathlib import Path
import pytest
from linkml_runtime.utils.schemaview import SchemaView
from scripts.export_deliverable1 import export_package

DIST_DIR = Path(__file__).parents[1] / "dist" / "synergy-static-schema"


@pytest.fixture(scope="session", autouse=True)
def ensure_dist_exists() -> None:
    if not DIST_DIR.exists():
        export_package(DIST_DIR)


def test_dist_contains_all_deliverable_schemas_and_files() -> None:
    assert DIST_DIR.exists(), "dist/synergy-static-schema should exist"
    assert (DIST_DIR / "README.md").exists()
    assert (DIST_DIR / "LICENSE").exists()
    assert (DIST_DIR / ".gitignore").exists()
    assert (DIST_DIR / "pyproject.toml").exists()
    assert (DIST_DIR / "uv.lock").exists()
    assert (DIST_DIR / "zensical.toml").exists()
    assert (DIST_DIR / ".github" / "workflows" / "deploy-pages.yml").exists()

    schema_dir = DIST_DIR / "schema"
    assert (schema_dir / "deliverable_1_static_schema.yaml").exists()
    assert (schema_dir / "models" / "urbansim" / "urbansim_land_use.yaml").exists()
    assert (
        schema_dir / "models" / "demos" / "demos_polaris_mapped_examples.yaml"
    ).exists()
    assert (
        schema_dir / "models" / "atlas" / "atlas_fleet_observed_example_v1.yaml"
    ).exists()
    assert (
        schema_dir / "models" / "polaris" / "polaris_demand_database_v1.yaml"
    ).exists()
    assert (schema_dir / "models" / "polaris" / "polaris_skims.yaml").exists()
    assert (schema_dir / "mappings" / "single_year_handoff.yaml").exists()
    assert (
        DIST_DIR / "docs" / "resources" / "DEMOS_and_ATLAS_to_POLARIS_interface.xlsx"
    ).exists()


def test_dist_site_is_compiled_with_all_sections() -> None:
    site_dir = DIST_DIR / "site"
    assert (site_dir / "index.html").exists()
    assert (site_dir / "contract-at-a-glance" / "index.html").exists()
    assert (site_dir / "deliverable_1_uml" / "index.html").exists()
    assert (site_dir / "schema" / "index.html").exists()
    assert (site_dir / "search.json").exists()
    assert (
        site_dir / "resources" / "DEMOS_and_ATLAS_to_POLARIS_interface.xlsx"
    ).exists()
    assert (site_dir / "javascripts" / "mathjax.js").exists()
    assert (site_dir / "javascripts" / "fullscreen.js").exists()

    index_html = (site_dir / "index.html").read_text(encoding="utf-8")
    assert "<li><strong>LinkML Source Schemas</strong>" in index_html
    assert "mathjax.js" in index_html

    contract_html = (site_dir / "contract-at-a-glance" / "index.html").read_text(
        encoding="utf-8"
    )
    assert "$\\to$" not in contract_html
    assert "$\\leftrightarrow$" not in contract_html
    assert "DEMOS Household → POLARIS" in contract_html

    channel_type_md = (
        DIST_DIR / "docs" / "schema" / "HandoffChannelType.md"
    ).read_text(encoding="utf-8")
    assert "Open Matrix OMX travel impedance matrices" in channel_type_md

    # Verify no link escapes above repository root via ../../schema/
    for html_file in site_dir.rglob("*.html"):
        content = html_file.read_text(encoding="utf-8")
        assert 'href="../../schema/' not in content, (
            f"Found broken root-escaping schema link in {html_file.relative_to(site_dir)}"
        )

    # Verify interactive-schema link resolves correctly to ../schema/
    interactive_html = (site_dir / "interactive-schema" / "index.html").read_text(
        encoding="utf-8"
    )
    assert '<a href="../schema/BlockToTazMapping/">' in interactive_html


def test_dist_isolation_from_fy27_longitudinal_ledger() -> None:
    """Strictly assert no FY27 longitudinal ledger code or core population assembly is in dist."""
    for root, dirs, files in os.walk(DIST_DIR):
        dirs[:] = [
            d for d in dirs if d not in {".venv", ".git", ".cache", "__pycache__"}
        ]
        for name in files:
            p = Path(root) / name
            assert "population_trajectory" not in name, (
                f"Found FY27 trajectory file: {p}"
            )
            assert "core_population" not in name, (
                f"Found FY27 core population file: {p}"
            )
            assert "duckdb" not in name.lower(), f"Found DuckDB file: {p}"
            assert name != "synergy_schema.yaml", f"Found aggregate FY27 schema: {p}"


def test_dist_schema_resolves_cleanly() -> None:
    schema_yaml = DIST_DIR / "schema" / "deliverable_1_static_schema.yaml"
    view = SchemaView(str(schema_yaml))
    classes = set(view.all_classes())

    expected = {
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
        "SingleYearModelHandoffPackage",
        "ModelHandoffChannel",
        "CategoricalCrosswalkRule",
        "SynthFirmEstablishmentRecord",
        "SynthFirmCarrierRecord",
        "SynthFirmB2BShipmentRecord",
        "SynthFirmInternationalFreightRecord",
    }
    assert expected.issubset(classes)
