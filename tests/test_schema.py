"""Contract tests for the canonical LinkML population handoff schema."""

from copy import deepcopy
from pathlib import Path

import yaml
from linkml.validator import Validator
from linkml.validator.plugins import JsonschemaValidationPlugin
from linkml_runtime.utils.schemaview import SchemaView


SCHEMA_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "synergy_schema"
    / "schema"
    / "synergy_schema.yaml"
)
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "population_snapshot_bundle.yaml"
ATLAS_RECORDS_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "atlas_population_records.yaml"
)

ATLAS_HOUSEHOLD_FIELDS = {
    "household_id",
    "tenure",
    "block_id",
    "hh_age_of_head",
    "gt55",
    "age_of_head",
    "serialno",
    "gt2",
    "seniors",
    "hh_children",
    "recent_mover",
    "hh_seniors",
    "tenure_mover",
    "workers",
    "race_of_head",
    "hispanic_status_of_head",
    "cars",
    "hh_cars",
    "lcm_county_id",
    "hispanic_head",
    "hh_size",
    "income",
    "hh_race_of_head",
    "hh_income",
    "hh_workers",
    "sf_detached",
    "persons",
    "hh_type",
}

ATLAS_PERSON_FIELDS = {
    "person_id",
    "p_hispanic",
    "person_age",
    "race_id",
    "school_id",
    "education_group",
    "workplace_taz",
    "school_block_id",
    "school_zone_id",
    "person_sex",
    "relate",
    "work_at_home",
    "hours",
    "earning",
    "student",
    "work_block_id",
    "hispanic",
    "worker",
    "age_group",
    "member_id",
    "work_zone_id",
    "sex",
    "race",
    "hispanic_1",
    "age",
    "household_id",
    "school_taz",
    "mar",
    "edu",
}

ATLAS_VEHICLE_FIELDS = {
    "household_id",
    "vehicle_id",
    "bodytype",
    "pred_power",
    "ownlease",
    "modelyear",
    "adopt_fuel",
    "adopt_veh",
    "acquire_year",
    "vehicle_tag",
    "year",
    "newhhflag",
    "maindriver_id",
    "vintage_category",
    "vehicletypeid",
}


def _load_fixture() -> dict[str, object]:
    return yaml.safe_load(FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_atlas_records_fixture() -> dict[str, dict[str, object]]:
    return yaml.safe_load(ATLAS_RECORDS_FIXTURE_PATH.read_text(encoding="utf-8"))


def _validation_messages(instance: dict[str, object]) -> list[str]:
    report = Validator(
        SCHEMA_PATH,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    ).validate(instance, "PopulationSnapshotBundle")
    return [result.message for result in report.results]


def _native_validation_messages(
    instance: dict[str, object], target_class: str
) -> list[str]:
    report = Validator(
        SCHEMA_PATH,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    ).validate(instance, target_class)
    return [result.message for result in report.results]


def test_root_schema_has_stable_identity_and_population_bundle_vocabulary() -> None:
    """The canonical root exposes the first core and PILATES profile concepts."""
    schema_view = SchemaView(str(SCHEMA_PATH))

    assert schema_view.schema.id == "https://w3id.org/LBNL-UCB-STI/synergy-schema"
    assert schema_view.schema.name == "synergy_schema"
    assert schema_view.schema.title == "Synergy Schema"
    assert (
        schema_view.schema.prefixes["synergy_schema"].prefix_reference
        == "https://w3id.org/LBNL-UCB-STI/synergy-schema/"
    )
    assert {
        "PopulationSnapshot",
        "ProducingRunReference",
        "PhysicalArtifactReference",
        "ImmutableArtifactIdentity",
        "SchemaContractReference",
        "HandoffBundleMember",
        "HandoffBundle",
        "PopulationSnapshotBundleMember",
        "PopulationSnapshotBundle",
    }.issubset(schema_view.all_classes())


def test_root_schema_resolves_profile_imports_and_required_population_members() -> None:
    """The operational profile composes the shared bundle without native rows."""
    schema_view = SchemaView(str(SCHEMA_PATH))

    bundle = schema_view.induced_class("PopulationSnapshotBundle")
    assert bundle.is_a == "HandoffBundle"
    assert bundle.attributes["population_snapshot"].required is True
    assert bundle.attributes["members"].range == "PopulationSnapshotBundleMember"
    assert bundle.attributes["members"].minimum_cardinality == 3

    member = schema_view.induced_class("PopulationSnapshotBundleMember")
    assert member.is_a == "HandoffBundleMember"
    assert member.attributes["semantic_role"].range == "PopulationMemberRole"


def test_population_snapshot_bundle_fixture_is_valid() -> None:
    """The hand-written post-ATLAS specimen validates through LinkML."""
    assert _validation_messages(_load_fixture()) == []


def test_population_snapshot_bundle_requires_snapshot_and_population_members() -> None:
    """A handoff cannot omit its snapshot or one of its three population members."""
    missing_snapshot = deepcopy(_load_fixture())
    del missing_snapshot["population_snapshot"]
    assert _validation_messages(missing_snapshot)

    missing_member = deepcopy(_load_fixture())
    missing_member["members"].pop()
    assert _validation_messages(missing_member)


def test_root_schema_imports_all_native_atlas_population_record_contracts() -> None:
    """The canonical root exposes ATLAS-owned input and output record roots."""
    schema_view = SchemaView(str(SCHEMA_PATH))

    assert {
        "AtlasHouseholdInput",
        "AtlasPersonInput",
        "AtlasVehicleOutput",
    }.issubset(schema_view.all_classes())


def test_atlas_native_record_contracts_cover_each_physical_field_once() -> None:
    """Native roots retain every current ATLAS physical column exactly once."""
    schema_view = SchemaView(str(SCHEMA_PATH))

    assert (
        set(schema_view.induced_class("AtlasHouseholdInput").attributes)
        == ATLAS_HOUSEHOLD_FIELDS
    )
    assert (
        set(schema_view.induced_class("AtlasPersonInput").attributes)
        == ATLAS_PERSON_FIELDS
    )
    vehicle = schema_view.induced_class("AtlasVehicleOutput")
    assert set(vehicle.attributes) == ATLAS_VEHICLE_FIELDS
    assert vehicle.unique_keys["atlas_vehicle_year"].unique_key_slots == [
        "household_id",
        "vehicle_id",
        "year",
    ]


def test_representative_atlas_native_records_validate_through_linkml() -> None:
    """Synthetic ATLAS input/output rows validate through the official surface."""
    records = _load_atlas_records_fixture()

    assert (
        _native_validation_messages(records["household"], "AtlasHouseholdInput") == []
    )
    assert _native_validation_messages(records["person"], "AtlasPersonInput") == []
    assert _native_validation_messages(records["vehicle"], "AtlasVehicleOutput") == []


def test_atlas_native_record_identifiers_and_composite_key_fields_are_required() -> (
    None
):
    """IDs and all parts of the vehicle's natural key cannot be omitted."""
    records = _load_atlas_records_fixture()

    missing_household_id = deepcopy(records["household"])
    del missing_household_id["household_id"]
    assert _native_validation_messages(missing_household_id, "AtlasHouseholdInput")

    missing_person_id = deepcopy(records["person"])
    del missing_person_id["person_id"]
    assert _native_validation_messages(missing_person_id, "AtlasPersonInput")

    for field_name in ("household_id", "vehicle_id", "year"):
        incomplete_vehicle_key = deepcopy(records["vehicle"])
        del incomplete_vehicle_key[field_name]
        assert _native_validation_messages(incomplete_vehicle_key, "AtlasVehicleOutput")


def test_atlas_relationships_and_profile_contract_bindings_are_visible() -> None:
    """The profile records row ownership and role-to-native-root bindings."""
    schema_view = SchemaView(str(SCHEMA_PATH))
    person_household = schema_view.induced_slot("household_id", "AtlasPersonInput")
    vehicle_household = schema_view.induced_slot("household_id", "AtlasVehicleOutput")
    member = schema_view.induced_class("PopulationSnapshotBundleMember")
    contract = schema_view.induced_class("SchemaContractReference")
    fixture = _load_fixture()

    assert (
        person_household.annotations["relationship_target"].value
        == "AtlasHouseholdInput"
    )
    assert (
        vehicle_household.annotations["relationship_target"].value
        == "AtlasHouseholdInput"
    )
    assert member.annotations["contract_root_by_role"].value == (
        "households=AtlasHouseholdInput; persons=AtlasPersonInput; "
        "vehicles=AtlasVehicleOutput"
    )
    assert [
        entry["schema_contract"]["selected_root"] for entry in fixture["members"]
    ] == ["AtlasHouseholdInput", "AtlasPersonInput", "AtlasVehicleOutput"]
    assert contract.attributes["schema_digest_algorithm"].required is True
    assert contract.attributes["schema_digest_algorithm"].range == "DigestAlgorithm"
    assert {
        entry["schema_contract"]["schema_digest_algorithm"]
        for entry in fixture["members"]
    } == {"sha256"}


def test_atlas_ownership_directions_year_meaning_and_float_mismatches_are_visible() -> (
    None
):
    """Native contracts expose ownership, forecast year, and source-type departures."""
    schema_view = SchemaView(str(SCHEMA_PATH))
    household = schema_view.induced_class("AtlasHouseholdInput")
    person = schema_view.induced_class("AtlasPersonInput")
    vehicle = schema_view.induced_class("AtlasVehicleOutput")

    assert household.annotations["owner"].value == "ATLAS"
    assert person.annotations["owner"].value == "ATLAS"
    assert vehicle.annotations["owner"].value == "ATLAS"
    assert household.annotations["direction"].value == "input"
    assert person.annotations["direction"].value == "input"
    assert vehicle.annotations["direction"].value == "output"

    assert "forecast/output year" in vehicle.description
    assert (
        "forecast/output year" in vehicle.unique_keys["atlas_vehicle_year"].description
    )
    assert "forecast/output year" in vehicle.attributes["year"].description
    assert "model year" in vehicle.attributes["modelyear"].description

    assert household.annotations["observed_sqlmodel_float_to_integer"].value == (
        "household_id, gt55, age_of_head, gt2, seniors, workers, race_of_head, "
        "hispanic_status_of_head, and cars are semantically integral identifiers, "
        "indicators, counts, or codes despite observed Float stubs."
    )
    assert person.annotations["observed_sqlmodel_float_to_integer"].value == (
        "household_id, race_id, work_at_home, hours, student, hispanic, worker, "
        "sex, hispanic_1, age, and edu are semantically integral identifiers, "
        "ages, hours, indicators, or legacy numeric codes despite observed Float "
        "stubs."
    )
