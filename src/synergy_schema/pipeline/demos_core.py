"""Core DEMOS native HDF5 <-> Synergy Core SQL derivation and projection.

Translates between core DEMOS native tables (``DemosCorePerson`` and
``DemosCoreHousehold`` in ``demos_core.yaml``) and Synergy Core facets
(``core_tables.yaml``) using DuckDB SQL.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from synergy_schema.conformance.tabular_digest import compute_tabular_digest
from synergy_schema.pipeline.derive import (
    CORE_FACET_COLUMNS,
    CORE_FACET_KEY_COLUMNS,
    _empty_table_for_facet,
    _register_input,
)


def _empty_extended_facet(facet_name: str) -> pa.Table:
    """Return an empty PyArrow table for facets not covered by derive._empty_table_for_facet."""
    if facet_name in {
        "households",
        "people",
        "household_membership",
        "person_demographics",
        "household_location",
        "household_income",
    }:
        return _empty_table_for_facet(facet_name)

    type_map: dict[str, pa.DataType] = {
        "household_id": pa.int64(),
        "person_id": pa.int64(),
        "housing_unit_type": pa.int32(),
        "tenure": pa.int32(),
        "has_residential_charging": pa.int32(),
        "time_in_home": pa.float64(),
        "school_status": pa.int32(),
        "school_location_id": pa.int32(),
        "education_level": pa.int32(),
        "school_grade_level": pa.int32(),
        "employment_status": pa.int32(),
        "worker_type": pa.int32(),
        "industry": pa.int32(),
        "work_location_id": pa.int32(),
        "hours_worked": pa.int32(),
        "commute_mode": pa.int32(),
        "income": pa.int64(),
    }
    cols = CORE_FACET_COLUMNS[facet_name]
    schema = pa.schema([pa.field(c, type_map[c]) for c in cols])
    return pa.Table.from_arrays(
        [pa.array([], type=type_map[c]) for c in cols], schema=schema
    )


def _table_columns(con: duckdb.DuckDBPyConnection, table_name: str) -> set[str]:
    return {row[0] for row in con.execute(f"DESCRIBE {table_name}").fetchall()}


def derive_core_from_demos_core(
    demos_households: Path | str | pa.Table | duckdb.DuckDBPyRelation,
    demos_persons: Path | str | pa.Table | duckdb.DuckDBPyRelation,
    prior_core_facets: Mapping[str, Path | str | pa.Table | duckdb.DuckDBPyRelation]
    | None = None,
    output_dir: Path | str | None = None,
    income_deflator: float = 1.0,
    duckdb_con: duckdb.DuckDBPyConnection | None = None,
) -> dict[str, Any]:
    """Derive Synergy Core facets from core DEMOS native ``persons`` and ``households`` tables."""
    con = duckdb_con or duckdb.connect()

    _register_input(con, "demos_core_households", demos_households)
    _register_input(con, "demos_core_persons", demos_persons)

    prior_facets = prior_core_facets or {}
    for facet_name in [
        "households",
        "people",
        "person_demographics",
        "person_schooling",
        "person_employment",
        "household_dwelling",
        "household_location",
    ]:
        if facet_name in prior_facets:
            _register_input(con, f"prior_{facet_name}", prior_facets[facet_name])
        else:
            con.register(f"prior_{facet_name}", _empty_extended_facet(facet_name))

    hh_cols = _table_columns(con, "demos_core_households")
    p_cols = _table_columns(con, "demos_core_persons")
    prior_loc_cols = _table_columns(con, "prior_household_location")

    hh_counts = con.execute("""
        SELECT
            COUNT(CASE WHEN h.household_id IN (SELECT household_id FROM prior_households) THEN 1 END),
            COUNT(CASE WHEN h.household_id NOT IN (SELECT household_id FROM prior_households) THEN 1 END),
            (SELECT COUNT(*) FROM prior_households WHERE household_id NOT IN (SELECT household_id FROM demos_core_households))
        FROM demos_core_households h
    """).fetchone()

    person_counts = con.execute("""
        SELECT
            COUNT(CASE WHEN p.person_id IN (SELECT person_id FROM prior_people) THEN 1 END),
            COUNT(CASE WHEN p.person_id NOT IN (SELECT person_id FROM prior_people) THEN 1 END),
            (SELECT COUNT(*) FROM prior_people WHERE person_id NOT IN (SELECT person_id FROM demos_core_persons))
        FROM demos_core_persons p
    """).fetchone()

    if hh_counts is None or person_counts is None:
        raise RuntimeError("Failed to compute DEMOS core classification counts.")

    classification = {
        "surviving_households": int(hh_counts[0]),
        "new_households": int(hh_counts[1]),
        "removed_households": int(hh_counts[2]),
        "surviving_persons": int(person_counts[0]),
        "new_persons": int(person_counts[1]),
        "removed_persons": int(person_counts[2]),
    }

    households_table = con.execute("""
        SELECT DISTINCT CAST(household_id AS BIGINT) AS household_id
        FROM demos_core_households
        ORDER BY household_id ASC
    """).to_arrow_table()

    people_table = con.execute("""
        SELECT DISTINCT CAST(person_id AS BIGINT) AS person_id
        FROM demos_core_persons
        ORDER BY person_id ASC
    """).to_arrow_table()

    membership_table = con.execute("""
        SELECT
            CAST(person_id AS BIGINT) AS person_id,
            CAST(household_id AS BIGINT) AS household_id
        FROM demos_core_persons
        ORDER BY person_id ASC
    """).to_arrow_table()

    race_of_head_expr = (
        "CAST(h.race_of_head AS INTEGER)"
        if "race_of_head" in hh_cols
        else "NULL::INTEGER"
    )
    hispanic_expr = (
        "CAST(p.hispanic AS INTEGER)" if "hispanic" in p_cols else "NULL::INTEGER"
    )

    demographics_table = con.execute(f"""
        WITH curr_heads AS (
            SELECT
                CAST(household_id AS BIGINT) AS household_id,
                CAST(COALESCE(MIN(race_id), 1) AS INTEGER) AS head_race
            FROM demos_core_persons
            WHERE relate = 0
            GROUP BY CAST(household_id AS BIGINT)
        )
        SELECT
            CAST(p.person_id AS BIGINT) AS person_id,
            CAST(p.age AS INTEGER) AS age,
            CAST(p.sex AS INTEGER) AS sex,
            CAST(
                COALESCE(
                    prior_d.race,
                    CAST(p.race_id AS INTEGER),
                    CASE WHEN p.relate = 0 THEN {race_of_head_expr} ELSE heads.head_race END,
                    1
                ) AS INTEGER
            ) AS race,
            CAST(COALESCE(prior_d.hispanic, {hispanic_expr}, 0) AS INTEGER) AS hispanic,
            CAST(p.relate AS INTEGER) AS relate
        FROM demos_core_persons p
        LEFT JOIN demos_core_households h ON CAST(p.household_id AS BIGINT) = CAST(h.household_id AS BIGINT)
        LEFT JOIN prior_person_demographics prior_d ON CAST(p.person_id AS BIGINT) = prior_d.person_id
        LEFT JOIN curr_heads heads ON CAST(p.household_id AS BIGINT) = heads.household_id
        ORDER BY person_id ASC
    """).to_arrow_table()

    school_zone_expr = (
        "TRY_CAST(p.school_zone_id AS INTEGER)"
        if "school_zone_id" in p_cols
        else "NULL::INTEGER"
    )
    schooling_table = con.execute(f"""
        SELECT
            CAST(p.person_id AS BIGINT) AS person_id,
            CAST(COALESCE(p.student, 0) AS INTEGER) AS school_status,
            CAST(COALESCE({school_zone_expr}, prior_s.school_location_id, -1) AS INTEGER) AS school_location_id,
            CAST(COALESCE(p.edu, 0) AS INTEGER) AS education_level,
            CAST(COALESCE(prior_s.school_grade_level, -1) AS INTEGER) AS school_grade_level
        FROM demos_core_persons p
        LEFT JOIN prior_person_schooling prior_s ON CAST(p.person_id AS BIGINT) = prior_s.person_id
        ORDER BY person_id ASC
    """).to_arrow_table()

    work_zone_expr = (
        "TRY_CAST(p.work_zone_id AS INTEGER)"
        if "work_zone_id" in p_cols
        else "NULL::INTEGER"
    )
    hours_expr = (
        "CAST(ROUND(p.hours) AS INTEGER)" if "hours" in p_cols else "NULL::INTEGER"
    )
    employment_table = con.execute(f"""
        SELECT
            CAST(p.person_id AS BIGINT) AS person_id,
            CAST(COALESCE(p.worker, 0) AS INTEGER) AS employment_status,
            CAST(COALESCE(prior_e.worker_type, -1) AS INTEGER) AS worker_type,
            CAST(COALESCE(prior_e.industry, -1) AS INTEGER) AS industry,
            CAST(COALESCE({work_zone_expr}, prior_e.work_location_id, -1) AS INTEGER) AS work_location_id,
            CAST(COALESCE({hours_expr}, prior_e.hours_worked, 0) AS INTEGER) AS hours_worked,
            CAST(COALESCE(prior_e.commute_mode, -1) AS INTEGER) AS commute_mode,
            CAST(ROUND(COALESCE(p.earning, 0.0) * {income_deflator}) AS BIGINT) AS income
        FROM demos_core_persons p
        LEFT JOIN prior_person_employment prior_e ON CAST(p.person_id AS BIGINT) = prior_e.person_id
        ORDER BY person_id ASC
    """).to_arrow_table()

    hh_income_expr = "COALESCE(h.income, 0.0)" if "income" in hh_cols else "0.0"
    income_table = con.execute(f"""
        WITH p_income AS (
            SELECT
                CAST(household_id AS BIGINT) AS household_id,
                SUM(COALESCE(earning, 0.0)) AS sum_earning
            FROM demos_core_persons
            GROUP BY CAST(household_id AS BIGINT)
        )
        SELECT
            CAST(h.household_id AS BIGINT) AS household_id,
            CAST(ROUND(
                CASE
                    WHEN {hh_income_expr} > 0 THEN {hh_income_expr} * {income_deflator}
                    ELSE COALESCE(pi.sum_earning, 0.0) * {income_deflator}
                END
            ) AS BIGINT) AS income
        FROM demos_core_households h
        LEFT JOIN p_income pi ON CAST(h.household_id AS BIGINT) = pi.household_id
        ORDER BY household_id ASC
    """).to_arrow_table()

    sf_expr = (
        """CASE LOWER(TRIM(CAST(h.sf_detached AS VARCHAR)))
               WHEN 'yes' THEN 1
               WHEN 'no' THEN 2
               ELSE NULL
           END"""
        if "sf_detached" in hh_cols
        else "NULL::INTEGER"
    )
    tenure_expr = (
        "TRY_CAST(h.tenure AS INTEGER)" if "tenure" in hh_cols else "NULL::INTEGER"
    )
    dwelling_table = con.execute(f"""
        SELECT
            CAST(h.household_id AS BIGINT) AS household_id,
            CAST(COALESCE({sf_expr}, prior_dw.housing_unit_type, 0) AS INTEGER) AS housing_unit_type,
            CAST(COALESCE({tenure_expr}, prior_dw.tenure, 0) AS INTEGER) AS tenure,
            CAST(COALESCE(prior_dw.has_residential_charging, 0) AS INTEGER) AS has_residential_charging,
            CAST(COALESCE(prior_dw.time_in_home, 0.0) AS DOUBLE) AS time_in_home
        FROM demos_core_households h
        LEFT JOIN prior_household_dwelling prior_dw ON CAST(h.household_id AS BIGINT) = prior_dw.household_id
        ORDER BY household_id ASC
    """).to_arrow_table()

    block_expr = (
        "NULLIF(TRIM(CAST(h.block_id AS VARCHAR)), '')"
        if "block_id" in hh_cols
        else "NULL::VARCHAR"
    )
    prior_block_expr = (
        "prior_loc.block" if "block" in prior_loc_cols else "NULL::VARCHAR"
    )
    location_table = con.execute(f"""
        SELECT
            CAST(h.household_id AS BIGINT) AS household_id,
            CAST(COALESCE(prior_loc.latitude, 0.0) AS DOUBLE) AS latitude,
            CAST(COALESCE(prior_loc.longitude, 0.0) AS DOUBLE) AS longitude,
            CAST(COALESCE(prior_loc.tract, TRY_CAST(SUBSTRING({block_expr}, 1, 11) AS BIGINT), 0) AS BIGINT) AS tract,
            CAST(COALESCE(prior_loc.block_group, TRY_CAST(SUBSTRING({block_expr}, 12, 1) AS INTEGER), 0) AS INTEGER) AS block_group,
            CAST(COALESCE({block_expr}, {prior_block_expr}, '') AS VARCHAR) AS block,
            CAST(COALESCE(prior_loc.taz, 0) AS INTEGER) AS taz
        FROM demos_core_households h
        LEFT JOIN prior_household_location prior_loc ON CAST(h.household_id AS BIGINT) = prior_loc.household_id
        ORDER BY household_id ASC
    """).to_arrow_table()

    facets: dict[str, pa.Table] = {
        "households": households_table,
        "people": people_table,
        "household_membership": membership_table,
        "person_demographics": demographics_table,
        "person_schooling": schooling_table,
        "person_employment": employment_table,
        "household_income": income_table,
        "household_dwelling": dwelling_table,
        "household_location": location_table,
    }

    file_paths: dict[str, Path] = {}
    if output_dir is not None:
        out_p = Path(output_dir)
        out_p.mkdir(parents=True, exist_ok=True)
        for name, table in facets.items():
            fpath = out_p / f"{name}.parquet"
            pq.write_table(table, fpath)
            file_paths[name] = fpath

    digests = {
        name: compute_tabular_digest(
            source=table,
            columns=CORE_FACET_COLUMNS[name],
            key_columns=CORE_FACET_KEY_COLUMNS[name],
            profile="core_facet_table/v1",
        )
        for name, table in facets.items()
    }

    return {
        "facets": facets,
        "file_paths": file_paths,
        "classification": classification,
        "digests": digests,
    }


def project_demos_core_from_core(
    core_facets: Mapping[str, Path | str | pa.Table | duckdb.DuckDBPyRelation],
    duckdb_con: duckdb.DuckDBPyConnection | None = None,
) -> dict[str, pa.Table]:
    """Project Synergy Core facets into core DEMOS native ``persons`` and ``households`` tables."""
    con = duckdb_con or duckdb.connect()

    for facet_name in [
        "households",
        "people",
        "household_membership",
        "person_demographics",
        "person_schooling",
        "person_employment",
        "household_income",
        "household_dwelling",
        "household_location",
    ]:
        if facet_name in core_facets:
            _register_input(con, f"core_{facet_name}", core_facets[facet_name])
        else:
            con.register(f"core_{facet_name}", _empty_extended_facet(facet_name))

    core_loc_cols = _table_columns(con, "core_household_location")
    block_select = (
        "COALESCE(NULLIF(loc.block, ''), '')" if "block" in core_loc_cols else "''"
    )

    persons_table = con.execute("""
        SELECT
            CAST(p.person_id AS BIGINT) AS person_id,
            CAST(m.household_id AS BIGINT) AS household_id,
            CAST(COALESCE(d.age, 0) AS INTEGER) AS age,
            CAST(COALESCE(d.sex, 1) AS INTEGER) AS sex,
            CAST(COALESCE(d.relate, 0) AS INTEGER) AS relate,
            CAST(CASE WHEN d.relate IN (0, 1) THEN 1 ELSE 5 END AS INTEGER) AS MAR,
            CAST(COALESCE(s.education_level, 0) AS INTEGER) AS edu,
            CAST(COALESCE(e.income, 0) AS DOUBLE) AS earning,
            CAST(COALESCE(e.employment_status, 0) AS INTEGER) AS worker,
            CAST(COALESCE(s.school_status, 0) AS INTEGER) AS student,
            CAST(0 AS INTEGER) AS work_at_home,
            CAST(COALESCE(d.race, 1) AS INTEGER) AS race_id,
            CASE COALESCE(d.race, 1)
                WHEN 1 THEN 'white'
                WHEN 2 THEN 'black'
                WHEN 6 THEN 'asian'
                ELSE 'other'
            END AS race,
            CAST(COALESCE(e.hours_worked, 0) AS DOUBLE) AS hours,
            CAST(COALESCE(s.school_location_id, -1) AS VARCHAR) AS school_zone_id,
            CAST(COALESCE(e.work_location_id, -1) AS VARCHAR) AS work_zone_id,
            CAST(COALESCE(d.hispanic, 0) AS INTEGER) AS hispanic,
            CASE WHEN COALESCE(d.sex, 1) = 1 THEN 'male' ELSE 'female' END AS person_sex
        FROM core_people p
        JOIN core_household_membership m ON p.person_id = m.person_id
        LEFT JOIN core_person_demographics d ON p.person_id = d.person_id
        LEFT JOIN core_person_schooling s ON p.person_id = s.person_id
        LEFT JOIN core_person_employment e ON p.person_id = e.person_id
        ORDER BY person_id ASC
    """).to_arrow_table()

    households_table = con.execute(f"""
        WITH hh_agg AS (
            SELECT
                m.household_id,
                COUNT(*) AS persons,
                SUM(CASE WHEN COALESCE(e.employment_status, 0) = 1 THEN 1 ELSE 0 END) AS workers,
                MAX(CASE WHEN d.relate = 0 THEN d.age END) AS age_of_head,
                MAX(CASE WHEN d.relate = 0 THEN d.race END) AS race_of_head
            FROM core_household_membership m
            LEFT JOIN core_person_demographics d ON m.person_id = d.person_id
            LEFT JOIN core_person_employment e ON m.person_id = e.person_id
            GROUP BY m.household_id
        )
        SELECT
            CAST(h.household_id AS BIGINT) AS household_id,
            CASE
                WHEN LENGTH({block_select}) >= 5 THEN SUBSTRING({block_select}, 1, 5)
                ELSE '00000'
            END AS lcm_county_id,
            {block_select} AS block_id,
            CAST(COALESCE(inc.income, 0) AS BIGINT) AS income,
            CAST(COALESCE(agg.persons, 0) AS BIGINT) AS persons,
            CAST(COALESCE(agg.workers, 0) AS BIGINT) AS workers,
            CAST(COALESCE(agg.age_of_head, 0) AS BIGINT) AS age_of_head,
            CAST(COALESCE(agg.race_of_head, 1) AS BIGINT) AS race_of_head,
            CASE COALESCE(dw.housing_unit_type, 0)
                WHEN 1 THEN 'yes'
                WHEN 2 THEN 'no'
                ELSE 'unknown'
            END AS sf_detached,
            CAST(COALESCE(dw.tenure, -1) AS VARCHAR) AS tenure
        FROM core_households h
        LEFT JOIN hh_agg agg ON h.household_id = agg.household_id
        LEFT JOIN core_household_income inc ON h.household_id = inc.household_id
        LEFT JOIN core_household_dwelling dw ON h.household_id = dw.household_id
        LEFT JOIN core_household_location loc ON h.household_id = loc.household_id
        ORDER BY household_id ASC
    """).to_arrow_table()

    return {
        "persons": persons_table,
        "households": households_table,
    }
