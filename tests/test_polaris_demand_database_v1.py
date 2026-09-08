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


def test_v1_is_a_provisional_observed_projection() -> None:
    view = SchemaView(str(SCHEMA_PATH))
    assert view.schema.name == "polaris_demand_database_v1"
    assert view.schema.annotations["version"].value == "v1"
    assert view.schema.annotations["model_association"].value == "POLARIS"
    assert view.schema.annotations["status"].value == "provisional"
    assert "observed_example" in view.schema.annotations["coverage"].value
    assert set(view.all_classes()) == {
        "PolarisDemandDatabaseV1Household",
        "PolarisDemandDatabaseV1Person",
        "PolarisDemandDatabaseV1Vehicle",
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
        },
        "PolarisDemandDatabaseV1Person": {"person", "household", "id"},
        "PolarisDemandDatabaseV1Vehicle": {"vehicle_id", "hhold", "type"},
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
    for class_name, slot_name in [
        ("PolarisDemandDatabaseV1Person", "household"),
        ("PolarisDemandDatabaseV1Vehicle", "hhold"),
    ]:
        slot = view.induced_slot(slot_name, class_name)
        assert slot.annotations["relationship_target"].value.endswith(".household")
        assert slot.annotations["validation_boundary"].value == (
            "external conformance check, not a SQLite foreign key"
        )
