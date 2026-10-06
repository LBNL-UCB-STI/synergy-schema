"""Tests for Consist-instrumented pipeline execution and cache validation (Stage 3 Task 3.5)."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from synergy_schema.pipeline.consist_runner import (
    HAS_CONSIST,
    run_simulation_with_consist,
)


@pytest.mark.skipif(not HAS_CONSIST, reason="Consist library not available")
def test_consist_runner_full_cycle_and_caching(tmp_path: Path) -> None:
    """Verify that Consist tracks the pipeline, records provenance, and serves cache hits

    on repeated identical execution, while invalidating granularly on seed changes.
    """
    # 1. Create sample DEMOS inputs
    demos_dir = tmp_path / "demos_data"
    demos_dir.mkdir(parents=True)
    demos_hh_file = demos_dir / "demos_hh.csv"
    demos_p_file = demos_dir / "demos_p.csv"

    demos_hh_file.write_text(
        "household,block_id,lcm_county_id,age_of_head,workers,race_of_head,income,persons,is_reorg_household\n"
        "101,48453000100,48453,45.0,2.0,1.0,120000.0,2,False\n"
        "102,48453000200,48453,32.0,1.0,3.0,65000.0,1,False\n"
    )

    demos_p_file.write_text(
        "person,relp,gender,education,income,id,age,household,marital_status,employment,school_enrollment\n"
        "1001,0,1,21,70000.0,0.0,45,101,1,1.0,1.0\n"
        "1002,1,2,21,50000.0,1.0,43,101,1,1.0,1.0\n"
        "2001,0,2,16,65000.0,0.0,32,102,5,1.0,1.0\n"
    )

    out_dir = tmp_path / "sim_output"

    # --- Run 1: Cold run ---
    res1 = run_simulation_with_consist(
        demos_households_path=demos_hh_file,
        demos_persons_path=demos_p_file,
        output_dir=out_dir,
        seed_prefix="seed-v1",
        income_deflator=1.0,
    )

    assert out_dir.exists()
    assert (out_dir / "Demand.sqlite").exists()
    assert (out_dir / "provenance.duckdb").exists()
    assert (out_dir / "run_manifest.json").exists()

    # In Run 1, all steps should have executed (no cache hits)
    assert res1["cache_hits"]["derive"] is False
    assert res1["cache_hits"]["refine_dwelling"] is False
    assert res1["cache_hits"]["refine_schooling"] is False
    assert res1["cache_hits"]["refine_employment"] is False
    assert res1["cache_hits"]["project_polaris"] is False

    # All producing run IDs should be non-empty strings
    for step_name, run_id in res1["producing_runs"].items():
        assert run_id is not None
        assert len(run_id) > 0

    # --- Run 2: Hot run (identical inputs and seed) ---
    res2 = run_simulation_with_consist(
        demos_households_path=demos_hh_file,
        demos_persons_path=demos_p_file,
        output_dir=out_dir,
        seed_prefix="seed-v1",
        income_deflator=1.0,
    )

    # In Run 2, every step should be a cache hit!
    assert res2["cache_hits"]["derive"] is True
    assert res2["cache_hits"]["refine_dwelling"] is True
    assert res2["cache_hits"]["refine_schooling"] is True
    assert res2["cache_hits"]["refine_employment"] is True
    assert res2["cache_hits"]["project_polaris"] is True

    # Manifest digests must be completely identical
    assert res1["core_facet_digests"] == res2["core_facet_digests"]
    assert res1["view_table_digests"] == res2["view_table_digests"]

    # --- Run 3: Granular cache invalidation (change seed only) ---
    res3 = run_simulation_with_consist(
        demos_households_path=demos_hh_file,
        demos_persons_path=demos_p_file,
        output_dir=out_dir,
        seed_prefix="seed-v2-different",
        income_deflator=1.0,
    )

    # Base derivation should still be a CACHE HIT because inputs & deflator didn't change!
    assert res3["cache_hits"]["derive"] is True
    # Refinement steps should re-run because seed changed!
    assert res3["cache_hits"]["refine_dwelling"] is False
    assert res3["cache_hits"]["refine_schooling"] is False
    assert res3["cache_hits"]["refine_employment"] is False

    # --- Verify provenance database directly in DuckDB ---
    db_con = duckdb.connect((out_dir / "provenance.duckdb").as_posix())
    runs = db_con.execute("SELECT id, model_name, status FROM run;").fetchall()
    assert len(runs) > 0

    artifacts = db_con.execute(
        "SELECT key, container_uri, driver, hash FROM artifact;"
    ).fetchall()
    assert len(artifacts) > 0

    links = db_con.execute(
        "SELECT run_id, artifact_id, direction FROM run_artifact_link;"
    ).fetchall()
    assert len(links) > 0
    input_links = [link for link in links if link[2] == "input"]
    output_links = [link for link in links if link[2] == "output"]
    assert len(input_links) > 0
    assert len(output_links) > 0
