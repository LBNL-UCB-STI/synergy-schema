"""Command line entry point for deterministic conformance checks."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from .diagnostics import CheckResult, InputError
from .documents import load_list, load_mapping
from .scenario import validate_scenario


_COMMANDS = (
    "check-scenario",
    "check-mappings",
    "check-population-bundle",
    "check-polaris-bundle",
    "check-all",
    "create-day-zero-manifest",
    "render-mapping",
    "diff-mappings",
    "import-mapping",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="synergy-conformance")
    commands = parser.add_subparsers(dest="command", required=True)
    scenario = commands.add_parser("check-scenario")
    scenario.add_argument("--schema", required=True)
    scenario.add_argument("--definition", required=True)
    scenario.add_argument("--bindings", required=True)
    scenario.add_argument("--trajectory", required=True)
    mappings = commands.add_parser("check-mappings")
    mappings.add_argument("--schema", required=True)
    mappings.add_argument("--mappings", required=True)
    for name in _COMMANDS[2:]:
        command = commands.add_parser(name)
        command.add_argument("--schema", required=True)
        command.add_argument("--dir", required=True)
    return parser


def _dispatch(args: argparse.Namespace) -> CheckResult:
    if args.command == "check-scenario":
        return validate_scenario(
            load_mapping(args.definition),
            load_list(args.bindings),
            load_mapping(args.trajectory),
        )
    raise InputError(f"{args.command} is not wired in this conformance foundation")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        result = _dispatch(args)
    except SystemExit as error:
        return int(error.code)
    except KeyboardInterrupt:
        return 130
    except InputError as error:
        print(str(error), file=sys.stderr)
        return 2
    for diagnostic in result.diagnostics:
        print(
            f"{diagnostic.severity.upper()} {diagnostic.code}: {diagnostic.message}",
            file=sys.stderr,
        )
    return result.exit_code
