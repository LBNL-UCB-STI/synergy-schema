"""Introspection contract for the additive ATLAS observed-example schema."""

from pathlib import Path

from linkml_runtime.utils.schemaview import SchemaView


SCHEMA_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "synergy_schema"
    / "schema"
    / "models"
    / "atlas"
    / "atlas_fleet_observed_example_v1.yaml"
)


def test_provisional_fleet_output_roots_and_annotations() -> None:
    view = SchemaView(str(SCHEMA_PATH))

    assert set(view.all_classes()) == {
        "AtlasHouseholdFleetOutputExampleV1",
        "AtlasVehicleFleetOutputExampleV1",
    }
    for class_name in view.all_classes():
        cls = view.induced_class(class_name)
        assert cls.annotations["contract_family"].value == "provisional_fleet_output"
        assert cls.annotations["status"].value == "provisional"


def test_physical_headers_identity_and_external_vehicle_key() -> None:
    view = SchemaView(str(SCHEMA_PATH))
    household = view.induced_class("AtlasHouseholdFleetOutputExampleV1")
    vehicle = view.induced_class("AtlasVehicleFleetOutputExampleV1")

    assert list(household.attributes) == ["houseid", "nvehicles"]
    assert list(vehicle.attributes) == [
        "houseid",
        "vehid",
        "bodytype",
        "vintage_category",
        "annual_mileage",
        "pred_power",
        "modelyear",
    ]
    assert household.attributes["houseid"].identifier is True
    assert (
        household.attributes["houseid"].annotations["physical_name"].value == "HOUSEID"
    )
    assert vehicle.attributes["vehid"].annotations["physical_name"].value == "VEHID"
    assert vehicle.unique_keys["atlas_vehicle_fleet_example_v1"].unique_key_slots == [
        "houseid",
        "vehid",
    ]
    assert (
        vehicle.attributes["houseid"].annotations["relationship_target"].value
        == "AtlasHouseholdFleetOutputExampleV1"
    )


def test_schema_has_no_year_attribute_or_year_semantics() -> None:
    view = SchemaView(str(SCHEMA_PATH))

    assert all(
        attribute_name.lower() != "year"
        for cls in view.all_classes()
        for attribute_name in view.induced_class(cls).attributes
    )
    for class_name in view.all_classes():
        cls = view.induced_class(class_name)
        assert cls.annotations["simulation_year"].value == "not_inferred"
