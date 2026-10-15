"""Unit tests for stochastic refinement pipeline (Stage 3 Task 3.3)."""

from __future__ import annotations

import pyarrow as pa

from synergy_schema.conformance.tabular_digest import compute_tabular_digest
from synergy_schema.pipeline.derive import (
    CORE_FACET_COLUMNS,
    CORE_FACET_KEY_COLUMNS,
    derive_core_from_demos,
)
from synergy_schema.pipeline.polaris_projection import project_core_to_polaris
from synergy_schema.pipeline.refine import (
    refine_core_facets,
    refine_household_dwelling,
    refine_person_employment,
    refine_person_schooling,
)


def test_refine_household_dwelling_surviving_and_new(tmp_path):
    """Verify dwelling refinement preserves surviving attributes, increments time_in_home,

    and assigns deterministic attributes to new households.
    """
    households = pa.table({"household_id": [101, 102]})

    # HH 101 is surviving with existing dwelling state
    prior_dwelling = pa.table(
        {
            "household_id": [101],
            "housing_unit_type": [1],
            "tenure": [1],
            "has_residential_charging": [1],
            "time_in_home": [4.0],
        }
    )

    out_file = tmp_path / "household_dwelling.parquet"
    res = refine_household_dwelling(
        households=households,
        prior_dwelling=prior_dwelling,
        seed="seed-austin-test",
        output_path=out_file,
    )

    table = res["table"]
    df = table.to_pandas().set_index("household_id")

    # Surviving HH 101: attributes preserved, time_in_home incremented from 4.0 to 5.0
    assert df.loc[101, "housing_unit_type"] == 1
    assert df.loc[101, "tenure"] == 1
    assert df.loc[101, "has_residential_charging"] == 1
    assert df.loc[101, "time_in_home"] == 5.0

    # New HH 102: attributes assigned via draw, time_in_home = 0.0
    assert df.loc[102, "housing_unit_type"] in [1, 2, 3, 4]
    assert df.loc[102, "tenure"] in [1, 2]
    assert df.loc[102, "has_residential_charging"] in [0, 1]
    assert df.loc[102, "time_in_home"] == 0.0

    # Digest verification
    assert res["digest"].startswith("sha256:")
    recomputed = compute_tabular_digest(
        source=out_file,
        columns=CORE_FACET_COLUMNS["household_dwelling"],
        key_columns=CORE_FACET_KEY_COLUMNS["household_dwelling"],
        profile="core_facet_table/v1",
    )
    assert recomputed == res["digest"]


def test_refine_person_schooling_progression_and_entry(tmp_path):
    """Verify schooling refinement implements X-P4 progression, X-P5 entry,

    and X-P6 education consistency.
    """
    # 5 test persons:
    # 1: Surviving K student (age 6, prior grade 2) -> advances to grade 3 (1st grade), keeps school_loc 501
    # 2: Surviving 12th grader (age 18, prior grade 14) -> advances to grade 15 (undergrad), keeps school_loc 502
    # 3: New preschool student (age 4, enrolled) -> entry grade 1 (preschool), loc -1
    # 4: New college student (age 20, enrolled, ed 19) -> entry grade 15, loc -1
    # 5: Adult not enrolled (age 40, ed 21, not enrolled) -> status 0, grade 0, loc -1
    people = pa.table({"person_id": [1, 2, 3, 4, 5]})
    demos_persons = pa.table(
        {
            "person": [1, 2, 3, 4, 5],
            "age": [6, 18, 4, 20, 40],
            "education": [2, 14, 0, 19, 21],
            "school_enrollment": [2.0, 2.0, 2.0, 2.0, 1.0],  # 1.0 = not enrolled
        }
    )

    prior_schooling = pa.table(
        {
            "person_id": [1, 2],
            "school_status": [1, 1],
            "school_location_id": [501, 502],
            "education_level": [2, 14],
            "school_grade_level": [2, 14],
        }
    )

    out_file = tmp_path / "person_schooling.parquet"
    res = refine_person_schooling(
        people=people,
        demos_persons=demos_persons,
        prior_schooling=prior_schooling,
        output_path=out_file,
    )

    df = res["table"].to_pandas().set_index("person_id")

    # Person 1: continuing K -> grade 3 (1st grade), keeps loc 501
    assert df.loc[1, "school_status"] == 1
    assert df.loc[1, "school_grade_level"] == 3
    assert df.loc[1, "school_location_id"] == 501
    # Person 2: continuing 12th grader -> grade 15 (undergraduate), keeps loc 502
    assert df.loc[2, "school_status"] == 1
    assert df.loc[2, "school_grade_level"] == 15
    assert df.loc[2, "school_location_id"] == 502
    # Person 3: new entrant preschooler -> grade 1, loc -1
    assert df.loc[3, "school_status"] == 1
    assert df.loc[3, "school_grade_level"] == 1
    assert df.loc[3, "school_location_id"] == -1
    # Person 4: new entrant undergrad -> grade 15, loc -1
    assert df.loc[4, "school_status"] == 1
    assert df.loc[4, "school_grade_level"] == 15
    assert df.loc[4, "school_location_id"] == -1
    # Person 5: not enrolled
    assert df.loc[5, "school_status"] == 0
    assert df.loc[5, "school_grade_level"] == 0
    assert df.loc[5, "school_location_id"] == -1
    assert df.loc[5, "education_level"] == 21

    # Digest verification
    assert res["digest"].startswith("sha256:")


def test_refine_person_employment_carry_forward_and_draws(tmp_path):
    """Verify employment refinement preserves continuing jobs and draws attributes for new workers."""
    # 3 persons:
    # 1: Surviving worker (ESR 1, employed, prior ind 7380, hours 40, commute 1, work_loc 801)
    # 2: Surviving unemployed (ESR 3, unemployed)
    # 3: New employed worker (ESR 1, age 26, new)
    people = pa.table({"person_id": [1, 2, 3]})
    demos_persons = pa.table(
        {
            "person": [1, 2, 3],
            "age": [35, 45, 26],
            "employment": [1.0, 3.0, 1.0],
            "income": [85000.0, 0.0, 60000.0],
        }
    )

    prior_employment = pa.table(
        {
            "person_id": [1, 2],
            "employment_status": [1, 3],
            "worker_type": [1, 0],
            "industry": [7380, 0],
            "work_location_id": [801, -1],
            "hours_worked": [40, 0],
            "commute_mode": [1, 0],
            "income": [80000, 0],
        }
    )

    out_file = tmp_path / "person_employment.parquet"
    res = refine_person_employment(
        people=people,
        demos_persons=demos_persons,
        prior_employment=prior_employment,
        seed="seed-job-test",
        output_path=out_file,
    )

    df = res["table"].to_pandas().set_index("person_id")

    # Person 1: continuing worker preserves job attributes
    assert df.loc[1, "employment_status"] == 1
    assert df.loc[1, "worker_type"] == 1
    assert df.loc[1, "industry"] == 7380
    assert df.loc[1, "work_location_id"] == 801
    assert df.loc[1, "hours_worked"] == 40
    assert df.loc[1, "commute_mode"] == 1
    assert df.loc[1, "income"] == 85000

    # Person 2: unemployed
    assert df.loc[2, "employment_status"] == 3
    assert df.loc[2, "worker_type"] == 0
    assert df.loc[2, "industry"] == 0
    assert df.loc[2, "work_location_id"] == -1
    assert df.loc[2, "hours_worked"] == 0

    # Person 3: new employed worker receives valid job attributes and work_loc = -1
    assert df.loc[3, "employment_status"] == 1
    assert df.loc[3, "worker_type"] in [1, 2, 3]
    assert df.loc[3, "industry"] > 0
    assert df.loc[3, "work_location_id"] == -1
    assert df.loc[3, "hours_worked"] in [20, 40, 45]
    assert df.loc[3, "commute_mode"] in [1, 2, 3]
    assert df.loc[3, "income"] == 60000


def test_refinement_to_polaris_projection_integration(tmp_path):
    """End-to-end integration: Derive Core -> Refine Core -> Project to POLARIS SQLite."""
    # 1. Setup sample input data
    demos_hh = pa.table(
        {
            "household": [101, 102],
            "block_id": [48453000100, 48453000200],
            "lcm_county_id": [48453, 48453],
            "age_of_head": [45.0, 30.0],
            "workers": [2.0, 1.0],
            "race_of_head": [1.0, 2.0],
            "income": [100000.0, 55000.0],
            "persons": [2, 1],
            "is_reorg_household": [False, False],
        }
    )

    demos_p = pa.table(
        {
            "person": [1001, 1002, 2001],
            "relp": [0, 1, 0],
            "gender": [1, 2, 1],
            "education": [21, 21, 19],
            "income": [60000.0, 40000.0, 55000.0],
            "id": [0.0, 1.0, 0.0],
            "age": [45, 43, 30],
            "household": [101, 101, 102],
            "marital_status": [1, 1, 5],
            "employment": [1.0, 1.0, 1.0],
            "school_enrollment": [1.0, 1.0, 1.0],
        }
    )

    # Step 1: Derive Core facets from DEMOS
    core_dir = tmp_path / "derived_core"
    derive_res = derive_core_from_demos(
        demos_households=demos_hh,
        demos_persons=demos_p,
        output_dir=core_dir,
    )
    derived_facets = derive_res["facets"]

    # Step 2: Refine Core facets (dwellings, schooling, employment)
    refine_dir = tmp_path / "refined_core"
    refine_res = refine_core_facets(
        households=derived_facets["households"],
        people=derived_facets["people"],
        demos_persons=demos_p,
        output_dir=refine_dir,
    )
    refined_facets = refine_res["facets"]

    # Combine all facets
    all_facets = {**derived_facets, **refined_facets}

    # Step 3: Project Core to POLARIS SQLite Demand database
    demand_db = tmp_path / "Demand.sqlite"
    proj_res = project_core_to_polaris(
        core_facets=all_facets,
        output_sqlite_path=demand_db,
    )

    # Assertions
    assert demand_db.exists()
    assert proj_res["row_counts"]["Household"] == 2
    assert proj_res["row_counts"]["Person"] == 3
    for table_name in ["Household", "Person", "Vehicle"]:
        assert proj_res["digests"][table_name].startswith("sha256:")
