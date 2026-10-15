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
    assert in_cls.annotations["default_skim_representation"].value is True
    assert in_cls.attributes["file_path"].identifier is True
    assert in_cls.attributes["zone_count"].required is True

    # 2D OD matrix dimensions [origin_zone, destination_zone]
    for slot_name in (
        "sov_time_am",
        "sov_time_pm",
        "sov_time_md",
        "sov_distance",
        "sov_toll_cost",
        "transit_travel_time",
    ):
        slot = in_cls.attributes[slot_name]
        assert slot.array is not None
        assert [d.alias for d in slot.array.dimensions] == [
            "origin_zone",
            "destination_zone",
        ]

    # 1D zonal vector dimension [origin_zone]
    acc_slot = in_cls.attributes["transit_accessibility_index"]
    assert acc_slot.array is not None
    assert [d.alias for d in acc_slot.array.dimensions] == ["origin_zone"]

    out_cls = view.induced_class("NextYearNetworkSkims")
    assert out_cls.annotations["format"].value == "omx"
    assert out_cls.annotations["default_skim_representation"].value is True
    assert out_cls.annotations["producer_model"].value == "POLARIS"
    assert out_cls.attributes["file_path"].identifier is True
    assert out_cls.attributes["iteration_count"].range == "integer"

    for slot_name in (
        "sov_time_am",
        "sov_time_pm",
        "sov_time_md",
        "sov_distance",
        "sov_toll_cost",
        "transit_travel_time",
        "congestion_index",
    ):
        slot = out_cls.attributes[slot_name]
        assert slot.array is not None
        assert [d.alias for d in slot.array.dimensions] == [
            "origin_zone",
            "destination_zone",
        ]


def test_polaris_skims_instances_validate() -> None:
    validator = Validator(
        SCHEMA_PATH,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    )

    input_skims_instance = {
        "file_path": "skims/austin_base_skims.omx",
        "zone_count": 2,
        "sov_time_am": [[8.0, 18.4], [19.2, 7.5]],
        "sov_time_pm": [[9.0, 22.1], [21.5, 8.2]],
        "sov_distance": [[3.1, 12.3], [12.5, 2.9]],
        "transit_travel_time": [[15.0, 45.0], [46.0, 14.0]],
        "transit_accessibility_index": [10.4, 9.8],
    }
    report = validator.validate(input_skims_instance, "InputNetworkSkims")
    assert len(report.results) == 0

    output_skims_instance = {
        "file_path": "skims/austin_next_year_skims.omx",
        "zone_count": 2,
        "iteration_count": 20,
        "gap_metric": 0.0001,
        "sov_time_am": [[8.4, 19.1], [19.8, 7.9]],
        "sov_time_pm": [[9.5, 23.0], [22.4, 8.6]],
        "congestion_index": [[1.05, 1.15], [1.12, 1.04]],
    }
    report = validator.validate(output_skims_instance, "NextYearNetworkSkims")
    assert len(report.results) == 0

    # Reject scalar or wrong-rank array
    invalid_rank = {
        "file_path": "skims/austin_base_skims.omx",
        "zone_count": 2,
        "sov_time_am": [18.4, 19.2],  # 1D instead of 2D
    }
    assert len(validator.validate(invalid_rank, "InputNetworkSkims").results) > 0

    # Reject congestion_index < 1.0 inside 2D matrix
    invalid_congestion = {
        "file_path": "skims/austin_next_year_skims.omx",
        "zone_count": 2,
        "congestion_index": [[1.05, 0.85], [1.12, 1.04]],
    }
    assert (
        len(validator.validate(invalid_congestion, "NextYearNetworkSkims").results) > 0
    )
