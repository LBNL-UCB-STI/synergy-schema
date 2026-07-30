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


def _messages(instance: dict[str, object], target_class: str) -> list[str]:
    report = Validator(
        SCHEMA_PATH,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    ).validate(instance, target_class)
    return [result.message for result in report.results]


def _mapping_fixture() -> dict[str, dict[str, object]]:
    import yaml

    return yaml.safe_load(MAPPINGS_PATH.read_text(encoding="utf-8"))


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
