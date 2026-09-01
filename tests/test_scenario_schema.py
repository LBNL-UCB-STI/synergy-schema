"""Contract tests for provider-neutral native and scenario vocabulary."""

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
EXAMPLE_PATH = (
    Path(__file__).parents[1]
    / "examples"
    / "post_atlas_population_bundle"
    / "population_snapshot_bundle.yaml"
)


def _load_fixture() -> dict[str, object]:
    return yaml.safe_load(EXAMPLE_PATH.read_text(encoding="utf-8"))


def _validation_messages(instance: dict[str, object]) -> list[str]:
    report = Validator(
        SCHEMA_PATH,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    ).validate(instance, "PopulationSnapshotBundle")
    return [result.message for result in report.results]


def test_root_schema_exposes_native_contract_and_scenario_vocabulary() -> None:
    """The root composes provider-neutral native and scenario contracts."""
    schema_view = SchemaView(str(SCHEMA_PATH))

    assert {
        "NativeContractCatalogReference",
        "NativeContractElementReference",
        "ScenarioDefinition",
        "ScenarioDefinitionReference",
        "ScenarioAssumption",
        "ScenarioAssumptionBinding",
        "ModelScenarioBinding",
    }.issubset(schema_view.all_classes())
    assert set(
        schema_view.get_enum("NativeContractElementKind").permissible_values
    ) == {
        "config_path",
        "artifact_key",
        "sql_column",
    }
    assert set(schema_view.get_enum("ScenarioScalarValueType").permissible_values) == {
        "integer",
        "number",
        "boolean",
        "string",
        "code",
        "reference",
    }
    assert set(
        schema_view.get_enum("ScenarioAssumptionBindingMode").permissible_values
    ) == {
        "direct",
        "alias",
        "transformed",
        "override",
        "unsupported",
    }
    assert set(
        schema_view.get_enum("ScenarioCompatibilityState").permissible_values
    ) == {
        "compatible",
        "compatible_with_gaps",
        "incompatible",
        "pending_review",
    }


def test_scenario_contracts_preserve_identity_and_conformance_boundaries() -> None:
    """Schema shape pins immutable identities and documents conditional rules."""
    schema_view = SchemaView(str(SCHEMA_PATH))
    catalog = schema_view.induced_class("NativeContractCatalogReference")
    element = schema_view.induced_class("NativeContractElementReference")
    scenario_reference = schema_view.induced_class("ScenarioDefinitionReference")
    assumption = schema_view.induced_class("ScenarioAssumption")
    definition = schema_view.induced_class("ScenarioDefinition")
    assumption_binding = schema_view.induced_class("ScenarioAssumptionBinding")
    model_binding = schema_view.induced_class("ModelScenarioBinding")
    snapshot = schema_view.induced_class("PopulationSnapshot")

    assert set(catalog.attributes) == {
        "catalog_id",
        "catalog_kind",
        "revision",
        "digest_algorithm",
        "content_digest",
    }
    assert set(element.attributes) == {"catalog", "kind", "path"}
    assert element.attributes["catalog"].inlined is True
    assert set(scenario_reference.attributes) == {
        "scenario_definition_id",
        "revision",
        "content_digest",
    }
    assert set(assumption.attributes) == {
        "assumption_key",
        "value",
        "value_type",
        "unit",
        "authority",
    }
    assert set(definition.attributes) == {
        "id",
        "revision",
        "content_digest",
        "region_ref",
        "start_year",
        "end_year",
        "parent_definition_ref",
        "assumptions",
    }
    assert definition.attributes["assumptions"].minimum_cardinality == 1
    assert (
        definition.annotations["conformance_requirements"].value
        == "start_year and end_year define an inclusive horizon with start_year <= end_year."
    )
    assert set(assumption_binding.attributes) == {
        "assumption_key",
        "native_element",
        "resolved_native_value",
        "binding_mode",
        "compatibility_state",
        "transformation_description",
        "override_rationale",
    }
    assert set(model_binding.attributes) == {
        "binding_id",
        "model_name",
        "scenario_definition_ref",
        "native_contract_catalog",
        "assumption_bindings",
    }
    assert model_binding.attributes["assumption_bindings"].minimum_cardinality == 1
    assert (
        assumption_binding.annotations["conformance_requirements"].value
        == "transformed requires transformation_description; override requires "
        "override_rationale and is incompatible; unsupported omits "
        "resolved_native_value and may be compatible_with_gaps; direct or alias "
        "value disagreement is incompatible."
    )
    assert snapshot.attributes["scenario_definition_ref"].range == (
        "ScenarioDefinitionReference"
    )
    assert snapshot.attributes["scenario_definition_ref"].required is True
    assert snapshot.attributes["scenario_definition_ref"].inlined is True


def test_population_snapshot_bundle_requires_an_inlined_scenario_reference() -> None:
    """A snapshot carries its scenario identity, revision, and content digest."""
    assert _validation_messages(_load_fixture()) == []

    legacy_fixture = deepcopy(_load_fixture())
    legacy_fixture["population_snapshot"]["scenario_definition_ref"] = (
        "scenario-definition:synthetic-region-baseline"
    )
    assert _validation_messages(legacy_fixture)
