"""Tests for the end-to-end simulation pipeline runner (Stage 3 Task 3.4)."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pyarrow as pa
import pytest

from synergy_schema.conformance.tabular_digest import compute_tabular_digest
from synergy_schema.pipeline.derive import (
    CORE_FACET_COLUMNS,
    CORE_FACET_KEY_COLUMNS,
)
from synergy_schema.pipeline.polaris_projection import (
    POLARIS_DEMAND_COLUMNS,
    POLARIS_DEMAND_KEY_COLUMNS,
)
from synergy_schema.pipeline.runner import run_simulation_pipeline


def test_simulation_runner_full_cycle(tmp_path: Path) -> None:
    """Verify that run_simulation_pipeline executes the full Derive -> Refine -> Project

    flow and emits all facet Parquet files, Demand.sqlite, and run_manifest.json.
    """
    # Create sample DEMOS inputs
    demos_hh = pa.table(
        {
            "household": [101, 102],
            "block_id": [48453000100, 48453000200],
            "lcm_county_id": [48453, 48453],
            "age_of_head": [45.0, 32.0],
            "workers": [2.0, 1.0],
            "race_of_head": [1.0, 3.0],
            "income": [120000.0, 65000.0],
            "persons": [2, 1],
            "is_reorg_household": [False, False],
        }
    )

    demos_p = pa.table(
        {
            "person": [1001, 1002, 2001],
            "relp": [0, 1, 0],
            "gender": [1, 2, 2],
            "education": [21, 21, 16],
            "income": [70000.0, 50000.0, 65000.0],
            "id": [0.0, 1.0, 0.0],
            "age": [45, 43, 32],
            "household": [101, 101, 102],
            "marital_status": [1, 1, 5],
            "employment": [1.0, 1.0, 1.0],
            "school_enrollment": [1.0, 1.0, 1.0],
        }
    )

    # Sample prior state for HH 101
    prior_dir = tmp_path / "prior_core"
    prior_dir.mkdir(parents=True)
    import pyarrow.parquet as pq

    prior_households = pa.table({"household_id": [101]})
    pq.write_table(prior_households, prior_dir / "households.parquet")

    prior_dwelling = pa.table(
        {
            "household_id": [101],
            "housing_unit_type": [1],
            "tenure": [1],
            "has_residential_charging": [1],
            "time_in_home": [3.0],
        }
    )
    pq.write_table(prior_dwelling, prior_dir / "household_dwelling.parquet")

    # Sample vehicles
    vehicles_data = pa.table(
        {
            "vehicle_id": [1, 2],
            "household_id": [101, 102],
            "type_id": [1, 2],
        }
    )

    out_dir = tmp_path / "sim_output"
    results = run_simulation_pipeline(
        demos_households=demos_hh,
        demos_persons=demos_p,
        prior_core_facets=prior_dir,
        vehicles=vehicles_data,
        output_dir=out_dir,
        seed_prefix="test-austin-seed",
        income_deflator=0.95,
    )

    # 1. Assert file outputs exist
    assert out_dir.exists()
    assert (out_dir / "run_manifest.json").exists()
    assert (out_dir / "Demand.sqlite").exists()
    facets_dir = out_dir / "core_facets"
    assert facets_dir.exists()

    for facet in CORE_FACET_COLUMNS:
        facet_file = facets_dir / f"{facet}.parquet"
        assert facet_file.exists(), f"Facet file {facet_file} is missing"

    # 2. Check manifest schema and contents
    manifest = results["manifest"]
    assert manifest["pipeline_version"] == "synergy-pipeline/v1"
    assert manifest["seed_prefix"] == "test-austin-seed"
    assert manifest["income_deflator"] == 0.95
    assert manifest["classification"]["surviving_households"] == 1
    assert manifest["classification"]["new_households"] == 1
    assert manifest["classification"]["removed_households"] == 0

    # 3. Check row counts
    assert results["row_counts"]["households"] == 2
    assert results["row_counts"]["people"] == 3
    assert results["row_counts"]["vehicles"] == 2
    assert results["row_counts"]["Household"] == 2
    assert results["row_counts"]["Person"] == 3
    assert results["row_counts"]["Vehicle"] == 2

    # 4. Verify on-disk digests match manifest digests
    for facet in CORE_FACET_COLUMNS:
        computed = compute_tabular_digest(
            source=facets_dir / f"{facet}.parquet",
            columns=CORE_FACET_COLUMNS[facet],
            key_columns=CORE_FACET_KEY_COLUMNS[facet],
            profile="core_facet_table/v1",
        )
        assert computed == manifest["core_facet_digests"][facet]

    for view_table in ["Household", "Person", "Vehicle"]:
        computed = compute_tabular_digest(
            source=out_dir / "Demand.sqlite",
            columns=POLARIS_DEMAND_COLUMNS[view_table],
            key_columns=POLARIS_DEMAND_KEY_COLUMNS[view_table],
            profile="view_table/v1",
            sqlite_table=view_table,
        )
        assert computed == manifest["view_table_digests"][view_table]


def test_simulation_runner_with_real_demos_sample(tmp_path: Path) -> None:
    """Verify execution using sample extract of real DEMOS CSV files."""
    repo_root = Path(__file__).parents[1]
    real_hh_path = repo_root / "evidence/demos_outputs/Household2018_POLARIS_mapped.csv"
    real_p_path = repo_root / "evidence/demos_outputs/Person2018_POLARIS_mapped.csv"

    if not (real_hh_path.exists() and real_p_path.exists()):
        pytest.skip("Evidence DEMOS files not available")

    # Extract 20 households and matching persons
    import duckdb

    con = duckdb.connect()
    hh_sample = con.execute(f"""
        SELECT * FROM read_csv_auto('{real_hh_path.as_posix()}') LIMIT 20;
    """).to_arrow_table()

    p_sample = con.execute(f"""
        SELECT p.*
        FROM read_csv_auto('{real_p_path.as_posix()}') p
        JOIN hh_sample h ON p.household = h.household;
    """).to_arrow_table()

    out_dir = tmp_path / "real_sample_output"
    results = run_simulation_pipeline(
        demos_households=hh_sample,
        demos_persons=p_sample,
        output_dir=out_dir,
        seed_prefix="austin-real-sample",
    )

    assert results["row_counts"]["households"] == 20
    assert results["row_counts"]["Household"] == 20
    assert results["row_counts"]["people"] == len(p_sample)
    assert results["row_counts"]["Person"] == len(p_sample)
    assert (out_dir / "Demand.sqlite").exists()


def test_simulation_runner_cli_execution(tmp_path: Path) -> None:
    """Verify that python -m synergy_schema.pipeline.runner CLI works as expected."""
    # Write input CSVs
    hh_csv = tmp_path / "demos_hh.csv"
    p_csv = tmp_path / "demos_p.csv"

    hh_csv.write_text(
        "household,block_id,lcm_county_id,age_of_head,workers,race_of_head,income,persons,is_reorg_household\n"
        "101,48453000100,48453,45.0,1.0,1.0,80000.0,1,False\n"
    )
    p_csv.write_text(
        "person,relp,gender,education,income,id,age,household,marital_status,employment,school_enrollment\n"
        "1001,0,1,21,80000.0,0.0,45,101,5,1.0,1.0\n"
    )

    out_dir = tmp_path / "cli_output"
    cmd = [
        sys.executable,
        "-m",
        "synergy_schema.pipeline.runner",
        "--demos-households",
        hh_csv.as_posix(),
        "--demos-persons",
        p_csv.as_posix(),
        "--output-dir",
        out_dir.as_posix(),
        "--seed-prefix",
        "test-cli",
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert "Pipeline run completed successfully" in proc.stdout
    assert (out_dir / "run_manifest.json").exists()
    assert (out_dir / "Demand.sqlite").exists()

    manifest = json.loads((out_dir / "run_manifest.json").read_text())
    assert manifest["row_counts"]["Household"] == 1
    assert manifest["row_counts"]["Person"] == 1
