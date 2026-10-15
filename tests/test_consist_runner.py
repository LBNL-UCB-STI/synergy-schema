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


@pytest.mark.skipif(not HAS_CONSIST, reason="Consist library not available")
def test_consist_runner_multi_year_state_preservation(tmp_path: Path) -> None:
    """Verify multi-year state preservation across prior core facets in consist_runner.

    Ensures surviving persons retain prior race/hispanic, non-moving surviving households
    retain prior latitude/longitude/taz, and vehicles.parquet carries forward when
    vehicles_path is omitted in year t > t_0.
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    demos_dir = tmp_path / "demos_multi_year"
    demos_dir.mkdir(parents=True)

    # Year t0 inputs
    hh_t0 = demos_dir / "hh_t0.csv"
    p_t0 = demos_dir / "p_t0.csv"
    hh_t0.write_text(
        "household,block_id,lcm_county_id,age_of_head,workers,race_of_head,income,persons,is_reorg_household\n"
        "101,48453000100,48453,45.0,2.0,1.0,120000.0,2,False\n"
    )
    p_t0.write_text(
        "person,relp,gender,education,income,id,age,household,marital_status,employment,school_enrollment\n"
        "1001,0,1,21,70000.0,0.0,45,101,1,1.0,1.0\n"
        "1002,1,2,21,50000.0,1.0,43,101,1,1.0,1.0\n"
    )

    veh_t0 = demos_dir / "vehicles_t0.parquet"
    pq.write_table(
        pa.table(
            {
                "vehicle_id": pa.array([9001], type=pa.int64()),
                "household_id": pa.array([101], type=pa.int64()),
                "type_id": pa.array([12], type=pa.int32()),
            }
        ),
        veh_t0,
    )

    out_t0 = tmp_path / "out_t0"
    run_simulation_with_consist(
        demos_households_path=hh_t0,
        demos_persons_path=p_t0,
        vehicles_path=veh_t0,
        output_dir=out_t0,
        seed_prefix="seed-t0",
        income_deflator=1.0,
    )

    # Enrich t0 prior facets with distinct non-head demographics and geocoded coordinates
    prior_facets_dir = out_t0 / "core_facets"
    pq.write_table(
        pa.table(
            {
                "person_id": pa.array([1001, 1002], type=pa.int64()),
                "age": pa.array([45, 43], type=pa.int32()),
                "sex": pa.array([1, 2], type=pa.int32()),
                "race": pa.array([1, 6], type=pa.int32()),
                "hispanic": pa.array([0, 1], type=pa.int32()),
            }
        ),
        prior_facets_dir / "person_demographics.parquet",
    )
    pq.write_table(
        pa.table(
            {
                "household_id": pa.array([101], type=pa.int64()),
                "latitude": pa.array([30.2999], type=pa.float64()),
                "longitude": pa.array([-97.7999], type=pa.float64()),
                "tract": pa.array([48453000100], type=pa.int64()),
                "block_group": pa.array([1], type=pa.int32()),
                "taz": pa.array([555], type=pa.int32()),
            }
        ),
        prior_facets_dir / "household_location.parquet",
    )

    # Year t1 inputs (household 101 stays at same block_id; person 1002 survives; new hh 103 added)
    hh_t1 = demos_dir / "hh_t1.csv"
    p_t1 = demos_dir / "p_t1.csv"
    hh_t1.write_text(
        "household,block_id,lcm_county_id,age_of_head,workers,race_of_head,income,persons,is_reorg_household\n"
        "101,48453000100,48453,46.0,2.0,1.0,125000.0,2,False\n"
        "103,48453000300,48453,29.0,1.0,2.0,80000.0,1,False\n"
    )
    p_t1.write_text(
        "person,relp,gender,education,income,id,age,household,marital_status,employment,school_enrollment\n"
        "1001,0,1,21,72000.0,0.0,46,101,1,1.0,1.0\n"
        "1002,1,2,21,53000.0,1.0,44,101,1,1.0,1.0\n"
        "3001,0,2,19,80000.0,0.0,29,103,5,1.0,1.0\n"
    )

    out_t1 = tmp_path / "out_t1"
    run_simulation_with_consist(
        demos_households_path=hh_t1,
        demos_persons_path=p_t1,
        prior_core_dir=prior_facets_dir,
        vehicles_path=None,
        output_dir=out_t1,
        seed_prefix="seed-t1",
        income_deflator=0.97,
    )

    t1_facets_dir = out_t1 / "core_facets"

    # 1. Verify surviving person 1002 retained prior race=6 and hispanic=1
    p_demo_t1 = pq.read_table(t1_facets_dir / "person_demographics.parquet").to_pylist()
    by_pid = {row["person_id"]: row for row in p_demo_t1}
    assert by_pid[1002]["race"] == 6
    assert by_pid[1002]["hispanic"] == 1
    assert by_pid[1002]["age"] == 44

    # 2. Verify non-moving surviving household 101 retained prior latitude/longitude/taz
    hh_loc_t1 = pq.read_table(t1_facets_dir / "household_location.parquet").to_pylist()
    by_hhid = {row["household_id"]: row for row in hh_loc_t1}
    assert by_hhid[101]["latitude"] == pytest.approx(30.2999)
    assert by_hhid[101]["longitude"] == pytest.approx(-97.7999)
    assert by_hhid[101]["taz"] == 555

    # 3. Verify vehicles.parquet carried forward from prior_core_dir when vehicles_path=None
    veh_t1 = pq.read_table(t1_facets_dir / "vehicles.parquet").to_pylist()
    assert len(veh_t1) == 1
    assert veh_t1[0]["vehicle_id"] == 9001
    assert veh_t1[0]["household_id"] == 101
    assert veh_t1[0]["type_id"] == 12


def test_step_derive_preserves_multi_year_core_facets_without_consist(
    tmp_path: Path,
) -> None:
    """Directly verify _step_derive multi-year state preservation without requiring Consist."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    from synergy_schema.pipeline.consist_runner import _step_derive

    demos_dir = tmp_path / "demos_step_derive"
    demos_dir.mkdir(parents=True)

    hh_t0 = demos_dir / "hh_t0.csv"
    p_t0 = demos_dir / "p_t0.csv"
    hh_t0.write_text(
        "household,block_id,lcm_county_id,age_of_head,workers,race_of_head,income,persons,is_reorg_household\n"
        "101,48453000100,48453,45.0,2.0,1.0,120000.0,2,False\n"
    )
    p_t0.write_text(
        "person,relp,gender,education,income,id,age,household,marital_status,employment,school_enrollment\n"
        "1001,0,1,21,70000.0,0.0,45,101,1,1.0,1.0\n"
        "1002,1,2,21,50000.0,1.0,43,101,1,1.0,1.0\n"
    )

    facets_t0 = tmp_path / "facets_t0"
    facets_t0.mkdir(parents=True)
    paths_t0 = _step_derive(
        demos_households_path=hh_t0,
        demos_persons_path=p_t0,
        income_deflator=1.0,
        output_dir=facets_t0,
    )
    assert paths_t0["person_demographics"].exists()

    pq.write_table(
        pa.table(
            {
                "person_id": pa.array([1001, 1002], type=pa.int64()),
                "age": pa.array([45, 43], type=pa.int32()),
                "sex": pa.array([1, 2], type=pa.int32()),
                "race": pa.array([1, 6], type=pa.int32()),
                "hispanic": pa.array([0, 1], type=pa.int32()),
            }
        ),
        facets_t0 / "person_demographics.parquet",
    )
    pq.write_table(
        pa.table(
            {
                "household_id": pa.array([101], type=pa.int64()),
                "latitude": pa.array([30.2999], type=pa.float64()),
                "longitude": pa.array([-97.7999], type=pa.float64()),
                "tract": pa.array([48453000100], type=pa.int64()),
                "block_group": pa.array([1], type=pa.int32()),
                "taz": pa.array([555], type=pa.int32()),
            }
        ),
        facets_t0 / "household_location.parquet",
    )

    hh_t1 = demos_dir / "hh_t1.csv"
    p_t1 = demos_dir / "p_t1.csv"
    hh_t1.write_text(
        "household,block_id,lcm_county_id,age_of_head,workers,race_of_head,income,persons,is_reorg_household\n"
        "101,48453000100,48453,46.0,2.0,1.0,125000.0,2,False\n"
        "103,48453000300,48453,29.0,1.0,2.0,80000.0,1,False\n"
    )
    p_t1.write_text(
        "person,relp,gender,education,income,id,age,household,marital_status,employment,school_enrollment\n"
        "1001,0,1,21,72000.0,0.0,46,101,1,1.0,1.0\n"
        "1002,1,2,21,53000.0,1.0,44,101,1,1.0,1.0\n"
        "3001,0,2,19,80000.0,0.0,29,103,5,1.0,1.0\n"
    )

    facets_t1 = tmp_path / "facets_t1"
    facets_t1.mkdir(parents=True)
    paths_t1 = _step_derive(
        demos_households_path=hh_t1,
        demos_persons_path=p_t1,
        prior_households_path=facets_t0 / "households.parquet",
        prior_people_path=facets_t0 / "people.parquet",
        prior_person_demographics_path=facets_t0 / "person_demographics.parquet",
        prior_household_location_path=facets_t0 / "household_location.parquet",
        prior_household_membership_path=facets_t0 / "household_membership.parquet",
        prior_household_income_path=facets_t0 / "household_income.parquet",
        income_deflator=0.97,
        output_dir=facets_t1,
    )

    p_demo_t1 = {
        row["person_id"]: row
        for row in pq.read_table(paths_t1["person_demographics"]).to_pylist()
    }
    assert p_demo_t1[1002]["race"] == 6
    assert p_demo_t1[1002]["hispanic"] == 1
    assert p_demo_t1[1002]["age"] == 44

    hh_loc_t1 = {
        row["household_id"]: row
        for row in pq.read_table(paths_t1["household_location"]).to_pylist()
    }
    assert hh_loc_t1[101]["latitude"] == pytest.approx(30.2999)
    assert hh_loc_t1[101]["longitude"] == pytest.approx(-97.7999)
    assert hh_loc_t1[101]["taz"] == 555
