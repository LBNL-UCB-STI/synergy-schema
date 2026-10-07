"""Shape tests for fabricated rows against observed-example candidate roots."""

from pathlib import Path

from linkml.validator import Validator
from linkml.validator.plugins import JsonschemaValidationPlugin


SCHEMA_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "synergy_schema"
    / "schema"
    / "observed_examples.yaml"
)


def _messages(instance: dict[str, object], target_class: str) -> list[str]:
    report = Validator(
        SCHEMA_PATH,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    ).validate(instance, target_class)
    return [result.message for result in report.results]


def test_candidate_rows_validate_after_explicit_physical_header_binding() -> None:
    demos_household = {
        "household": 1,
        "block_id": 48053960800,
        "lcm_county_id": 48053,
        "age_of_head": 75.0,
        "workers": 0.0,
        "race_of_head": 1.0,
        "income": 0.0,
        "persons": 1,
        "is_reorg_household": False,
        "serialno_pums": "2017000024288",
    }
    demos_person_without_id = {
        "person": 1,
        "relp": 0,
        "gender": 2,
        "education": 20,
        "income": 0.0,
        "age": 76,
        "household": 1,
        "marital_status": 2,
        "employment": 6.0,
        "school_enrollment": 1.0,
        "serialno_pums": "2017000024288",
        "sporder": 1.0,
    }
    atlas_household = {"houseid": 236587, "nvehicles": 4}
    atlas_vehicle = {
        "houseid": 527120,
        "vehid": 1,
        "bodytype": "car",
        "vintage_category": "0~5 years",
        "annual_mileage": 17306.8450820586,
        "pred_power": "ICE",
        "modelyear": 2015,
    }
    polaris_household = {
        "household": 1,
        "hhold": 99,
        "location": 1,
        "persons": 1,
        "workers": 0,
        "vehicles": 1,
        "type": 1,
        "income": 0,
        "housing_unit_type": 1,
    }

    assert _messages(demos_household, "DemosPolarisMappedHousehold") == []
    assert _messages(demos_person_without_id, "DemosPolarisMappedPerson") == []
    assert _messages(atlas_household, "AtlasHouseholdFleetOutput") == []
    assert _messages(atlas_vehicle, "AtlasVehicleFleetOutput") == []
    assert _messages(polaris_household, "PolarisDemandDatabaseHousehold") == []


def test_candidate_shape_rejects_missing_required_or_unobserved_columns() -> None:
    missing_atlas_household_key = {"nvehicles": 4}
    demos_person_with_unobserved_hhold = {
        "person": 1,
        "relp": 0,
        "gender": 2,
        "education": 20,
        "income": 0.0,
        "age": 76,
        "household": 1,
        "marital_status": 2,
        "employment": 6.0,
        "school_enrollment": 1.0,
        "hhold": 1,
    }

    assert _messages(missing_atlas_household_key, "AtlasHouseholdFleetOutput")
    assert _messages(demos_person_with_unobserved_hhold, "DemosPolarisMappedPerson")
    invalid_atlas_vehicle = {
        "houseid": 527120,
        "vehid": 1,
        "bodytype": "spaceship",
        "vintage_category": "unknown",
        "annual_mileage": 1000.0,
        "pred_power": "warp_drive",
        "modelyear": 2020,
    }
    assert _messages(invalid_atlas_vehicle, "AtlasVehicleFleetOutput")
