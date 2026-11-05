from pathlib import Path

from linkml_runtime.utils.schemaview import SchemaView


SCHEMA_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "synergy_schema"
    / "schema"
    / "synergy_schema.yaml"
)


def _annotation_value(schema_view: SchemaView, class_name: str, key: str) -> str:
    annotation = schema_view.get_class(class_name).annotations[key]
    return str(annotation.value)


def _assert_required_slots(
    schema_view: SchemaView, class_name: str, *slot_names: str
) -> None:
    class_definition = schema_view.get_class(class_name)
    for slot_name in slot_names:
        assert class_definition.attributes[slot_name].required is True


def _assert_digest_pair(
    schema_view: SchemaView,
    class_name: str,
    algorithm_slot_name: str,
    digest_slot_name: str,
) -> None:
    class_definition = schema_view.get_class(class_name)
    algorithm_slot = class_definition.attributes[algorithm_slot_name]
    digest_slot = class_definition.attributes[digest_slot_name]
    assert algorithm_slot.required is True
    assert algorithm_slot.range == "DigestAlgorithm"
    assert digest_slot.required is True


def test_population_translation_contract_exposes_contract_revision_shape() -> None:
    schema_view = SchemaView(str(SCHEMA_PATH))

    assert {
        "PopulationTranslationContract",
        "PopulationTranslationContractReference",
        "PopulationFieldMapping",
        "MappingResidueRecord",
        "LookupTableSpec",
        "LookupTableColumn",
        "LookupTableRow",
        "MappingResidueObservation",
        "MappingGovernance",
        "MappingReviewRecord",
        "TranslationImplementationBinding",
        "TranslationImplementationBindingReference",
    }.issubset(schema_view.all_classes())

    residue_class = schema_view.get_class("MappingResidueRecord")
    assert "default_value" in residue_class.attributes
    assert residue_class.attributes["lookup_table"].range == "LookupTableSpec"

    contract = schema_view.get_class("PopulationTranslationContract")
    assert "implementation_bindings" not in contract.attributes
    _assert_required_slots(
        schema_view,
        "PopulationTranslationContract",
        "id",
        "revision",
        "encoding_source",
        "source_catalog",
        "target_catalog",
        "field_mappings",
        "governance",
    )
    _assert_digest_pair(
        schema_view,
        "PopulationTranslationContract",
        "semantic_content_digest_algorithm",
        "semantic_content_digest",
    )
    _assert_required_slots(
        schema_view,
        "PopulationTranslationContractReference",
        "population_translation_contract_id",
        "revision",
    )
    _assert_digest_pair(
        schema_view,
        "PopulationTranslationContractReference",
        "semantic_content_digest_algorithm",
        "semantic_content_digest",
    )

    encoding_source = schema_view.induced_slot(
        "encoding_source", "PopulationTranslationContract"
    )
    assert encoding_source.range == "PhysicalArtifactReference"
    assert encoding_source.required is True
    assert encoding_source.inlined is True

    supporting_sources = schema_view.induced_slot(
        "supporting_sources", "PopulationTranslationContract"
    )
    assert supporting_sources.range == "PhysicalArtifactReference"
    assert supporting_sources.multivalued is True
    assert supporting_sources.required is not True
    assert supporting_sources.inlined_as_list is True

    _assert_required_slots(
        schema_view,
        "PopulationFieldMapping",
        "source_element",
        "target_element",
        "transformation_mode",
        "rule",
        "implementation_evidence",
    )
    field_mapping = schema_view.get_class("PopulationFieldMapping")
    assert (
        field_mapping.attributes["source_element"].range
        == "NativeContractElementReference"
    )
    assert (
        field_mapping.attributes["target_element"].range
        == "NativeContractElementReference"
    )
    assert (
        field_mapping.attributes["transformation_mode"].range
        == "PopulationFieldTransformationMode"
    )
    assert set(
        schema_view.get_enum("PopulationFieldTransformationMode").permissible_values
    ) == {"direct", "renamed", "unit_or_enum_converted", "derived"}

    assert set(schema_view.get_enum("MappingResidueKind").permissible_values) == {
        "unmapped_source",
        "required_target_default",
        "lookup_or_crosswalk",
        "filtered_rows",
        "aggregated_or_split",
        "dropped_context",
    }
    assert _annotation_value(
        schema_view, "MappingResidueRecord", "conformance_requirements"
    ) == (
        "Every source exchange column has one primary disposition: a field "
        "mapping or an unmapped_source/dropped_context residue; every required "
        "target column has one primary disposition: a field mapping or a "
        "required_target_default residue. lookup_or_crosswalk, filtered_rows, "
        "and aggregated_or_split residues may attach to that primary disposition "
        "and do not establish another one."
    )
    _assert_required_slots(
        schema_view,
        "MappingResidueObservation",
        "residue_record_id",
        "simulation_year",
        "affected_artifact_roles",
        "resulting_disposition",
    )
    _assert_digest_pair(
        schema_view,
        "MappingResidueObservation",
        "semantic_content_digest_algorithm",
        "semantic_content_digest",
    )

    assert set(schema_view.get_enum("MappingLifecycleStatus").permissible_values) == {
        "draft",
        "approved",
        "superseded",
        "deprecated",
    }
    assert set(schema_view.get_enum("MappingReviewRole").permissible_values) == {
        "source_owner",
        "target_owner",
        "workflow_integrator",
    }
    assert _annotation_value(
        schema_view, "MappingGovernance", "conformance_requirements"
    ) == (
        "approved requires accept decisions from both the source_owner and "
        "target_owner roles for the contract's current semantic_content_digest "
        "with its semantic_content_digest_algorithm; standard LinkML validation "
        "does not resolve this cross-record rule."
    )
    _assert_required_slots(
        schema_view,
        "MappingReviewRecord",
        "reviewer_role",
        "reviewing_team",
        "review_date",
        "decision",
        "rationale",
    )
    _assert_digest_pair(
        schema_view,
        "MappingReviewRecord",
        "assessed_semantic_content_digest_algorithm",
        "assessed_semantic_content_digest",
    )

    assert set(
        schema_view.get_enum("TranslationImplementationStatus").permissible_values
    ) == {"declared", "conformance_checked", "retired"}
    _assert_required_slots(
        schema_view,
        "TranslationImplementationBinding",
        "id",
        "implementation_artifact",
        "workflow_owner",
        "status",
    )
    _assert_digest_pair(
        schema_view,
        "TranslationImplementationBinding",
        "implemented_semantic_content_digest_algorithm",
        "implemented_semantic_content_digest",
    )
    _assert_required_slots(
        schema_view,
        "TranslationImplementationBindingReference",
        "translation_implementation_binding_id",
    )
    _assert_digest_pair(
        schema_view,
        "TranslationImplementationBindingReference",
        "implemented_semantic_content_digest_algorithm",
        "implemented_semantic_content_digest",
    )
    _assert_digest_pair(
        schema_view,
        "TranslationImplementationBindingReference",
        "implementation_content_digest_algorithm",
        "implementation_content_digest",
    )


def test_semantic_digest_projection_excludes_provenance_and_governance() -> None:
    schema_view = SchemaView(str(SCHEMA_PATH))

    projection = _annotation_value(
        schema_view, "PopulationTranslationContract", "semantic_digest_projection"
    )
    assert projection == (
        "Includes source_catalog, target_catalog, source_schema_contract, "
        "target_schema_contract, field_mappings, and residue_records. Excludes "
        "encoding_source, supporting_sources, "
        "PopulationFieldMapping.implementation_evidence, "
        "MappingResidueRecord.implementation_evidence, governance, review "
        "records, lifecycle status, and implementation bindings; cross-document "
        "digest checks are enforced by the conformance layer rather than standard "
        "LinkML validation."
    )
    assert _annotation_value(
        schema_view, "PopulationFieldMapping", "semantic_digest_projection"
    ) == (
        "Includes id, source_element, target_element, transformation_mode, and "
        "rule. Excludes implementation_evidence."
    )
    assert _annotation_value(
        schema_view, "MappingResidueRecord", "semantic_digest_projection"
    ) == (
        "Includes id, residue_kind, affected_elements, deterministic_rule, "
        "default_value, lookup_table, rationale, and disposition. Excludes "
        "implementation_evidence."
    )


def test_release_contract_and_implementation_validate_under_closed_jsonschema() -> None:
    import yaml
    from linkml.validator import Validator
    from linkml.validator.plugins import JsonschemaValidationPlugin

    validator = Validator(
        schema=str(SCHEMA_PATH),
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    )
    release_dir = (
        Path(__file__).parents[1]
        / "mappings"
        / "releases"
        / "atlas-demos-to-polaris"
        / "revision-1"
    )
    contract_doc = yaml.safe_load(
        (release_dir / "contract" / "population-translation-contract.yaml").read_text(
            encoding="utf-8"
        )
    )
    contract_report = validator.validate(
        contract_doc, target_class="PopulationTranslationContract"
    )
    assert list(contract_report.results) == []

    impl_doc = yaml.safe_load(
        (release_dir / "implementation" / "polaris-translation.yaml").read_text(
            encoding="utf-8"
        )
    )
    impl_report = validator.validate(
        impl_doc, target_class="TranslationImplementationBinding"
    )
    assert list(impl_report.results) == []
