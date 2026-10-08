from copy import deepcopy
from pathlib import Path

import pytest
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

MAPPINGS_PATH = (
    Path(__file__).parents[1]
    / "examples"
    / "post_atlas_population_bundle"
    / "population_identity_mappings.yaml"
)

CROSS_MODEL_RECORDS_PATH = (
    Path(__file__).parents[1]
    / "examples"
    / "post_atlas_population_bundle"
    / "cross_model_population_records.yaml"
)
ATLAS_RECORDS_PATH = (
    Path(__file__).parents[1]
    / "examples"
    / "post_atlas_population_bundle"
    / "atlas_population_records.yaml"
)
BUNDLE_PATH = (
    Path(__file__).parents[1]
    / "examples"
    / "post_atlas_population_bundle"
    / "population_snapshot_bundle.yaml"
)


def _messages(instance: dict[str, object], target_class: str) -> list[str]:
    report = Validator(
        SCHEMA_PATH,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    ).validate(instance, target_class)
    return [result.message for result in report.results]


def _mapping_fixture() -> dict[str, dict[str, object]]:
    import yaml

    return yaml.safe_load(MAPPINGS_PATH.read_text(encoding="utf-8"))


def _yaml(path: Path) -> dict[str, object]:
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _evidence_by_path_pair(
    slot_mappings: list[dict[str, object]],
) -> dict[tuple[str, str], str]:
    for entry in slot_mappings:
        assert isinstance(entry["evidence"], list), "mapping evidence must be a list"
        assert (
            len(entry["source_paths"])
            == len(entry["target_paths"])
            == len(entry["evidence"])
        ), "mapping legs require aligned evidence"
    leg_count = sum(len(entry["source_paths"]) for entry in slot_mappings)
    evidence = {
        (source_path, target_path): evidence_path
        for entry in slot_mappings
        for source_path, target_path, evidence_path in zip(
            entry["source_paths"], entry["target_paths"], entry["evidence"], strict=True
        )
    }
    assert len(evidence) == leg_count, "duplicate source and target path pair"
    return evidence


def _evidence_by_mapping_target(
    slot_mappings: list[dict[str, object]],
) -> dict[tuple[str, str], str]:
    for entry in slot_mappings:
        assert isinstance(entry["evidence"], list), "mapping evidence must be a list"
        assert len(entry["target_paths"]) == len(entry["evidence"]), (
            "mapping targets require aligned evidence"
        )
    target_count = sum(len(entry["target_paths"]) for entry in slot_mappings)
    evidence = {
        (entry["id"], target_path): evidence_path
        for entry in slot_mappings
        for target_path, evidence_path in zip(
            entry["target_paths"], entry["evidence"], strict=True
        )
    }
    assert len(evidence) == target_count, "duplicate mapping identifier and target"
    return evidence


def _scoped_vehicle_identity(
    atlas_vehicle: dict[str, object],
    polaris_vehicle: dict[str, object],
    snapshot: dict[str, object],
) -> tuple[int, int, int]:
    assert set(atlas_vehicle).issuperset({"household_id", "vehicle_id", "year"})
    assert set(polaris_vehicle) == {"vehicle_id", "hhold"}
    assert polaris_vehicle["hhold"] == atlas_vehicle["household_id"]
    assert polaris_vehicle["vehicle_id"] == atlas_vehicle["vehicle_id"]
    snapshot_year = snapshot.get("simulation_year")
    assert snapshot_year is not None, "enclosing snapshot year is required"
    assert atlas_vehicle["year"] == snapshot_year, (
        "ATLAS vehicle year must match the enclosing population snapshot year"
    )
    return (
        polaris_vehicle["hhold"],
        polaris_vehicle["vehicle_id"],
        snapshot_year,
    )


def test_mapping_vocabulary_is_imported_with_controlled_classifications() -> None:
    schema_view = SchemaView(str(SCHEMA_PATH))
    assert {
        "PopulationIdentityConstruction",
        "PopulationRepresentationMapping",
        "PopulationSlotMapping",
    }.issubset(schema_view.all_classes())
    construction_slot = schema_view.induced_slot(
        "identity_constructions", "PopulationRepresentationMapping"
    )
    assert construction_slot.range == "PopulationIdentityConstruction"
    assert construction_slot.multivalued is True
    assert construction_slot.inlined_as_list is True
    assert set(schema_view.get_enum("PopulationMappingStatus").permissible_values) == {
        "direct",
        "renamed",
        "unit_or_enum_converted",
        "derived",
        "unsupported",
        "platform_specific",
    }
    assert set(schema_view.get_enum("PopulationIdentityRole").permissible_values) == {
        "entity_identifier",
        "relationship_foreign_key",
        "within_parent_ordinal",
        "geographic_identifier",
        "artifact_scoped_identifier",
    }
    assert set(schema_view.get_enum("PopulationValueStability").permissible_values) == {
        "preserved",
        "derived",
        "regenerated",
        "alias",
        "artifact_scoped",
    }


def test_root_exposes_cross_model_population_identity_projections() -> None:
    schema_view = SchemaView(str(SCHEMA_PATH))
    assert {
        "UrbanSimHouseholdPopulationRecord",
        "UrbanSimPersonPopulationRecord",
        "ActivitySimHouseholdInputRecord",
        "ActivitySimPersonInputRecord",
        "ActivitySimLandUseZoneRecord",
        "PolarisHouseholdRecord",
        "PolarisPersonRecord",
        "PolarisVehicleRecord",
    }.issubset(schema_view.all_classes())


def test_population_projection_shapes_expose_only_identity_join_fields() -> None:
    schema_view = SchemaView(str(SCHEMA_PATH))
    expected = {
        "UrbanSimHouseholdPopulationRecord": {"household_id", "block_id"},
        "UrbanSimPersonPopulationRecord": {
            "person_id",
            "household_id",
            "member_id",
            "work_zone_id",
            "school_zone_id",
        },
        "ActivitySimHouseholdInputRecord": {
            "household_id",
            "block_id",
            "taz",
            "cars",
            "auto_ownership",
        },
        "ActivitySimPersonInputRecord": {
            "person_id",
            "household_id",
            "member_id",
            "taz",
            "work_zone_id",
            "workplace_taz",
            "school_zone_id",
            "school_taz",
        },
        "ActivitySimLandUseZoneRecord": {"taz"},
        "PolarisHouseholdRecord": {"household", "hhold", "location"},
        "PolarisPersonRecord": {"person", "household", "id"},
        "PolarisVehicleRecord": {"vehicle_id", "hhold"},
    }
    for class_name, fields in expected.items():
        assert set(schema_view.induced_class(class_name).attributes) == fields


def test_projection_identifiers_and_physical_names_are_explicit() -> None:
    schema_view = SchemaView(str(SCHEMA_PATH))
    cases = {
        "UrbanSimHouseholdPopulationRecord": ({"household_id": 101}, "household_id"),
        "UrbanSimPersonPopulationRecord": (
            {"person_id": 1001, "household_id": 101},
            "person_id",
        ),
        "ActivitySimHouseholdInputRecord": ({"household_id": 101}, "household_id"),
        "ActivitySimPersonInputRecord": (
            {"person_id": 1001, "household_id": 101, "member_id": 1},
            "person_id",
        ),
        "ActivitySimLandUseZoneRecord": ({"taz": 5001}, "taz"),
        "PolarisHouseholdRecord": (
            {"household": 101, "hhold": 101},
            "household",
        ),
        "PolarisPersonRecord": (
            {"person": 1001, "household": 101, "id": 0},
            "person",
        ),
    }
    for class_name, (record, identifier) in cases.items():
        assert _messages(record, class_name) == []
        induced = schema_view.induced_class(class_name)
        assert induced.attributes[identifier].identifier is True
        missing = deepcopy(record)
        del missing[identifier]
        assert _messages(missing, class_name)

    assert (
        schema_view.induced_slot("taz", "ActivitySimLandUseZoneRecord")
        .annotations["physical_name"]
        .value
        == "TAZ"
    )


def test_polaris_vehicle_uses_a_composite_row_key_with_snapshot_scope() -> None:
    schema_view = SchemaView(str(SCHEMA_PATH))
    vehicle = schema_view.induced_class("PolarisVehicleRecord")

    assert vehicle.attributes["vehicle_id"].identifier is not True
    assert vehicle.unique_keys["polaris_vehicle_row"].unique_key_slots == [
        "hhold",
        "vehicle_id",
    ]
    assert (
        vehicle.annotations["identity_scope"].value
        == "enclosing translated population snapshot artifact"
    )

    record = {"hhold": 101, "vehicle_id": 1}
    assert _messages(record, "PolarisVehicleRecord") == []
    for required_field in ("hhold", "vehicle_id"):
        missing = deepcopy(record)
        del missing[required_field]
        assert _messages(missing, "PolarisVehicleRecord")


@pytest.mark.parametrize(
    ("target_class", "record", "required_field"),
    [
        (
            "UrbanSimPersonPopulationRecord",
            {"person_id": 1001, "household_id": 101},
            "household_id",
        ),
        (
            "ActivitySimPersonInputRecord",
            {"person_id": 1001, "household_id": 101, "member_id": 1},
            "household_id",
        ),
        (
            "ActivitySimPersonInputRecord",
            {"person_id": 1001, "household_id": 101, "member_id": 1},
            "member_id",
        ),
        (
            "PolarisHouseholdRecord",
            {"household": 101, "hhold": 101},
            "hhold",
        ),
        (
            "PolarisPersonRecord",
            {"person": 1001, "household": 101, "id": 0},
            "household",
        ),
        (
            "PolarisPersonRecord",
            {"person": 1001, "household": 101, "id": 0},
            "id",
        ),
        (
            "PolarisVehicleRecord",
            {"vehicle_id": 1, "hhold": 101},
            "hhold",
        ),
    ],
)
def test_required_relationship_and_ordinal_fields_are_enforced(
    target_class: str,
    record: dict[str, object],
    required_field: str,
) -> None:
    assert _messages(record, target_class) == []
    missing = deepcopy(record)
    del missing[required_field]
    assert _messages(missing, target_class)


@pytest.mark.parametrize(
    ("target_class", "slot_name", "relationship_target", "scalar_record"),
    [
        (
            "PopulationSnapshot",
            "parent_snapshot_ref",
            "PopulationSnapshot",
            {
                "id": "population-snapshot:synthetic-region-2025-r1",
                "scenario_definition_ref": {
                    "scenario_definition_id": "scenario:synthetic-region",
                    "revision": "synthetic-r1",
                    "content_digest": "a" * 64,
                },
                "stochastic_realization_id": "r1",
                "simulation_year": 2025,
                "parent_snapshot_ref": "population-snapshot:synthetic-region-2020-r1",
            },
        ),
        (
            "HouseholdState",
            "population_snapshot_ref",
            "PopulationSnapshot",
            {
                "household_state_id": "household-state:synthetic-region-2025-r1:101",
                "population_snapshot_ref": "population-snapshot:synthetic-region-2025-r1",
            },
        ),
        (
            "PersonState",
            "population_snapshot_ref",
            "PopulationSnapshot",
            {
                "person_state_id": "person-state:synthetic-region-2025-r1:1001",
                "population_snapshot_ref": "population-snapshot:synthetic-region-2025-r1",
            },
        ),
        (
            "HouseholdMembership",
            "population_snapshot_ref",
            "PopulationSnapshot",
            {
                "household_membership_id": "household-membership:synthetic-region-2025-r1:1001:101",
                "population_snapshot_ref": "population-snapshot:synthetic-region-2025-r1",
                "person_state_ref": "person-state:synthetic-region-2025-r1:1001",
                "household_state_ref": "household-state:synthetic-region-2025-r1:101",
            },
        ),
        (
            "HouseholdMembership",
            "person_state_ref",
            "PersonState",
            {
                "household_membership_id": "household-membership:synthetic-region-2025-r1:1001:101",
                "population_snapshot_ref": "population-snapshot:synthetic-region-2025-r1",
                "person_state_ref": "person-state:synthetic-region-2025-r1:1001",
                "household_state_ref": "household-state:synthetic-region-2025-r1:101",
            },
        ),
        (
            "HouseholdMembership",
            "household_state_ref",
            "HouseholdState",
            {
                "household_membership_id": "household-membership:synthetic-region-2025-r1:1001:101",
                "population_snapshot_ref": "population-snapshot:synthetic-region-2025-r1",
                "person_state_ref": "person-state:synthetic-region-2025-r1:1001",
                "household_state_ref": "household-state:synthetic-region-2025-r1:101",
            },
        ),
        (
            "UrbanSimPersonPopulationRecord",
            "household_id",
            "UrbanSimHouseholdPopulationRecord",
            {"person_id": 1001, "household_id": 101},
        ),
        (
            "ActivitySimHouseholdInputRecord",
            "taz",
            "ActivitySimLandUseZoneRecord",
            {"household_id": 101, "taz": 5001},
        ),
        (
            "ActivitySimPersonInputRecord",
            "household_id",
            "ActivitySimHouseholdInputRecord",
            {"person_id": 1001, "household_id": 101, "member_id": 1},
        ),
        (
            "ActivitySimPersonInputRecord",
            "taz",
            "ActivitySimLandUseZoneRecord",
            {"person_id": 1001, "household_id": 101, "member_id": 1, "taz": 5001},
        ),
        (
            "AtlasPersonInput",
            "household_id",
            "AtlasHouseholdInput",
            {"person_id": 1001, "household_id": 101},
        ),
        (
            "AtlasVehicleOutput",
            "household_id",
            "AtlasHouseholdInput",
            {"household_id": 101, "vehicle_id": 1, "year": 2025},
        ),
        (
            "AtlasVehicleOutput",
            "maindriver_id",
            "AtlasPersonInput",
            {
                "household_id": 101,
                "vehicle_id": 1,
                "year": 2025,
                "maindriver_id": 1001,
            },
        ),
        (
            "PolarisPersonRecord",
            "household",
            "PolarisHouseholdRecord",
            {"person": 1001, "household": 101, "id": 0},
        ),
        (
            "PolarisVehicleRecord",
            "hhold",
            "PolarisHouseholdRecord",
            {"vehicle_id": 1, "hhold": 101},
        ),
    ],
)
def test_native_reference_ranges_preserve_scalar_identifier_encodings(
    target_class: str,
    slot_name: str,
    relationship_target: str,
    scalar_record: dict[str, object],
) -> None:
    schema_view = SchemaView(str(SCHEMA_PATH))
    slot = schema_view.induced_slot(slot_name, target_class)

    assert slot.range == relationship_target
    assert slot.inlined is False
    assert slot.annotations["relationship_target"].value == relationship_target
    assert _messages(scalar_record, target_class) == []


def test_population_mapping_manifest_validates_and_is_evidence_complete() -> None:
    mappings = _mapping_fixture()
    assert set(mappings) == {
        "urbansim_activitysim_population",
        "activitysim_atlas_population",
        "atlas_core_population_state",
        "atlas_polaris_population",
    }
    for mapping in mappings.values():
        assert _messages(mapping, "PopulationRepresentationMapping") == []
        for slot_mapping in mapping["slot_mappings"]:
            assert slot_mapping["mapping_status"]
            assert slot_mapping["identity_role"]
            assert slot_mapping["value_stability"]
            assert slot_mapping["transformation"]
            assert (
                len(slot_mapping["source_paths"])
                == len(slot_mapping["target_paths"])
                == len(slot_mapping["evidence"])
            )
            assert all(
                evidence.startswith(("pilates/", "src/", "examples/"))
                for evidence in slot_mapping["evidence"]
            )
        for construction in mapping.get("identity_constructions", []):
            assert construction["mapping_status"] == "derived"
            assert len(construction["source_paths"]) >= 2
            assert construction["target_path"]
            assert construction["identity_role"] == "artifact_scoped_identifier"
            assert construction["value_stability"] == "artifact_scoped"
            assert construction["transformation"]
            assert construction["evidence"]


def test_atlas_and_snapshot_context_map_to_core_population_states() -> None:
    mapping = _mapping_fixture()["atlas_core_population_state"]
    slots = {
        entry["id"]: (
            entry["source_paths"],
            entry["target_paths"],
            entry["mapping_status"],
            entry["identity_role"],
            entry["value_stability"],
            entry["relationship_cardinality"],
        )
        for entry in mapping["slot_mappings"]
    }
    assert slots == {
        "atlas_core_household_longitudinal_identity": (
            ["AtlasHouseholdInput.household_id"],
            ["HouseholdState.longitudinal_household_ref"],
            "derived",
            "entity_identifier",
            "preserved",
            "one-to-one",
        ),
        "atlas_core_household_snapshot_scope": (
            ["PopulationSnapshot.id"],
            ["HouseholdState.population_snapshot_ref"],
            "direct",
            "relationship_foreign_key",
            "preserved",
            "one-to-many",
        ),
        "atlas_core_person_longitudinal_identity": (
            ["AtlasPersonInput.person_id"],
            ["PersonState.longitudinal_person_ref"],
            "derived",
            "entity_identifier",
            "preserved",
            "one-to-one",
        ),
        "atlas_core_person_snapshot_scope": (
            ["PopulationSnapshot.id"],
            ["PersonState.population_snapshot_ref"],
            "direct",
            "relationship_foreign_key",
            "preserved",
            "one-to-many",
        ),
        "atlas_core_membership_person_state": (
            ["AtlasPersonInput.person_id"],
            ["HouseholdMembership.person_state_ref"],
            "derived",
            "relationship_foreign_key",
            "artifact_scoped",
            "one-to-one",
        ),
        "atlas_core_membership_household_state": (
            ["AtlasPersonInput.household_id"],
            ["HouseholdMembership.household_state_ref"],
            "derived",
            "relationship_foreign_key",
            "artifact_scoped",
            "many-to-one",
        ),
        "atlas_core_membership_snapshot_scope": (
            ["PopulationSnapshot.id"],
            ["HouseholdMembership.population_snapshot_ref"],
            "direct",
            "relationship_foreign_key",
            "preserved",
            "one-to-many",
        ),
    }

    constructions = {
        entry["id"]: (entry["source_paths"], entry["target_path"])
        for entry in mapping["identity_constructions"]
    }
    assert constructions == {
        "construct_household_state_identity": (
            [
                "PopulationSnapshot.id",
                "HouseholdState.longitudinal_household_ref",
            ],
            "HouseholdState.household_state_id",
        ),
        "construct_person_state_identity": (
            [
                "PopulationSnapshot.id",
                "PersonState.longitudinal_person_ref",
            ],
            "PersonState.person_state_id",
        ),
        "construct_household_membership_identity": (
            [
                "PopulationSnapshot.id",
                "HouseholdMembership.person_state_ref",
                "HouseholdMembership.household_state_ref",
            ],
            "HouseholdMembership.household_membership_id",
        ),
    }


def test_unstable_local_ordinals_are_not_mapped_as_preserved_entity_ids() -> None:
    slot_mappings = [
        entry
        for mapping in _mapping_fixture().values()
        for entry in mapping["slot_mappings"]
    ]
    for entry in slot_mappings:
        if any(path.endswith(".member_id") for path in entry["source_paths"]):
            assert entry["identity_role"] == "within_parent_ordinal"
            assert entry["value_stability"] in {"derived", "regenerated"}


def test_atlas_polaris_evidence_is_exact_for_each_translation_path_pair() -> None:
    slot_mappings = _mapping_fixture()["atlas_polaris_population"]["slot_mappings"]
    actual = _evidence_by_path_pair(slot_mappings)
    assert actual == {
        ("AtlasHouseholdInput.household_id", "PolarisHouseholdRecord.household"): (
            "pilates/generated/polaris_population_translation/10_households.sql:7"
        ),
        ("AtlasHouseholdInput.household_id", "PolarisHouseholdRecord.hhold"): (
            "pilates/generated/polaris_population_translation/10_households.sql:8"
        ),
        ("AtlasPersonInput.person_id", "PolarisPersonRecord.person"): (
            "pilates/generated/polaris_population_translation/20_persons.sql:10"
        ),
        ("AtlasPersonInput.household_id", "PolarisPersonRecord.household"): (
            "pilates/generated/polaris_population_translation/20_persons.sql:79"
        ),
        ("AtlasPersonInput.member_id", "PolarisPersonRecord.id"): (
            "pilates/generated/polaris_population_translation/20_persons.sql:11"
        ),
        ("AtlasVehicleOutput.household_id", "PolarisVehicleRecord.hhold"): (
            "pilates/generated/polaris_population_translation/40_vehicles.sql:6"
        ),
        ("AtlasVehicleOutput.vehicle_id", "PolarisVehicleRecord.vehicle_id"): (
            "pilates/generated/polaris_population_translation/40_vehicles.sql:5"
        ),
        ("AtlasVehicleOutput.year", "PopulationSnapshot.simulation_year"): (
            "pilates/generated/polaris_population_translation/40_vehicles.sql:3-6"
        ),
    }


def test_atlas_polaris_evidence_rejects_duplicate_translation_path_pairs() -> None:
    slot_mappings = deepcopy(
        _mapping_fixture()["atlas_polaris_population"]["slot_mappings"]
    )
    duplicate = deepcopy(slot_mappings[0])
    duplicate["id"] = "duplicate_household_identity"
    duplicate["evidence"] = [
        "pilates/generated/polaris_population_translation/10_households.sql:999"
    ]
    slot_mappings.append(duplicate)

    with pytest.raises(AssertionError, match="duplicate source and target path pair"):
        _evidence_by_path_pair(slot_mappings)


def test_atlas_polaris_identity_mappings_match_the_generated_sql_contract() -> None:
    slot_mappings = _mapping_fixture()["atlas_polaris_population"]["slot_mappings"]
    actual = {
        entry["id"]: (
            entry["source_paths"],
            entry["target_paths"],
            entry["mapping_status"],
            entry["value_stability"],
        )
        for entry in slot_mappings
    }
    assert actual == {
        "atlas_polaris_household_identity": (
            ["AtlasHouseholdInput.household_id"],
            ["PolarisHouseholdRecord.household"],
            "renamed",
            "preserved",
        ),
        "atlas_polaris_household_hhold_identity": (
            ["AtlasHouseholdInput.household_id"],
            ["PolarisHouseholdRecord.hhold"],
            "renamed",
            "alias",
        ),
        "atlas_polaris_person_identity": (
            ["AtlasPersonInput.person_id"],
            ["PolarisPersonRecord.person"],
            "renamed",
            "preserved",
        ),
        "atlas_polaris_person_household_membership": (
            ["AtlasPersonInput.household_id"],
            ["PolarisPersonRecord.household"],
            "renamed",
            "preserved",
        ),
        "atlas_polaris_member_ordinal": (
            ["AtlasPersonInput.member_id"],
            ["PolarisPersonRecord.id"],
            "derived",
            "derived",
        ),
        "atlas_polaris_vehicle_scoped_identity": (
            [
                "AtlasVehicleOutput.household_id",
                "AtlasVehicleOutput.vehicle_id",
                "AtlasVehicleOutput.year",
            ],
            [
                "PolarisVehicleRecord.hhold",
                "PolarisVehicleRecord.vehicle_id",
                "PopulationSnapshot.simulation_year",
            ],
            "derived",
            "artifact_scoped",
        ),
    }


def test_activitysim_atlas_identity_mappings_match_the_population_handoff() -> None:
    slot_mappings = _mapping_fixture()["activitysim_atlas_population"]["slot_mappings"]
    actual = {
        entry["id"]: (
            entry["source_paths"],
            entry["target_paths"],
            entry["mapping_status"],
            entry["identity_role"],
            entry["relationship_cardinality"],
            entry["value_stability"],
        )
        for entry in slot_mappings
    }
    assert actual == {
        "activitysim_atlas_household_identity": (
            ["ActivitySimHouseholdInputRecord.household_id"],
            ["AtlasHouseholdInput.household_id"],
            "direct",
            "entity_identifier",
            "one-to-one",
            "preserved",
        ),
        "activitysim_atlas_person_identity": (
            ["ActivitySimPersonInputRecord.person_id"],
            ["AtlasPersonInput.person_id"],
            "direct",
            "entity_identifier",
            "one-to-one",
            "preserved",
        ),
        "activitysim_atlas_person_household_membership": (
            ["ActivitySimPersonInputRecord.household_id"],
            ["AtlasPersonInput.household_id"],
            "direct",
            "relationship_foreign_key",
            "many-to-one",
            "preserved",
        ),
    }


def test_each_population_mapping_target_has_exact_implementation_evidence() -> None:
    slot_mappings = [
        entry
        for mapping in _mapping_fixture().values()
        for entry in mapping["slot_mappings"]
        if all(evidence.startswith("pilates/") for evidence in entry["evidence"])
    ]
    assert _evidence_by_mapping_target(slot_mappings) == {
        (
            "urbansim_activitysim_household_identity",
            "ActivitySimHouseholdInputRecord.household_id",
        ): ("pilates/activitysim/preprocessor.py:3524"),
        (
            "activitysim_atlas_household_identity",
            "AtlasHouseholdInput.household_id",
        ): (
            "pilates/activitysim/postprocessor.py:470-488; "
            "pilates/activitysim/postprocessor.py:715-723; "
            "pilates/atlas/preprocessor.py:836-844"
        ),
        (
            "activitysim_atlas_person_identity",
            "AtlasPersonInput.person_id",
        ): (
            "pilates/activitysim/postprocessor.py:424-468; "
            "pilates/activitysim/postprocessor.py:715-723; "
            "pilates/atlas/preprocessor.py:855-861"
        ),
        (
            "activitysim_atlas_person_household_membership",
            "AtlasPersonInput.household_id",
        ): (
            "pilates/activitysim/postprocessor.py:424-468; "
            "pilates/activitysim/postprocessor.py:715-723; "
            "pilates/atlas/preprocessor.py:855-861"
        ),
        (
            "urbansim_activitysim_person_identity",
            "ActivitySimPersonInputRecord.person_id",
        ): ("pilates/activitysim/preprocessor.py:3259"),
        (
            "urbansim_activitysim_person_household_membership",
            "ActivitySimPersonInputRecord.household_id",
        ): ("pilates/activitysim/preprocessor.py:3269"),
        (
            "urbansim_activitysim_person_household_membership",
            "ActivitySimHouseholdInputRecord.household_id",
        ): ("pilates/activitysim/preprocessor.py:3269"),
        (
            "urbansim_activitysim_member_ordinal",
            "ActivitySimPersonInputRecord.member_id",
        ): ("pilates/activitysim/preprocessor.py:3349"),
        (
            "urbansim_activitysim_household_block_to_taz",
            "ActivitySimHouseholdInputRecord.taz",
        ): ("pilates/activitysim/preprocessor.py:3523"),
        (
            "urbansim_activitysim_person_block_to_taz",
            "ActivitySimPersonInputRecord.taz",
        ): ("pilates/activitysim/preprocessor.py:3268-3271"),
        (
            "activitysim_work_location_aliases",
            "ActivitySimPersonInputRecord.workplace_taz",
        ): ("pilates/activitysim/preprocessor.py:3255"),
        (
            "activitysim_school_location_alias",
            "ActivitySimPersonInputRecord.school_taz",
        ): ("pilates/activitysim/preprocessor.py:3257"),
        ("atlas_polaris_household_identity", "PolarisHouseholdRecord.household"): (
            "pilates/generated/polaris_population_translation/10_households.sql:7"
        ),
        ("atlas_polaris_household_hhold_identity", "PolarisHouseholdRecord.hhold"): (
            "pilates/generated/polaris_population_translation/10_households.sql:8"
        ),
        ("atlas_polaris_person_identity", "PolarisPersonRecord.person"): (
            "pilates/generated/polaris_population_translation/20_persons.sql:10"
        ),
        (
            "atlas_polaris_person_household_membership",
            "PolarisPersonRecord.household",
        ): ("pilates/generated/polaris_population_translation/20_persons.sql:79"),
        ("atlas_polaris_member_ordinal", "PolarisPersonRecord.id"): (
            "pilates/generated/polaris_population_translation/20_persons.sql:11"
        ),
        ("atlas_polaris_vehicle_scoped_identity", "PolarisVehicleRecord.hhold"): (
            "pilates/generated/polaris_population_translation/40_vehicles.sql:6"
        ),
        ("atlas_polaris_vehicle_scoped_identity", "PolarisVehicleRecord.vehicle_id"): (
            "pilates/generated/polaris_population_translation/40_vehicles.sql:5"
        ),
        (
            "atlas_polaris_vehicle_scoped_identity",
            "PopulationSnapshot.simulation_year",
        ): ("pilates/generated/polaris_population_translation/40_vehicles.sql:3-6"),
    }


def test_core_population_mapping_targets_have_exact_schema_evidence() -> None:
    slot_mappings = _mapping_fixture()["atlas_core_population_state"]["slot_mappings"]
    assert _evidence_by_mapping_target(slot_mappings) == {
        (
            "atlas_core_household_longitudinal_identity",
            "HouseholdState.longitudinal_household_ref",
        ): (
            "src/synergy_schema/schema/models/atlas/atlas_population.yaml:35-39; "
            "examples/post_atlas_population_bundle/core_population_states.yaml:1-4"
        ),
        (
            "atlas_core_household_snapshot_scope",
            "HouseholdState.population_snapshot_ref",
        ): "src/synergy_schema/schema/core/population_snapshot.yaml:26-29;66-78",
        (
            "atlas_core_person_longitudinal_identity",
            "PersonState.longitudinal_person_ref",
        ): (
            "src/synergy_schema/schema/models/atlas/atlas_population.yaml:127-131; "
            "examples/post_atlas_population_bundle/core_population_states.yaml:5-8"
        ),
        (
            "atlas_core_person_snapshot_scope",
            "PersonState.population_snapshot_ref",
        ): "src/synergy_schema/schema/core/population_snapshot.yaml:26-29;95-107",
        (
            "atlas_core_membership_person_state",
            "HouseholdMembership.person_state_ref",
        ): (
            "src/synergy_schema/schema/models/atlas/atlas_population.yaml:127-131; "
            "src/synergy_schema/schema/core/population_snapshot.yaml:137-146"
        ),
        (
            "atlas_core_membership_household_state",
            "HouseholdMembership.household_state_ref",
        ): (
            "src/synergy_schema/schema/models/atlas/atlas_population.yaml:203-210; "
            "src/synergy_schema/schema/core/population_snapshot.yaml:147-156"
        ),
        (
            "atlas_core_membership_snapshot_scope",
            "HouseholdMembership.population_snapshot_ref",
        ): "src/synergy_schema/schema/core/population_snapshot.yaml:26-29;124-136",
    }


def test_mapping_evidence_rejects_duplicate_declared_targets() -> None:
    slot_mappings = deepcopy(
        _mapping_fixture()["urbansim_activitysim_population"]["slot_mappings"]
    )
    duplicate = deepcopy(slot_mappings[0])
    duplicate["evidence"] = ["pilates/activitysim/preprocessor.py:999"]
    slot_mappings.append(duplicate)

    with pytest.raises(AssertionError, match="duplicate mapping identifier and target"):
        _evidence_by_mapping_target(slot_mappings)


def test_cross_model_example_records_validate() -> None:
    records = _yaml(CROSS_MODEL_RECORDS_PATH)
    targets = {
        "urbansim_household": "UrbanSimHouseholdPopulationRecord",
        "urbansim_person": "UrbanSimPersonPopulationRecord",
        "activitysim_household": "ActivitySimHouseholdInputRecord",
        "activitysim_person": "ActivitySimPersonInputRecord",
        "activitysim_land_use": "ActivitySimLandUseZoneRecord",
        "polaris_household": "PolarisHouseholdRecord",
        "polaris_person": "PolarisPersonRecord",
        "polaris_vehicle": "PolarisVehicleRecord",
    }
    for record_name, target_class in targets.items():
        assert _messages(records[record_name], target_class) == []


@pytest.mark.parametrize(
    ("target_class", "record"),
    [
        (
            "UrbanSimHouseholdPopulationRecord",
            {"household_id": 101, "block_id": "060750101001001"},
        ),
        (
            "ActivitySimHouseholdInputRecord",
            {"household_id": 101, "block_id": "060750101001001"},
        ),
    ],
)
def test_household_projections_preserve_leading_zero_block_identifiers(
    target_class: str,
    record: dict[str, object],
) -> None:
    assert _messages(record, target_class) == []


def test_cross_model_example_preserves_entities_and_exposes_transformations() -> None:
    records = _yaml(CROSS_MODEL_RECORDS_PATH)
    atlas = _yaml(ATLAS_RECORDS_PATH)

    assert {
        records["urbansim_household"]["household_id"],
        records["activitysim_household"]["household_id"],
        atlas["household"]["household_id"],
        records["polaris_household"]["household"],
        records["polaris_household"]["hhold"],
        records["polaris_person"]["household"],
        records["polaris_vehicle"]["hhold"],
    } == {101}
    assert {
        records["urbansim_person"]["person_id"],
        records["activitysim_person"]["person_id"],
        atlas["person"]["person_id"],
        records["polaris_person"]["person"],
    } == {1001}
    assert records["activitysim_person"]["household_id"] == 101
    assert records["urbansim_person"]["member_id"] == 1
    assert records["activitysim_person"]["member_id"] == 1
    assert atlas["person"]["member_id"] == 1
    assert records["polaris_person"]["id"] == 0
    assert {
        records["urbansim_household"]["block_id"],
        records["activitysim_household"]["block_id"],
        atlas["household"]["block_id"],
    } == {"060750101001001"}
    assert (
        records["activitysim_household"]["taz"]
        == records["activitysim_land_use"]["taz"]
    )
    assert records["polaris_vehicle"]["vehicle_id"] == atlas["vehicle"]["vehicle_id"]


def test_cross_model_vehicle_identity_is_scoped_by_atlas_year_and_snapshot() -> None:
    atlas = _yaml(ATLAS_RECORDS_PATH)
    records = _yaml(CROSS_MODEL_RECORDS_PATH)
    bundle = _yaml(BUNDLE_PATH)
    vehicle_member = next(
        member for member in bundle["members"] if member["semantic_role"] == "vehicles"
    )
    assert vehicle_member["schema_contract"]["selected_root"] == "AtlasVehicleOutput"
    assert _scoped_vehicle_identity(
        atlas["vehicle"],
        records["polaris_vehicle"],
        bundle["population_snapshot"],
    ) == (101, 1, 2025)


def test_same_polaris_vehicle_row_is_distinct_across_snapshot_years() -> None:
    atlas_2025 = _yaml(ATLAS_RECORDS_PATH)["vehicle"]
    atlas_2026 = deepcopy(atlas_2025)
    atlas_2026["year"] = 2026
    polaris_vehicle = _yaml(CROSS_MODEL_RECORDS_PATH)["polaris_vehicle"]
    snapshot_2025 = _yaml(BUNDLE_PATH)["population_snapshot"]
    snapshot_2026 = deepcopy(snapshot_2025)
    snapshot_2026["simulation_year"] = 2026

    assert (
        (atlas_2025["household_id"], atlas_2025["vehicle_id"])
        == (
            atlas_2026["household_id"],
            atlas_2026["vehicle_id"],
        )
        == (101, 1)
    )
    assert {
        _scoped_vehicle_identity(atlas_2025, polaris_vehicle, snapshot_2025),
        _scoped_vehicle_identity(atlas_2026, polaris_vehicle, snapshot_2026),
    } == {(101, 1, 2025), (101, 1, 2026)}


def test_vehicle_identity_rejects_changed_or_missing_snapshot_year() -> None:
    atlas_vehicle = _yaml(ATLAS_RECORDS_PATH)["vehicle"]
    polaris_vehicle = _yaml(CROSS_MODEL_RECORDS_PATH)["polaris_vehicle"]
    changed_snapshot = deepcopy(_yaml(BUNDLE_PATH)["population_snapshot"])
    changed_snapshot["simulation_year"] = 2026

    for invalid_snapshot in (changed_snapshot, {}):
        with pytest.raises(
            AssertionError,
            match="ATLAS vehicle year|enclosing snapshot year",
        ):
            _scoped_vehicle_identity(
                atlas_vehicle,
                polaris_vehicle,
                invalid_snapshot,
            )
