"""Tests for the static single-year cross-model handoff and crosswalk schema."""

from pathlib import Path
from linkml_runtime.utils.schemaview import SchemaView
from linkml.validator import Validator
from linkml.validator.plugins import JsonschemaValidationPlugin

SCHEMA_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "synergy_schema"
    / "schema"
    / "mappings"
    / "single_year_handoff.yaml"
)


def test_single_year_handoff_classes_and_enums() -> None:
    view = SchemaView(str(SCHEMA_PATH))
    assert set(view.all_classes()) == {
        "SingleYearModelHandoffPackage",
        "ModelHandoffChannel",
        "FieldMappingSpec",
        "MappingResidueSpec",
        "CategoricalCrosswalkRule",
        "CategoryValueMapping",
    }
    assert set(view.all_enums()) == {
        "HandoffChannelType",
        "FieldTransformationMode",
        "ResidueKind",
    }


def test_single_year_package_instance_validates() -> None:
    validator = Validator(
        SCHEMA_PATH,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    )

    package_instance = {
        "package_id": "SYNERGY_HANDOFF_2018_AUSTIN",
        "simulation_year": 2018,
        "geographic_scope": "Austin Metropolitan Area (6-County)",
        "channels": [
            {
                "channel_id": "DEMOS_TO_POLARIS_HH",
                "source_model": "DEMOS",
                "source_artifact": "Household2018_POLARIS_mapped.csv",
                "target_model": "POLARIS",
                "target_artifact": "Demand.sqlite/Household",
                "channel_type": "tabular_microdata",
                "join_keys": ["household"],
                "field_mappings": [
                    {
                        "source_field": "household",
                        "target_field": "household",
                        "transformation_mode": "direct",
                        "description": "Primary household integer key",
                    },
                    {
                        "source_field": "income",
                        "target_field": "income",
                        "transformation_mode": "direct",
                        "description": "Household annual income",
                    },
                ],
                "residues": [
                    {
                        "field_name": "SERIALNO_PUMS",
                        "residue_kind": "synthetic_seed_trace",
                        "rationale": "Audit lineage back to Census PUMS microdata",
                    }
                ],
            },
            {
                "channel_id": "ATLAS_TO_POLARIS_VEH",
                "source_model": "ATLAS",
                "source_artifact": "atlas_veh.csv",
                "target_model": "POLARIS",
                "target_artifact": "Demand.sqlite/Vehicle",
                "channel_type": "tabular_microdata",
                "join_keys": ["HOUSEID", "VEHID"],
                "field_mappings": [
                    {
                        "source_field": "pred_power",
                        "target_field": "powertrain",
                        "transformation_mode": "enum_crosswalk",
                        "crosswalk_id": "X-V1",
                        "description": "Crosswalk powertrain to POLARIS integer code",
                    }
                ],
                "residues": [
                    {
                        "field_name": "odometer",
                        "residue_kind": "target_default",
                        "default_value": "0",
                        "rationale": "Internal POLARIS vehicle mileage counter initialized to zero",
                    }
                ],
            },
            {
                "channel_id": "POLARIS_TO_NEXT_YEAR_SKIMS",
                "source_model": "POLARIS",
                "source_artifact": "Demand/Supply Simulation",
                "target_model": "NextYearCycle",
                "target_artifact": "austin_skims.omx",
                "channel_type": "matrix_skims",
                "join_keys": ["zone_id_origin", "zone_id_destination"],
                "field_mappings": [
                    {
                        "source_field": "dta_sov_travel_time",
                        "target_field": "SOV_TIME__AM",
                        "transformation_mode": "direct",
                        "description": "Simulated dynamic travel time matrix",
                    }
                ],
                "residues": [],
            },
        ],
        "crosswalks": [
            {
                "crosswalk_id": "X-V1",
                "source_attribute": "pred_power",
                "target_attribute": "powertrain",
                "description": "Translates ATLAS powertrain categories to POLARIS integer types",
                "value_mappings": [
                    {
                        "source_value": "ICE",
                        "target_value": "1",
                        "notes": "Internal combustion gasoline/diesel",
                    },
                    {
                        "source_value": "Hybrid",
                        "target_value": "3",
                        "notes": "Standard HEV",
                    },
                    {
                        "source_value": "PHEV",
                        "target_value": "4",
                        "notes": "Plug-in hybrid electric",
                    },
                    {
                        "source_value": "AEV",
                        "target_value": "5",
                        "notes": "Battery electric vehicle",
                    },
                ],
            }
        ],
    }

    report = validator.validate(package_instance, "SingleYearModelHandoffPackage")
    assert len(report.results) == 0
