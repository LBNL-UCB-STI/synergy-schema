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
    evidence = {
        (entry["source_paths"][0], entry["target_paths"][0]): entry["evidence"]
        for entry in slot_mappings
    }
    assert len(evidence) == len(slot_mappings), "duplicate source and target path pair"
    return evidence


def _evidence_by_mapping_target(
    slot_mappings: list[dict[str, object]],
) -> dict[tuple[str, str], str]:
    target_count = sum(len(entry["target_paths"]) for entry in slot_mappings)
    evidence = {
        (entry["id"], target_path): entry["evidence"]
        for entry in slot_mappings
        for target_path in entry["target_paths"]
    }
    assert len(evidence) == target_count, "duplicate mapping identifier and target"
    return evidence


def _assert_vehicle_identity_scope(
    atlas: dict[str, object],
    records: dict[str, object],
    bundle: dict[str, object],
) -> None:
    atlas_vehicle = atlas["vehicle"]
    polaris_vehicle = records["polaris_vehicle"]
    snapshot = bundle["population_snapshot"]
    vehicle_member = next(
        member for member in bundle["members"] if member["semantic_role"] == "vehicles"
    )

    assert set(atlas_vehicle).issuperset({"household_id", "vehicle_id", "year"})
    assert set(polaris_vehicle) == {"vehicle_id", "hhold"}
    assert polaris_vehicle["hhold"] == atlas_vehicle["household_id"]
    assert polaris_vehicle["vehicle_id"] == atlas_vehicle["vehicle_id"]
    assert vehicle_member["schema_contract"]["selected_root"] == "AtlasVehicleOutput"
    assert atlas_vehicle["year"] == snapshot["simulation_year"] == 2025, (
        "ATLAS vehicle year must match the enclosing population snapshot year"
    )


def test_mapping_vocabulary_is_imported_with_controlled_classifications() -> None:
    schema_view = SchemaView(str(SCHEMA_PATH))
    assert {
        "PopulationRepresentationMapping",
        "PopulationSlotMapping",
    }.issubset(schema_view.all_classes())
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
        "ActivitySimHouseholdInputRecord": {"household_id", "block_id", "taz"},
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
        "PolarisVehicleRecord": ({"vehicle_id": 1, "hhold": 101}, "vehicle_id"),
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
    ("target_class", "slot_name", "relationship_target"),
    [
        (
            "UrbanSimPersonPopulationRecord",
            "household_id",
            "UrbanSimHouseholdPopulationRecord",
        ),
        (
            "ActivitySimHouseholdInputRecord",
            "taz",
            "ActivitySimLandUseZoneRecord",
        ),
        (
            "ActivitySimPersonInputRecord",
            "household_id",
            "ActivitySimHouseholdInputRecord",
        ),
        (
            "ActivitySimPersonInputRecord",
            "taz",
            "ActivitySimLandUseZoneRecord",
        ),
        ("PolarisPersonRecord", "household", "PolarisHouseholdRecord"),
        ("PolarisVehicleRecord", "hhold", "PolarisHouseholdRecord"),
    ],
)
def test_relationship_targets_are_explicit(
    target_class: str,
    slot_name: str,
    relationship_target: str,
) -> None:
    schema_view = SchemaView(str(SCHEMA_PATH))
    assert (
        schema_view.induced_slot(slot_name, target_class)
        .annotations["relationship_target"]
        .value
        == relationship_target
    )


def test_population_mapping_manifest_validates_and_is_evidence_complete() -> None:
    mappings = _mapping_fixture()
    assert set(mappings) == {
        "urbansim_activitysim_population",
        "atlas_polaris_population",
    }
    for mapping in mappings.values():
        assert _messages(mapping, "PopulationRepresentationMapping") == []
        for slot_mapping in mapping["slot_mappings"]:
            assert slot_mapping["mapping_status"]
            assert slot_mapping["identity_role"]
            assert slot_mapping["value_stability"]
            assert slot_mapping["transformation"]
            assert slot_mapping["evidence"].startswith("pilates/")


def test_unstable_local_ordinals_are_not_mapped_as_preserved_entity_ids() -> None:
    slot_mappings = [
        entry
        for mapping in _mapping_fixture().values()
        for entry in mapping["slot_mappings"]
    ]
    for entry in slot_mappings:
        if any(path.endswith((".member_id", ".id")) for path in entry["source_paths"]):
            assert entry["identity_role"] == "within_parent_ordinal"
            assert entry["value_stability"] in {"derived", "regenerated"}


def test_atlas_polaris_evidence_is_exact_for_each_translation_path_pair() -> None:
    slot_mappings = _mapping_fixture()["atlas_polaris_population"]["slot_mappings"]
    assert all(
        len(entry["source_paths"]) == len(entry["target_paths"]) == 1
        for entry in slot_mappings
    )
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
    duplicate["evidence"] = (
        "pilates/generated/polaris_population_translation/10_households.sql:999"
    )
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
        "atlas_polaris_vehicle_household_membership": (
            ["AtlasVehicleOutput.household_id"],
            ["PolarisVehicleRecord.hhold"],
            "renamed",
            "preserved",
        ),
        "atlas_polaris_vehicle_identity": (
            ["AtlasVehicleOutput.vehicle_id"],
            ["PolarisVehicleRecord.vehicle_id"],
            "direct",
            "artifact_scoped",
        ),
        "atlas_polaris_vehicle_year_scope": (
            ["AtlasVehicleOutput.year"],
            ["PopulationSnapshot.simulation_year"],
            "direct",
            "artifact_scoped",
        ),
    }


def test_each_population_mapping_target_has_exact_implementation_evidence() -> None:
    slot_mappings = [
        entry
        for mapping in _mapping_fixture().values()
        for entry in mapping["slot_mappings"]
    ]
    assert _evidence_by_mapping_target(slot_mappings) == {
        (
            "urbansim_activitysim_household_identity",
            "ActivitySimHouseholdInputRecord.household_id",
        ): ("pilates/activitysim/preprocessor.py:3524"),
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
        ("atlas_polaris_vehicle_household_membership", "PolarisVehicleRecord.hhold"): (
            "pilates/generated/polaris_population_translation/40_vehicles.sql:6"
        ),
        ("atlas_polaris_vehicle_identity", "PolarisVehicleRecord.vehicle_id"): (
            "pilates/generated/polaris_population_translation/40_vehicles.sql:5"
        ),
        ("atlas_polaris_vehicle_year_scope", "PopulationSnapshot.simulation_year"): (
            "pilates/generated/polaris_population_translation/40_vehicles.sql:3-6"
        ),
    }


def test_mapping_evidence_rejects_duplicate_declared_targets() -> None:
    slot_mappings = deepcopy(
        _mapping_fixture()["urbansim_activitysim_population"]["slot_mappings"]
    )
    duplicate = deepcopy(slot_mappings[0])
    duplicate["evidence"] = "pilates/activitysim/preprocessor.py:999"
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
    _assert_vehicle_identity_scope(
        _yaml(ATLAS_RECORDS_PATH),
        _yaml(CROSS_MODEL_RECORDS_PATH),
        _yaml(BUNDLE_PATH),
    )


def test_cross_model_vehicle_identity_rejects_atlas_year_drift() -> None:
    atlas = _yaml(ATLAS_RECORDS_PATH)
    atlas["vehicle"]["year"] = 2026

    with pytest.raises(AssertionError, match="ATLAS vehicle year"):
        _assert_vehicle_identity_scope(
            atlas,
            _yaml(CROSS_MODEL_RECORDS_PATH),
            _yaml(BUNDLE_PATH),
        )
