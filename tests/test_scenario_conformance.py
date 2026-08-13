from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml
import pytest

from synergy_schema.conformance.cli import main
from synergy_schema.conformance.scenario import (
    canonical_scenario_json,
    scenario_digest,
    validate_scenario,
)
from synergy_schema.native_catalog import load_catalog, write_catalog


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


def _catalog(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    path = tmp_path / "catalogs" / "pilates" / "r1" / "catalog.yaml"
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
    document = load_catalog(path).document
    return (
        path,
        {
            key: document[key]
            for key in (
                "catalog_id",
                "catalog_kind",
                "revision",
                "digest_algorithm",
                "content_digest",
            )
        },
    )


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
    _catalog_path, catalog = _catalog(tmp_path)
    binding = {
        "binding_id": "pilates",
        "model_name": "PILATES",
        "scenario_definition_ref": {
            "scenario_definition_id": definition["id"],
            "revision": "r1",
            "content_digest": definition["content_digest"],
        },
        "native_contract_catalog": catalog,
        "assumption_bindings": [
            {
                "assumption_key": "tax",
                "native_element": {
                    "catalog": catalog,
                    "kind": "config_path",
                    "path": "run.tax",
                },
                "resolved_native_value": "1",
                "binding_mode": "direct",
                "compatibility_state": "compatible",
            },
            {
                "assumption_key": "enabled",
                "native_element": {
                    "catalog": catalog,
                    "kind": "config_path",
                    "path": "run.enabled",
                },
                "resolved_native_value": "1",
                "binding_mode": "alias",
                "compatibility_state": "compatible",
            },
        ],
    }
    assert (
        validate_scenario(
            definition,
            [binding],
            _trajectory(definition),
            catalog_root=tmp_path / "catalogs",
        ).diagnostics
        == ()
    )

    broken = deepcopy(definition)
    broken["content_digest"] = "0" * 64
    diagnostics = validate_scenario(
        broken, [binding], _trajectory(definition), catalog_root=tmp_path / "catalogs"
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
        "native_contract_catalog": _catalog(tmp_path)[1],
        "assumption_bindings": [
            {
                "assumption_key": "tax",
                "native_element": {
                    "catalog": _catalog(tmp_path)[1],
                    "kind": "config_path",
                    "path": "missing",
                },
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
        for item in validate_scenario(
            definition, [binding], trajectory, catalog_root=tmp_path / "catalogs"
        ).diagnostics
    ]
    assert codes == [
        "NATIVE_ELEMENT_UNRESOLVED",
        "SCENARIO_BINDING_CONFLICT",
        "TRAJECTORY_COMPLETENESS_MISMATCH",
    ]


def test_catalog_identity_must_match_binding_and_native_elements(
    tmp_path: Path,
) -> None:
    definition = _definition()
    _path, catalog = _catalog(tmp_path)
    binding = {
        "scenario_definition_ref": {
            "scenario_definition_id": definition["id"],
            "revision": "r1",
            "content_digest": definition["content_digest"],
        },
        "native_contract_catalog": catalog,
        "assumption_bindings": [
            {
                "assumption_key": "tax",
                "native_element": {
                    "catalog": {**catalog, "content_digest": "0" * 64},
                    "kind": "config_path",
                    "path": "run.tax",
                },
                "resolved_native_value": "1",
                "binding_mode": "direct",
                "compatibility_state": "compatible",
            }
        ],
    }
    assert [
        item.code
        for item in validate_scenario(
            definition,
            [binding],
            _trajectory(definition),
            catalog_root=tmp_path / "catalogs",
        ).diagnostics
    ] == ["NATIVE_ELEMENT_UNRESOLVED"]
    binding["native_contract_catalog"] = {**catalog, "content_digest": "1" * 64}
    assert [
        item.code
        for item in validate_scenario(
            definition,
            [binding],
            _trajectory(definition),
            catalog_root=tmp_path / "catalogs",
        ).diagnostics
    ] == ["NATIVE_ELEMENT_UNRESOLVED"]


def test_completeness_status_matches_successful_and_skipped_years(
    tmp_path: Path,
) -> None:
    definition = _definition()
    _path, catalog = _catalog(tmp_path)
    binding = {
        "scenario_definition_ref": {
            "scenario_definition_id": definition["id"],
            "revision": "r1",
            "content_digest": definition["content_digest"],
        },
        "native_contract_catalog": catalog,
        "assumption_bindings": [
            {
                "assumption_key": "tax",
                "native_element": {
                    "catalog": catalog,
                    "kind": "config_path",
                    "path": "run.tax",
                },
                "resolved_native_value": "1",
                "binding_mode": "direct",
                "compatibility_state": "compatible",
            }
        ],
    }
    trajectory = _trajectory(definition)
    trajectory["snapshots"] = trajectory["snapshots"][:1]
    trajectory["skipped_years"] = [{"year": 2030, "reason": "not run"}]
    trajectory["completeness_status"] = "incomplete"
    assert (
        validate_scenario(
            definition, [binding], trajectory, catalog_root=tmp_path / "catalogs"
        ).diagnostics
        == ()
    )
    trajectory["completeness_status"] = "complete"
    assert [
        item.code
        for item in validate_scenario(
            definition, [binding], trajectory, catalog_root=tmp_path / "catalogs"
        ).diagnostics
    ] == ["TRAJECTORY_COMPLETENESS_MISMATCH"]


def test_cli_handles_malformed_trajectory_members_and_checks_schema(
    tmp_path: Path,
) -> None:
    definition = _definition()
    _path, catalog = _catalog(tmp_path)
    binding = {
        "bindings": [
            {
                "scenario_definition_ref": {
                    "scenario_definition_id": definition["id"],
                    "revision": "r1",
                    "content_digest": definition["content_digest"],
                },
                "native_contract_catalog": catalog,
                "assumption_bindings": [
                    {
                        "assumption_key": "tax",
                        "native_element": {
                            "catalog": catalog,
                            "kind": "config_path",
                            "path": "run.tax",
                        },
                        "resolved_native_value": "1",
                        "binding_mode": "direct",
                        "compatibility_state": "compatible",
                    }
                ],
            }
        ]
    }
    definition_path, bindings_path, trajectory_path = (
        tmp_path / "definition.yaml",
        tmp_path / "bindings.yaml",
        tmp_path / "trajectory.yaml",
    )
    definition_path.write_text(yaml.safe_dump(definition), encoding="utf-8")
    bindings_path.write_text(yaml.safe_dump(binding), encoding="utf-8")
    for malformed in (
        {
            **_trajectory(definition),
            "snapshots": [
                {**_trajectory(definition)["snapshots"][0], "simulation_year": None}
            ],
        },
        {**_trajectory(definition), "snapshots": ["not-a-mapping"]},
    ):
        trajectory_path.write_text(yaml.safe_dump(malformed), encoding="utf-8")
        assert (
            main(
                [
                    "check-scenario",
                    "--schema",
                    str(
                        Path(__file__).parents[1]
                        / "src/synergy_schema/schema/synergy_schema.yaml"
                    ),
                    "--definition",
                    str(definition_path),
                    "--bindings",
                    str(bindings_path),
                    "--trajectory",
                    str(trajectory_path),
                    "--catalog-root",
                    str(tmp_path / "catalogs"),
                ]
            )
            == 1
        )
    assert (
        main(
            [
                "check-scenario",
                "--schema",
                str(tmp_path / "missing.yaml"),
                "--definition",
                str(definition_path),
                "--bindings",
                str(bindings_path),
                "--trajectory",
                str(trajectory_path),
                "--catalog-root",
                str(tmp_path / "catalogs"),
            ]
        )
        == 2
    )


def test_cli_rejects_malformed_skipped_year_members(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    definition = _definition()
    _path, catalog = _catalog(tmp_path)
    binding = {
        "bindings": [
            {
                "scenario_definition_ref": {
                    "scenario_definition_id": definition["id"],
                    "revision": "r1",
                    "content_digest": definition["content_digest"],
                },
                "native_contract_catalog": catalog,
                "assumption_bindings": [
                    {
                        "assumption_key": "tax",
                        "native_element": {
                            "catalog": catalog,
                            "kind": "config_path",
                            "path": "run.tax",
                        },
                        "resolved_native_value": "1",
                        "binding_mode": "direct",
                        "compatibility_state": "compatible",
                    }
                ],
            }
        ]
    }
    definition_path, bindings_path, trajectory_path = (
        tmp_path / "definition.yaml",
        tmp_path / "bindings.yaml",
        tmp_path / "trajectory.yaml",
    )
    definition_path.write_text(yaml.safe_dump(definition), encoding="utf-8")
    bindings_path.write_text(yaml.safe_dump(binding), encoding="utf-8")
    schema_path = (
        Path(__file__).parents[1] / "src/synergy_schema/schema/synergy_schema.yaml"
    )
    for skipped_years in ([{}], [{"year": 2030, "reason": None}], ["scalar"]):
        trajectory = _trajectory(definition)
        trajectory["snapshots"] = trajectory["snapshots"][:1]
        trajectory["skipped_years"] = skipped_years
        trajectory["completeness_status"] = "incomplete"
        trajectory_path.write_text(yaml.safe_dump(trajectory), encoding="utf-8")
        assert (
            main(
                [
                    "check-scenario",
                    "--schema",
                    str(schema_path),
                    "--definition",
                    str(definition_path),
                    "--bindings",
                    str(bindings_path),
                    "--trajectory",
                    str(trajectory_path),
                    "--catalog-root",
                    str(tmp_path / "catalogs"),
                ]
            )
            == 1
        )
        assert "SCENARIO_DOCUMENT_INVALID" in capsys.readouterr().err
    incompatible_schema = tmp_path / "incompatible.yaml"
    incompatible_schema.write_text(
        "id: https://example.org/test\nname: test\n", encoding="utf-8"
    )
    assert (
        main(
            [
                "check-scenario",
                "--schema",
                str(incompatible_schema),
                "--definition",
                str(definition_path),
                "--bindings",
                str(bindings_path),
                "--trajectory",
                str(trajectory_path),
                "--catalog-root",
                str(tmp_path / "catalogs"),
            ]
        )
        == 2
    )
