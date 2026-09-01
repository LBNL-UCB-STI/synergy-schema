"""Contract tests for provider-neutral population trajectories."""

from copy import deepcopy
from pathlib import Path

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


def _validation_messages(instance: dict[str, object]) -> list[str]:
    report = Validator(
        SCHEMA_PATH,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    ).validate(instance, "PopulationTrajectory")
    return [result.message for result in report.results]


def _trajectory_fixture() -> dict[str, object]:
    scenario_reference = {
        "scenario_definition_id": "scenario:synthetic-region:baseline",
        "revision": "2026.08",
        "content_digest": "a" * 64,
    }
    return {
        "id": "population-trajectory:synthetic-region:baseline:r1",
        "scenario_definition_ref": scenario_reference,
        "stochastic_realization_id": "r1",
        "snapshots": [
            {
                "id": "population-snapshot:synthetic-region-2025-r1",
                "scenario_definition_ref": scenario_reference,
                "stochastic_realization_id": "r1",
                "simulation_year": 2025,
            },
            {
                "id": "population-snapshot:synthetic-region-2030-r1",
                "scenario_definition_ref": scenario_reference,
                "stochastic_realization_id": "r1",
                "simulation_year": 2030,
            },
        ],
        "requested_years": [2025, 2027, 2030],
        "skipped_years": [
            {
                "year": 2027,
                "reason": "No population export was requested for this bridge year.",
            }
        ],
        "completeness_status": "incomplete",
    }


def test_population_trajectory_exposes_ordered_scenario_scoped_snapshots() -> None:
    """Missing trajectory structure would prevent declaring evolving snapshots."""
    schema_view = SchemaView(str(SCHEMA_PATH))

    assert {"PopulationTrajectory", "SkippedPopulationYear"}.issubset(
        schema_view.all_classes()
    )
    trajectory = schema_view.induced_class("PopulationTrajectory")
    skipped_year = schema_view.induced_class("SkippedPopulationYear")

    assert set(trajectory.attributes) == {
        "id",
        "scenario_definition_ref",
        "stochastic_realization_id",
        "snapshots",
        "requested_years",
        "skipped_years",
        "completeness_status",
    }
    assert "successful_years" not in trajectory.attributes
    assert trajectory.attributes["id"].identifier is True
    assert trajectory.attributes["id"].required is True
    assert trajectory.attributes["scenario_definition_ref"].range == (
        "ScenarioDefinitionReference"
    )
    assert trajectory.attributes["scenario_definition_ref"].inlined is True
    assert trajectory.attributes["scenario_definition_ref"].required is True
    assert trajectory.attributes["stochastic_realization_id"].required is True

    snapshots = trajectory.attributes["snapshots"]
    assert snapshots.range == "PopulationSnapshot"
    assert snapshots.required is True
    assert snapshots.multivalued is True
    assert snapshots.inlined_as_list is True
    assert "chronological order" in str(
        snapshots.annotations["sequence_semantics"].value
    )

    requested_years = trajectory.attributes["requested_years"]
    assert requested_years.range == "integer"
    assert requested_years.required is True
    assert requested_years.multivalued is True

    skipped_years = trajectory.attributes["skipped_years"]
    assert skipped_years.range == "SkippedPopulationYear"
    assert skipped_years.multivalued is True
    assert skipped_years.inlined_as_list is True
    assert skipped_year.attributes["year"].range == "integer"
    assert skipped_year.attributes["year"].required is True
    assert skipped_year.attributes["reason"].required is True

    completeness = trajectory.attributes["completeness_status"]
    assert completeness.range == "HandoffCompletenessStatus"
    assert completeness.required is True


def test_population_trajectory_fixture_requires_trajectory_metadata() -> None:
    """A trajectory cannot omit its stable, scenario-scoped declaration."""
    fixture = _trajectory_fixture()
    assert _validation_messages(fixture) == []

    for required_field in (
        "id",
        "scenario_definition_ref",
        "stochastic_realization_id",
        "snapshots",
        "requested_years",
        "completeness_status",
    ):
        incomplete_fixture = deepcopy(fixture)
        del incomplete_fixture[required_field]
        assert _validation_messages(incomplete_fixture)


def test_evolving_population_relationships_remain_snapshot_scoped() -> None:
    """Shared state links retain relationship evidence without native model fields."""
    schema_view = SchemaView(str(SCHEMA_PATH))

    assert {
        "HouseholdState",
        "VehicleState",
        "HouseholdVehicleAssignment",
    }.issubset(schema_view.all_classes())
    household = schema_view.induced_class("HouseholdState")
    vehicle = schema_view.induced_class("VehicleState")
    assignment = schema_view.induced_class("HouseholdVehicleAssignment")

    assert set(household.attributes) == {
        "household_state_id",
        "population_snapshot_ref",
        "longitudinal_household_ref",
        "predecessor_state_refs",
    }
    predecessor_refs = household.attributes["predecessor_state_refs"]
    assert predecessor_refs.range == "HouseholdState"
    assert predecessor_refs.multivalued is True
    assert predecessor_refs.inlined is False
    assert predecessor_refs.annotations["relationship_target"].value == "HouseholdState"
    assert "conformance" in str(
        predecessor_refs.annotations["validation_boundary"].value
    )

    assert set(vehicle.attributes) == {
        "vehicle_state_id",
        "population_snapshot_ref",
        "longitudinal_vehicle_ref",
    }
    assert vehicle.attributes["vehicle_state_id"].identifier is True
    assert vehicle.attributes["vehicle_state_id"].required is True
    assert vehicle.attributes["population_snapshot_ref"].required is True

    assert set(assignment.attributes) == {
        "household_vehicle_assignment_id",
        "population_snapshot_ref",
        "household_state_ref",
        "vehicle_state_ref",
        "relationship_kind",
    }
    assert assignment.attributes["household_vehicle_assignment_id"].identifier is True
    for reference_name, target in (
        ("household_state_ref", "HouseholdState"),
        ("vehicle_state_ref", "VehicleState"),
    ):
        reference = assignment.attributes[reference_name]
        assert reference.required is True
        assert reference.inlined is False
        assert reference.annotations["relationship_target"].value == target
        assert "conformance" in str(reference.annotations["validation_boundary"].value)
    assert assignment.attributes["relationship_kind"].required is True
    assert assignment.attributes["relationship_kind"].range == (
        "HouseholdVehicleRelationshipKind"
    )
    assert set(
        schema_view.get_enum("HouseholdVehicleRelationshipKind").permissible_values
    ) == {"ownership", "leasing", "availability", "assignment", "unresolved"}
