"""Contract tests for the notional UrbanSim land use and zonal marginals schema."""

from pathlib import Path
from linkml_runtime.utils.schemaview import SchemaView
from linkml.validator import Validator
from linkml.validator.plugins import JsonschemaValidationPlugin

SCHEMA_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "synergy_schema"
    / "schema"
    / "models"
    / "urbansim"
    / "urbansim_land_use.yaml"
)


def test_urbansim_classes_and_annotations() -> None:
    view = SchemaView(str(SCHEMA_PATH))
    assert set(view.all_classes()) == {
        "UrbanSimBlockMarginals",
        "BlockToTazMapping",
        "UrbanSimZonalTotals",
    }

    block_cls = view.induced_class("UrbanSimBlockMarginals")
    assert block_cls.annotations["spatial_granularity"].value == "census_block"
    assert block_cls.attributes["block_id"].identifier is True
    assert block_cls.attributes["total_households"].required is True

    map_cls = view.induced_class("BlockToTazMapping")
    assert map_cls.unique_keys["block_taz_pair"].unique_key_slots == [
        "block_id",
        "zone_id",
    ]

    zone_cls = view.induced_class("UrbanSimZonalTotals")
    assert zone_cls.annotations["spatial_granularity"].value == "taz_zone"
    assert zone_cls.attributes["zone_id"].identifier is True
    assert (
        zone_cls.attributes["pop_households"].annotations["physical_name"].value
        == "pop_households"
    )
    assert (
        zone_cls.attributes["employment_total"].annotations["physical_name"].value
        == "employment_total"
    )


def test_urbansim_instances_validate() -> None:
    validator = Validator(
        SCHEMA_PATH,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    )

    block_instance = {
        "block_id": "484530018041002",
        "county_id": 48453,
        "total_households": 120,
        "total_population": 310,
        "residential_units": 130,
        "jobs_total": 45,
    }
    report = validator.validate(block_instance, "UrbanSimBlockMarginals")
    assert len(report.results) == 0

    taz_map_instance = {
        "block_id": "484530018041002",
        "zone_id": 142,
        "area_share": 1.0,
        "housing_share": 1.0,
    }
    report = validator.validate(taz_map_instance, "BlockToTazMapping")
    assert len(report.results) == 0

    zone_instance = {
        "zone_id": 142,
        "area_type": 2,
        "residential_area": 150000.0,
        "pop_households": 1200,
        "pop_persons": 3100,
        "employment_total": 850,
        "hh_inc_avg": 75000.0,
    }
    report = validator.validate(zone_instance, "UrbanSimZonalTotals")
    assert len(report.results) == 0
