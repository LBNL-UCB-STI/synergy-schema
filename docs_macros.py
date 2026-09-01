"""Build-time Zensical macros backed by the executable documentation fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).parent
EVOLVING = ROOT / "examples" / "evolving_population"
YEARS = (2025, 2030, 2035)


def _load(relative_path: str) -> dict[str, Any]:
    document = yaml.safe_load((ROOT / relative_path).read_text())
    if not isinstance(document, dict):
        raise ValueError(f"Expected a mapping in {relative_path}")
    return document


def _table(rows: list[dict[str, object]], indent: int = 0) -> str:
    markdown = pd.DataFrame(rows).to_markdown(index=False)
    prefix = " " * indent
    return "\n".join(f"{prefix}{line}" for line in markdown.splitlines())


def _core_view() -> dict[str, Any]:
    core = _load("examples/evolving_population/core-population-evolution.yaml")
    snapshots = {item["id"]: item for item in core["population_snapshots"]}
    memberships = {
        item["person_state_ref"]: item for item in core["household_memberships"]
    }
    assignments = {
        item["vehicle_state_ref"]: item
        for item in core["household_vehicle_assignments"]
    }
    ages: dict[tuple[int, str], object] = {}
    for year in YEARS:
        evidence = _load(
            f"examples/evolving_population/evidence/atlas-{year}-persons.yaml"
        )
        ages.update({(year, row["person_id"]): row["age"] for row in evidence["rows"]})
    by_year = {
        year: {"households": [], "persons": [], "vehicles": []} for year in YEARS
    }
    for item in core["household_states"]:
        by_year[snapshots[item["population_snapshot_ref"]]["simulation_year"]][
            "households"
        ].append(item)
    for item in core["person_states"]:
        year = snapshots[item["population_snapshot_ref"]]["simulation_year"]
        person_id = item["longitudinal_person_ref"].rsplit(":", 1)[-1]
        by_year[year]["persons"].append(
            {
                **item,
                "membership": memberships[item["person_state_id"]],
                "age": ages[(year, person_id)],
            }
        )
    for item in core["vehicle_states"]:
        year = snapshots[item["population_snapshot_ref"]]["simulation_year"]
        by_year[year]["vehicles"].append(
            {**item, "assignment": assignments[item["vehicle_state_id"]]}
        )
    return {"core": core, "snapshots": snapshots, "by_year": by_year}


def showcase_snapshot_summary_table(indent: int = 0) -> str:
    """Render record counts for every year in the core evidence fixture."""
    view = _core_view()
    rows = [
        {
            "Year": year,
            "Household state records": len(view["by_year"][year]["households"]),
            "Person state records": len(view["by_year"][year]["persons"]),
            "Vehicle records": len(view["by_year"][year]["vehicles"]),
            "Event represented": f"{len(view['by_year'][year]['households'])} household states; {len(view['by_year'][year]['persons'])} person states; {len(view['by_year'][year]['vehicles'])} vehicle states",
        }
        for year in YEARS
    ]
    return _table(rows, indent)


def showcase_person_history_table(indent: int = 0) -> str:
    """Render one row for every person-year record in the fixture."""
    view = _core_view()
    rows = []
    for year in YEARS:
        for person in view["by_year"][year]["persons"]:
            rows.append(
                {
                    "Year": year,
                    "Person": f"`{person['longitudinal_person_ref']}`",
                    "Longitudinal identity": f"`{person['longitudinal_person_ref']}`",
                    "Age (model-owned)": person["age"],
                    "Household membership": f"`{person['membership']['household_state_ref']}`",
                }
            )
    return _table(rows, indent)


def showcase_household_lineage_table(indent: int = 0) -> str:
    """Render one row for every household-year lineage record."""
    view = _core_view()
    rows = []
    for year in YEARS:
        for household in view["by_year"][year]["households"]:
            predecessors = household.get("predecessor_state_refs", [])
            rows.append(
                {
                    "Year": year,
                    "Household state": f"`{household['household_state_id']}`",
                    "Longitudinal identity": f"`{household['longitudinal_household_ref']}`",
                    "Predecessor states": ", ".join(
                        f"`{value}`" for value in predecessors
                    )
                    or "None",
                }
            )
    return _table(rows, indent)


def showcase_vehicle_history_table(indent: int = 0) -> str:
    """Render one row for every vehicle-year assignment record."""
    view = _core_view()
    rows = []
    for year in YEARS:
        for vehicle in view["by_year"][year]["vehicles"]:
            rows.append(
                {
                    "Year": year,
                    "Vehicle": f"`{vehicle['longitudinal_vehicle_ref']}`",
                    "Assigned household": f"`{vehicle['assignment']['household_state_ref']}`",
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
    rows = []
    for binding in bindings:
        for assumption in binding["assumption_bindings"]:
            rows.append(
                {
                    "Model": binding["model_name"],
                    "Shared assumption": f"`{assumption['assumption_key']}`",
                    "Native element": f"`{assumption['native_element']['path']}`",
                    "Resolved native value": f"`{assumption['resolved_native_value']}`"
                    if "resolved_native_value" in assumption
                    else "Not declared",
                    "Binding mode": f"`{assumption['binding_mode']}`",
                    "Compatibility": f"`{assumption['compatibility_state']}`",
                }
            )
    return _table(rows, indent)


def showcase_population_timeline_table(indent: int = 0) -> str:
    """Render household lineage, person membership, and vehicle assignment."""
    view = _core_view()
    rows = []
    for year in YEARS:
        for household in view["by_year"][year]["households"]:
            rows.append(
                {
                    "Year": year,
                    "Record": household["household_state_id"],
                    "Relationship": ", ".join(
                        household.get("predecessor_state_refs", [])
                    )
                    or "root household state",
                }
            )
        for person in view["by_year"][year]["persons"]:
            rows.append(
                {
                    "Year": year,
                    "Record": person["longitudinal_person_ref"],
                    "Relationship": f"member of {person['membership']['household_state_ref']}",
                }
            )
        for vehicle in view["by_year"][year]["vehicles"]:
            rows.append(
                {
                    "Year": year,
                    "Record": vehicle["longitudinal_vehicle_ref"],
                    "Relationship": f"assigned to {vehicle['assignment']['household_state_ref']}",
                }
            )
    return _table(rows, indent)


def _branch_bundle(branch: str, kind: str) -> dict[str, Any]:
    return _load(f"examples/evolving_population/{branch}-{kind}-bundle.yaml")


def showcase_branch_comparison_table(indent: int = 0) -> str:
    """Compare shared vehicle identity with native branch-owned vehicle type."""
    shared_vehicle = next(
        item["longitudinal_vehicle_ref"]
        for item in _core_view()["core"]["vehicle_states"]
        if item["population_snapshot_ref"].endswith("2025")
    )
    rows = []
    for branch in ("baseline", "zev"):
        receipt = _branch_bundle(branch, "polaris-translation")
        role = next(
            item
            for item in receipt["members"]
            if item["simulation_year"] == 2025
            and item["semantic_role"] == "vehicle_type"
        )
        native = _load(str(EVOLVING / role["artifact"]["locator"]))
        rows.append(
            {
                "Branch": branch,
                "Shared vehicle": shared_vehicle,
                "Native vehicle type": native["rows"][0]["vehicle_type"],
                "Receipt mode": receipt["receipt_generation_mode"],
            }
        )
    return _table(rows, indent)


def showcase_evidence_trace_table(indent: int = 0) -> str:
    """Render one fixture-backed assumption-to-evidence chain."""
    scenario = _load("examples/evolving_population/zev-scenario-definition.yaml")
    binding = next(
        item
        for item in _load("examples/evolving_population/zev-model-bindings.yaml")[
            "bindings"
        ]
        if item["model_name"] == "POLARIS"
    )
    assumption = next(
        item
        for item in scenario["assumptions"]
        if item["assumption_key"] == "zev_policy"
    )
    bound_assumption = next(
        item
        for item in binding["assumption_bindings"]
        if item["assumption_key"] == assumption["assumption_key"]
    )
    contract = _load(
        "examples/evolving_population/mapping-release/revision-1/contract/population-translation-contract.yaml"
    )
    implementation = _load(
        "examples/evolving_population/mapping-release/revision-1/implementation/pilates-translation.yaml"
    )
    receipt = _load("examples/evolving_population/zev-polaris-translation-bundle.yaml")
    member = next(
        item
        for item in receipt["members"]
        if item["simulation_year"] == 2025 and item["semantic_role"] == "vehicle_type"
    )
    rows = [
        {
            "Step": "Shared assumption",
            "Value": f"{assumption['assumption_key']}={assumption['value']}",
        },
        {"Step": "Model binding", "Value": bound_assumption["native_element"]["path"]},
        {"Step": "Mapping release", "Value": contract["revision"]},
        {
            "Step": "Review records",
            "Value": str(len(contract["governance"]["review_records"])),
        },
        {
            "Step": "Implementation identity",
            "Value": implementation["implementation_content_digest"],
        },
        {"Step": "Receipt member", "Value": member["semantic_role"]},
        {"Step": "Exact evidence", "Value": member["artifact"]["locator"]},
    ]
    return _table(rows, indent)


def showcase_status_ladder_table(indent: int = 0) -> str:
    """Render fixture-derived draft-proof boundaries and non-claims."""
    core = _load("examples/evolving_population/core-population-evolution.yaml")
    trajectory = _load(
        "examples/evolving_population/zev-pilates-trajectory-bundle.yaml"
    )
    receipt = _load("examples/evolving_population/zev-polaris-translation-bundle.yaml")
    binding = next(
        item
        for item in _load("examples/evolving_population/zev-model-bindings.yaml")[
            "bindings"
        ]
        if item["model_name"] == "POLARIS"
    )
    contract = _load(
        "examples/evolving_population/mapping-release/revision-1/contract/population-translation-contract.yaml"
    )
    rows = [
        {
            "Level": "1",
            "Boundary": "Schema-valid structure",
            "Status": f"{len(core)} collections",
            "Evidence": ", ".join(core),
        },
        {
            "Level": "2",
            "Boundary": "Cross-document checker boundary",
            "Status": f"{trajectory['completeness_status']} / {receipt['completeness_status']}",
            "Evidence": ", ".join(
                str(year)
                for year in trajectory["population_trajectory"]["requested_years"]
            ),
        },
        {
            "Level": "3",
            "Boundary": "Draft mapping review",
            "Status": contract["governance"]["lifecycle_status"],
            "Evidence": f"{contract['revision']}; review_records={len(contract['governance']['review_records'])}",
        },
        {
            "Level": "4",
            "Boundary": "Compatibility gap",
            "Status": binding["assumption_bindings"][0]["compatibility_state"],
            "Evidence": binding["assumption_bindings"][0]["binding_mode"],
        },
        {
            "Level": "5",
            "Boundary": "Production evidence not claimed",
            "Status": receipt["receipt_generation_mode"],
            "Evidence": f"{contract['governance']['lifecycle_status']} mapping",
        },
    ]
    return _table(rows, indent)


def _digest_prefix(value: object) -> str:
    return f"`{str(value).zfill(64)[:12]}…`"


def showcase_broken_scenario_table(indent: int = 0) -> str:
    """Compare the valid and altered scenario declarations."""
    valid = _load("examples/evolving_population/zev-scenario-definition.yaml")
    broken = _load(
        "examples/evolving_population_broken_scenario/broken-scenario-definition.yaml"
    )
    valid_body = "; ".join(
        f"{item['assumption_key']}={item['value']}" for item in valid["assumptions"]
    )
    broken_body = "; ".join(
        f"{item['assumption_key']}={item['value']}" for item in broken["assumptions"]
    )
    return _table(
        [
            {
                "Field": "Scenario assumptions",
                "Valid declaration": f"`{valid_body}`",
                "Broken declaration": f"`{broken_body}`",
                "Checker interpretation": "readable declarations",
            },
            {
                "Field": "Scenario content digest",
                "Valid declaration": _digest_prefix(valid["content_digest"]),
                "Broken declaration": _digest_prefix(broken["content_digest"]),
                "Checker interpretation": "`SCENARIO_DIGEST_MISMATCH`"
                if valid["content_digest"] != broken["content_digest"]
                else "match",
            },
        ],
        indent,
    )


def showcase_broken_artifact_table(indent: int = 0) -> str:
    """Compare valid and altered implementation-artifact declarations."""
    valid = _load("examples/evolving_population/zev-polaris-translation-bundle.yaml")
    broken = _load(
        "examples/evolving_population_broken_artifact_identity/broken-polaris-bundle.yaml"
    )
    return _table(
        [
            {
                "Field": "Implementation binding digest",
                "Valid declaration": _digest_prefix(
                    valid["translation_implementation_binding"][
                        "implementation_content_digest"
                    ]
                ),
                "Broken declaration": _digest_prefix(
                    broken["translation_implementation_binding"][
                        "implementation_content_digest"
                    ]
                ),
                "Checker interpretation": "binding remains unchanged",
            },
            {
                "Field": "Receipt's implementation artifact digest",
                "Valid declaration": _digest_prefix(
                    valid["implementation_artifact"]["artifact_identity"][
                        "content_digest"
                    ]
                ),
                "Broken declaration": _digest_prefix(
                    broken["implementation_artifact"]["artifact_identity"][
                        "content_digest"
                    ]
                ),
                "Checker interpretation": "`ARTIFACT_IDENTITY_MISMATCH`"
                if valid["implementation_artifact"]["artifact_identity"][
                    "content_digest"
                ]
                != broken["implementation_artifact"]["artifact_identity"][
                    "content_digest"
                ]
                else "match",
            },
        ],
        indent,
    )


def define_env(env: Any) -> None:
    """Register fixture-backed table macros with Zensical."""
    for macro in (
        showcase_snapshot_summary_table,
        showcase_person_history_table,
        showcase_household_lineage_table,
        showcase_vehicle_history_table,
        showcase_scenario_assumptions_table,
        showcase_bindings_table,
        showcase_population_timeline_table,
        showcase_branch_comparison_table,
        showcase_evidence_trace_table,
        showcase_status_ladder_table,
        showcase_broken_scenario_table,
        showcase_broken_artifact_table,
    ):
        env.macro(macro)
