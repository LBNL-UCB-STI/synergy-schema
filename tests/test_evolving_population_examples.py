from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import yaml
from linkml.validator import Validator
from linkml.validator.plugins import JsonschemaValidationPlugin

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
    assert manifest["mapping_release"] == "mapping-release/revision-1"
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


def _load_core() -> dict[str, object]:
    return yaml.safe_load(
        (_example("evolving_population") / "core-population-evolution.yaml").read_text()
    )


def _records(core: dict[str, object], key: str) -> list[dict[str, object]]:
    value = core[key]
    assert isinstance(value, list)
    assert all(isinstance(item, dict) for item in value)
    return value


def test_evolving_population_has_schema_native_relationships_and_lineage() -> None:
    core = _load_core()
    assert set(core) == {
        "population_snapshots",
        "household_states",
        "person_states",
        "household_memberships",
        "vehicle_states",
        "household_vehicle_assignments",
    }
    assert "states" not in core

    snapshots = _records(core, "population_snapshots")
    snapshots_by_id = {item["id"]: item for item in snapshots}
    scenario = yaml.safe_load(
        (_example("evolving_population") / "zev-scenario-definition.yaml").read_text()
    )
    scenario_identity = {
        "scenario_definition_id": scenario["id"],
        "revision": scenario["revision"],
        "content_digest": scenario["content_digest"],
    }
    assert {
        tuple(snapshot["scenario_definition_ref"].items()) for snapshot in snapshots
    } == {tuple(scenario_identity.items())}
    persons = _records(core, "person_states")
    memberships = _records(core, "household_memberships")
    vehicles = _records(core, "vehicle_states")
    assignments = _records(core, "household_vehicle_assignments")
    schema = Validator(
        str(SCHEMA), validation_plugins=[JsonschemaValidationPlugin(closed=True)]
    )
    for key, root_name in (
        ("population_snapshots", "PopulationSnapshot"),
        ("household_states", "HouseholdState"),
        ("person_states", "PersonState"),
        ("household_memberships", "HouseholdMembership"),
        ("vehicle_states", "VehicleState"),
        ("household_vehicle_assignments", "HouseholdVehicleAssignment"),
    ):
        for record in _records(core, key):
            assert not schema.validate(record, root_name).results, (key, record)

    for person in persons:
        matching = [
            row
            for row in memberships
            if row["person_state_ref"] == person["person_state_id"]
            and row["population_snapshot_ref"] == person["population_snapshot_ref"]
        ]
        assert len(matching) == 1
        household_ids = {
            item["household_state_id"]
            for item in _records(core, "household_states")
            if item["population_snapshot_ref"] == person["population_snapshot_ref"]
        }
        assert matching[0]["population_snapshot_ref"] in snapshots_by_id
        assert matching[0]["household_state_ref"] in household_ids
    for vehicle in vehicles:
        matching = [
            row
            for row in assignments
            if row["vehicle_state_ref"] == vehicle["vehicle_state_id"]
            and row["population_snapshot_ref"] == vehicle["population_snapshot_ref"]
        ]
        assert len(matching) == 1
        household_ids = {
            item["household_state_id"]
            for item in _records(core, "household_states")
            if item["population_snapshot_ref"] == vehicle["population_snapshot_ref"]
        }
        assert matching[0]["population_snapshot_ref"] in snapshots_by_id
        assert matching[0]["household_state_ref"] in household_ids

    alex = [
        item
        for item in persons
        if item.get("longitudinal_person_ref") == "person:synthetic-evolving:alex"
    ]
    assert [
        snapshots_by_id[item["population_snapshot_ref"]]["simulation_year"]
        for item in alex
    ] == [2025, 2030, 2035]
    assert any(
        item.get("longitudinal_person_ref") == "person:synthetic-evolving:new-2030"
        and snapshots_by_id[item["population_snapshot_ref"]]["simulation_year"] == 2030
        for item in persons
    )

    households = _records(core, "household_states")
    split = [
        item
        for item in households
        if snapshots_by_id[item["population_snapshot_ref"]]["simulation_year"] == 2030
    ]
    assert {tuple(item["predecessor_state_refs"]) for item in split} == {
        ("household-state:synthetic-evolving-2025:family-a",)
    }
    vehicle = [
        item
        for item in vehicles
        if item.get("longitudinal_vehicle_ref") == "vehicle:synthetic-evolving:shared-1"
    ]
    household_by_vehicle_year = {
        snapshots_by_id[item["population_snapshot_ref"]]["simulation_year"]: next(
            row["household_state_ref"]
            for row in assignments
            if row["vehicle_state_ref"] == item["vehicle_state_id"]
        )
        for item in vehicle
    }
    assert household_by_vehicle_year[2025].endswith(":family-a")
    assert household_by_vehicle_year[2030].endswith(":family-a-2")
    assert household_by_vehicle_year[2035].endswith(":family-a-2")


def test_evolving_population_branches_have_real_role_artifacts_and_native_rows() -> (
    None
):
    root = _example("evolving_population")
    expected_story = {
        2025: {
            "households": {"family-a"},
            "persons": {"alex": "family-a"},
            "vehicles": {"shared-1": "family-a"},
        },
        2030: {
            "households": {"family-a-1", "family-a-2"},
            "persons": {"alex": "family-a-1", "new-2030": "family-a-2"},
            "vehicles": {"shared-1": "family-a-2"},
        },
        2035: {
            "households": {"family-a-1", "family-a-2"},
            "persons": {"alex": "family-a-1", "new-2030": "family-a-2"},
            "vehicles": {"shared-1": "family-a-2"},
        },
    }
    manifests = {}
    for branch in ("baseline", "zev"):
        branch_root = root / branch
        assert (
            main(["check-all", "--schema", str(SCHEMA), "--dir", str(branch_root)]) == 0
        )
        manifest = yaml.safe_load((branch_root / "showcase.yaml").read_text())
        manifests[branch] = manifest
        bundle_path = branch_root / manifest["population_bundle"]
        bundle = yaml.safe_load(bundle_path.read_text())
        for snapshot_bundle in bundle["population_snapshot_bundles"]:
            year = snapshot_bundle["population_snapshot"]["simulation_year"]
            locators = [
                member["artifact"]["locator"] for member in snapshot_bundle["members"]
            ]
            assert len(locators) == len(set(locators))
            for member in snapshot_bundle["members"]:
                artifact = bundle_path.parent / member["artifact"]["locator"]
                assert artifact.resolve().is_relative_to(ROOT.resolve())
                assert artifact.is_file()
                assert (
                    sha256(artifact.read_bytes()).hexdigest()
                    == member["artifact"]["artifact_identity"]["content_digest"]
                )
            provenance_locator = snapshot_bundle["consist_provenance"][
                "provenance_context"
            ]["locator"]
            provenance_artifact = bundle_path.parent / provenance_locator
            assert provenance_artifact.resolve().is_relative_to(ROOT.resolve())
            assert provenance_artifact.is_file()
            provenance = snapshot_bundle["consist_provenance"]
            provenance_artifacts = {
                artifact["artifact_id"]: artifact
                for artifact in provenance["artifacts"]
            }
            associations = provenance["associations"]
            assert len(associations) == len(snapshot_bundle["members"])
            assert {
                item["artifact"]["artifact_identity"]["content_digest"]
                for item in snapshot_bundle["members"]
            } == {
                provenance_artifacts[item["artifact"]["artifact_id"]][
                    "immutable_identity"
                ]["digest"]
                for item in associations
            }
            for member, association in zip(snapshot_bundle["members"], associations):
                provenance_record = provenance_artifacts[
                    association["artifact"]["artifact_id"]
                ]
                assert (
                    provenance_record["immutable_identity"]["digest"]
                    == member["artifact"]["artifact_identity"]["content_digest"]
                )
                if "artifact_key" in provenance_record:
                    assert str(year) in provenance_record["artifact_key"]
            atlas_files = {
                member["semantic_role"]: yaml.safe_load(
                    (bundle_path.parent / member["artifact"]["locator"]).read_text()
                )
                for member in snapshot_bundle["members"]
            }
            assert {
                row["household_id"] for row in atlas_files["households"]["rows"]
            } == expected_story[year]["households"]
            assert {
                row["person_id"]: row["household_id"]
                for row in atlas_files["persons"]["rows"]
            } == expected_story[year]["persons"]
            assert {
                row["vehicle_id"]: row["household_id"]
                for row in atlas_files["vehicles"]["rows"]
            } == expected_story[year]["vehicles"]
        polaris_path = branch_root / manifest["polaris_bundle"]
        polaris = yaml.safe_load(polaris_path.read_text())
        assert {
            (member["simulation_year"], member["semantic_role"])
            for member in polaris["members"]
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
        for member in polaris["members"]:
            artifact = polaris_path.parent / member["artifact"]["locator"]
            assert artifact.resolve().is_relative_to(ROOT.resolve())
            assert artifact.is_file()
            assert (
                sha256(artifact.read_bytes()).hexdigest()
                == member["artifact"]["artifact_identity"]["content_digest"]
            )
        for year in (2025, 2030, 2035):
            role_files = {
                member["semantic_role"]: yaml.safe_load(
                    (polaris_path.parent / member["artifact"]["locator"]).read_text()
                )
                for member in polaris["members"]
                if member["simulation_year"] == year
            }
            assert {
                row["hhold"] for row in role_files["households"]["rows"]
            } == expected_story[year]["households"]
            assert {
                row["person_id"]: row["hhold"] for row in role_files["persons"]["rows"]
            } == expected_story[year]["persons"]
            assert {
                row["vehicle_id"]: row["hhold"]
                for row in role_files["vehicles"]["rows"]
            } == expected_story[year]["vehicles"]
            assert {
                row["vehicle_id"] for row in role_files["vehicle_class"]["rows"]
            } == set(expected_story[year]["vehicles"])
            assert {
                row["vehicle_id"] for row in role_files["vehicle_type"]["rows"]
            } == set(expected_story[year]["vehicles"])

    assert (
        manifests["baseline"]["population_bundle"]
        != manifests["zev"]["population_bundle"]
    )
    baseline_pol = yaml.safe_load(
        (root / "baseline-polaris-translation-bundle.yaml").read_text()
    )
    zev_pol = yaml.safe_load((root / "zev-polaris-translation-bundle.yaml").read_text())
    baseline_pop = yaml.safe_load(
        (root / "baseline-pilates-trajectory-bundle.yaml").read_text()
    )
    zev_pop = yaml.safe_load((root / "zev-pilates-trajectory-bundle.yaml").read_text())
    assert [
        m["artifact"]["locator"]
        for m in baseline_pop["population_snapshot_bundles"][0]["members"]
    ] == [
        m["artifact"]["locator"]
        for m in zev_pop["population_snapshot_bundles"][0]["members"]
    ]
    for year in (2025, 2030, 2035):
        for role in ("households", "persons", "vehicles", "vehicle_class"):
            baseline_member = next(
                item
                for item in baseline_pol["members"]
                if item["simulation_year"] == year and item["semantic_role"] == role
            )
            zev_member = next(
                item
                for item in zev_pol["members"]
                if item["simulation_year"] == year and item["semantic_role"] == role
            )
            assert (
                baseline_member["artifact"]["artifact_identity"]
                == zev_member["artifact"]["artifact_identity"]
            )
    for year in (2025, 2030, 2035):
        baseline_types = yaml.safe_load(
            (
                root
                / next(
                    item
                    for item in baseline_pol["members"]
                    if item["simulation_year"] == year
                    and item["semantic_role"] == "vehicle_type"
                )["artifact"]["locator"]
            ).read_text()
        )
        zev_types = yaml.safe_load(
            (
                root
                / next(
                    item
                    for item in zev_pol["members"]
                    if item["simulation_year"] == year
                    and item["semantic_role"] == "vehicle_type"
                )["artifact"]["locator"]
            ).read_text()
        )
        assert {row["vehicle_type"] for row in baseline_types["rows"]} == {"gasoline"}
        assert {row["vehicle_type"] for row in zev_types["rows"]} == {
            "battery_electric"
        }


def test_evolving_population_receipts_and_bindings_are_traceable() -> None:
    root = _example("evolving_population")
    for branch in ("baseline", "zev"):
        branch_root = root / branch
        manifest = yaml.safe_load((branch_root / "showcase.yaml").read_text())
        bindings = yaml.safe_load(
            (branch_root / manifest["model_bindings"]).read_text()
        )["bindings"]
        catalog_root = branch_root / manifest["catalog_root"]
        for binding in bindings:
            for assumption in binding["assumption_bindings"]:
                native = assumption["native_element"]
                assert native["kind"] == "config_path"
                catalogs = list(catalog_root.glob("*/*/catalog.yaml"))
                assert any(
                    any(
                        element["kind"] == native["kind"]
                        and element["path"] == native["path"]
                        for element in yaml.safe_load(path.read_text())["elements"]
                    )
                    for path in catalogs
                )
        receipt = yaml.safe_load((branch_root / manifest["polaris_bundle"]).read_text())
        receipt_path = branch_root / manifest["polaris_bundle"]
        for declaration in (receipt["implementation_artifact"],):
            artifact = receipt_path.parent / declaration["locator"]
            assert artifact.resolve().is_relative_to(ROOT.resolve())
            assert artifact.is_file()
            assert (
                sha256(artifact.read_bytes()).hexdigest()
                == declaration["artifact_identity"]["content_digest"]
            )
        population_path = branch_root / manifest["population_bundle"]
        population = yaml.safe_load(population_path.read_text())
        for declaration in (
            population["schedule_evidence"]["config_catalog"],
            population["schedule_evidence"]["scheduler_implementation"],
        ):
            artifact = population_path.parent / declaration["locator"]
            assert artifact.resolve().is_relative_to(ROOT.resolve())
            assert artifact.is_file()
            assert (
                sha256(artifact.read_bytes()).hexdigest()
                == declaration["artifact_identity"]["content_digest"]
            )
        trajectory_member = population["members"][0]
        trajectory_artifact = (
            population_path.parent / trajectory_member["artifact"]["locator"]
        )
        assert trajectory_artifact.resolve().is_relative_to(ROOT.resolve())
        assert trajectory_artifact.is_file()
        assert (
            sha256(trajectory_artifact.read_bytes()).hexdigest()
            == trajectory_member["artifact"]["artifact_identity"]["content_digest"]
        )
        contract_path = (
            branch_root
            / manifest["mapping_release"]
            / "contract"
            / "population-translation-contract.yaml"
        )
        contract = yaml.safe_load(contract_path.read_text())
        mapping_artifact = contract_path.parent / contract["encoding_source"]["locator"]
        assert mapping_artifact.resolve().is_relative_to(ROOT.resolve())
        assert mapping_artifact.is_file()
        assert (
            sha256(mapping_artifact.read_bytes()).hexdigest()
            == contract["encoding_source"]["artifact_identity"]["content_digest"]
        )
        implementation_path = (
            branch_root
            / manifest["mapping_release"]
            / "implementation"
            / "pilates-translation.yaml"
        )
        implementation = yaml.safe_load(implementation_path.read_text())
        implementation_artifact = (
            implementation_path.parent
            / implementation["implementation_artifact"]["locator"]
        )
        assert implementation_artifact.resolve().is_relative_to(ROOT.resolve())
        assert implementation_artifact.is_file()
        assert (
            sha256(implementation_artifact.read_bytes()).hexdigest()
            == implementation["implementation_artifact"]["artifact_identity"][
                "content_digest"
            ]
        )
        source_roles = {
            (member["simulation_year"], member["semantic_role"]): member
            for member in receipt["members"]
        }
        for residue in receipt["residue_observations"]:
            for role in residue["affected_artifact_roles"]:
                assert (residue["simulation_year"], role) in source_roles
                relevant = len(
                    yaml.safe_load(
                        (
                            receipt_path.parent
                            / source_roles[(residue["simulation_year"], role)][
                                "artifact"
                            ]["locator"]
                        ).read_text()
                    ).get("rows", [])
                )
                assert residue["observed_count"] <= relevant

    valid = yaml.safe_load((root / "zev-polaris-translation-bundle.yaml").read_text())
    broken = yaml.safe_load(
        (
            _example("evolving_population_broken_artifact_identity")
            / "broken-polaris-bundle.yaml"
        ).read_text()
    )
    expected = deepcopy(valid)
    expected["implementation_artifact"]["artifact_identity"]["content_digest"] = broken[
        "implementation_artifact"
    ]["artifact_identity"]["content_digest"]
    assert broken == expected
