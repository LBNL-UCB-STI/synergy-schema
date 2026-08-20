"""Build-time Zensical macros backed by the executable documentation fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).parent
EVOLVING = ROOT / "examples" / "evolving_population"


def _load(relative_path: str) -> dict[str, Any]:
    document = yaml.safe_load((ROOT / relative_path).read_text())
    if not isinstance(document, dict):
        raise ValueError(f"Expected a mapping in {relative_path}")
    return document


def _table(rows: list[dict[str, object]], indent: int = 0) -> str:
    markdown = pd.DataFrame(rows).to_markdown(index=False)
    prefix = " " * indent
    return "\n".join(f"{prefix}{line}" for line in markdown.splitlines())


def _population_states() -> dict[object, Any]:
    return _load("examples/evolving_population/core-population-evolution.yaml")[
        "states"
    ]


def showcase_snapshot_summary_table(indent: int = 0) -> str:
    """Render record counts for every year in the core evidence fixture."""
    changes = {
        2025: "Starting snapshot",
        2030: "Household split, new person, and vehicle transfer",
        2035: "Identities persist and model-owned ages change",
    }
    rows = [
        {
            "Year": int(raw_year),
            "Household state records": len(state["households"]),
            "Person state records": len(state["persons"]),
            "Vehicle records": len(state["vehicles"]),
            "Event represented": changes[int(raw_year)],
        }
        for raw_year, state in _population_states().items()
    ]
    return _table(rows, indent)


def showcase_person_history_table(indent: int = 0) -> str:
    """Render one row for every person-year record in the fixture."""
    rows: list[dict[str, object]] = []
    for raw_year, state in _population_states().items():
        for person_id, person in state["persons"].items():
            rows.append(
                {
                    "Year": int(raw_year),
                    "Person": f"`{person_id}`",
                    "Longitudinal identity": (
                        f"`{person['core_state']['longitudinal_person_id']}`"
                    ),
                    "Age (model-owned)": person["model_owned"]["age"],
                    "Household membership": "Not declared in this fixture",
                }
            )
    return _table(rows, indent)


def showcase_household_lineage_table(indent: int = 0) -> str:
    """Render one row for every household-year lineage record."""
    rows: list[dict[str, object]] = []
    for raw_year, state in _population_states().items():
        for household_id, household in state["households"].items():
            relationships: list[str] = []
            if "predecessor" in household:
                relationships.append(f"predecessor `{household['predecessor']}`")
            if "successors" in household:
                successors = ", ".join(f"`{item}`" for item in household["successors"])
                relationships.append(f"successors {successors}")
            rows.append(
                {
                    "Year": int(raw_year),
                    "Household state": f"`{household_id}`",
                    "Declared lineage": "; ".join(relationships) or "None declared",
                }
            )
    return _table(rows, indent)


def showcase_vehicle_history_table(indent: int = 0) -> str:
    """Render one row for every vehicle-year assignment record."""
    rows: list[dict[str, object]] = []
    for raw_year, state in _population_states().items():
        for vehicle_id, vehicle in state["vehicles"].items():
            rows.append(
                {
                    "Year": int(raw_year),
                    "Vehicle": f"`{vehicle_id}`",
                    "Assigned household": f"`{vehicle['household_assignment']}`",
                }
            )
    return _table(rows, indent)


def showcase_scenario_assumptions_table(indent: int = 0) -> str:
    """Render every shared assumption in the ZEV scenario definition."""
    scenario = _load("examples/evolving_population/zev-scenario-definition.yaml")
    rows = [
        {
            "Shared assumption": f"`{assumption['assumption_key']}`",
            "Shared value": f"`{assumption['value']}`",
            "Value type": f"`{assumption['value_type']}`",
            "Authority": f"`{assumption['authority']}`",
        }
        for assumption in scenario["assumptions"]
    ]
    return _table(rows, indent)


def showcase_bindings_table(indent: int = 0) -> str:
    """Render every assumption binding in the ZEV model-binding fixture."""
    bindings = _load("examples/evolving_population/zev-model-bindings.yaml")["bindings"]
    rows: list[dict[str, object]] = []
    for binding in bindings:
        for assumption in binding["assumption_bindings"]:
            rows.append(
                {
                    "Model": binding["model_name"],
                    "Shared assumption": f"`{assumption['assumption_key']}`",
                    "Native element": f"`{assumption['native_element']['path']}`",
                    "Resolved native value": (
                        f"`{assumption['resolved_native_value']}`"
                        if "resolved_native_value" in assumption
                        else "Not declared"
                    ),
                    "Binding mode": f"`{assumption['binding_mode']}`",
                    "Compatibility": f"`{assumption['compatibility_state']}`",
                }
            )
    return _table(rows, indent)


def _digest_prefix(value: object) -> str:
    return f"`{str(value).zfill(64)[:12]}…`"


def showcase_broken_scenario_table(indent: int = 0) -> str:
    """Compare the valid and altered scenario declarations."""
    valid_scenario = _load("examples/evolving_population/zev-scenario-definition.yaml")
    broken_scenario = _load(
        "examples/evolving_population_broken_scenario/broken-scenario-definition.yaml"
    )
    rows = [
        {
            "Field": "Scenario assumptions",
            "Valid declaration": "`population_seed=synthetic-evolving`; `zev_policy=accelerated`",
            "Broken declaration": "Unchanged",
            "Checker interpretation": "The readable scenario body still looks plausible",
        },
        {
            "Field": "Scenario content digest",
            "Valid declaration": _digest_prefix(valid_scenario["content_digest"]),
            "Broken declaration": _digest_prefix(broken_scenario["content_digest"]),
            "Checker interpretation": "`SCENARIO_DIGEST_MISMATCH`",
        },
    ]
    return _table(rows, indent)


def showcase_broken_artifact_table(indent: int = 0) -> str:
    """Compare valid and altered implementation-artifact declarations."""
    valid_bundle = _load(
        "examples/evolving_population/zev-polaris-translation-bundle.yaml"
    )
    broken_bundle = _load(
        "examples/evolving_population_broken_artifact_identity/broken-polaris-bundle.yaml"
    )
    rows = [
        {
            "Field": "Implementation binding digest",
            "Valid declaration": _digest_prefix(
                valid_bundle["translation_implementation_binding"][
                    "implementation_content_digest"
                ]
            ),
            "Broken declaration": "Unchanged",
            "Checker interpretation": "The workflow still claims the original SQL identity",
        },
        {
            "Field": "Receipt's implementation artifact digest",
            "Valid declaration": _digest_prefix(
                valid_bundle["implementation_artifact"]["artifact_identity"][
                    "content_digest"
                ]
            ),
            "Broken declaration": _digest_prefix(
                broken_bundle["implementation_artifact"]["artifact_identity"][
                    "content_digest"
                ]
            ),
            "Checker interpretation": "`ARTIFACT_IDENTITY_MISMATCH`",
        },
    ]
    return _table(rows, indent)


def define_env(env: Any) -> None:
    """Register fixture-backed table macros with Zensical."""
    env.macro(showcase_snapshot_summary_table)
    env.macro(showcase_person_history_table)
    env.macro(showcase_household_lineage_table)
    env.macro(showcase_vehicle_history_table)
    env.macro(showcase_scenario_assumptions_table)
    env.macro(showcase_bindings_table)
    env.macro(showcase_broken_scenario_table)
    env.macro(showcase_broken_artifact_table)
