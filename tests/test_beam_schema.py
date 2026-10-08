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

    # Test BeamNetworkSkims
    skims = view.induced_class("BeamNetworkSkims")
    assert skims.attributes["file_path"].identifier is True
    assert skims.attributes["zone_count"].required is True
    assert skims.annotations["contract_family"].value == "network_skims"
    assert "BeamSkims" in skims.aliases

    expected_skims_fields = {
        "file_path",
        "format",
        "zone_count",
        "time_periods",
        "iteration_number",
        "converged",
        "sov_time_am",
        "sov_time_pm",
        "sov_time_md",
        "sov_distance",
        "sov_toll_cost",
        "hov2_time_am",
        "hov3_time_am",
        "transit_in_vehicle_time",
        "transit_initial_wait_time",
        "transit_transfer_wait_time",
        "transit_fare",
        "transit_failures",
        "walk_distance",
        "bike_distance",
        "ridehail_solo_wait_time",
        "ridehail_solo_cost",
        "ridehail_pooled_wait_time",
        "ridehail_pooled_cost",
        "ridehail_pooled_rejection_prob",
        "ridehail_solo_trips",
        "ridehail_pooled_trips",
    }
    assert expected_skims_fields <= set(skims.attributes.keys())

    # Test BeamODSkimsRecord
    od_rec = view.induced_class("BeamODSkimsRecord")
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

    valid_skims = {
        "file_path": "output/beam/skims.omx",
        "format": "omx",
        "zone_count": 1454,
        "time_periods": "EA,AM,MD,PM,EV",
        "iteration_number": 10,
        "converged": True,
        "sov_time_am": 24.5,
        "sov_time_pm": 26.2,
        "sov_distance": 12.3,
        "sov_toll_cost": 5.0,
        "walk_distance": 1.2,
        "bike_distance": 3.4,
        "ridehail_solo_wait_time": 4.5,
        "ridehail_solo_cost": 15.0,
        "ridehail_pooled_rejection_prob": 0.05,
    }
    report = validator.validate(valid_skims, "BeamNetworkSkims")
    assert len(report.results) == 0

    # Test invalid: negative minimum value
    invalid_skims = {
        "file_path": "output/beam/skims.omx",
        "zone_count": 1454,
        "sov_time_am": -5.0,
    }
    report = validator.validate(invalid_skims, "BeamNetworkSkims")
    assert len(report.results) > 0
