from pathlib import Path

import yaml

from synergy_schema.conformance.cli import main
from synergy_schema.conformance.shapes import validate_bundle_shape

ROOT = Path(__file__).parents[1]
EXAMPLE = ROOT / "examples" / "core_population_assembly"
SCHEMA = ROOT / "src" / "synergy_schema" / "schema" / "synergy_schema.yaml"


def _load(name: str) -> dict[str, object]:
    value = yaml.safe_load((EXAMPLE / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_canonical_manifests_are_shape_valid() -> None:
    assert (
        validate_bundle_shape(
            SCHEMA, _load("assembly.yaml"), "CorePopulationAssembly"
        ).exit_code
        == 0
    )
    for name in ("demos-contribution.yaml", "atlas-contribution.yaml"):
        assert (
            validate_bundle_shape(
                SCHEMA, _load(name), "CorePopulationContribution"
            ).exit_code
            == 0
        )


def test_synthetic_assembly_passes_with_typed_refs(capsys: object) -> None:
    assert (
        main(
            [
                "check-population-assembly",
                "--schema",
                str(SCHEMA),
                "--assembly",
                str(EXAMPLE / "assembly.yaml"),
                "--contribution",
                str(EXAMPLE / "demos-contribution.yaml"),
                "--contribution",
                str(EXAMPLE / "atlas-contribution.yaml"),
            ]
        )
        == 0
    )
    assert capsys.readouterr().err == ""
    assert _load("assembly.yaml")["status"] == "partial"


def test_semantic_failure_fixtures_are_shape_valid() -> None:
    for name in (
        "invalid-overlapping-assertions.yaml",
        "invalid-missing-carried-through-upstream.yaml",
    ):
        assert (
            validate_bundle_shape(
                SCHEMA, _load(name), "CorePopulationContribution"
            ).exit_code
            == 0
        )
