"""Consist-instrumented simulation pipeline runner for Synergy schema (Stage 3 Task 3.5).

Wraps the discrete Derive, Refine (dwelling, schooling, employment), and Projection steps
using Consist `tracker.run(...)`, providing:
  - Granular facet-level cache detection
  - Skip-on-hit behavior for expensive DuckDB execution
  - Authentic execution provenance and run IDs logged to provenance.duckdb
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

try:
    import consist
    from consist import ExecutionOptions, Tracker

    HAS_CONSIST = True
except ImportError:  # pragma: no cover
    HAS_CONSIST = False
    consist = None  # type: ignore[assignment]
    ExecutionOptions = None  # type: ignore[assignment,misc]
    Tracker = None  # type: ignore[assignment,misc]

from synergy_schema.conformance.tabular_digest import compute_tabular_digest
from synergy_schema.pipeline.derive import (
    CORE_FACET_COLUMNS,
    CORE_FACET_KEY_COLUMNS,
    derive_core_from_demos,
)
from synergy_schema.pipeline.polaris_projection import (
    POLARIS_DEMAND_COLUMNS,
    POLARIS_DEMAND_KEY_COLUMNS,
    project_core_to_polaris,
)
from synergy_schema.pipeline.refine import (
    refine_household_dwelling,
    refine_person_employment,
    refine_person_schooling,
)


def _step_derive(
    demos_households_path: Path,
    demos_persons_path: Path,
    prior_households_path: Path | None = None,
    prior_people_path: Path | None = None,
    prior_person_demographics_path: Path | None = None,
    prior_household_location_path: Path | None = None,
    prior_household_membership_path: Path | None = None,
    prior_household_income_path: Path | None = None,
    income_deflator: float = 1.0,
    output_dir: Path | str | None = None,
) -> dict[str, Path]:
    """Execute Step 1-3, 7, 12 base derivation in DuckDB and persist core facet files."""
    assert output_dir is not None
    out_d = Path(output_dir)
    prior_facets: dict[str, Path] = {}
    prior_path_map = {
        "households": prior_households_path,
        "people": prior_people_path,
        "person_demographics": prior_person_demographics_path,
        "household_location": prior_household_location_path,
        "household_membership": prior_household_membership_path,
        "household_income": prior_household_income_path,
    }
    for facet_name, facet_path in prior_path_map.items():
        if facet_path and Path(facet_path).exists():
            prior_facets[facet_name] = Path(facet_path)

    con = duckdb.connect()
    derive_core_from_demos(
        demos_households=demos_households_path,
        demos_persons=demos_persons_path,
        prior_core_facets=prior_facets if prior_facets else None,
        income_deflator=income_deflator,
        output_dir=out_d,
        duckdb_con=con,
    )

    return {
        "households": out_d / "households.parquet",
        "people": out_d / "people.parquet",
        "household_membership": out_d / "household_membership.parquet",
        "household_location": out_d / "household_location.parquet",
        "person_demographics": out_d / "person_demographics.parquet",
        "household_income": out_d / "household_income.parquet",
    }


def _step_refine_dwelling(
    households_path: Path,
    prior_dwelling_path: Path | None = None,
    seed_prefix: str = "seed-dwelling",
    output_path: Path | str | None = None,
) -> dict[str, Path]:
    """Refine dwelling units (D-H1 and time_in_home carry-forward)."""
    assert output_path is not None
    out_p = Path(output_path)
    hh_table = pq.read_table(households_path)
    prior_dwelling = (
        pq.read_table(prior_dwelling_path)
        if (prior_dwelling_path and Path(prior_dwelling_path).exists())
        else None
    )

    con = duckdb.connect()
    refine_household_dwelling(
        households=hh_table,
        prior_dwelling=prior_dwelling,
        seed=f"{seed_prefix}-dwelling",
        output_path=out_p,
        duckdb_con=con,
    )
    return {"household_dwelling": out_p}


def _step_refine_schooling(
    people_path: Path,
    demos_persons_path: Path,
    prior_schooling_path: Path | None = None,
    seed_prefix: str = "seed-schooling",
    output_path: Path | str | None = None,
) -> dict[str, Path]:
    """Refine schooling progression and entry grades (X-P4..X-P6)."""
    assert output_path is not None
    out_p = Path(output_path)
    people_table = pq.read_table(people_path)
    prior_schooling = (
        pq.read_table(prior_schooling_path)
        if (prior_schooling_path and Path(prior_schooling_path).exists())
        else None
    )

    con = duckdb.connect()
    refine_person_schooling(
        people=people_table,
        demos_persons=demos_persons_path,
        prior_schooling=prior_schooling,
        seed=f"{seed_prefix}-schooling",
        output_path=out_p,
        duckdb_con=con,
    )
    return {"person_schooling": out_p}


def _step_refine_employment(
    people_path: Path,
    demos_persons_path: Path,
    prior_employment_path: Path | None = None,
    seed_prefix: str = "seed-employment",
    output_path: Path | str | None = None,
) -> dict[str, Path]:
    """Refine employment status, industry, and commute mode (D-P1, D-P2)."""
    assert output_path is not None
    out_p = Path(output_path)
    people_table = pq.read_table(people_path)
    prior_employment = (
        pq.read_table(prior_employment_path)
        if (prior_employment_path and Path(prior_employment_path).exists())
        else None
    )

    con = duckdb.connect()
    refine_person_employment(
        people=people_table,
        demos_persons=demos_persons_path,
        prior_employment=prior_employment,
        seed=f"{seed_prefix}-employment",
        output_path=out_p,
        duckdb_con=con,
    )
    return {"person_employment": out_p}


def _step_project_polaris(
    households_path: Path,
    people_path: Path,
    household_membership_path: Path,
    person_demographics_path: Path,
    household_location_path: Path,
    household_income_path: Path,
    household_dwelling_path: Path,
    person_schooling_path: Path,
    person_employment_path: Path,
    vehicles_path: Path,
    output_sqlite_path: Path | str | None = None,
) -> dict[str, Path]:
    """Project all 10 core facets into POLARIS Demand.sqlite."""
    assert output_sqlite_path is not None
    out_sqlite = Path(output_sqlite_path)
    core_facets = {
        "households": pq.read_table(households_path),
        "people": pq.read_table(people_path),
        "household_membership": pq.read_table(household_membership_path),
        "person_demographics": pq.read_table(person_demographics_path),
        "household_location": pq.read_table(household_location_path),
        "household_income": pq.read_table(household_income_path),
        "household_dwelling": pq.read_table(household_dwelling_path),
        "person_schooling": pq.read_table(person_schooling_path),
        "person_employment": pq.read_table(person_employment_path),
        "vehicles": pq.read_table(vehicles_path),
    }

    con = duckdb.connect()
    project_core_to_polaris(
        core_facets=core_facets,
        output_sqlite_path=out_sqlite,
        duckdb_con=con,
    )
    return {"demand_sqlite": out_sqlite}


def run_simulation_with_consist(
    demos_households_path: Path | str,
    demos_persons_path: Path | str,
    output_dir: Path | str,
    prior_core_dir: Path | str | None = None,
    vehicles_path: Path | str | None = None,
    seed_prefix: str = "seed-austin-2026",
    income_deflator: float = 1.0,
    tracker: Tracker | None = None,
) -> dict[str, Any]:
    """Run simulation pipeline instrumented with Consist for cache-awareness and provenance.

    Args:
        demos_households_path: Path to DEMOS households CSV/Parquet.
        demos_persons_path: Path to DEMOS persons CSV/Parquet.
        output_dir: Destination directory for artifacts and runs.
        prior_core_dir: Directory containing prior core facets, if available.
        vehicles_path: Path to vehicles dataset, if available.
        seed_prefix: Seed prefix for stochastic modeling steps.
        income_deflator: Nominal income deflation multiplier.
        tracker: Optional Consist Tracker instance.

    Returns:
        Dictionary with run results (cache hits, run IDs), file paths, and manifest.
    """
    if not HAS_CONSIST:
        raise RuntimeError(
            "Consist is not installed. Install with `uv sync --extra consist` to use consist runner."
        )

    out_p = Path(output_dir)
    facets_dir = out_p / "core_facets"
    facets_dir.mkdir(parents=True, exist_ok=True)

    if tracker is None:
        tracker = Tracker(
            run_dir=out_p / "consist_runs",
            db_path=out_p / "provenance.duckdb",
        )

    dh_p = Path(demos_households_path)
    dp_p = Path(demos_persons_path)
    prior_p = Path(prior_core_dir) if prior_core_dir else None

    run_results: dict[str, Any] = {}

    with consist.use_tracker(tracker):
        # Step 1: Base Derivation
        derive_inputs: dict[str, Path] = {
            "demos_households_path": dh_p,
            "demos_persons_path": dp_p,
        }
        if prior_p:
            for facet_name in (
                "households",
                "people",
                "person_demographics",
                "household_location",
                "household_membership",
                "household_income",
            ):
                candidate = prior_p / f"{facet_name}.parquet"
                if candidate.exists():
                    derive_inputs[f"prior_{facet_name}_path"] = candidate

        r_derive = tracker.run(
            fn=_step_derive,
            inputs=derive_inputs,
            config={
                "income_deflator": income_deflator,
                "output_dir": facets_dir.as_posix(),
            },
            outputs=[
                "households",
                "people",
                "household_membership",
                "household_location",
                "person_demographics",
                "household_income",
            ],
            execution_options=ExecutionOptions(input_binding="paths"),
        )
        run_results["derive"] = r_derive

        # Step 2: Dwelling Refinement
        dwelling_inputs: dict[str, Any] = {
            "households_path": r_derive.outputs["households"]
        }
        if prior_p and (prior_p / "household_dwelling.parquet").exists():
            dwelling_inputs["prior_dwelling_path"] = (
                prior_p / "household_dwelling.parquet"
            )

        r_dwelling = tracker.run(
            fn=_step_refine_dwelling,
            inputs=dwelling_inputs,
            config={
                "seed_prefix": seed_prefix,
                "output_path": (facets_dir / "household_dwelling.parquet").as_posix(),
            },
            outputs=["household_dwelling"],
            execution_options=ExecutionOptions(input_binding="paths"),
        )
        run_results["refine_dwelling"] = r_dwelling

        # Step 3: Schooling Refinement
        schooling_inputs: dict[str, Any] = {
            "people_path": r_derive.outputs["people"],
            "demos_persons_path": dp_p,
        }
        if prior_p and (prior_p / "person_schooling.parquet").exists():
            schooling_inputs["prior_schooling_path"] = (
                prior_p / "person_schooling.parquet"
            )

        r_schooling = tracker.run(
            fn=_step_refine_schooling,
            inputs=schooling_inputs,
            config={
                "seed_prefix": seed_prefix,
                "output_path": (facets_dir / "person_schooling.parquet").as_posix(),
            },
            outputs=["person_schooling"],
            execution_options=ExecutionOptions(input_binding="paths"),
        )
        run_results["refine_schooling"] = r_schooling

        # Step 4: Employment Refinement
        employment_inputs: dict[str, Any] = {
            "people_path": r_derive.outputs["people"],
            "demos_persons_path": dp_p,
        }
        if prior_p and (prior_p / "person_employment.parquet").exists():
            employment_inputs["prior_employment_path"] = (
                prior_p / "person_employment.parquet"
            )

        r_employment = tracker.run(
            fn=_step_refine_employment,
            inputs=employment_inputs,
            config={
                "seed_prefix": seed_prefix,
                "output_path": (facets_dir / "person_employment.parquet").as_posix(),
            },
            outputs=["person_employment"],
            execution_options=ExecutionOptions(input_binding="paths"),
        )
        run_results["refine_employment"] = r_employment

        # Handle vehicles table
        v_out_path = facets_dir / "vehicles.parquet"
        if vehicles_path and Path(vehicles_path).exists():
            v_tbl = pq.read_table(Path(vehicles_path))
            pq.write_table(v_tbl, v_out_path)
        elif prior_p and (prior_p / "vehicles.parquet").exists():
            v_tbl = pq.read_table(prior_p / "vehicles.parquet")
            pq.write_table(v_tbl, v_out_path)
        elif not v_out_path.exists():
            v_tbl = pa.table(
                {
                    "vehicle_id": pa.array([], type=pa.int64()),
                    "household_id": pa.array([], type=pa.int64()),
                    "type_id": pa.array([], type=pa.int32()),
                }
            )
            pq.write_table(v_tbl, v_out_path)

        # Step 5: POLARIS Demand Projection
        proj_sqlite = out_p / "Demand.sqlite"
        proj_inputs: dict[str, Any] = {
            "households_path": r_derive.outputs["households"],
            "people_path": r_derive.outputs["people"],
            "household_membership_path": r_derive.outputs["household_membership"],
            "person_demographics_path": r_derive.outputs["person_demographics"],
            "household_location_path": r_derive.outputs["household_location"],
            "household_income_path": r_derive.outputs["household_income"],
            "household_dwelling_path": r_dwelling.outputs["household_dwelling"],
            "person_schooling_path": r_schooling.outputs["person_schooling"],
            "person_employment_path": r_employment.outputs["person_employment"],
            "vehicles_path": v_out_path,
        }
        r_project = tracker.run(
            fn=_step_project_polaris,
            inputs=proj_inputs,
            config={"output_sqlite_path": proj_sqlite.as_posix()},
            outputs=["demand_sqlite"],
            execution_options=ExecutionOptions(input_binding="paths"),
        )
        run_results["project_polaris"] = r_project

    # Compute tabular content digests
    core_facet_digests: dict[str, str] = {}
    for facet, cols in CORE_FACET_COLUMNS.items():
        core_facet_digests[facet] = compute_tabular_digest(
            source=facets_dir / f"{facet}.parquet",
            columns=cols,
            key_columns=CORE_FACET_KEY_COLUMNS[facet],
            profile="core_facet_table/v1",
        )

    view_digests: dict[str, str] = {}
    for view_table in ["Household", "Person", "Vehicle"]:
        view_digests[view_table] = compute_tabular_digest(
            source=proj_sqlite,
            columns=POLARIS_DEMAND_COLUMNS[view_table],
            key_columns=POLARIS_DEMAND_KEY_COLUMNS[view_table],
            profile="view_table/v1",
            sqlite_table=view_table,
        )

    producing_runs = {
        name: r.run.id if hasattr(r, "run") and r.run else None
        for name, r in run_results.items()
    }
    cache_hits = {
        name: r.cache_hit if hasattr(r, "cache_hit") else False
        for name, r in run_results.items()
    }

    manifest = {
        "pipeline_version": "synergy-pipeline/v1",
        "consist_instrumented": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seed_prefix": seed_prefix,
        "income_deflator": income_deflator,
        "producing_runs": producing_runs,
        "cache_hits": cache_hits,
        "core_facet_digests": core_facet_digests,
        "view_table_digests": view_digests,
        "provenance_database": (out_p / "provenance.duckdb").as_posix(),
    }

    manifest_path = out_p / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    return {
        "manifest": manifest,
        "manifest_path": manifest_path,
        "run_results": run_results,
        "producing_runs": producing_runs,
        "cache_hits": cache_hits,
        "core_facet_digests": core_facet_digests,
        "view_table_digests": view_digests,
        "polaris_database_path": proj_sqlite,
    }
