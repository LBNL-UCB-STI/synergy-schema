from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from synergy_schema.conformance.scenario import (
    canonical_scenario_json,
    scenario_digest,
    validate_scenario,
)
from synergy_schema.native_catalog import write_catalog


def _definition() -> dict[str, object]:
    definition: dict[str, object] = {
        "id": "scenario:demo",
        "revision": "r1",
        "content_digest": "",
        "display_name": "Human display text",
        "region_ref": "region:demo",
        "start_year": 2025,
        "end_year": 2030,
        "assumptions": [
            {
                "assumption_key": "tax",
                "value": "1",
                "value_type": "integer",
                "authority": "policy",
            },
            {
                "assumption_key": "enabled",
                "value": "true",
                "value_type": "boolean",
                "authority": "policy",
            },
        ],
        "workflow_bindings": [{"not": "canonical"}],
    }
    definition["content_digest"] = scenario_digest(definition)
    return definition


def _catalog(tmp_path: Path) -> Path:
    path = tmp_path / "catalog.yaml"
    write_catalog(
        {
            "catalog_id": "pilates-native-contract",
            "catalog_kind": "pilates",
            "revision": "r1",
            "upstream": {"revision": "r1", "source_paths": ["config.py"]},
            "elements": [
                {"kind": "config_path", "path": "run.tax"},
                {"kind": "config_path", "path": "run.enabled"},
            ],
        },
        path,
    )
    return path


def _trajectory(definition: dict[str, object]) -> dict[str, object]:
    ref = {
        key: definition[key]
        for key in ("scenario_definition_id", "revision", "content_digest")
        if key in definition
    }
    ref["scenario_definition_id"] = definition["id"]
    return {
        "id": "trajectory:demo",
        "scenario_definition_ref": ref,
        "stochastic_realization_id": "seed-1",
        "snapshots": [
            {
                "id": "snapshot:2025",
                "simulation_year": 2025,
                "scenario_definition_ref": ref,
                "stochastic_realization_id": "seed-1",
            },
            {
                "id": "snapshot:2030",
                "simulation_year": 2030,
                "scenario_definition_ref": ref,
                "stochastic_realization_id": "seed-1",
                "parent_snapshot_ref": "snapshot:2025",
            },
        ],
        "requested_years": [2025, 2030],
        "skipped_years": [],
        "completeness_status": "complete",
    }


def test_canonical_projection_excludes_display_digest_and_workflow_bindings() -> None:
    definition = _definition()
    rendered = canonical_scenario_json(definition)
    assert "content_digest" not in rendered
    assert "display_name" not in rendered
    assert "workflow_bindings" not in rendered
    assert rendered == canonical_scenario_json(deepcopy(definition))


def test_scenario_validation_checks_digest_bindings_catalog_and_trajectory(
    tmp_path: Path,
) -> None:
    definition = _definition()
    catalog = _catalog(tmp_path)
    binding = {
        "binding_id": "pilates",
        "model_name": "PILATES",
        "scenario_definition_ref": {
            "scenario_definition_id": definition["id"],
            "revision": "r1",
            "content_digest": definition["content_digest"],
        },
        "native_contract_catalog": {"catalog_path": str(catalog)},
        "assumption_bindings": [
            {
                "assumption_key": "tax",
                "native_element": {"kind": "config_path", "path": "run.tax"},
                "resolved_native_value": "1",
                "binding_mode": "direct",
                "compatibility_state": "compatible",
            },
            {
                "assumption_key": "enabled",
                "native_element": {"kind": "config_path", "path": "run.enabled"},
                "resolved_native_value": "1",
                "binding_mode": "alias",
                "compatibility_state": "compatible",
            },
        ],
    }
    assert (
        validate_scenario(definition, [binding], _trajectory(definition)).diagnostics
        == ()
    )

    broken = deepcopy(definition)
    broken["content_digest"] = "0" * 64
    diagnostics = validate_scenario(
        broken, [binding], _trajectory(definition)
    ).diagnostics
    assert [diagnostic.code for diagnostic in diagnostics] == [
        "SCENARIO_DIGEST_MISMATCH"
    ]


def test_binding_and_trajectory_failures_are_stable(tmp_path: Path) -> None:
    definition = _definition()
    binding = {
        "scenario_definition_ref": {
            "scenario_definition_id": definition["id"],
            "revision": "r1",
            "content_digest": definition["content_digest"],
        },
        "native_contract_catalog": {"catalog_path": str(_catalog(tmp_path))},
        "assumption_bindings": [
            {
                "assumption_key": "tax",
                "native_element": {"kind": "config_path", "path": "missing"},
                "resolved_native_value": "2",
                "binding_mode": "direct",
                "compatibility_state": "compatible",
            }
        ],
    }
    trajectory = _trajectory(definition)
    trajectory["requested_years"] = [2025]
    codes = [
        item.code
        for item in validate_scenario(definition, [binding], trajectory).diagnostics
    ]
    assert codes == [
        "NATIVE_ELEMENT_UNRESOLVED",
        "SCENARIO_BINDING_CONFLICT",
        "TRAJECTORY_COMPLETENESS_MISMATCH",
    ]
