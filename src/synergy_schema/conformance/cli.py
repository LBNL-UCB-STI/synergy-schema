"""Command line entry point for deterministic conformance checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

import yaml

from linkml_runtime.utils.schemaview import SchemaView

from .bundles import validate_polaris_bundle, validate_population_bundle
from .day_zero import create_day_zero_manifest, validate_day_zero_manifest
from .diagnostics import CheckResult, InputError
from .documents import load_list, load_mapping, load_mapping_release, load_showcase
from .mappings import validate_mapping_release
from .review import diff_mappings, import_mapping, render_mapping
from .scenario import validate_scenario
from .shapes import validate_bundle_shape


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
    population = commands.add_parser("check-population-bundle")
    population.add_argument("--schema", required=True)
    population.add_argument("--bundle", required=True)
    polaris = commands.add_parser("check-polaris-bundle")
    polaris.add_argument("--schema", required=True)
    polaris.add_argument("--bundle", required=True)
    polaris.add_argument("--source-population-bundle", required=True)
    polaris.add_argument("--mapping-release", required=True)
    polaris.add_argument("--production", action="store_true")
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
    if args.command == "check-population-bundle":
        _require_roots(args.schema, {"PopulationTrajectoryBundle"})
        bundle = load_mapping(args.bundle)
        return _check_population_bundle(args.schema, bundle)
    if args.command == "check-polaris-bundle":
        _require_roots(args.schema, {"PolarisPopulationTranslationBundle"})
        bundle = load_mapping(args.bundle)
        source = load_mapping(args.source_population_bundle)
        contract, implementations, ownership = load_mapping_release(
            args.mapping_release
        )
        return _check_polaris_bundle(
            args.schema,
            bundle,
            source,
            contract,
            implementations,
            ownership,
            production=args.production,
        )
    if args.command == "check-all":
        _require_roots(
            args.schema,
            {
                "ScenarioDefinition",
                "PopulationTrajectoryBundle",
                "PolarisPopulationTranslationBundle",
                "PopulationTranslationContract",
            },
        )
        root = Path(args.dir)
        manifest = load_showcase(root)

        def document(name: str) -> dict[str, object]:
            value = manifest.get(name)
            if not isinstance(value, str):
                raise InputError(f"showcase.yaml requires relative {name}")
            return load_mapping(root / value)

        definition = document("scenario_definition")
        bindings = load_list(root / str(manifest["model_bindings"]))
        trajectory = document("trajectory")
        population = document("population_bundle")
        polaris = document("polaris_bundle")
        release_value = manifest.get("mapping_release")
        if not isinstance(release_value, str):
            raise InputError("showcase.yaml requires relative mapping_release")
        release = root / release_value
        contract, implementations, ownership = load_mapping_release(release)
        catalog_root = (
            root / str(manifest["catalog_root"])
            if manifest.get("catalog_root")
            else None
        )
        results = [
            validate_scenario(
                definition, bindings, trajectory, catalog_root=catalog_root
            ),
            validate_mapping_release(
                release,
                require_approved=args.require_approved_mapping or args.production,
                new_receipt=True,
                schema_path=args.schema,
                catalog_root=catalog_root,
            ),
            _check_polaris_bundle(
                args.schema,
                polaris,
                population,
                contract,
                implementations,
                ownership,
                production=args.production,
            ),
        ]
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


def _check_population_bundle(
    schema_path: str, bundle: dict[str, object]
) -> CheckResult:
    shape = validate_bundle_shape(schema_path, bundle, "PopulationTrajectoryBundle")
    return shape if shape.exit_code else validate_population_bundle(bundle)


def _check_polaris_bundle(
    schema_path: str,
    bundle: dict[str, object],
    source: dict[str, object],
    contract: dict[str, object],
    implementations: list[dict[str, object]],
    ownership: dict[str, object],
    *,
    production: bool,
) -> CheckResult:
    shapes = _combine(
        validate_bundle_shape(schema_path, source, "PopulationTrajectoryBundle"),
        validate_bundle_shape(
            schema_path, bundle, "PolarisPopulationTranslationBundle"
        ),
    )
    if shapes.exit_code:
        return shapes
    return validate_polaris_bundle(
        bundle,
        source,
        contract,
        implementations,
        ownership,
        production=production,
    )


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
