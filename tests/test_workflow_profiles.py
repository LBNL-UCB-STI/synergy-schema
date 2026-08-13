"""Contract tests for the composed PILATES and POLARIS workflow profiles."""

from pathlib import Path

from linkml_runtime.utils.schemaview import SchemaView


SCHEMA_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "synergy_schema"
    / "schema"
    / "synergy_schema.yaml"
)


def _required_slots(schema_view: SchemaView, class_name: str, *slot_names: str) -> None:
    class_definition = schema_view.induced_class(class_name)
    for slot_name in slot_names:
        assert class_definition.attributes[slot_name].required is True


def test_pilates_profile_composes_operational_trajectory_evidence() -> None:
    """PILATES owns schedule and Consist evidence around its yearly handoffs."""
    schema_view = SchemaView(str(SCHEMA_PATH))

    assert {
        "DayZeroExchangeManifest",
        "PilatesScheduleEvidence",
        "PilatesScheduleYearStatus",
        "PilatesConsistTrajectoryEvidence",
        "PilatesConsistChildRunEvidence",
        "PopulationTrajectoryBundle",
        "PopulationTrajectoryBundleReference",
    }.issubset(schema_view.all_classes())

    _required_slots(
        schema_view,
        "DayZeroExchangeManifest",
        "payload_artifact",
        "producer_artifact",
        "native_scenario_namespace",
        "native_scenario_label",
        "simulation_year",
        "generation_mode",
    )
    manifest = schema_view.induced_class("DayZeroExchangeManifest")
    assert manifest.attributes["payload_artifact"].range == "PhysicalArtifactReference"
    assert manifest.attributes["producer_artifact"].range == "PhysicalArtifactReference"
    assert manifest.attributes["simulation_year"].range == "integer"
    assert (
        manifest.attributes["generation_mode"].range
        == "DiscoveryManifestGenerationMode"
    )
    assert set(
        schema_view.get_enum("DiscoveryManifestGenerationMode").permissible_values
    ) == {"manual_discovery"}

    _required_slots(
        schema_view,
        "PilatesScheduleEvidence",
        "planned_execution_boundaries",
        "handoff_year_statuses",
        "config_catalog",
        "scheduler_implementation",
    )
    schedule = schema_view.induced_class("PilatesScheduleEvidence")
    assert schedule.attributes["planned_execution_boundaries"].multivalued is True
    assert (
        schedule.attributes["handoff_year_statuses"].range
        == "PilatesScheduleYearStatus"
    )
    assert schedule.attributes["handoff_year_statuses"].inlined_as_list is True
    assert "every requested handoff year" in str(
        schedule.annotations["conformance_requirements"].value
    )

    child_run = schema_view.induced_class("PilatesConsistChildRunEvidence")
    assert child_run.attributes["child_run"].range == "ConsistRunReference"
    assert child_run.attributes["child_run"].inlined is True
    _required_slots(
        schema_view,
        "PilatesConsistChildRunEvidence",
        "child_run",
        "simulation_year",
    )

    trajectory_bundle = schema_view.induced_class("PopulationTrajectoryBundle")
    _required_slots(
        schema_view,
        "PopulationTrajectoryBundle",
        "population_trajectory",
        "population_snapshot_bundles",
        "schedule_evidence",
        "consist_trajectory_evidence",
        "manifest_content_digest_algorithm",
        "manifest_content_digest",
    )
    assert trajectory_bundle.attributes["population_trajectory"].range == (
        "PopulationTrajectory"
    )
    assert trajectory_bundle.attributes["population_snapshot_bundles"].range == (
        "PopulationSnapshotBundle"
    )
    assert (
        trajectory_bundle.attributes["population_snapshot_bundles"].multivalued is True
    )
    assert trajectory_bundle.attributes["manifest_content_digest_algorithm"].range == (
        "DigestAlgorithm"
    )
    assert "canonical content projection" in str(
        trajectory_bundle.annotations["manifest_digest_projection"].value
    )
    assert "manifest_content_digest itself" in str(
        trajectory_bundle.annotations["manifest_digest_projection"].value
    )

    _required_slots(
        schema_view,
        "PopulationTrajectoryBundleReference",
        "population_trajectory_bundle_id",
        "manifest_content_digest_algorithm",
        "manifest_content_digest",
    )


def test_polaris_profile_packages_yearly_translation_receipts() -> None:
    """POLARIS packaging stays separate from its partial native projections."""
    schema_view = SchemaView(str(SCHEMA_PATH))

    assert {
        "PolarisPopulationTranslationBundleMember",
        "PolarisPopulationTranslationBundle",
    }.issubset(schema_view.all_classes())
    assert set(
        schema_view.get_enum("PolarisPopulationArtifactRole").permissible_values
    ) == {"households", "persons", "vehicles", "vehicle_class", "vehicle_type"}
    assert set(
        schema_view.get_enum("PopulationReceiptGenerationMode").permissible_values
    ) == {"manual_discovery", "automatic_adapter"}

    member = schema_view.induced_class("PolarisPopulationTranslationBundleMember")
    assert member.attributes["semantic_role"].range == "PolarisPopulationArtifactRole"
    assert member.attributes["simulation_year"].range == "integer"
    assert member.attributes["simulation_year"].required is True

    bundle = schema_view.induced_class("PolarisPopulationTranslationBundle")
    _required_slots(
        schema_view,
        "PolarisPopulationTranslationBundle",
        "source_trajectory_bundle",
        "scenario_definition_ref",
        "stochastic_realization_id",
        "population_translation_contract",
        "translation_implementation_binding",
        "implementation_artifact",
        "members",
        "receipt_generation_mode",
        "requested_years",
        "successful_years",
        "completeness_status",
    )
    assert bundle.attributes["source_trajectory_bundle"].range == (
        "PopulationTrajectoryBundleReference"
    )
    assert bundle.attributes["population_translation_contract"].range == (
        "PopulationTranslationContractReference"
    )
    assert bundle.attributes["translation_implementation_binding"].range == (
        "TranslationImplementationBindingReference"
    )
    assert bundle.attributes["implementation_artifact"].range == (
        "PhysicalArtifactReference"
    )
    assert (
        bundle.attributes["residue_observations"].range == "MappingResidueObservation"
    )
    assert bundle.attributes["skipped_years"].range == "SkippedPopulationYear"
    assert (
        "conditional"
        in str(bundle.annotations["conformance_requirements"].value).lower()
    )

    for class_name in (
        "PolarisHouseholdRecord",
        "PolarisPersonRecord",
        "PolarisVehicleRecord",
    ):
        assert (
            schema_view.induced_class(class_name).annotations["coverage"].value
            == "identity-bearing partial projection"
        )
