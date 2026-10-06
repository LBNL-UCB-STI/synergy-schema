"""End-to-end simulation pipeline runner for Synergy schema.

Executes the complete longitudinal simulation cycle:
    DEMOS CSVs + Prior Core Facets
        -> Derive Core Facets (classification, race inheritance, income deflation, spatial preservation)
        -> Refine Core Facets (dwelling D-H1, schooling X-P4..P6, employment D-P1..P2)
        -> Project to POLARIS Demand.sqlite (Household, Person, Vehicle)
        -> Emit Run Manifest with canonical digests (core_facet_table/v1, view_table/v1)
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from synergy_schema.conformance.tabular_digest import compute_tabular_digest
from synergy_schema.pipeline.derive import (
    CORE_FACET_COLUMNS,
    CORE_FACET_KEY_COLUMNS,
    derive_core_from_demos,
)
from synergy_schema.pipeline.polaris_projection import project_core_to_polaris
from synergy_schema.pipeline.refine import refine_core_facets


def run_simulation_pipeline(
    demos_households: Path | str | pa.Table | duckdb.DuckDBPyRelation,
    demos_persons: Path | str | pa.Table | duckdb.DuckDBPyRelation,
    prior_core_facets: (
        Mapping[str, Path | str | pa.Table | duckdb.DuckDBPyRelation]
        | Path
        | str
        | None
    ) = None,
    vehicles: Path | str | pa.Table | duckdb.DuckDBPyRelation | None = None,
    output_dir: Path | str = "output/simulation_run",
    seed_prefix: str = "seed-austin-2026",
    income_deflator: float = 1.0,
    duckdb_con: duckdb.DuckDBPyConnection | None = None,
) -> dict[str, Any]:
    """Execute the end-to-end Derive -> Refine -> Project simulation pipeline.

    Args:
        demos_households: DEMOS households dataset (CSV path, Parquet path, Table, or Relation).
        demos_persons: DEMOS persons dataset (CSV path, Parquet path, Table, or Relation).
        prior_core_facets: Mapping of prior facet names to sources, or path to directory of .parquet files.
        vehicles: Optional vehicles dataset (e.g. from ATLAS fleet model). Defaults to empty table if omitted.
        output_dir: Directory where core facets, Demand.sqlite, and run_manifest.json will be saved.
        seed_prefix: Prefix used for deterministic pseudo-random draws.
        income_deflator: Deflator applied to nominal household income (default: 1.0).
        duckdb_con: Optional existing DuckDB connection.

    Returns:
        Dictionary containing run manifest, facet digests, view digests, and file paths.
    """
    out_dir = Path(output_dir)
    facets_dir = out_dir / "core_facets"
    facets_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb_con or duckdb.connect()

    # 1. Resolve prior core facets if provided as directory path
    resolved_prior: dict[str, Any] = {}
    if isinstance(prior_core_facets, (str, Path)):
        prior_path = Path(prior_core_facets)
        if prior_path.is_dir():
            for facet_name in CORE_FACET_COLUMNS:
                candidate = prior_path / f"{facet_name}.parquet"
                if candidate.exists():
                    resolved_prior[facet_name] = candidate
    elif isinstance(prior_core_facets, Mapping):
        resolved_prior = dict(prior_core_facets)

    # 2. Stage 3.2: Derive Core base facets from DEMOS
    derive_results = derive_core_from_demos(
        demos_households=demos_households,
        demos_persons=demos_persons,
        prior_core_facets=resolved_prior if resolved_prior else None,
        income_deflator=income_deflator,
        output_dir=facets_dir,
        duckdb_con=con,
    )
    derived_facets = derive_results["facets"]
    derived_digests = derive_results["digests"]

    # 3. Stage 3.3: Stochastic Refinements (dwelling, schooling, employment)
    refine_results = refine_core_facets(
        households=derived_facets["households"],
        people=derived_facets["people"],
        demos_persons=demos_persons,
        prior_core_facets=resolved_prior if resolved_prior else None,
        output_dir=facets_dir,
        seed_prefix=seed_prefix,
        duckdb_con=con,
    )
    refined_facets = refine_results["facets"]
    refined_digests = refine_results["digests"]

    # 4. Handle vehicles facet
    vehicles_path = facets_dir / "vehicles.parquet"
    if vehicles is not None:
        if isinstance(vehicles, (str, Path)):
            v_p = Path(vehicles)
            if v_p.suffix == ".parquet":
                vehicles_table = pq.read_table(v_p)
            else:
                vehicles_table = con.execute(
                    f"SELECT * FROM read_csv_auto('{v_p.as_posix()}');"
                ).to_arrow_table()
        elif isinstance(vehicles, pa.Table):
            vehicles_table = vehicles
        else:
            vehicles_table = vehicles.to_arrow_table()
        pq.write_table(vehicles_table, vehicles_path)
    elif "vehicles" in resolved_prior:
        v_prior = resolved_prior["vehicles"]
        if isinstance(v_prior, (str, Path)):
            vehicles_table = pq.read_table(Path(v_prior))
        elif isinstance(v_prior, pa.Table):
            vehicles_table = v_prior
        else:
            vehicles_table = v_prior.to_arrow_table()
        pq.write_table(vehicles_table, vehicles_path)
    else:
        # Create empty vehicles table
        vehicles_table = pa.table(
            {
                "vehicle_id": pa.array([], type=pa.int64()),
                "household_id": pa.array([], type=pa.int64()),
                "type_id": pa.array([], type=pa.int32()),
            }
        )
        pq.write_table(vehicles_table, vehicles_path)

    vehicles_digest = compute_tabular_digest(
        source=vehicles_table,
        columns=CORE_FACET_COLUMNS["vehicles"],
        key_columns=CORE_FACET_KEY_COLUMNS["vehicles"],
        profile="core_facet_table/v1",
    )

    # 5. Assemble all 10 core facets
    all_facets: dict[str, Any] = {
        **derived_facets,
        **refined_facets,
        "vehicles": vehicles_table,
    }
    all_core_digests = {
        **derived_digests,
        **refined_digests,
        "vehicles": vehicles_digest,
    }

    # 6. Stage 3.1 & 3.4: Project Core into POLARIS Demand.sqlite
    polaris_sqlite_path = out_dir / "Demand.sqlite"
    proj_results = project_core_to_polaris(
        core_facets=all_facets,
        output_sqlite_path=polaris_sqlite_path,
        duckdb_con=con,
    )

    # 7. Build and write run execution manifest
    row_counts = {
        **{facet: len(tbl) for facet, tbl in all_facets.items()},
        **proj_results["row_counts"],
    }
    manifest = {
        "pipeline_version": "synergy-pipeline/v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seed_prefix": seed_prefix,
        "income_deflator": income_deflator,
        "classification": derive_results["classification"],
        "core_facet_digests": all_core_digests,
        "view_table_digests": proj_results["digests"],
        "row_counts": row_counts,
        "artifacts": {
            "core_facets_dir": facets_dir.as_posix(),
            "polaris_database": polaris_sqlite_path.as_posix(),
        },
    }

    manifest_path = out_dir / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    return {
        "manifest": manifest,
        "manifest_path": manifest_path,
        "facets": all_facets,
        "core_facet_digests": all_core_digests,
        "polaris_database_path": polaris_sqlite_path,
        "view_table_digests": proj_results["digests"],
        "row_counts": row_counts,
    }


def main() -> None:
    """CLI entry point for simulation pipeline run."""
    parser = argparse.ArgumentParser(
        description="Run end-to-end Synergy simulation pipeline."
    )
    parser.add_argument(
        "--demos-households",
        required=True,
        help="Path to DEMOS households CSV/Parquet.",
    )
    parser.add_argument(
        "--demos-persons", required=True, help="Path to DEMOS persons CSV/Parquet."
    )
    parser.add_argument(
        "--prior-core-dir",
        default=None,
        help="Path to directory containing prior core facet Parquet files.",
    )
    parser.add_argument(
        "--vehicles",
        default=None,
        help="Path to vehicles CSV/Parquet (optional, e.g. from ATLAS).",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for generated core facets and Demand.sqlite.",
    )
    parser.add_argument(
        "--seed-prefix",
        default="seed-austin-run",
        help="Prefix string for deterministic pseudo-random seeds.",
    )
    parser.add_argument(
        "--income-deflator",
        type=float,
        default=1.0,
        help="Deflator multiplier for nominal household income.",
    )

    args = parser.parse_args()

    results = run_simulation_pipeline(
        demos_households=args.demos_households,
        demos_persons=args.demos_persons,
        prior_core_facets=args.prior_core_dir,
        vehicles=args.vehicles,
        output_dir=args.output_dir,
        seed_prefix=args.seed_prefix,
        income_deflator=args.income_deflator,
    )

    print(
        f"Pipeline run completed successfully. Manifest written to: {results['manifest_path']}"
    )
    print(f"Demand.sqlite written to: {results['polaris_database_path']}")
    print("Table row counts:")
    for name, count in results["row_counts"].items():
        print(f"  {name}: {count}")


if __name__ == "__main__":
    main()
