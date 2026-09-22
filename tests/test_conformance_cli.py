from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys

import yaml

from synergy_schema.conformance.cli import build_parser, main
from synergy_schema.conformance.diagnostics import CheckResult, Diagnostic, InputError


ROOT = Path(__file__).parents[1]


def test_diagnostics_are_immutable_and_ordered() -> None:
    first = Diagnostic("A", "first", "warning")
    second = Diagnostic("B", "second", "error")
    result = CheckResult((second, first))
    assert result.diagnostics == (first, second)
    assert result.exit_code == 1
    assert CheckResult((first,)).exit_code == 0


def test_parser_exposes_the_complete_conformance_surface() -> None:
    parser = build_parser()
    subcommands = next(action for action in parser._actions if action.dest == "command")
    assert set(subcommands.choices) == {
        "check-scenario",
        "check-mappings",
        "check-population-bundle",
        "check-population-assembly",
        "check-polaris-bundle",
        "check-all",
        "create-day-zero-manifest",
        "render-mapping",
        "diff-mappings",
        "import-mapping",
    }


def test_help_and_error_exit_codes(capsys: object) -> None:
    assert main(["--help"]) == 0
    assert main(["check-all"]) == 2
    assert main(["check-population-bundle"]) == 2
    assert isinstance(InputError("bad input"), Exception)


def test_module_help_runs_with_conformance_runtime_dependencies() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "synergy_schema.conformance", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "check-scenario" in result.stdout


def test_keyboard_interrupt_returns_130(monkeypatch: object) -> None:
    import synergy_schema.conformance.cli as cli

    def interrupted(_: object) -> CheckResult:
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "_dispatch", interrupted)
    assert cli.main(["check-all", "--dir", ".", "--schema", "schema.yaml"]) == 130


def test_bundle_commands_use_explicit_bundle_and_manifest_directory_arguments() -> None:
    parser = build_parser()
    population = parser.parse_args(
        [
            "check-population-bundle",
            "--schema",
            "schema.yaml",
            "--bundle",
            "bundle.yaml",
        ]
    )
    polaris = parser.parse_args(
        [
            "check-polaris-bundle",
            "--schema",
            "schema.yaml",
            "--bundle",
            "bundle.yaml",
            "--source-population-bundle",
            "source.yaml",
            "--mapping-release",
            "release",
        ]
    )
    check_all = parser.parse_args(
        ["check-all", "--schema", "schema.yaml", "--dir", "example"]
    )
    assert population.bundle == "bundle.yaml"
    assert polaris.bundle == "bundle.yaml"
    assert polaris.source_population_bundle == "source.yaml"
    assert polaris.mapping_release == "release"
    assert check_all.dir == "example"

    assembly = parser.parse_args(
        [
            "check-population-assembly",
            "--schema",
            "schema.yaml",
            "--assembly",
            "assembly.yaml",
        ]
    )
    assert assembly.assembly == "assembly.yaml"
    assert assembly.contribution == []

    assembly_with_contributions = parser.parse_args(
        [
            "check-population-assembly",
            "--schema",
            "schema.yaml",
            "--assembly",
            "assembly.yaml",
            "--contribution",
            "demos.yaml",
            "--contribution",
            "atlas.yaml",
        ]
    )
    assert assembly_with_contributions.contribution == ["demos.yaml", "atlas.yaml"]


def test_bundle_command_rejects_unknown_closed_profile_field_before_semantics(
    tmp_path: Path, capsys: object
) -> None:
    """Closed LinkML profile validation guards semantic checks from unknown data."""
    example = ROOT / "examples" / "one_year_mapping_handshake"
    bundle = yaml.safe_load(
        (example / "pilates-trajectory-bundle.yaml").read_text(encoding="utf-8")
    )
    bundle["not_a_profile_slot"] = "forged"
    path = tmp_path / "bundle.yaml"
    path.write_text(yaml.safe_dump(bundle), encoding="utf-8")

    assert (
        main(
            [
                "check-population-bundle",
                "--schema",
                str(ROOT / "src/synergy_schema/schema/synergy_schema.yaml"),
                "--bundle",
                str(path),
            ]
        )
        == 1
    )
    assert "BUNDLE_SHAPE_INVALID" in capsys.readouterr().err


def test_granular_bundle_commands_gate_semantics_on_invalid_population_shape(
    tmp_path: Path, capsys: object
) -> None:
    """Malformed years stop both granular paths before integer coercion."""
    example = ROOT / "examples" / "one_year_mapping_handshake"
    schema = ROOT / "src/synergy_schema/schema/synergy_schema.yaml"
    bundle = yaml.safe_load(
        (example / "pilates-trajectory-bundle.yaml").read_text(encoding="utf-8")
    )
    bundle["population_trajectory"]["requested_years"] = ["not-a-year"]
    path = tmp_path / "bundle.yaml"
    path.write_text(yaml.safe_dump(bundle), encoding="utf-8")

    commands = (
        [
            "check-population-bundle",
            "--schema",
            str(schema),
            "--bundle",
            str(path),
        ],
        [
            "check-polaris-bundle",
            "--schema",
            str(schema),
            "--bundle",
            str(example / "polaris-translation-bundle.yaml"),
            "--source-population-bundle",
            str(path),
            "--mapping-release",
            str(example / "mapping-release/revision-1"),
        ],
    )
    for command in commands:
        assert main(command) == 1
        error = capsys.readouterr().err
        assert error.count("BUNDLE_SHAPE_INVALID") == 1
        assert "Traceback" not in error


def test_check_all_gates_semantics_on_invalid_population_shape(
    tmp_path: Path, capsys: object
) -> None:
    """The aggregate path reports shape once without running bundle semantics."""
    source = ROOT / "examples" / "one_year_mapping_handshake"
    example = tmp_path / "one_year_mapping_handshake"
    shutil.copytree(source, example)
    bundle_path = example / "pilates-trajectory-bundle.yaml"
    bundle = yaml.safe_load(bundle_path.read_text(encoding="utf-8"))
    bundle["population_trajectory"]["requested_years"] = ["not-a-year"]
    bundle_path.write_text(yaml.safe_dump(bundle), encoding="utf-8")

    assert (
        main(
            [
                "check-all",
                "--schema",
                str(ROOT / "src/synergy_schema/schema/synergy_schema.yaml"),
                "--dir",
                str(example),
            ]
        )
        == 1
    )
    error = capsys.readouterr().err
    assert error.count("BUNDLE_SHAPE_INVALID") == 1
    assert "Traceback" not in error


def test_adoption_commands_expose_their_public_arguments() -> None:
    parser = build_parser()
    day_zero = parser.parse_args(
        [
            "create-day-zero-manifest",
            "--artifact",
            "payload.csv",
            "--producer-artifact",
            "producer.sql",
            "--native-scenario-namespace",
            "atlas",
            "--native-scenario",
            "demo",
            "--year",
            "2025",
            "--out",
            "receipt.yaml",
        ]
    )
    rendered = parser.parse_args(
        ["render-mapping", "--release", "release", "--out-dir", "review"]
    )
    diffed = parser.parse_args(
        ["diff-mappings", "--old", "old", "--new", "new", "--format", "json"]
    )
    imported = parser.parse_args(
        ["import-mapping", "--review-dir", "review", "--out-release", "release"]
    )
    assert day_zero.year == 2025
    assert rendered.out_dir == "review"
    assert diffed.format == "json"
    assert imported.out_release == "release"
