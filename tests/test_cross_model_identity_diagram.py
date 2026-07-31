from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from synergy_schema.cross_model_identity_diagram import (
    DiagramInputError,
    render_cross_model_identity_map,
    write_cross_model_identity_map,
)


MAPPINGS_PATH = (
    Path(__file__).parents[1]
    / "examples"
    / "post_atlas_population_bundle"
    / "population_identity_mappings.yaml"
)


def _mappings() -> dict[str, object]:
    return yaml.safe_load(MAPPINGS_PATH.read_text(encoding="utf-8"))


def test_cross_model_identity_map_renders_semantic_mapping_edges() -> None:
    rendered = render_cross_model_identity_map(_mappings())

    assert rendered.startswith("# Cross-model population identity map\n")
    assert rendered.count("```mermaid\nflowchart LR\n") == 2

    stable_identity, derived_and_scoped = rendered.split(
        "## Derived, renamed, and artifact-scoped mappings\n", maxsplit=1
    )
    assert "## Stable identity and household membership\n" in stable_identity
    assert "UrbanSimPersonPopulationRecord.person_id" in stable_identity
    assert "ActivitySimPersonInputRecord.person_id" in stable_identity
    assert "AtlasPersonInput.person_id" in stable_identity
    assert "PolarisPersonRecord.person" in stable_identity
    assert "UrbanSimPersonPopulationRecord.household_id" in stable_identity
    assert "ActivitySimHouseholdInputRecord.household_id" in stable_identity
    assert "AtlasHouseholdInput.household_id" in stable_identity
    assert "PolarisHouseholdRecord.household" in stable_identity
    assert "direct | entity_identifier | one-to-one" in stable_identity
    assert "renamed | relationship_foreign_key | many-to-one" in stable_identity
    assert "UrbanSimHouseholdPopulationRecord.block_id" not in stable_identity
    assert "AtlasVehicleOutput.year" not in stable_identity

    assert "UrbanSimHouseholdPopulationRecord.block_id" in derived_and_scoped
    assert "ActivitySimPersonInputRecord.taz" in derived_and_scoped
    assert "AtlasVehicleOutput.year" in derived_and_scoped
    assert "PopulationSnapshot.simulation_year" in derived_and_scoped
    assert "HouseholdState.longitudinal_household_ref" in stable_identity
    assert "PersonState.longitudinal_person_ref" in stable_identity
    assert "HouseholdState.household_state_id" in derived_and_scoped
    assert "PersonState.person_state_id" in derived_and_scoped
    assert "HouseholdMembership.household_membership_id" in derived_and_scoped
    assert '["construct_household_state_identity"]' in derived_and_scoped
    assert "derived | geographic_identifier | many-to-one" in derived_and_scoped
    assert "derived | artifact_scoped_identifier | one-to-one" in derived_and_scoped


def test_cross_model_identity_manifest_connects_all_four_model_representations() -> (
    None
):
    edges = {
        (source_path, target_path)
        for representation in _mappings().values()
        for slot_mapping in representation["slot_mappings"]
        for source_path, target_path in zip(
            slot_mapping["source_paths"], slot_mapping["target_paths"], strict=True
        )
    }

    person_chain = [
        (
            "UrbanSimPersonPopulationRecord.person_id",
            "ActivitySimPersonInputRecord.person_id",
        ),
        ("ActivitySimPersonInputRecord.person_id", "AtlasPersonInput.person_id"),
        ("AtlasPersonInput.person_id", "PolarisPersonRecord.person"),
    ]
    household_chain = [
        (
            "UrbanSimHouseholdPopulationRecord.household_id",
            "ActivitySimHouseholdInputRecord.household_id",
        ),
        (
            "ActivitySimHouseholdInputRecord.household_id",
            "AtlasHouseholdInput.household_id",
        ),
        ("AtlasHouseholdInput.household_id", "PolarisHouseholdRecord.household"),
    ]

    assert set(person_chain) <= edges
    assert set(household_chain) <= edges


def test_cross_model_identity_map_rejects_malformed_composite_construction() -> None:
    mappings = deepcopy(_mappings())
    mappings["atlas_core_population_state"] = {
        "id": "atlas_core_population_state",
        "source_representation": "ATLAS rows and snapshot",
        "target_representation": "Core population states",
        "slot_mappings": [],
        "identity_constructions": [
            {
                "id": "bad_construction",
                "source_paths": ["PopulationSnapshot.id"],
                "target_path": "HouseholdState.household_state_id",
                "mapping_status": "derived",
                "identity_role": "artifact_scoped_identifier",
                "value_stability": "artifact_scoped",
                "relationship_cardinality": "one-to-one",
                "transformation": "Missing its second composite input.",
                "evidence": ["examples/core.yaml:1"],
            }
        ],
    }

    with pytest.raises(DiagramInputError, match="at least two source_paths"):
        render_cross_model_identity_map(mappings)


def test_cross_model_identity_map_writes_deterministic_markdown(tmp_path: Path) -> None:
    output_path = tmp_path / "cross-model-population-identity.md"

    write_cross_model_identity_map(_mappings(), output_path)

    assert output_path.read_text(encoding="utf-8") == render_cross_model_identity_map(
        _mappings()
    )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda mappings: mappings["urbansim_activitysim_population"][
                "slot_mappings"
            ][0].update(
                {
                    "target_paths": [
                        "ActivitySimHouseholdInputRecord.household_id",
                        "ActivitySimHouseholdInputRecord.block_id",
                    ]
                }
            ),
            "aligned source_paths and target_paths",
        ),
        (
            lambda mappings: mappings["urbansim_activitysim_population"][
                "slot_mappings"
            ][0].update(
                {"source_paths": "UrbanSimHouseholdPopulationRecord.household_id"}
            ),
            "source_paths must be a list of field paths",
        ),
    ],
)
def test_cross_model_identity_map_rejects_malformed_mapping_legs(
    mutate: object, message: str
) -> None:
    mappings = deepcopy(_mappings())
    mutate(mappings)

    with pytest.raises(DiagramInputError, match=message):
        render_cross_model_identity_map(mappings)
