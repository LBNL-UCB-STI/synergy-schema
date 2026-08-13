from __future__ import annotations

from pathlib import Path

import yaml

from synergy_schema.conformance.cli import main
from synergy_schema.conformance.documents import load_mapping


ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "src/synergy_schema/schema/synergy_schema.yaml"


def _example(name: str) -> Path:
    return ROOT / "examples" / name


def test_evolving_population_showcase_preserves_two_immutable_branches(
    capsys: object,
) -> None:
    example = _example("evolving_population")
    assert main(["check-all", "--schema", str(SCHEMA), "--dir", str(example)]) == 0
    warnings = capsys.readouterr().err
    assert "SCENARIO_COMPATIBILITY_GAP" in warnings
    assert "MAPPING_NOT_APPROVED" in warnings

    baseline = load_mapping(example / "baseline-scenario-definition.yaml")
    zev = load_mapping(example / "zev-scenario-definition.yaml")
    assert baseline["content_digest"] != zev["content_digest"]
    assert baseline["id"] != zev["id"]

    for branch in ("baseline", "zev"):
        trajectory = load_mapping(example / f"{branch}-trajectory.yaml")
        assert trajectory["requested_years"] == [2025, 2030, 2035]
        assert [
            snapshot["simulation_year"] for snapshot in trajectory["snapshots"]
        ] == [
            2025,
            2030,
            2035,
        ]
        assert (
            len(
                load_mapping(example / f"{branch}-pilates-trajectory-bundle.yaml")[
                    "population_snapshot_bundles"
                ]
            )
            == 3
        )
        members = load_mapping(example / f"{branch}-polaris-translation-bundle.yaml")[
            "members"
        ]
        assert {
            (member["simulation_year"], member["semantic_role"]) for member in members
        } == {
            (year, role)
            for year in (2025, 2030, 2035)
            for role in (
                "households",
                "persons",
                "vehicles",
                "vehicle_class",
                "vehicle_type",
            )
        }

    core = yaml.safe_load((example / "core-population-evolution.yaml").read_text())
    states = core["states"]
    assert "person:new-2030" not in states[2025]["persons"]
    assert "person:new-2030" in states[2030]["persons"]
    assert (
        states[2025]["persons"]["person:alex"]["core_state"]
        == states[2030]["persons"]["person:alex"]["core_state"]
    )
    assert (
        states[2025]["persons"]["person:alex"]["model_owned"]["age"]
        < states[2030]["persons"]["person:alex"]["model_owned"]["age"]
    )
    assert states[2030]["households"]["household:family-a"]["successors"] == [
        "household:family-a-1",
        "household:family-a-2",
    ]
    assert (
        states[2025]["vehicles"]["vehicle:shared-1"]["household_assignment"]
        == "household:family-a"
    )
    assert (
        states[2030]["vehicles"]["vehicle:shared-1"]["household_assignment"]
        == "household:family-a-2"
    )

    bindings = load_mapping(example / "zev-model-bindings.yaml")["bindings"]
    polaris = next(
        binding for binding in bindings if binding["model_name"] == "POLARIS"
    )
    assert (
        polaris["assumption_bindings"][0]["compatibility_state"]
        == "compatible_with_gaps"
    )
    assert polaris["assumption_bindings"][0]["binding_mode"] == "unsupported"
    manifest = yaml.safe_load((example / "showcase.yaml").read_text())
    assert (
        manifest["mapping_release"]
        == "../one_year_mapping_handshake/mapping-release/revision-1"
    )
    assert (ROOT / "examples/one_year_mapping_handshake/review/residues.csv").exists()


def test_evolving_population_broken_examples_have_stable_diagnostics(
    capsys: object,
) -> None:
    scenario = _example("evolving_population_broken_scenario")
    assert main(["check-all", "--schema", str(SCHEMA), "--dir", str(scenario)]) == 1
    assert "SCENARIO_DIGEST_MISMATCH" in capsys.readouterr().err

    artifact = _example("evolving_population_broken_artifact_identity")
    assert main(["check-all", "--schema", str(SCHEMA), "--dir", str(artifact)]) == 1
    assert "ARTIFACT_IDENTITY_MISMATCH" in capsys.readouterr().err


def test_broken_showcases_only_replace_their_changed_documents() -> None:
    for name, changed in (
        ("evolving_population_broken_scenario", "scenario_definition"),
        ("evolving_population_broken_artifact_identity", "polaris_bundle"),
    ):
        manifest = yaml.safe_load((_example(name) / "showcase.yaml").read_text())
        local_documents = {path.name for path in _example(name).glob("*.yaml")}
        assert local_documents == {
            "showcase.yaml",
            f"broken-{changed.replace('_', '-')}.yaml",
        }
        assert manifest[changed] == f"broken-{changed.replace('_', '-')}.yaml"
        for key in (
            "scenario_definition",
            "model_bindings",
            "trajectory",
            "population_bundle",
            "polaris_bundle",
        ):
            if key != changed:
                assert manifest[key].startswith("../evolving_population/")
