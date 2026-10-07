"""Contract and shape tests for POLARIS network skims schema."""

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
    / "polaris"
    / "polaris_skims.yaml"
)


def test_polaris_skims_classes_and_annotations() -> None:
    view = SchemaView(str(SCHEMA_PATH))
    assert set(view.all_classes()) == {
        "InputNetworkSkims",
        "NextYearNetworkSkims",
    }

    in_cls = view.induced_class("InputNetworkSkims")
    assert in_cls.annotations["format"].value == "omx"
    assert in_cls.attributes["file_path"].identifier is True
    assert in_cls.attributes["zone_count"].required is True

    out_cls = view.induced_class("NextYearNetworkSkims")
    assert out_cls.annotations["format"].value == "omx"
    assert out_cls.annotations["producer_model"].value == "POLARIS"
    assert out_cls.attributes["file_path"].identifier is True
    assert out_cls.attributes["iteration_count"].range == "integer"


def test_polaris_skims_instances_validate() -> None:
    validator = Validator(
        SCHEMA_PATH,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    )

    input_skims_instance = {
        "file_path": "skims/austin_base_skims.omx",
        "zone_count": 2351,
        "sov_time_am": 18.4,
        "sov_time_pm": 22.1,
        "sov_distance": 12.3,
        "transit_travel_time": 45.0,
    }
    report = validator.validate(input_skims_instance, "InputNetworkSkims")
    assert len(report.results) == 0

    output_skims_instance = {
        "file_path": "skims/austin_next_year_skims.omx",
        "zone_count": 2351,
        "iteration_count": 20,
        "gap_metric": 0.0001,
        "sov_time_am": 19.1,
        "sov_time_pm": 23.0,
        "congestion_index": 1.15,
    }
    report = validator.validate(output_skims_instance, "NextYearNetworkSkims")
    assert len(report.results) == 0
