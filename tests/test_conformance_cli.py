from __future__ import annotations

from pathlib import Path
import subprocess
import sys

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


def test_module_help_runs_without_linkml_validator_import() -> None:
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
        ["check-polaris-bundle", "--schema", "schema.yaml", "--bundle", "bundle.yaml"]
    )
    check_all = parser.parse_args(
        ["check-all", "--schema", "schema.yaml", "--dir", "example"]
    )
    assert population.bundle == "bundle.yaml"
    assert polaris.bundle == "bundle.yaml"
    assert check_all.dir == "example"


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
