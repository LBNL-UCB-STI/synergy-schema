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


def test_population_translation_contract_exposes_semantic_release_shape() -> None:
    schema_view = SchemaView(str(SCHEMA_PATH))

    assert {
        "PopulationTranslationContract",
        "PopulationTranslationContractReference",
        "PopulationFieldMapping",
        "MappingResidueRecord",
        "MappingResidueObservation",
        "MappingGovernance",
        "MappingReviewRecord",
        "TranslationImplementationBinding",
        "TranslationImplementationBindingReference",
    }.issubset(schema_view.all_classes())

    contract = schema_view.get_class("PopulationTranslationContract")
    assert "implementation_bindings" not in contract.attributes

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

    field_mapping = schema_view.get_class("PopulationFieldMapping")
    for slot_name in (
        "source_element",
        "target_element",
        "transformation_mode",
        "rule",
        "implementation_evidence",
    ):
        assert field_mapping.attributes[slot_name].required is True
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
    ).startswith("Every source exchange column")

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
    ).startswith("approved requires accept decisions")

    assert set(
        schema_view.get_enum("TranslationImplementationStatus").permissible_values
    ) == {"declared", "conformance_checked", "retired"}
    implementation_binding = schema_view.get_class("TranslationImplementationBinding")
    assert (
        implementation_binding.attributes[
            "implemented_semantic_content_digest"
        ].required
        is True
    )


def test_semantic_digest_projection_excludes_provenance_and_governance() -> None:
    schema_view = SchemaView(str(SCHEMA_PATH))

    projection = _annotation_value(
        schema_view, "PopulationTranslationContract", "semantic_digest_projection"
    )
    assert "source_catalog" in projection
    assert "target_catalog" in projection
    assert "field_mappings" in projection
    assert "residue_records" in projection
    assert "encoding_source" in projection
    assert "supporting_sources" in projection
    assert "governance" in projection
    assert "implementation bindings" in projection
