"""Bootstrap contract tests for the canonical LinkML schema."""

from pathlib import Path

from linkml_runtime.utils.schemaview import SchemaView


SCHEMA_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "synergy_schema"
    / "schema"
    / "synergy_schema.yaml"
)


def test_root_schema_has_stable_identity_without_bootstrap_examples() -> None:
    """The canonical root identifies the project but defines no domain model yet."""
    schema_view = SchemaView(str(SCHEMA_PATH))

    assert schema_view.schema.id == "https://w3id.org/LBNL-UCB-STI/synergy-schema"
    assert schema_view.schema.name == "synergy_schema"
    assert schema_view.schema.title == "Synergy Schema"
    assert (
        schema_view.schema.prefixes["synergy_schema"].prefix_reference
        == "https://w3id.org/LBNL-UCB-STI/synergy-schema/"
    )
    assert {"NamedThing", "Person", "PersonCollection"}.isdisjoint(
        schema_view.all_classes()
    )
