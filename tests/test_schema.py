"""Contract tests for the canonical LinkML population handoff schema."""

from copy import deepcopy
import hashlib
from pathlib import Path

import pytest
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
EXAMPLE_PATH = (
    Path(__file__).parents[1]
    / "examples"
    / "post_atlas_population_bundle"
    / "population_snapshot_bundle.yaml"
)
ATLAS_RECORDS_EXAMPLE_PATH = (
    Path(__file__).parents[1]
    / "examples"
    / "post_atlas_population_bundle"
    / "atlas_population_records.yaml"
)
CORE_POPULATION_STATES_EXAMPLE_PATH = (
    Path(__file__).parents[1]
    / "examples"
    / "post_atlas_population_bundle"
    / "core_population_states.yaml"
)
VENDORED_CONSIST_RELEASE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "synergy_schema"
    / "schema"
    / "vendor"
    / "consist-provenance"
    / "0.1.0"
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
    return yaml.safe_load(EXAMPLE_PATH.read_text(encoding="utf-8"))


def _load_atlas_records_fixture() -> dict[str, dict[str, object]]:
    return yaml.safe_load(ATLAS_RECORDS_EXAMPLE_PATH.read_text(encoding="utf-8"))


def _load_core_population_states_fixture() -> dict[str, dict[str, object]]:
    return yaml.safe_load(
        CORE_POPULATION_STATES_EXAMPLE_PATH.read_text(encoding="utf-8")
    )


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
        "ConsistProvenanceContext",
        "ConsistProvenanceDocument",
        "ConsistRunReference",
        "ConsistArtifactReference",
        "ConsistRunArtifactAssociation",
    }.issubset(schema_view.all_classes())


def test_vendored_consist_release_matches_its_checksum_manifest() -> None:
    """The imported Consist closure remains byte-for-byte identical to its release."""
    checksum_path = VENDORED_CONSIST_RELEASE_PATH / "SHA256SUMS"
    assert checksum_path.is_file()

    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        expected_digest, relative_path = line.split("  ", maxsplit=1)
        asset_path = VENDORED_CONSIST_RELEASE_PATH / relative_path
        assert asset_path.is_file()
        assert hashlib.sha256(asset_path.read_bytes()).hexdigest() == expected_digest


def test_core_population_states_and_membership_are_snapshot_scoped() -> None:
    """Core records capture only state identity, snapshot scope, and membership."""
    schema_view = SchemaView(str(SCHEMA_PATH))

    assert {
        "HouseholdState",
        "PersonState",
        "HouseholdMembership",
    }.issubset(schema_view.all_classes())

    household = schema_view.induced_class("HouseholdState")
    person = schema_view.induced_class("PersonState")
    membership = schema_view.induced_class("HouseholdMembership")

    assert set(household.attributes) == {
        "household_state_id",
        "population_snapshot_ref",
        "longitudinal_household_ref",
    }
    assert set(person.attributes) == {
        "person_state_id",
        "population_snapshot_ref",
        "longitudinal_person_ref",
    }
    assert set(membership.attributes) == {
        "household_membership_id",
        "population_snapshot_ref",
        "person_state_ref",
        "household_state_ref",
    }

    for record, identifier in (
        (household, "household_state_id"),
        (person, "person_state_id"),
        (membership, "household_membership_id"),
    ):
        assert record.attributes[identifier].identifier is True
        assert record.attributes[identifier].required is True
        assert record.attributes["population_snapshot_ref"].required is True

    assert (
        membership.attributes["person_state_ref"]
        .annotations["relationship_target"]
        .value
        == "PersonState"
    )
    assert (
        membership.attributes["household_state_ref"]
        .annotations["relationship_target"]
        .value
        == "HouseholdState"
    )


def test_core_population_state_fixture_validates_and_requires_snapshot_scope() -> None:
    """Population state and membership cannot be modeled outside a snapshot."""
    records = _load_core_population_states_fixture()

    for target_class in ("HouseholdState", "PersonState", "HouseholdMembership"):
        assert _native_validation_messages(records[target_class], target_class) == []

    incomplete_membership = deepcopy(records["HouseholdMembership"])
    del incomplete_membership["population_snapshot_ref"]
    assert _native_validation_messages(incomplete_membership, "HouseholdMembership")


def _assert_example_cross_file_identity(
    bundle: dict[str, object],
    native_records: dict[str, dict[str, object]],
    population_states: dict[str, dict[str, object]],
) -> None:
    snapshot_id = bundle["population_snapshot"]["id"]
    household_id = native_records["household"]["household_id"]
    person_id = native_records["person"]["person_id"]
    region_context = "synthetic-region"

    assert native_records["person"]["household_id"] == household_id
    assert native_records["vehicle"]["household_id"] == household_id
    assert population_states["HouseholdState"]["population_snapshot_ref"] == snapshot_id
    assert population_states["PersonState"]["population_snapshot_ref"] == snapshot_id
    assert (
        population_states["HouseholdMembership"]["population_snapshot_ref"]
        == snapshot_id
    )
    assert (
        population_states["HouseholdMembership"]["household_state_ref"]
        == population_states["HouseholdState"]["household_state_id"]
    )
    assert (
        population_states["HouseholdMembership"]["person_state_ref"]
        == population_states["PersonState"]["person_state_id"]
    )
    assert population_states["HouseholdState"]["longitudinal_household_ref"] == (
        f"household:{region_context}:{household_id}"
    )
    assert population_states["PersonState"]["longitudinal_person_ref"] == (
        f"person:{region_context}:{person_id}"
    )
    assert population_states["HouseholdMembership"]["household_membership_id"].rsplit(
        ":", 2
    )[1:] == [str(person_id), str(household_id)]


def _consist_reference_identity(
    reference: dict[str, object],
    enclosing_context: dict[str, object],
    identifier_field: str,
) -> tuple[object, object]:
    context = reference.get("provenance_context", enclosing_context)
    return context["namespace"], reference[identifier_field]


def _assert_example_provenance_consistency(bundle: dict[str, object]) -> None:
    provenance = bundle["consist_provenance"]
    enclosing_context = provenance["provenance_context"]
    producing_run = bundle["producing_run"]
    assert producing_run["provider"] == "consist"

    run_identity = (
        enclosing_context["namespace"],
        producing_run["run_id"],
    )
    assert {
        _consist_reference_identity(run, enclosing_context, "run_id")
        for run in provenance["runs"]
    } == {run_identity}

    artifacts_by_id = {
        artifact["artifact_id"]: artifact for artifact in provenance["artifacts"]
    }
    members_by_role = {member["semantic_role"]: member for member in bundle["members"]}
    output_associations_by_role = {
        association["role"]: association
        for association in provenance["associations"]
        if association["direction"] == "output"
    }
    assert set(output_associations_by_role) == set(members_by_role)

    for role, member in members_by_role.items():
        association = output_associations_by_role[role]
        artifact = artifacts_by_id[association["artifact"]["artifact_id"]]
        assert (
            _consist_reference_identity(association["run"], enclosing_context, "run_id")
            == run_identity
        )
        assert (
            _consist_reference_identity(
                artifact["producing_run"], enclosing_context, "run_id"
            )
            == run_identity
        )
        assert (
            artifact["immutable_identity"]["algorithm"]
            == (member["artifact"]["artifact_identity"]["digest_algorithm"])
        )
        assert (
            artifact["immutable_identity"]["digest"]
            == (member["artifact"]["artifact_identity"]["content_digest"])
        )


def test_example_records_share_the_snapshot_and_household_identity() -> None:
    """The tracked example tells one internally consistent synthetic story."""
    _assert_example_cross_file_identity(
        _load_fixture(),
        _load_atlas_records_fixture(),
        _load_core_population_states_fixture(),
    )


def test_example_consist_provenance_matches_bundle_members_and_producer() -> None:
    """Consist production edges and identities agree with the semantic handoff."""
    bundle = _load_fixture()
    assert "consist_provenance" in bundle
    _assert_example_provenance_consistency(bundle)


def test_example_provenance_identity_uses_namespace_but_not_locator() -> None:
    """Namespace changes identity while mutable locator changes do not."""
    bundle = _load_fixture()
    assert "consist_provenance" in bundle
    provenance = bundle["consist_provenance"]
    context = provenance["provenance_context"]
    run = provenance["runs"][0]
    original_identity = _consist_reference_identity(run, context, "run_id")

    relocated_bundle = deepcopy(bundle)
    relocated_provenance = relocated_bundle["consist_provenance"]
    relocated_provenance["provenance_context"]["locator"] = (
        "https://ledger.example.org/moved"
    )
    relocated_bundle["producing_run"]["run_locator"] = "runs/moved"
    for member in relocated_bundle["members"]:
        member["artifact"]["locator"] = f"moved/{member['semantic_role']}.parquet"
    relocated_identity = _consist_reference_identity(
        relocated_provenance["runs"][0],
        relocated_provenance["provenance_context"],
        "run_id",
    )
    assert relocated_identity == original_identity
    _assert_example_provenance_consistency(relocated_bundle)

    other_namespace_bundle = deepcopy(bundle)
    other_provenance = other_namespace_bundle["consist_provenance"]
    other_provenance["provenance_context"]["namespace"] = "urn:consist:other"
    other_identity = _consist_reference_identity(
        other_provenance["runs"][0],
        other_provenance["provenance_context"],
        "run_id",
    )
    assert other_identity != original_identity


def test_example_provenance_checks_reject_producer_and_digest_drift() -> None:
    """Conflicting producers and artifact digests cannot pass the example checks."""
    bundle = _load_fixture()
    assert "consist_provenance" in bundle

    wrong_producer = deepcopy(bundle)
    wrong_producer["consist_provenance"]["artifacts"][0]["producing_run"]["run_id"] = (
        "run:other"
    )
    with pytest.raises(AssertionError):
        _assert_example_provenance_consistency(wrong_producer)

    wrong_digest = deepcopy(bundle)
    wrong_digest["consist_provenance"]["artifacts"][0]["immutable_identity"][
        "digest"
    ] = "f" * 64
    with pytest.raises(AssertionError):
        _assert_example_provenance_consistency(wrong_digest)


def test_example_identity_assertions_reject_corrupted_state_copies() -> None:
    """Longitudinal and membership identities cannot drift from native IDs."""
    bundle = _load_fixture()
    native_records = _load_atlas_records_fixture()
    population_states = _load_core_population_states_fixture()

    corruptions = (
        (
            "HouseholdState",
            "longitudinal_household_ref",
            "household:synthetic-region:999",
        ),
        ("PersonState", "longitudinal_person_ref", "person:synthetic-region:999"),
        (
            "HouseholdMembership",
            "household_membership_id",
            "household-membership:synthetic-region-2025-r1:999:999",
        ),
    )
    for record_name, field_name, corrupted_value in corruptions:
        corrupted_states = deepcopy(population_states)
        corrupted_states[record_name][field_name] = corrupted_value

        with pytest.raises(AssertionError):
            _assert_example_cross_file_identity(
                bundle,
                native_records,
                corrupted_states,
            )


def test_root_schema_resolves_profile_imports_and_required_population_members() -> None:
    """The operational profile composes the shared bundle without native rows."""
    schema_view = SchemaView(str(SCHEMA_PATH))

    bundle = schema_view.induced_class("PopulationSnapshotBundle")
    assert bundle.is_a == "HandoffBundle"
    assert bundle.attributes["population_snapshot"].required is True
    assert bundle.attributes["consist_provenance"].required is True
    assert bundle.attributes["consist_provenance"].range == "ConsistProvenanceDocument"
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
