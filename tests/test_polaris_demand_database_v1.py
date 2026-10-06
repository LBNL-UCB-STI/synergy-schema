from pathlib import Path

from linkml_runtime.utils.schemaview import SchemaView


SCHEMA_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "synergy_schema"
    / "schema"
    / "models"
    / "polaris"
    / "polaris_demand_database_v1.yaml"
)


def test_v1_is_a_provisional_observed_record_set() -> None:
    view = SchemaView(str(SCHEMA_PATH))
    assert view.schema.name == "polaris_demand_database_v1"
    assert view.schema.annotations["version"].value == "v1"
    assert view.schema.annotations["model_association"].value == "POLARIS"
    assert view.schema.annotations["status"].value == "provisional"
    assert "observed example" in view.schema.annotations["coverage"].value
    assert set(view.all_classes()) == {
        "PolarisDemandDatabaseV1Household",
        "PolarisDemandDatabaseV1Person",
        "PolarisDemandDatabaseV1Vehicle",
        "PolarisDemandDatabaseV1VehicleClass",
        "PolarisDemandDatabaseV1VehicleType",
    }


def test_selected_roots_have_observed_physical_keys_and_names() -> None:
    view = SchemaView(str(SCHEMA_PATH))
    expected = {
        "PolarisDemandDatabaseV1Household": {
            "household",
            "hhold",
            "location",
            "persons",
            "workers",
            "vehicles",
            "type",
            "income",
            "housing_unit_type",
            "bikes",
            "delRat",
            "dispose_veh",
            "ecom",
            "Has_Residential_Charging",
            "num_groceries",
            "num_meals",
            "time_in_home",
        },
        "PolarisDemandDatabaseV1Person": {
            "person",
            "household",
            "id",
            "age",
            "disability",
            "education",
            "employment",
            "escooter_use_level",
            "gender",
            "income",
            "industry",
            "is_long_term_chooser",
            "journey_to_work_arrival_time",
            "journey_to_work_mode",
            "journey_to_work_travel_time",
            "journey_to_work_vehicle_occupancy",
            "marital_status",
            "race",
            "school_enrollment",
            "school_grade_level",
            "school_location_id",
            "telecommute_level",
            "time_in_job",
            "transit_pass",
            "work_hours",
            "work_location_id",
            "worker_class",
        },
        "PolarisDemandDatabaseV1Vehicle": {
            "vehicle_id",
            "hhold",
            "parking",
            "L3_wtp",
            "L4_wtp",
            "type",
            "fleet",
            "subtype",
        },
        "PolarisDemandDatabaseV1VehicleClass": {
            "class_id",
            "class_type",
            "capacity",
            "length",
            "max_speed",
            "max_accel",
            "max_decel",
            "ev_ml_class",
        },
        "PolarisDemandDatabaseV1VehicleType": {
            "type_id",
            "vehicle_class",
            "connectivity_type",
            "powertrain_type",
            "automation_type",
            "fuel_type",
            "vintage_type",
            "ev_features_id",
            "operating_cost_per_mile",
        },
    }
    for class_name, fields in expected.items():
        cls = view.induced_class(class_name)
        assert set(cls.attributes) == fields
        assert sum(slot.identifier is True for slot in cls.attributes.values()) == 1
        assert all(
            slot.annotations["physical_name"].value == name
            for name, slot in cls.attributes.items()
        )


def test_hhold_is_distinct_from_household_and_not_unique() -> None:
    view = SchemaView(str(SCHEMA_PATH))
    household = view.induced_class("PolarisDemandDatabaseV1Household")
    hhold = household.attributes["hhold"]
    assert hhold.identifier is not True
    assert "alias_of" not in hhold.annotations
    assert not household.unique_keys


def test_population_joins_are_external_validation_checks() -> None:
    view = SchemaView(str(SCHEMA_PATH))
    for class_name, slot_name, target in [
        ("PolarisDemandDatabaseV1Person", "household", ".household"),
        ("PolarisDemandDatabaseV1Vehicle", "hhold", ".household"),
        ("PolarisDemandDatabaseV1Vehicle", "type", ".type_id"),
        ("PolarisDemandDatabaseV1VehicleType", "vehicle_class", ".class_id"),
    ]:
        slot = view.induced_slot(slot_name, class_name)
        assert slot.annotations["relationship_target"].value.endswith(target)
        assert slot.annotations["validation_boundary"].value == (
            "external conformance check, not a SQLite foreign key"
        )
