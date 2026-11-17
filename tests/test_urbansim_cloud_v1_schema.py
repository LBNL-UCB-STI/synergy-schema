"""Contract tests for the observed UrbanSim Cloud API v1 I/O schema."""

from pathlib import Path

from linkml.validator import Validator
from linkml.validator.plugins import JsonschemaValidationPlugin
from linkml_runtime.utils.schemaview import SchemaView

SCHEMA_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "synergy_schema"
    / "schema"
    / "models"
    / "urbansim"
    / "urbansim_cloud_v1.yaml"
)


def test_urbansim_cloud_v1_classes_and_annotations() -> None:
    view = SchemaView(str(SCHEMA_PATH))
    assert set(view.all_classes()) == {
        "UrbanSimCloudSkimsInput",
        "UrbanSimCloudBlockMarginals",
    }

    skims_cls = view.induced_class("UrbanSimCloudSkimsInput")
    assert skims_cls.annotations["model_variant"].value == "cloud_api"
    assert skims_cls.annotations["enforcement_status"].value == "observed_sample"
    assert skims_cls.unique_keys["od_pair"].unique_key_slots == [
        "from_zone_id",
        "to_zone_id",
    ]

    marginals_cls = view.induced_class("UrbanSimCloudBlockMarginals")
    assert marginals_cls.annotations["model_variant"].value == "cloud_api"
    assert marginals_cls.annotations["spatial_granularity"].value == "census_block"
    assert marginals_cls.attributes["block"].identifier is True
    assert len(marginals_cls.attributes) == 41


def test_urbansim_cloud_v1_instances_validate() -> None:
    validator = Validator(
        SCHEMA_PATH,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    )

    skims_instance = {
        "from_zone_id": 1,
        "to_zone_id": 4,
        "travel_time_sov": 6.615427,
        "travel_time_transit": 23.15,
    }
    report = validator.validate(skims_instance, "UrbanSimCloudSkimsInput")
    assert len(report.results) == 0

    marginals_instance = {
        "block": 480219501011000,
        "STPUMA20": 4805100,
        "inc_0_10": 1.0,
        "inc_10_90": 28.0,
        "inc_90_over": 6.0,
        "households_age_head_lt_65_no_children": 11.0,
        "households_age_head_lt_65_with_children": 13.0,
        "households_age_head_gt_65": 11.0,
        "households_own": 24.0,
        "households_rent": 10.0,
        "HHSIZE_1": 0.0,
        "HHSIZE_2": 19.0,
        "HHSIZE_3": 5.0,
        "HHSIZE_4": 5.0,
        "HHSIZE_5": 6.0,
        "HHSIZE_6": 0.0,
        "HHSIZE_7+": 0.0,
        "num_persons": 103.0,
        "male": 55.0,
        "female": 48.0,
        "num_households": 35.0,
        "emp_n2_11": 0.0,
        "emp_n2_21": 0.0,
        "emp_n2_22": 2.0,
        "emp_n2_23": 5.0,
        "emp_n2_31_32_33": 3.0,
        "emp_n2_42": 0.0,
        "emp_n2_44_45": 2.0,
        "emp_n2_48_49": 0.0,
        "emp_n2_51": 0.0,
        "emp_n2_52": 0.0,
        "emp_n2_53": 0.0,
        "emp_n2_54": 0.0,
        "emp_n2_55": 0.0,
        "emp_n2_56": 0.0,
        "emp_n2_61": 0.0,
        "emp_n2_62": 0.0,
        "emp_n2_71": 0.0,
        "emp_n2_72": 3.0,
        "emp_n2_81": 0.0,
        "emp_n2_92": 0.0,
    }
    report = validator.validate(marginals_instance, "UrbanSimCloudBlockMarginals")
    assert len(report.results) == 0
