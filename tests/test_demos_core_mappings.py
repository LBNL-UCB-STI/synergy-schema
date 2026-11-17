"""Tests for core DEMOS <-> Synergy Core mapping catalog and SQL derivation/projection."""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import yaml
from linkml.validator import Validator
from linkml.validator.plugins import JsonschemaValidationPlugin
from linkml_runtime.utils.schemaview import SchemaView

from synergy_schema.pipeline.demos_core import (
    derive_core_from_demos_core,
    project_demos_core_from_core,
)

ROOT = Path(__file__).parents[1]
FACET_MAPPINGS_SCHEMA = (
    ROOT / "src" / "synergy_schema" / "schema" / "core" / "facet_mappings.yaml"
)
DEMOS_CORE_SCHEMA = (
    ROOT / "src" / "synergy_schema" / "schema" / "models" / "demos" / "demos_core.yaml"
)
CATALOG_PATH = ROOT / "examples" / "ledger" / "demos_core_mapping_catalog.yaml"


def test_demos_core_mapping_catalog_validates() -> None:
    catalog = yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))
    report = Validator(
        FACET_MAPPINGS_SCHEMA,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    ).validate(catalog, "CoreFacetMappingCatalog")
    assert len(report.results) == 0

    loc_mapping = next(
        m for m in catalog["mappings"] if m["facet"] == "household_location"
    )
    assert any(
        b["view_column"] == "block_id" and b["core_field"] == "block"
        for b in loc_mapping["field_bindings"]
    )


def test_core_household_location_has_block_slot() -> None:
    view = SchemaView(
        str(ROOT / "src" / "synergy_schema" / "schema" / "core" / "core_tables.yaml")
    )
    assert "block" in view.class_slots("CoreHouseholdLocation")


def test_derive_core_from_demos_core_and_project_roundtrip(tmp_path: Path) -> None:
    prior_facets = {
        "households": pa.table({"household_id": [101, 102]}),
        "people": pa.table({"person_id": [1001, 2001]}),
        "person_demographics": pa.table(
            {
                "person_id": [1001, 2001],
                "age": [40, 30],
                "sex": [1, 2],
                "race": [6, 1],
                "hispanic": [0, 1],
                "relate": [0, 0],
            }
        ),
        "household_location": pa.table(
            {
                "household_id": [101, 102],
                "latitude": [37.8, 37.9],
                "longitude": [-122.2, -122.3],
                "tract": [6055201004, 6041121200],
                "block_group": [2, 3],
                "block": ["060552010042027", "060411212003008"],
                "taz": [10, 20],
            }
        ),
    }

    demos_hh = pa.table(
        {
            "household_id": [101, 103],
            "lcm_county_id": ["06055", "06041"],
            "block_id": ["060552010042027", "060411282002016"],
            "income": [100000, 80000],
            "race_of_head": [6.0, 2.0],
            "sf_detached": ["yes", "no"],
            "tenure": ["1", "2"],
        }
    )
    demos_p = pa.table(
        {
            "person_id": [1001, 1002, 3001],
            "household_id": [101, 101, 103],
            "age": [41, 0, 29],
            "sex": [1, 2, 2],
            "relate": [0, 2, 0],
            "MAR": [1, 5, 5],
            "edu": [21, 0, 19],
            "earning": [100000.0, 0.0, 80000.0],
            "worker": [1, 0, 1],
            "student": [0, 0, 0],
            "work_at_home": [0, 0, 0],
            "race_id": [6, 6, 2],
            "race": ["asian", "asian", "black"],
            "hispanic": [0, 0, 0],
            "hours": [40.0, 0.0, 35.0],
            "school_zone_id": ["-1", "-1", "-1"],
            "work_zone_id": ["1256", "-1", "208"],
        }
    )

    result = derive_core_from_demos_core(
        demos_households=demos_hh,
        demos_persons=demos_p,
        prior_core_facets=prior_facets,
        output_dir=tmp_path / "facets",
        income_deflator=0.9,
    )

    assert result["classification"] == {
        "surviving_households": 1,
        "new_households": 1,
        "removed_households": 1,
        "surviving_persons": 1,
        "new_persons": 2,
        "removed_persons": 1,
    }

    facets = result["facets"]
    assert set(facets.keys()) == {
        "households",
        "people",
        "household_membership",
        "person_demographics",
        "person_schooling",
        "person_employment",
        "household_income",
        "household_dwelling",
        "household_location",
    }

    loc_df = facets["household_location"].to_pandas().set_index("household_id")
    assert loc_df.loc[101, "block"] == "060552010042027"
    assert loc_df.loc[103, "block"] == "060411282002016"
    assert loc_df.loc[103, "tract"] == 6041128200
    assert loc_df.loc[103, "block_group"] == 2

    dw_df = facets["household_dwelling"].to_pandas().set_index("household_id")
    assert dw_df.loc[101, "housing_unit_type"] == 1
    assert dw_df.loc[103, "housing_unit_type"] == 2
    assert dw_df.loc[103, "tenure"] == 2

    emp_df = facets["person_employment"].to_pandas().set_index("person_id")
    assert emp_df.loc[1001, "work_location_id"] == 1256
    assert emp_df.loc[1001, "income"] == 90000

    # Round-trip project back to core DEMOS format
    projected = project_demos_core_from_core(facets)
    p_rows = projected["persons"].to_pylist()
    hh_rows = projected["households"].to_pylist()
    assert len(p_rows) == 3
    assert len(hh_rows) == 2

    validator = Validator(
        DEMOS_CORE_SCHEMA,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    )
    for row in p_rows:
        row_for_schema = dict(row)
        row_for_schema["mar"] = row_for_schema.pop("MAR")
        assert len(validator.validate(row_for_schema, "DemosCorePerson").results) == 0
    for row in hh_rows:
        assert len(validator.validate(row, "DemosCoreHousehold").results) == 0
