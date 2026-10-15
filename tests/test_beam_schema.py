"""Tests for BEAM model LinkML schemas."""

from pathlib import Path

from linkml.validator import Validator
from linkml.validator.plugins import JsonschemaValidationPlugin
from linkml_runtime.utils.schemaview import SchemaView


BEAM_DIR = (
    Path(__file__).parents[1] / "src" / "synergy_schema" / "schema" / "models" / "beam"
)
POPULATION_SCHEMA_PATH = BEAM_DIR / "beam_population.yaml"
PLANS_SCHEMA_PATH = BEAM_DIR / "beam_plans.yaml"
SKIMS_SCHEMA_PATH = BEAM_DIR / "beam_skims.yaml"
COMPOSITE_SCHEMA_PATH = BEAM_DIR / "beam.yaml"


def test_beam_population_schema_structure() -> None:
    view = SchemaView(str(POPULATION_SCHEMA_PATH))
    assert view.schema.name == "beam_population"
    assert "BEAM" in view.schema.description

    classes = set(view.all_classes())
    assert "BeamHouseholdRecord" in classes
    assert "BeamPersonRecord" in classes
    assert "BeamVehicleRecord" in classes

    # Test BeamHouseholdRecord
    hh = view.induced_class("BeamHouseholdRecord")
    assert hh.attributes["household_id"].identifier is True
    assert hh.attributes["household_id"].required is True
    assert hh.annotations["owner"].value == "BEAM"
    assert "HouseholdsBeamIn" in hh.aliases

    # Test key household fields from PILATES
    expected_hh_fields = {
        "household_id",
        "block_id",
        "home_zone_id",
        "income",
        "income_in_thousands",
        "income_segment",
        "hhsize",
        "hht",
        "cars",
        "num_workers",
        "num_non_workers",
        "num_drivers",
        "num_adults",
        "num_children",
        "num_young_children",
        "num_children_5_to_15",
        "num_children_16_to_17",
        "num_college_age",
        "num_young_adults",
        "non_family",
        "family",
        "home_is_urban",
        "home_is_rural",
        "median_value_of_time",
        "hh_value_of_time",
        "hh_work_auto_savings_ratio",
        "num_under16_not_at_school",
        "num_travel_active",
        "num_travel_active_adults",
        "num_travel_active_preschoolers",
        "num_travel_active_children",
        "num_travel_active_non_preschoolers",
        "participates_in_jtf_model",
        "joint_tour_frequency",
        "num_hh_joint_tours",
        "sample_rate",
    }
    assert expected_hh_fields <= set(hh.attributes.keys())

    # Test BeamPersonRecord
    person = view.induced_class("BeamPersonRecord")
    assert person.attributes["person_id"].identifier is True
    assert person.attributes["person_id"].required is True
    assert person.attributes["household_id"].required is True
    assert (
        person.attributes["household_id"].annotations["foreign_key"].value
        == "BeamHouseholdRecord.household_id"
    )
    assert "PersonsBeamIn" in person.aliases

    # Test key person fields from PILATES
    expected_person_fields = {
        "person_id",
        "household_id",
        "age",
        "pnum",
        "sex",
        "pemploy",
        "pstudent",
        "ptype",
        "home_x",
        "home_y",
        "home_zone_id",
        "workplace_zone_id",
        "school_zone_id",
        "distance_to_work",
        "roundtrip_auto_time_to_work",
        "value_of_time",
        "transit_pass_ownership",
        "transit_pass_subsidy",
        "parking_cost",
        "free_parking_at_work",
        "has_electric_bike",
        "has_carshare",
        "has_rideshare",
        "is_worker",
        "is_student",
        "work_from_home",
    }
    assert expected_person_fields <= set(person.attributes.keys())

    # Test BeamVehicleRecord
    veh = view.induced_class("BeamVehicleRecord")
    assert veh.attributes["vehicle_id"].identifier is True
    assert veh.attributes["household_id"].required is True
    assert (
        veh.attributes["household_id"].annotations["foreign_key"].value
        == "BeamHouseholdRecord.household_id"
    )
    assert "VehiclesBeamIn" in veh.aliases


def test_beam_plans_schema_structure() -> None:
    view = SchemaView(str(PLANS_SCHEMA_PATH))
    assert view.schema.name == "beam_plans"

    classes = set(view.all_classes())
    assert "BeamPlanRecord" in classes
    assert "BeamPlanOutputRecord" in classes

    # Test BeamPlanRecord
    plan = view.induced_class("BeamPlanRecord")
    assert plan.attributes["person_id"].required is True
    assert plan.attributes["planelementindex"].required is True
    assert plan.attributes["activityelement"].required is True
    assert "PlansBeamIn" in plan.aliases

    # Test unique key definition
    assert "composite_plan_element" in plan.unique_keys
    assert plan.unique_keys["composite_plan_element"].unique_key_slots == [
        "person_id",
        "planindex",
        "planelementindex",
    ]

    expected_plan_fields = {
        "person_id",
        "planelementindex",
        "activityelement",
        "activitytype",
        "x",
        "y",
        "departure_time",
        "tour_id",
        "trip_id",
        "number_of_participants",
        "tour_mode",
        "trip_mode",
        "trip_dur_min",
        "trip_cost_dollars",
        "planindex",
        "planselected",
        "planscore",
        "legtraveltime",
        "legroutetype",
        "legroutestartlink",
        "legrouteendlink",
        "legroutetraveltime",
        "legroutedistance",
        "legroutelinks",
    }
    assert expected_plan_fields <= set(plan.attributes.keys())

    # Test BeamPlanOutputRecord
    out_plan = view.induced_class("BeamPlanOutputRecord")
    assert out_plan.attributes["person_id"].required is True
    assert "BeamPlansOut" in out_plan.aliases


def test_beam_skims_schema_structure() -> None:
    view = SchemaView(str(SKIMS_SCHEMA_PATH))
    assert view.schema.name == "beam_skims"

    classes = set(view.all_classes())
    assert "BeamNetworkSkims" in classes
    assert "BeamODSkimsRecord" in classes

    # Test BeamNetworkSkims (default OMX/Zarr skim representation)
    skims = view.induced_class("BeamNetworkSkims")
    assert skims.attributes["file_path"].identifier is True
    assert skims.attributes["zone_count"].required is True
    assert skims.attributes["format"].ifabsent == "string(omx)"
    assert skims.attributes["omx_version"].ifabsent == "string(0.2)"
    assert skims.annotations["contract_family"].value == "network_skims"
    assert skims.annotations["default_skim_representation"].value is True
    assert skims.annotations["schema_status"].value == "authoritative"
    assert skims.annotations["status"].value == "provisional"
    assert "provisional" in skims.description.lower()
    assert "BeamSkims" in skims.aliases

    # Verify 1D [origin_zone] lookup table
    lookup_slot = skims.attributes["zone_lookup"]
    assert lookup_slot.required is False
    assert lookup_slot.array is not None
    assert [d.alias for d in lookup_slot.array.dimensions] == ["origin_zone"]

    # Verify required core skims (DIST, DISTWALK, SOV, WLK_TRN_WLK)
    required_2d = ("DIST", "DISTWALK")
    for slot_name in required_2d:
        slot = skims.attributes[slot_name]
        assert slot.required is True, f"{slot_name} must be required"
        assert slot.annotations["status"].value == "provisional"
        assert slot.array is not None
        assert [d.alias for d in slot.array.dimensions] == [
            "origin_zone",
            "destination_zone",
        ]

    required_3d = (
        "SOV_TIME",
        "SOV_DIST",
        "SOV_BTOLL",
        "WLK_TRN_WLK_IVT",
        "WLK_TRN_WLK_IWAIT",
        "WLK_TRN_WLK_XWAIT",
        "WLK_TRN_WLK_WACC",
        "WLK_TRN_WLK_WAUX",
        "WLK_TRN_WLK_WEGR",
    )
    for slot_name in required_3d:
        slot = skims.attributes[slot_name]
        assert slot.required is True, f"{slot_name} must be required"
        assert slot.annotations["status"].value == "provisional"
        assert slot.array is not None
        assert [d.alias for d in slot.array.dimensions] == [
            "time_period",
            "origin_zone",
            "destination_zone",
        ]

    # Verify optional mode families (DISTBIKE, managed-lane/HOV, transit submodes)
    assert skims.attributes["DISTBIKE"].required is not True
    assert skims.attributes["DISTBIKE"].annotations["status"].value == "provisional"

    optional_2d = (
        "DISTBIKE",
        "sov_time_am",
        "sov_time_pm",
        "sov_time_md",
        "sov_distance",
        "sov_toll_cost",
        "hov2_time_am",
        "hov3_time_am",
        "hov2_distance",
        "hov3_distance",
        "walk_distance",
        "bike_distance",
    )
    for slot_name in optional_2d:
        slot = skims.attributes[slot_name]
        assert slot.required is not True, f"{slot_name} must be optional"
        assert slot.array is not None, f"Expected 2D array on {slot_name}"
        assert [d.alias for d in slot.array.dimensions] == [
            "origin_zone",
            "destination_zone",
        ]

    canonical_optional_3d = (
        "SOVTOLL_TIME",
        "SOVTOLL_DIST",
        "SOVTOLL_BTOLL",
        "SOVTOLL_VTOLL",
        "HOV2_TIME",
        "HOV2_DIST",
        "HOV2_BTOLL",
        "HOV2TOLL_TIME",
        "HOV2TOLL_DIST",
        "HOV2TOLL_BTOLL",
        "HOV2TOLL_VTOLL",
        "HOV3_TIME",
        "HOV3_DIST",
        "HOV3_BTOLL",
        "HOV3TOLL_TIME",
        "HOV3TOLL_DIST",
        "HOV3TOLL_BTOLL",
        "HOV3TOLL_VTOLL",
        "WLK_SUBMODE_WLK_SKIMS",
        "DRV_SUBMODE_WLK_SKIMS",
        "WLK_SUBMODE_DRV_SKIMS",
    )
    for slot_name in canonical_optional_3d:
        slot = skims.attributes[slot_name]
        assert slot.required is not True, f"{slot_name} must be optional"
        assert slot.annotations["status"].value == "provisional"

    optional_3d = canonical_optional_3d + (
        "transit_in_vehicle_time",
        "transit_initial_wait_time",
        "transit_transfer_wait_time",
        "transit_fare",
        "transit_failures",
        "ridehail_solo_wait_time",
        "ridehail_solo_cost",
        "ridehail_pooled_wait_time",
        "ridehail_pooled_cost",
        "ridehail_pooled_rejection_prob",
        "ridehail_solo_trips",
        "ridehail_pooled_trips",
    )
    for slot_name in optional_3d:
        slot = skims.attributes[slot_name]
        assert slot.required is not True, f"{slot_name} must be optional"
        assert slot.array is not None, f"Expected 3D array on {slot_name}"
        assert [d.alias for d in slot.array.dimensions] == [
            "time_period",
            "origin_zone",
            "destination_zone",
        ]

    # Test BeamODSkimsRecord (secondary intermediate router CSV record)
    od_rec = view.induced_class("BeamODSkimsRecord")
    assert od_rec.annotations["default_skim_representation"].value is False
    assert od_rec.attributes["time_period"].required is True
    assert od_rec.attributes["orig_taz"].required is True
    assert od_rec.attributes["dest_taz"].required is True
    assert od_rec.attributes["path_type"].required is True
    assert od_rec.attributes["travel_time_minutes"].required is True
    assert od_rec.attributes["distance_miles"].required is True


def test_composite_beam_schema_loads_all_components() -> None:
    view = SchemaView(str(COMPOSITE_SCHEMA_PATH))
    assert view.schema.name == "beam"
    all_classes = set(view.all_classes())
    assert {
        "BeamHouseholdRecord",
        "BeamPersonRecord",
        "BeamVehicleRecord",
        "BeamPlanRecord",
        "BeamPlanOutputRecord",
        "BeamNetworkSkims",
        "BeamODSkimsRecord",
    } <= all_classes


def test_beam_population_instances_validate() -> None:
    validator = Validator(
        POPULATION_SCHEMA_PATH,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    )

    valid_hh = {
        "household_id": 1001,
        "block_id": 60750101001001,
        "home_zone_id": 42,
        "income": 125000.0,
        "income_in_thousands": 125.0,
        "income_segment": 3,
        "hhsize": 2,
        "hht": 1,
        "cars": 1,
        "num_workers": 2.0,
        "num_drivers": 2,
        "num_adults": 2,
        "num_children": 0,
        "family": True,
        "home_is_urban": True,
        "median_value_of_time": 25.5,
    }
    report = validator.validate(valid_hh, "BeamHouseholdRecord")
    assert len(report.results) == 0

    valid_person = {
        "person_id": 2001,
        "household_id": 1001,
        "age": 34,
        "pnum": 1,
        "sex": 1,
        "male": True,
        "adult": True,
        "age_16_p": True,
        "ptype": 1,
        "is_worker": True,
        "home_x": -122.4194,
        "home_y": 37.7749,
        "home_zone_id": 42,
        "workplace_zone_id": 15,
        "distance_to_work": 4.5,
        "value_of_time": 30.0,
        "has_rideshare": True,
    }
    report = validator.validate(valid_person, "BeamPersonRecord")
    assert len(report.results) == 0

    # Test invalid: missing identifier
    invalid_hh = {"income": 50000.0}
    report = validator.validate(invalid_hh, "BeamHouseholdRecord")
    assert len(report.results) > 0


def test_beam_plans_instances_validate() -> None:
    validator = Validator(
        PLANS_SCHEMA_PATH,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    )

    valid_plan = {
        "person_id": 2001,
        "planelementindex": 0,
        "activityelement": "activity",
        "activitytype": "Home",
        "x": -122.4194,
        "y": 37.7749,
        "departure_time": 8.5,
        "planindex": 0,
        "planselected": True,
    }
    report = validator.validate(valid_plan, "BeamPlanRecord")
    assert len(report.results) == 0

    valid_leg = {
        "person_id": 2001,
        "planelementindex": 1,
        "activityelement": "leg",
        "trip_mode": "car",
        "departure_time": 8.5,
        "trip_dur_min": 18.5,
        "trip_cost_dollars": 2.5,
        "legtraveltime": 1110.0,
        "legroutetype": "link-set-links",
        "legroutestartlink": 101,
        "legrouteendlink": 202,
        "legroutedistance": 7240.0,
        "legroutelinks": "101 102 103 202",
    }
    report = validator.validate(valid_leg, "BeamPlanRecord")
    assert len(report.results) == 0


def test_beam_skims_instances_validate() -> None:
    validator = Validator(
        SKIMS_SCHEMA_PATH,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    )

    mat_2d = [[1.0, 2.5], [2.5, 1.0]]
    tensor_3d = [
        [[10.0, 24.5], [25.1, 9.5]],
        [[11.0, 26.2], [27.0, 10.2]],
    ]

    valid_skims = {
        "file_path": "output/beam/skims.omx",
        "format": "omx",
        "omx_version": "0.2",
        "zone_count": 2,
        "zone_lookup": [1, 2],
        "time_periods": "EA,AM,MD,PM,EV",
        "iteration_number": 10,
        "converged": True,
        # Required core skims (DIST, DISTWALK, SOV, WLK_TRN_WLK)
        "DIST": mat_2d,
        "DISTWALK": mat_2d,
        "SOV_TIME": tensor_3d,
        "SOV_DIST": tensor_3d,
        "SOV_BTOLL": tensor_3d,
        "WLK_TRN_WLK_IVT": tensor_3d,
        "WLK_TRN_WLK_IWAIT": tensor_3d,
        "WLK_TRN_WLK_XWAIT": tensor_3d,
        "WLK_TRN_WLK_WACC": tensor_3d,
        "WLK_TRN_WLK_WAUX": tensor_3d,
        "WLK_TRN_WLK_WEGR": tensor_3d,
        # Optional mode skims and semantic aliases
        "DISTBIKE": mat_2d,
        "SOVTOLL_TIME": tensor_3d,
        "HOV2_TIME": tensor_3d,
        "HOV3TOLL_VTOLL": tensor_3d,
        "WLK_SUBMODE_WLK_SKIMS": tensor_3d,
        "sov_time_am": [[10.0, 24.5], [25.1, 9.5]],
        "sov_time_pm": [[11.0, 26.2], [27.0, 10.2]],
        "sov_distance": [[3.2, 12.3], [12.4, 3.0]],
        "sov_toll_cost": [[0.0, 5.0], [5.0, 0.0]],
        "walk_distance": [[0.4, 1.2], [1.2, 0.4]],
        "bike_distance": [[1.0, 3.4], [3.4, 1.0]],
        "transit_in_vehicle_time": [
            [[12.0, 35.0], [36.0, 11.5]],
            [[14.0, 38.0], [39.0, 13.0]],
        ],
        "ridehail_solo_wait_time": [
            [[3.0, 4.5], [4.2, 2.9]],
            [[3.5, 5.1], [4.8, 3.2]],
        ],
        "ridehail_solo_cost": [
            [[8.0, 15.0], [15.5, 7.5]],
            [[9.0, 16.5], [17.0, 8.2]],
        ],
        "ridehail_pooled_rejection_prob": [
            [[0.01, 0.05], [0.04, 0.01]],
            [[0.02, 0.08], [0.07, 0.02]],
        ],
    }
    report = validator.validate(valid_skims, "BeamNetworkSkims")
    assert len(report.results) == 0

    # Minimal valid instance with ONLY required core skims (omitting all optional modes)
    minimal_valid_skims = {
        "file_path": "output/beam/skims.omx",
        "zone_count": 2,
        "DIST": mat_2d,
        "DISTWALK": mat_2d,
        "SOV_TIME": tensor_3d,
        "SOV_DIST": tensor_3d,
        "SOV_BTOLL": tensor_3d,
        "WLK_TRN_WLK_IVT": tensor_3d,
        "WLK_TRN_WLK_IWAIT": tensor_3d,
        "WLK_TRN_WLK_XWAIT": tensor_3d,
        "WLK_TRN_WLK_WACC": tensor_3d,
        "WLK_TRN_WLK_WAUX": tensor_3d,
        "WLK_TRN_WLK_WEGR": tensor_3d,
    }
    report = validator.validate(minimal_valid_skims, "BeamNetworkSkims")
    assert len(report.results) == 0

    # Test invalid: missing a required core skim (WLK_TRN_WLK_WEGR omitted)
    missing_required = dict(minimal_valid_skims)
    del missing_required["WLK_TRN_WLK_WEGR"]
    report = validator.validate(missing_required, "BeamNetworkSkims")
    assert len(report.results) > 0

    # Test invalid: negative minimum value inside 2D matrix
    invalid_skims = dict(minimal_valid_skims)
    invalid_skims["sov_time_am"] = [[10.0, -5.0], [25.1, 9.5]]
    report = validator.validate(invalid_skims, "BeamNetworkSkims")
    assert len(report.results) > 0

    # Test invalid: probability > 1.0 inside 3D tensor
    invalid_prob = dict(minimal_valid_skims)
    invalid_prob["ridehail_pooled_rejection_prob"] = [[[0.01, 1.25], [0.04, 0.01]]]
    report = validator.validate(invalid_prob, "BeamNetworkSkims")
    assert len(report.results) > 0

    # Test invalid: wrong rank (2D passed to 3D tensor)
    invalid_rank = dict(minimal_valid_skims)
    invalid_rank["transit_in_vehicle_time"] = [[12.0, 35.0], [36.0, 11.5]]
    report = validator.validate(invalid_rank, "BeamNetworkSkims")
    assert len(report.results) > 0


def test_activitysim_skims_schema_structure_and_validation() -> None:
    activitysim_skims_path = (
        Path(__file__).parents[1]
        / "src"
        / "synergy_schema"
        / "schema"
        / "models"
        / "activitysim"
        / "activitysim_skims.yaml"
    )
    view = SchemaView(str(activitysim_skims_path))
    assert view.schema.name == "activitysim_skims"
    assert "ActivitySimNetworkSkims" in view.all_classes()

    cls = view.induced_class("ActivitySimNetworkSkims")
    assert cls.annotations["owner"].value == "ActivitySim"
    assert cls.annotations["default_skim_representation"].value is True
    assert cls.annotations["status"].value == "provisional"
    assert "provisional" in cls.description.lower()
    assert cls.attributes["file_path"].identifier is True
    assert cls.attributes["zone_count"].required is True
    assert cls.attributes["omx_version"].ifabsent == "string(0.2)"
    assert [d.alias for d in cls.attributes["zone_lookup"].array.dimensions] == [
        "origin_zone"
    ]

    for req_slot in (
        "DIST",
        "DISTWALK",
        "SOV_TIME",
        "SOV_DIST",
        "SOV_BTOLL",
        "WLK_TRN_WLK_IVT",
        "WLK_TRN_WLK_IWAIT",
        "WLK_TRN_WLK_XWAIT",
        "WLK_TRN_WLK_WACC",
        "WLK_TRN_WLK_WAUX",
        "WLK_TRN_WLK_WEGR",
    ):
        assert cls.attributes[req_slot].required is True
        assert cls.attributes[req_slot].annotations["status"].value == "provisional"

    for opt_slot in (
        "DISTBIKE",
        "SOVTOLL_TIME",
        "SOVTOLL_VTOLL",
        "HOV2_TIME",
        "HOV2TOLL_TIME",
        "HOV3_TIME",
        "HOV3TOLL_TIME",
        "WLK_SUBMODE_WLK_SKIMS",
        "DRV_SUBMODE_WLK_SKIMS",
        "WLK_SUBMODE_DRV_SKIMS",
    ):
        assert cls.attributes[opt_slot].required is not True
        assert cls.attributes[opt_slot].annotations["status"].value == "provisional"

    validator = Validator(
        activitysim_skims_path,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    )
    mat_2d = [[1.0, 2.5], [2.5, 1.0]]
    tensor_3d = [[[10.0, 20.0], [20.0, 10.0]]]
    valid_instance = {
        "file_path": "data/skims.omx",
        "zone_count": 2,
        "zone_lookup": [1, 2],
        "DIST": mat_2d,
        "DISTWALK": mat_2d,
        "SOV_TIME": tensor_3d,
        "SOV_DIST": tensor_3d,
        "SOV_BTOLL": tensor_3d,
        "WLK_TRN_WLK_IVT": tensor_3d,
        "WLK_TRN_WLK_IWAIT": tensor_3d,
        "WLK_TRN_WLK_XWAIT": tensor_3d,
        "WLK_TRN_WLK_WACC": tensor_3d,
        "WLK_TRN_WLK_WAUX": tensor_3d,
        "WLK_TRN_WLK_WEGR": tensor_3d,
    }
    assert (
        len(validator.validate(valid_instance, "ActivitySimNetworkSkims").results) == 0
    )

    missing_dist = dict(valid_instance)
    del missing_dist["DIST"]
    assert len(validator.validate(missing_dist, "ActivitySimNetworkSkims").results) > 0
