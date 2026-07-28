"""Contract tests for the canonical LinkML population handoff schema."""

from copy import deepcopy
from pathlib import Path

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
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "population_snapshot_bundle.yaml"


def _load_fixture() -> dict[str, object]:
    return yaml.safe_load(FIXTURE_PATH.read_text(encoding="utf-8"))


def _validation_messages(instance: dict[str, object]) -> list[str]:
    report = Validator(
        SCHEMA_PATH,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    ).validate(instance, "PopulationSnapshotBundle")
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
    }.issubset(schema_view.all_classes())


def test_root_schema_resolves_profile_imports_and_required_population_members() -> None:
    """The operational profile composes the shared bundle without native rows."""
    schema_view = SchemaView(str(SCHEMA_PATH))

    bundle = schema_view.induced_class("PopulationSnapshotBundle")
    assert bundle.is_a == "HandoffBundle"
    assert bundle.attributes["population_snapshot"].required is True
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
