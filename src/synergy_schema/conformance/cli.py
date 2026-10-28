"""Command line entry point for deterministic conformance checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

import yaml

from linkml_runtime.utils.schemaview import SchemaView

from .day_zero import create_day_zero_manifest, validate_day_zero_manifest
from .diagnostics import CheckResult, InputError
from .documents import load_list, load_mapping, load_showcase
from .empirical import (
    DEFAULT_EVIDENCE_DIR,
    DEFAULT_SCHEMA_PATH,
    render_empirical_report_markdown,
    run_empirical_conformance_audit,
)
from .ledger import validate_ledger
from .mappings import validate_mapping_release
from .review import diff_mappings, import_mapping, render_mapping
from .scenario import validate_scenario


_COMMANDS = (
    "check-scenario",
    "check-mappings",
    "check-ledger",
    "check-all",
    "check-empirical",
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
    ledger = commands.add_parser("check-ledger")
    ledger.add_argument(
        "ledger", nargs="?", default=None, help="path to PopulationLedger document"
    )
    ledger.add_argument(
        "--ledger", dest="ledger_flag", help="path to PopulationLedger document"
    )
    ledger.add_argument(
        "--schema", help="path to schema (defaults to population_ledger.yaml)"
    )
    ledger.add_argument(
        "--mapping-catalog", help="path to CoreFacetMappingCatalog document"
    )
    ledger.add_argument(
        "--verify-consist-provenance",
        action="store_true",
        help="verify producing_run and artifact hashes against Consist DuckDB provenance",
    )
    ledger.add_argument(
        "--consist-db",
        help="path to Consist provenance.duckdb",
    )
    ledger.add_argument(
        "--data-root",
        help="root directory for resolving relative view and stored_object artifact locators",
    )
    ledger.add_argument(
        "--verify-state-digest",
        action="store_true",
        help="verify that core_state.state_digest matches recomputed core_state/v1 hash",
    )
    check_all = commands.add_parser("check-all")
    check_all.add_argument("--schema", required=True)
    check_all.add_argument("--dir", required=True)
    check_all.add_argument("--production", action="store_true")
    check_all.add_argument("--require-approved-mapping", action="store_true")
    day_zero = commands.add_parser("create-day-zero-manifest")
    day_zero.add_argument("--artifact", required=True)
    day_zero.add_argument("--producer-artifact", required=True)
    day_zero.add_argument("--native-scenario-namespace", required=True)
    day_zero.add_argument("--native-scenario", required=True)
    day_zero.add_argument("--year", required=True, type=int)
    day_zero.add_argument("--out", required=True)
    render = commands.add_parser("render-mapping")
    render.add_argument("--release", required=True)
    render.add_argument("--out-dir", required=True)
    diff = commands.add_parser("diff-mappings")
    diff.add_argument("--old", required=True)
    diff.add_argument("--new", required=True)
    diff.add_argument("--format", choices=("text", "markdown", "json"), default="text")
    imported = commands.add_parser("import-mapping")
    imported.add_argument("--review-dir", required=True)
    imported.add_argument("--out-release", required=True)
    empirical = commands.add_parser("check-empirical")
    empirical.add_argument("--schema", default=str(DEFAULT_SCHEMA_PATH))
    empirical.add_argument("--evidence-dir", default=str(DEFAULT_EVIDENCE_DIR))
    empirical.add_argument("--sample-size", type=int, default=20)
    empirical.add_argument("--format", choices=("markdown", "json"), default="markdown")
    empirical.add_argument("--out")
    return parser


def _dispatch(args: argparse.Namespace) -> CheckResult:
    if args.command == "check-scenario":
        try:
            schema = SchemaView(args.schema)
            required_roots = {
                "ScenarioDefinition",
                "ModelScenarioBinding",
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
    if args.command == "check-ledger":
        path = args.ledger or args.ledger_flag
        if not path:
            raise InputError("check-ledger requires a ledger document path")
        ledger_doc = load_mapping(path)
        catalog_doc = (
            load_mapping(args.mapping_catalog) if args.mapping_catalog else None
        )
        return validate_ledger(
            ledger_doc,
            catalog=catalog_doc,
            schema_path=args.schema,
            verify_consist_provenance=args.verify_consist_provenance,
            consist_db=args.consist_db,
            data_root=args.data_root,
            verify_state_digest=args.verify_state_digest,
        )
    if args.command == "check-all":
        root = Path(args.dir)
        manifest = load_showcase(root)

        def document(name: str) -> dict[str, object]:
            value = manifest.get(name)
            if not isinstance(value, str):
                raise InputError(f"showcase.yaml requires relative {name}")
            return load_mapping(root / value)

        results: list[CheckResult] = []
        catalog_root = (
            root / str(manifest["catalog_root"])
            if manifest.get("catalog_root")
            else None
        )
        if "scenario_definition" in manifest:
            _require_roots(args.schema, {"ScenarioDefinition", "ModelScenarioBinding"})
            definition = document("scenario_definition")
            bindings = load_list(root / str(manifest["model_bindings"]))
            target = None
            if "ledger" in manifest:
                target = document("ledger")
            elif "trajectory" in manifest:
                target = document("trajectory")
            results.append(
                validate_scenario(
                    definition, bindings, target, catalog_root=catalog_root
                )
            )

        if "mapping_release" in manifest:
            _require_roots(args.schema, {"PopulationTranslationContract"})
            release_value = manifest["mapping_release"]
            release = root / str(release_value)
            results.append(
                validate_mapping_release(
                    release,
                    require_approved=args.require_approved_mapping or args.production,
                    new_receipt=True,
                    schema_path=args.schema,
                    catalog_root=catalog_root,
                )
            )

        if "ledger" in manifest:
            _require_roots(args.schema, {"PopulationLedger"})
            ledger_doc = document("ledger")
            catalog_doc = (
                document("mapping_catalog") if "mapping_catalog" in manifest else None
            )
            results.append(
                validate_ledger(
                    ledger_doc, catalog=catalog_doc, schema_path=args.schema
                )
            )

        return _combine(*results)
    if args.command == "create-day-zero-manifest":
        manifest = create_day_zero_manifest(
            args.artifact,
            args.producer_artifact,
            args.native_scenario_namespace,
            args.native_scenario,
            args.year,
        )
        Path(args.out).write_text(
            yaml.safe_dump(manifest, sort_keys=True), encoding="utf-8"
        )
        return validate_day_zero_manifest(manifest)
    if args.command == "render-mapping":
        render_mapping(args.release, args.out_dir)
        return CheckResult()
    if args.command == "diff-mappings":
        changes = diff_mappings(args.old, args.new)
        if args.format == "json":
            print(json.dumps(changes, sort_keys=True))
        elif args.format == "markdown":
            for category, entries in changes.items():
                print(f"## {category}\n")
                for entry in entries:
                    print(f"- {entry}")
        else:
            for category, entries in changes.items():
                for entry in entries:
                    print(f"{category}: {entry}")
        return CheckResult()
    if args.command == "import-mapping":
        import_mapping(args.review_dir, args.out_release)
        return CheckResult()
    if args.command == "check-empirical":
        report = run_empirical_conformance_audit(
            schema_path=Path(args.schema),
            evidence_dir=Path(args.evidence_dir),
            sample_size=args.sample_size,
        )
        rendered = (
            json.dumps(report.to_dict(), indent=2)
            if args.format == "json"
            else render_empirical_report_markdown(report)
        )
        if args.out:
            Path(args.out).write_text(rendered, encoding="utf-8")
        else:
            print(rendered)
        return report.to_check_result()
    raise InputError(f"{args.command} is not wired in this conformance foundation")


def _require_roots(schema_path: str, roots: set[str]) -> None:
    try:
        schema = SchemaView(schema_path)
        missing = sorted(root for root in roots if schema.get_class(root) is None)
        if missing:
            raise InputError(
                f"schema does not define required conformance roots: {', '.join(missing)}"
            )
    except InputError:
        raise
    except Exception as error:
        raise InputError(f"cannot load conformance schema: {error}") from error


def _combine(*results: CheckResult) -> CheckResult:
    """Return deterministic unique diagnostics from several validation seams."""
    unique = {
        (item.code, item.message, item.severity): item
        for result in results
        for item in result.diagnostics
    }
    return CheckResult(tuple(unique.values()))


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        result = _dispatch(args)
    except SystemExit as error:
        if error.code is None:
            return 0
        if isinstance(error.code, int):
            return error.code
        return 1
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
