"""Command line entry point for deterministic conformance checks."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from linkml_runtime.utils.schemaview import SchemaView

from .diagnostics import CheckResult, InputError
from .documents import load_list, load_mapping
from .mappings import validate_mapping_release
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
    scenario.add_argument("--catalog-root")
    mappings = commands.add_parser("check-mappings")
    mappings.add_argument("--schema", required=True)
    mappings.add_argument("--mappings", required=True)
    mappings.add_argument("--require-approved-mapping", action="store_true")
    mappings.add_argument("--new-receipt", action="store_true")
    mappings.add_argument("--catalog-root")
    for name in _COMMANDS[2:]:
        command = commands.add_parser(name)
        command.add_argument("--schema", required=True)
        command.add_argument("--dir", required=True)
    return parser


def _dispatch(args: argparse.Namespace) -> CheckResult:
    if args.command == "check-scenario":
        try:
            schema = SchemaView(args.schema)
            required_roots = {
                "ScenarioDefinition",
                "ModelScenarioBinding",
                "PopulationTrajectory",
            }
            if any(schema.get_class(root) is None for root in required_roots):
                raise InputError(
                    "schema does not define required scenario conformance roots"
                )
        except InputError:
            raise
        except Exception as error:
            raise InputError(f"cannot load scenario schema: {error}") from error
        return validate_scenario(
            load_mapping(args.definition),
            load_list(args.bindings),
            load_mapping(args.trajectory),
            catalog_root=args.catalog_root,
        )
    if args.command == "check-mappings":
        return validate_mapping_release(
            args.mappings,
            require_approved=args.require_approved_mapping,
            new_receipt=args.new_receipt,
            schema_path=args.schema,
            catalog_root=args.catalog_root,
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
