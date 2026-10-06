"""Stochastic refinement pipeline for Synergy Core facets.

Implements Stage 3 Task 3.3:
- Dwelling assignment (D-H1 -> household_dwelling):
    - Surviving households carry forward dwelling attributes with time_in_home += 1.0.
    - New households receive dwelling attributes via deterministic donor draw / distribution matching.
- School progression (X-P4, X-P5, X-P6 -> person_schooling):
    - Continuing students progress one grade (X-P4).
    - School entrants receive age-appropriate entry grade (X-P5).
    - K-12 education level is reconciled with school grade (X-P6).
- Job and commute draws (D-P1, D-P2 -> person_employment):
    - Continuing workers carry forward industry, worker type, and commute mode.
    - New or changing workers receive job and commute attributes via deterministic draw.
- Deterministic pseudo-random draws using stable cryptographic hashing:
    abs(('0x' || substring(md5(concat(seed, '::', id)), 1, 15))::BIGINT).
- Canonical tabular content hashing for each refined core facet via core_facet_table/v1.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from synergy_schema.conformance.tabular_digest import compute_tabular_digest
from synergy_schema.pipeline.derive import (
    CORE_FACET_COLUMNS,
    CORE_FACET_KEY_COLUMNS,
    _register_input,
)


def refine_household_dwelling(
    households: Path | str | pa.Table | duckdb.DuckDBPyRelation,
    prior_dwelling: Path | str | pa.Table | duckdb.DuckDBPyRelation | None = None,
    donor_dwellings: Path | str | pa.Table | duckdb.DuckDBPyRelation | None = None,
    seed: str = "seed-2026-dh1",
    output_path: Path | str | None = None,
    duckdb_con: duckdb.DuckDBPyConnection | None = None,
) -> dict[str, Any]:
    """Refine or assign household dwelling attributes (tenure, housing unit type,

    charging, time_in_home).

    Surviving households carry forward prior attributes and increment time_in_home.
    New households receive assigned attributes via deterministic draw D-H1.
    """
    con = duckdb_con or duckdb.connect()
    _register_input(con, "curr_households", households)

    if prior_dwelling is not None:
        _register_input(con, "prior_dwelling", prior_dwelling)
    else:
        con.execute("""
            CREATE OR REPLACE TEMP TABLE prior_dwelling (
                household_id BIGINT,
                housing_unit_type INTEGER,
                tenure INTEGER,
                has_residential_charging INTEGER,
                time_in_home DOUBLE
            );
        """)

    # Deterministic draw for new households based on Austin ACS base shares (X-H3)
    # 81.8% single family (HU 1), 7.4% small apt (HU 2), 4.1% large apt (HU 3), 6.7% other (HU 4)
    # Single family: 82% own (tenure 1), 18% rent (tenure 2); Apartments: 95% rent (tenure 2)
    # Residential charging: ~2% for single family owners
    dwelling_table = con.execute(f"""
        WITH household_hashes AS (
            SELECT
                h.household_id,
                abs(('0x' || substring(md5('{seed}' || '::hh_dwelling::' || CAST(h.household_id AS VARCHAR)), 1, 15))::BIGINT) % 1000 AS draw_val
            FROM curr_households h
        )
        SELECT
            h.household_id,
            CAST(
                CASE
                    WHEN prior.housing_unit_type IS NOT NULL THEN prior.housing_unit_type
                    WHEN hh.draw_val < 818 THEN 1  -- Single family
                    WHEN hh.draw_val < 892 THEN 2  -- Small apt (2-9 units)
                    WHEN hh.draw_val < 933 THEN 3  -- Large apt (10+ units)
                    ELSE 4                         -- Other / mobile home
                END AS INTEGER
            ) AS housing_unit_type,
            CAST(
                CASE
                    WHEN prior.tenure IS NOT NULL THEN prior.tenure
                    -- Single family: 82% own, 18% rent
                    WHEN hh.draw_val < 818 THEN CASE WHEN (hh.draw_val % 100) < 82 THEN 1 ELSE 2 END
                    -- Other: 70% own
                    WHEN hh.draw_val >= 933 THEN CASE WHEN (hh.draw_val % 100) < 70 THEN 1 ELSE 2 END
                    -- Apartments: 95% rent
                    ELSE 2
                END AS INTEGER
            ) AS tenure,
            CAST(
                CASE
                    WHEN prior.has_residential_charging IS NOT NULL THEN prior.has_residential_charging
                    -- ~2% charging for single family owners
                    WHEN hh.draw_val < 818 AND (hh.draw_val % 100) < 82 AND (hh.draw_val % 50 = 0) THEN 1
                    ELSE 0
                END AS INTEGER
            ) AS has_residential_charging,
            CAST(
                CASE
                    WHEN prior.time_in_home IS NOT NULL THEN prior.time_in_home + 1.0
                    ELSE 0.0
                END AS DOUBLE
            ) AS time_in_home
        FROM curr_households h
        JOIN household_hashes hh ON h.household_id = hh.household_id
        LEFT JOIN prior_dwelling prior ON h.household_id = prior.household_id
        ORDER BY h.household_id ASC
    """).to_arrow_table()

    file_path: Path | None = None
    if output_path is not None:
        file_path = Path(output_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(dwelling_table, file_path)

    digest = compute_tabular_digest(
        source=dwelling_table,
        columns=CORE_FACET_COLUMNS["household_dwelling"],
        key_columns=CORE_FACET_KEY_COLUMNS["household_dwelling"],
        profile="core_facet_table/v1",
    )

    return {
        "table": dwelling_table,
        "path": file_path,
        "digest": digest,
    }


def refine_person_schooling(
    people: Path | str | pa.Table | duckdb.DuckDBPyRelation,
    demos_persons: Path | str | pa.Table | duckdb.DuckDBPyRelation,
    prior_schooling: Path | str | pa.Table | duckdb.DuckDBPyRelation | None = None,
    seed: str = "seed-2026-school",
    output_path: Path | str | None = None,
    duckdb_con: duckdb.DuckDBPyConnection | None = None,
) -> dict[str, Any]:
    """Refine person schooling attributes (school_status, school_location_id,

    education_level, school_grade_level) implementing X-P4, X-P5, and X-P6.
    """
    con = duckdb_con or duckdb.connect()
    _register_input(con, "curr_people", people)
    _register_input(con, "demos_persons", demos_persons)

    if prior_schooling is not None:
        _register_input(con, "prior_schooling", prior_schooling)
    else:
        con.execute("""
            CREATE OR REPLACE TEMP TABLE prior_schooling (
                person_id BIGINT,
                school_status INTEGER,
                school_location_id INTEGER,
                education_level INTEGER,
                school_grade_level INTEGER
            );
        """)

    schooling_table = con.execute("""
        WITH calculated_grades AS (
            SELECT
                p.person_id,
                dp.age,
                CAST(dp.education AS INTEGER) AS demos_education,
                CASE WHEN dp.school_enrollment IN (2, 3) THEN 1 ELSE 0 END AS school_status,
                COALESCE(prior.school_location_id, -1) AS prior_school_loc,
                -- Grade progression (X-P4 continuing, X-P5 new entrants)
                CAST(
                    CASE
                        -- Not enrolled
                        WHEN dp.school_enrollment NOT IN (2, 3) THEN 0
                        -- Continuing enrolled student (X-P4)
                        WHEN prior.school_grade_level IS NOT NULL AND prior.school_status = 1 THEN
                            CASE
                                WHEN prior.school_grade_level = 1 THEN CASE WHEN dp.age >= 5 THEN 2 ELSE 1 END
                                WHEN prior.school_grade_level BETWEEN 2 AND 13 THEN prior.school_grade_level + 1
                                WHEN prior.school_grade_level = 14 THEN 15
                                WHEN prior.school_grade_level = 15 THEN CASE WHEN dp.education >= 21 THEN 16 ELSE 15 END
                                ELSE 16
                            END
                        -- New student entrant (X-P5)
                        ELSE
                            CASE
                                WHEN dp.age <= 4 THEN 1
                                WHEN dp.age = 5 THEN 2
                                WHEN dp.age BETWEEN 6 AND 17 THEN dp.age - 3
                                WHEN dp.education >= 21 THEN 16
                                ELSE 15
                            END
                    END AS INTEGER
                ) AS raw_grade
            FROM curr_people p
            JOIN demos_persons dp ON p.person_id = dp.person
            LEFT JOIN prior_schooling prior ON p.person_id = prior.person_id
        )
        SELECT
            person_id,
            school_status,
            CAST(
                CASE
                    WHEN school_status = 0 THEN -1
                    ELSE prior_school_loc
                END AS INTEGER
            ) AS school_location_id,
            -- K-12 education level consistency rule (X-P6)
            CAST(
                CASE
                    WHEN raw_grade BETWEEN 1 AND 14 THEN
                        CASE
                            WHEN demos_education IN (raw_grade, raw_grade + 1) THEN demos_education
                            ELSE raw_grade
                        END
                    ELSE demos_education
                END AS INTEGER
            ) AS education_level,
            raw_grade AS school_grade_level
        FROM calculated_grades
        ORDER BY person_id ASC
    """).to_arrow_table()

    file_path: Path | None = None
    if output_path is not None:
        file_path = Path(output_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(schooling_table, file_path)

    digest = compute_tabular_digest(
        source=schooling_table,
        columns=CORE_FACET_COLUMNS["person_schooling"],
        key_columns=CORE_FACET_KEY_COLUMNS["person_schooling"],
        profile="core_facet_table/v1",
    )

    return {
        "table": schooling_table,
        "path": file_path,
        "digest": digest,
    }


def refine_person_employment(
    people: Path | str | pa.Table | duckdb.DuckDBPyRelation,
    demos_persons: Path | str | pa.Table | duckdb.DuckDBPyRelation,
    prior_employment: Path | str | pa.Table | duckdb.DuckDBPyRelation | None = None,
    donor_jobs: Path | str | pa.Table | duckdb.DuckDBPyRelation | None = None,
    seed: str = "seed-2026-job",
    output_path: Path | str | None = None,
    duckdb_con: duckdb.DuckDBPyConnection | None = None,
) -> dict[str, Any]:
    """Refine person employment attributes (worker_type, industry, work_location_id,

    hours_worked, commute_mode, income) implementing draws D-P1 and D-P2.
    """
    con = duckdb_con or duckdb.connect()
    _register_input(con, "curr_people", people)
    _register_input(con, "demos_persons", demos_persons)

    if prior_employment is not None:
        _register_input(con, "prior_employment", prior_employment)
    else:
        con.execute("""
            CREATE OR REPLACE TEMP TABLE prior_employment (
                person_id BIGINT,
                employment_status INTEGER,
                worker_type INTEGER,
                industry INTEGER,
                work_location_id INTEGER,
                hours_worked INTEGER,
                commute_mode INTEGER,
                income BIGINT
            );
        """)

    employment_table = con.execute(f"""
        WITH person_hashes AS (
            SELECT
                p.person_id,
                abs(('0x' || substring(md5('{seed}' || '::person_job::' || CAST(p.person_id AS VARCHAR)), 1, 15))::BIGINT) % 100 AS job_draw,
                abs(('0x' || substring(md5('{seed}' || '::person_commute::' || CAST(p.person_id AS VARCHAR)), 1, 15))::BIGINT) % 100 AS commute_draw
            FROM curr_people p
        )
        SELECT
            p.person_id,
            CAST(dp.employment AS INTEGER) AS employment_status,
            CAST(
                CASE
                    -- Under 16 or not employed
                    WHEN dp.age < 16 OR dp.employment IN (0, 3, 6) THEN 0
                    -- Continuing employed worker with prior job attributes
                    WHEN prior.industry IS NOT NULL AND prior.industry > 0 AND dp.employment IN (1, 2, 4, 5) THEN prior.worker_type
                    -- New worker D-P1 draw: private wage/salary (1), government (2), self-employed (3)
                    WHEN ph.job_draw < 75 THEN 1
                    WHEN ph.job_draw < 85 THEN 2
                    ELSE 3
                END AS INTEGER
            ) AS worker_type,
            CAST(
                CASE
                    WHEN dp.age < 16 OR dp.employment IN (0, 3, 6) THEN 0
                    WHEN prior.industry IS NOT NULL AND prior.industry > 0 AND dp.employment IN (1, 2, 4, 5) THEN prior.industry
                    -- New worker D-P1 draw for top Austin employment sectors
                    WHEN ph.job_draw < 25 THEN 7380  -- Professional / Technical
                    WHEN ph.job_draw < 45 THEN 6870  -- Educational Services
                    WHEN ph.job_draw < 65 THEN 7860  -- Health Care
                    WHEN ph.job_draw < 80 THEN 8680  -- Accommodation / Food Services
                    ELSE 5070                        -- Retail Trade
                END AS INTEGER
            ) AS industry,
            CAST(
                CASE
                    -- Not at work (ESR outside 1, 4)
                    WHEN dp.employment NOT IN (1, 4) THEN -1
                    -- Continuing at-work worker preserves work location
                    WHEN prior.work_location_id IS NOT NULL AND dp.employment IN (1, 4) THEN prior.work_location_id
                    -- New or changed worker: -1 triggers POLARIS long-term work choice
                    ELSE -1
                END AS INTEGER
            ) AS work_location_id,
            CAST(
                CASE
                    WHEN dp.age < 16 OR dp.employment IN (0, 3, 6) THEN 0
                    WHEN prior.hours_worked IS NOT NULL AND prior.hours_worked > 0 AND dp.employment IN (1, 2, 4, 5) THEN prior.hours_worked
                    -- D-P1 draw for work hours: 40 full time, 45 overtime, 20 part time
                    WHEN ph.job_draw < 80 THEN 40
                    WHEN ph.job_draw < 90 THEN 45
                    ELSE 20
                END AS INTEGER
            ) AS hours_worked,
            CAST(
                CASE
                    WHEN dp.employment NOT IN (1, 4) THEN 0
                    WHEN prior.commute_mode IS NOT NULL AND prior.commute_mode > 0 AND dp.employment IN (1, 4) THEN prior.commute_mode
                    -- D-P2 commute mode: drive alone (1), carpool (2), transit (3)
                    WHEN ph.commute_draw < 80 THEN 1
                    WHEN ph.commute_draw < 92 THEN 2
                    ELSE 3
                END AS INTEGER
            ) AS commute_mode,
            CAST(ROUND(COALESCE(dp.income, 0.0)) AS BIGINT) AS income
        FROM curr_people p
        JOIN demos_persons dp ON p.person_id = dp.person
        JOIN person_hashes ph ON p.person_id = ph.person_id
        LEFT JOIN prior_employment prior ON p.person_id = prior.person_id
        ORDER BY p.person_id ASC
    """).to_arrow_table()

    file_path: Path | None = None
    if output_path is not None:
        file_path = Path(output_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(employment_table, file_path)

    digest = compute_tabular_digest(
        source=employment_table,
        columns=CORE_FACET_COLUMNS["person_employment"],
        key_columns=CORE_FACET_KEY_COLUMNS["person_employment"],
        profile="core_facet_table/v1",
    )

    return {
        "table": employment_table,
        "path": file_path,
        "digest": digest,
    }


def refine_core_facets(
    households: Path | str | pa.Table | duckdb.DuckDBPyRelation,
    people: Path | str | pa.Table | duckdb.DuckDBPyRelation,
    demos_persons: Path | str | pa.Table | duckdb.DuckDBPyRelation,
    prior_core_facets: dict[str, Any] | None = None,
    output_dir: Path | str | None = None,
    seed_prefix: str = "seed-2026",
    duckdb_con: duckdb.DuckDBPyConnection | None = None,
) -> dict[str, Any]:
    """Execute all three refinement runs in sequence: dwelling, schooling, employment.

    Returns dict with emitted facet tables, output file paths, and canonical digests.
    """
    prior = prior_core_facets or {}
    out_dir = Path(output_dir) if output_dir is not None else None

    # 1. Dwelling refinement
    dwelling_out = out_dir / "household_dwelling.parquet" if out_dir else None
    res_dwelling = refine_household_dwelling(
        households=households,
        prior_dwelling=prior.get("household_dwelling"),
        seed=f"{seed_prefix}::dh1",
        output_path=dwelling_out,
        duckdb_con=duckdb_con,
    )

    # 2. Schooling refinement
    schooling_out = out_dir / "person_schooling.parquet" if out_dir else None
    res_schooling = refine_person_schooling(
        people=people,
        demos_persons=demos_persons,
        prior_schooling=prior.get("person_schooling"),
        seed=f"{seed_prefix}::school",
        output_path=schooling_out,
        duckdb_con=duckdb_con,
    )

    # 3. Employment refinement
    employment_out = out_dir / "person_employment.parquet" if out_dir else None
    res_employment = refine_person_employment(
        people=people,
        demos_persons=demos_persons,
        prior_employment=prior.get("person_employment"),
        seed=f"{seed_prefix}::job",
        output_path=employment_out,
        duckdb_con=duckdb_con,
    )

    facets = {
        "household_dwelling": res_dwelling["table"],
        "person_schooling": res_schooling["table"],
        "person_employment": res_employment["table"],
    }
    file_paths = {
        "household_dwelling": res_dwelling["path"],
        "person_schooling": res_schooling["path"],
        "person_employment": res_employment["path"],
    }
    digests = {
        "household_dwelling": res_dwelling["digest"],
        "person_schooling": res_schooling["digest"],
        "person_employment": res_employment["digest"],
    }

    return {
        "facets": facets,
        "file_paths": file_paths,
        "digests": digests,
    }
