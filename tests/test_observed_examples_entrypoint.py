"""Boundary checks for the separate provisional-contract schema entry point."""

from pathlib import Path

from linkml_runtime.utils.schemaview import SchemaView


SCHEMA_DIR = Path(__file__).parents[1] / "src" / "synergy_schema" / "schema"
OBSERVED_EXAMPLES_PATH = SCHEMA_DIR / "observed_examples.yaml"
AGGREGATE_SCHEMA_PATH = SCHEMA_DIR / "synergy_schema.yaml"
OBSERVED_ROOTS = {
    "AtlasHouseholdFleetOutputExampleV1",
    "AtlasVehicleFleetOutputExampleV1",
    "DemosPolarisMappedHouseholdExampleV1",
    "DemosPolarisMappedPersonExampleV1",
    "PolarisDemandDatabaseV1Household",
    "PolarisDemandDatabaseV1Person",
    "PolarisDemandDatabaseV1Vehicle",
    "PolarisDemandDatabaseV1VehicleClass",
    "PolarisDemandDatabaseV1VehicleType",
}


def test_observed_examples_entrypoint_exposes_only_provisional_roots() -> None:
    view = SchemaView(str(OBSERVED_EXAMPLES_PATH))

    assert OBSERVED_ROOTS == set(view.all_classes())
    assert view.schema.annotations["evidence_status"].value == "observed_example"
    assert view.schema.annotations["schema_status"].value == "provisional"
    assert (
        view.schema.annotations["handoff_status"].value == "not_a_cross_model_handoff"
    )


def test_established_aggregate_schema_keeps_provisional_roots_separate() -> None:
    aggregate_view = SchemaView(str(AGGREGATE_SCHEMA_PATH))

    assert OBSERVED_ROOTS.isdisjoint(aggregate_view.all_classes())
