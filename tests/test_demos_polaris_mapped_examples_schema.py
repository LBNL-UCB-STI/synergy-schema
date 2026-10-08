from pathlib import Path

from linkml_runtime.utils.schemaview import SchemaView


SCHEMA_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "synergy_schema"
    / "schema"
    / "models"
    / "demos"
    / "demos_polaris_mapped_examples.yaml"
)


def test_demos_candidate_schema_has_exact_observed_example_roots_and_headers() -> None:
    view = SchemaView(str(SCHEMA_PATH))

    assert set(view.all_classes()) == {
        "DemosPolarisMappedHousehold",
        "DemosPolarisMappedPerson",
    }
    assert list(view.get_class("DemosPolarisMappedHousehold").attributes) == [
        "household",
        "block_id",
        "lcm_county_id",
        "age_of_head",
        "workers",
        "race_of_head",
        "income",
        "persons",
        "is_reorg_household",
        "serialno_pums",
    ]
    assert list(view.get_class("DemosPolarisMappedPerson").attributes) == [
        "person",
        "relp",
        "gender",
        "education",
        "income",
        "id",
        "age",
        "household",
        "marital_status",
        "employment",
        "school_enrollment",
        "serialno_pums",
        "sporder",
    ]


def test_demos_provisional_schema_marks_status_and_conservative_required_types() -> (
    None
):
    view = SchemaView(str(SCHEMA_PATH))
    household = view.get_class("DemosPolarisMappedHousehold")
    person = view.get_class("DemosPolarisMappedPerson")

    for cls in (household, person):
        assert str(cls.annotations["schema_status"].value) == "authoritative"
        assert str(cls.annotations["status"].value) == "active"

    assert household.attributes["household"].range == "integer"
    assert household.attributes["persons"].range == "integer"
    assert household.attributes["is_reorg_household"].range == "boolean"
    assert person.attributes["person"].range == "integer"
    assert person.attributes["household"].range == "integer"
    assert person.attributes["id"].range == "float"
    assert person.attributes["id"].required is not True
    assert "observed_value_gap" in person.attributes["id"].annotations

    assert "hhold" not in household.attributes
    assert "hhold" not in person.attributes
    assert not person.attributes["id"].identifier
    assert not person.unique_keys
