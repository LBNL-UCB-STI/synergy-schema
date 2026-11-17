"""Contract tests for the core DEMOS native I/O schema."""

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
    / "demos"
    / "demos_core.yaml"
)


def test_demos_core_classes_and_annotations() -> None:
    view = SchemaView(str(SCHEMA_PATH))
    assert set(view.all_classes()) == {
        "DemosCorePerson",
        "DemosCoreHousehold",
        "DemosIncomeRateRow",
        "DemosHouseholdSizeControlRow",
        "DemosObservedAnnualCountRow",
        "DemosObservedMaritalCountRow",
    }

    person_cls = view.induced_class("DemosCorePerson")
    assert person_cls.annotations["model_variant"].value == "core"
    assert person_cls.annotations["format"].value == "hdf5"
    assert person_cls.annotations["h5_key"].value == "persons"
    assert person_cls.attributes["person_id"].identifier is True
    assert person_cls.attributes["mar"].annotations["physical_name"].value == "MAR"
    assert (
        person_cls.attributes["hispanic_1"].annotations["physical_name"].value
        == "hispanic.1"
    )
    assert (
        person_cls.attributes["household_id"].annotations["foreign_key"].value
        == "DemosCoreHousehold.household_id"
    )
    assert len(person_cls.attributes) == 22

    hh_cls = view.induced_class("DemosCoreHousehold")
    assert hh_cls.annotations["model_variant"].value == "core"
    assert hh_cls.annotations["format"].value == "hdf5"
    assert hh_cls.annotations["h5_key"].value == "households"
    assert hh_cls.attributes["household_id"].identifier is True
    assert hh_cls.attributes["lcm_county_id"].required is True
    assert len(hh_cls.attributes) == 28


def test_demos_core_instances_validate() -> None:
    validator = Validator(
        SCHEMA_PATH,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    )

    seed_person = {
        "person_id": 7475752,
        "household_id": 3344875,
        "age": 24,
        "sex": 1,
        "relate": 2,
        "mar": 5,
        "edu": 19,
        "earning": 744.0,
        "worker": 0,
        "student": 0,
        "work_at_home": 0,
        "race_id": 6,
        "race": "asian",
        "hours": 10.0,
        "school_zone_id": "-1",
        "work_zone_id": "-1",
        "hispanic": 0,
        "hispanic_1": 0,
        "p_hispanic": "no",
        "person_sex": "male",
        "person_age": "20 to 35",
        "member_id": 3,
    }
    assert len(validator.validate(seed_person, "DemosCorePerson").results) == 0

    newborn_person = {
        "person_id": 9999999,
        "household_id": 3344875,
        "age": 0,
        "sex": 2,
        "relate": 2,
        "mar": 5,
        "edu": 0,
        "earning": 0.0,
        "worker": 0,
        "student": 0,
        "work_at_home": 0,
        "race_id": 6,
        "race": "other",
    }
    assert len(validator.validate(newborn_person, "DemosCorePerson").results) == 0

    seed_hh = {
        "household_id": 3344875,
        "lcm_county_id": "06055",
        "block_id": "060552010042027",
        "income": 92814,
        "persons": 4,
        "workers": 2,
        "cars": 4,
        "age_of_head": 55,
        "race_of_head": 6,
        "hispanic_head": "no",
        "hispanic_status_of_head": "0.0",
        "hh_size": "four or more",
        "hh_type": 4,
        "hh_workers": "two or more",
        "hh_cars": "two or more",
        "hh_children": "yes",
        "hh_income": "gt150",
        "hh_age_of_head": "gt35-lt65",
        "hh_seniors": "no",
        "hh_race_of_head": "asian",
        "seniors": 0,
        "gt2": 1,
        "gt55": 1,
        "tenure": "1",
        "tenure_mover": "own not recent",
        "recent_mover": "0",
        "sf_detached": "yes",
        "serialno": "2010001367034",
    }
    assert len(validator.validate(seed_hh, "DemosCoreHousehold").results) == 0

    new_hh = {
        "household_id": 8888888,
        "lcm_county_id": "06041",
    }
    assert len(validator.validate(new_hh, "DemosCoreHousehold").results) == 0

    income_rate = {"year": 2011, "lcm_county_id": "06001", "rate": -0.02}
    assert len(validator.validate(income_rate, "DemosIncomeRateRow").results) == 0

    hsize_ct = {
        "year": 2011,
        "lcm_county_id": "06041",
        "hh_size": "one",
        "total_number_of_households": 29456,
    }
    assert (
        len(validator.validate(hsize_ct, "DemosHouseholdSizeControlRow").results) == 0
    )

    obs_count = {"year": 2010, "count": 2397}
    assert (
        len(validator.validate(obs_count, "DemosObservedAnnualCountRow").results) == 0
    )

    obs_marital = {"year": 2011, "mar": 1, "count": 157251}
    assert (
        len(validator.validate(obs_marital, "DemosObservedMaritalCountRow").results)
        == 0
    )

    invalid_person = dict(newborn_person, unknown_col="bad")
    assert len(validator.validate(invalid_person, "DemosCorePerson").results) > 0
