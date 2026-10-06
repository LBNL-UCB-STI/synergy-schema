"""DEMOS to Synergy Core population derivation pipeline.

Implements Stage 3 Task 3.2:
- Step 1: Record classification (surviving, new, removed households and persons).
- Step 2 & 7: Person demographics with race inheritance (preserving surviving race,
  assigning head race to new households, and inheriting head race for new members).
- Step 3: Household income deflation into base-year dollars.
- Step 12: Household spatial carried locations and membership keys.
- Tabular content hashing for each emitted core facet via core_facet_table/v1.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from synergy_schema.conformance.tabular_digest import compute_tabular_digest

CORE_FACET_COLUMNS: dict[str, list[str]] = {
    "households": ["household_id"],
    "people": ["person_id"],
    "household_membership": ["person_id", "household_id"],
    "person_demographics": ["person_id", "age", "sex", "race", "hispanic", "relate"],
    "household_location": [
        "household_id",
        "latitude",
        "longitude",
        "tract",
        "block_group",
        "taz",
    ],
    "household_income": ["household_id", "income"],
    "household_dwelling": [
        "household_id",
        "housing_unit_type",
        "tenure",
        "has_residential_charging",
        "time_in_home",
    ],
    "person_schooling": [
        "person_id",
        "school_status",
        "school_location_id",
        "education_level",
        "school_grade_level",
    ],
    "person_employment": [
        "person_id",
        "employment_status",
        "worker_type",
        "industry",
        "work_location_id",
        "hours_worked",
        "commute_mode",
        "income",
    ],
}

CORE_FACET_KEY_COLUMNS: dict[str, list[str]] = {
    "households": ["household_id"],
    "people": ["person_id"],
    "household_membership": ["person_id"],
    "person_demographics": ["person_id"],
    "household_location": ["household_id"],
    "household_income": ["household_id"],
    "household_dwelling": ["household_id"],
    "person_schooling": ["person_id"],
    "person_employment": ["person_id"],
}


def _register_input(
    con: duckdb.DuckDBPyConnection,
    view_name: str,
    source: Path | str | pa.Table | duckdb.DuckDBPyRelation,
) -> None:
    """Register an input table/file in DuckDB."""
    if isinstance(source, (str, Path)):
        p = Path(source)
        if not p.exists():
            raise FileNotFoundError(f"Input file for {view_name} not found: {p}")
        if p.suffix.lower() == ".csv":
            con.execute(
                f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_csv_auto('{p.as_posix()}');"
            )
        else:
            con.execute(
                f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_parquet('{p.as_posix()}');"
            )
    elif isinstance(source, pa.Table):
        con.register(view_name, source)
    elif isinstance(source, duckdb.DuckDBPyRelation):
        con.register(view_name, source.to_arrow_table())
    else:
        raise TypeError(f"Unsupported source type for {view_name}: {type(source)}")


def _empty_table_for_facet(facet_name: str) -> pa.Table:
    """Return an empty PyArrow table matching the facet schema."""
    cols = CORE_FACET_COLUMNS[facet_name]
    type_map: dict[str, pa.DataType] = {
        "household_id": pa.int64(),
        "person_id": pa.int64(),
        "age": pa.int32(),
        "sex": pa.int32(),
        "race": pa.int32(),
        "hispanic": pa.int32(),
        "relate": pa.int32(),
        "latitude": pa.float64(),
        "longitude": pa.float64(),
        "tract": pa.int64(),
        "block_group": pa.int32(),
        "taz": pa.int32(),
        "income": pa.int64(),
    }
    schema = pa.schema([pa.field(c, type_map[c]) for c in cols])
    return pa.Table.from_arrays(
        [pa.array([], type=type_map[c]) for c in cols], schema=schema
    )


def derive_core_from_demos(
    demos_households: Path | str | pa.Table | duckdb.DuckDBPyRelation,
    demos_persons: Path | str | pa.Table | duckdb.DuckDBPyRelation,
    prior_core_facets: Mapping[str, Path | str | pa.Table | duckdb.DuckDBPyRelation]
    | None = None,
    output_dir: Path | str | None = None,
    income_deflator: float = 1.0,
    duckdb_con: duckdb.DuckDBPyConnection | None = None,
) -> dict[str, Any]:
    """Execute Step 1 (classification), Step 2 & 7 (demographics & race inheritance),

    and Step 3 (income deflation) from DEMOS simulated outputs to Synergy Core facets.

    Args:
        demos_households: DEMOS household table or file.
        demos_persons: DEMOS person table or file.
        prior_core_facets: Optional mapping of prior year core facets (households, people,
            person_demographics, household_location, etc.) for longitudinal updates.
        output_dir: Optional path to save Parquet facet files.
        income_deflator: Deflation multiplier to convert simulation dollars to base year dollars.
        duckdb_con: Optional existing DuckDB connection.

    Returns:
        Dict with emitted facet tables, record classification counts, and tabular digests.
    """
    con = duckdb_con or duckdb.connect()

    # 1. Register current DEMOS inputs
    _register_input(con, "demos_households", demos_households)
    _register_input(con, "demos_persons", demos_persons)

    # 2. Register prior core facets or empty fallbacks
    prior_facets = prior_core_facets or {}
    for facet_name in [
        "households",
        "people",
        "person_demographics",
        "household_location",
    ]:
        if facet_name in prior_facets:
            _register_input(con, f"prior_{facet_name}", prior_facets[facet_name])
        else:
            con.register(f"prior_{facet_name}", _empty_table_for_facet(facet_name))

    # 3. Step 1: Record classification
    hh_counts = con.execute("""
        SELECT
            COUNT(CASE WHEN h.household IN (SELECT household_id FROM prior_households) THEN 1 END) AS surviving_hh,
            COUNT(CASE WHEN h.household NOT IN (SELECT household_id FROM prior_households) THEN 1 END) AS new_hh,
            (SELECT COUNT(*) FROM prior_households WHERE household_id NOT IN (SELECT household FROM demos_households)) AS removed_hh
        FROM demos_households h
    """).fetchone()

    person_counts = con.execute("""
        SELECT
            COUNT(CASE WHEN p.person IN (SELECT person_id FROM prior_people) THEN 1 END) AS surviving_persons,
            COUNT(CASE WHEN p.person NOT IN (SELECT person_id FROM prior_people) THEN 1 END) AS new_persons,
            (SELECT COUNT(*) FROM prior_people WHERE person_id NOT IN (SELECT person FROM demos_persons)) AS removed_persons
        FROM demos_persons p
    """).fetchone()

    classification = {
        "surviving_households": int(hh_counts[0]),
        "new_households": int(hh_counts[1]),
        "removed_households": int(hh_counts[2]),
        "surviving_persons": int(person_counts[0]),
        "new_persons": int(person_counts[1]),
        "removed_persons": int(person_counts[2]),
    }

    # 4. Core tables generation: households, people, household_membership
    households_table = con.execute("""
        SELECT DISTINCT CAST(household AS BIGINT) AS household_id
        FROM demos_households
        ORDER BY household_id ASC
    """).to_arrow_table()

    people_table = con.execute("""
        SELECT DISTINCT CAST(person AS BIGINT) AS person_id
        FROM demos_persons
        ORDER BY person_id ASC
    """).to_arrow_table()

    membership_table = con.execute("""
        SELECT
            CAST(person AS BIGINT) AS person_id,
            CAST(household AS BIGINT) AS household_id
        FROM demos_persons
        ORDER BY person_id ASC
    """).to_arrow_table()

    # 5. Step 2 & 7: Person Demographics with Race Inheritance
    # - Surviving persons preserve prior race and hispanic (preserve write policy)
    # - New head of household uses demos race_of_head
    # - New non-head inherits head race
    demographics_table = con.execute("""
        WITH curr_heads AS (
            SELECT
                p.household,
                COALESCE(
                    prior_d.race,
                    CAST(h.race_of_head AS INTEGER),
                    1
                ) AS head_race
            FROM demos_persons p
            LEFT JOIN demos_households h ON p.household = h.household
            LEFT JOIN prior_person_demographics prior_d ON p.person = prior_d.person_id
            WHERE p.relp = 0
        )
        SELECT
            CAST(p.person AS BIGINT) AS person_id,
            CAST(p.age AS INTEGER) AS age,
            CAST(p.gender AS INTEGER) AS sex,
            CAST(
                CASE
                    -- Surviving person preserves prior race
                    WHEN prior_d.race IS NOT NULL THEN prior_d.race
                    -- New head of household uses demos race_of_head
                    WHEN p.relp = 0 THEN COALESCE(CAST(h.race_of_head AS INTEGER), 1)
                    -- New non-head member inherits head's race
                    ELSE COALESCE(heads.head_race, 1)
                END AS INTEGER
            ) AS race,
            CAST(COALESCE(prior_d.hispanic, 0) AS INTEGER) AS hispanic,
            CAST(p.relp AS INTEGER) AS relate
        FROM demos_persons p
        LEFT JOIN demos_households h ON p.household = h.household
        LEFT JOIN prior_person_demographics prior_d ON p.person = prior_d.person_id
        LEFT JOIN curr_heads heads ON p.household = heads.household
        ORDER BY person_id ASC
    """).to_arrow_table()

    # 6. Step 3: Household Income Deflation
    income_table = con.execute(f"""
        WITH p_income AS (
            SELECT
                household,
                SUM(COALESCE(income, 0.0)) AS sum_income
            FROM demos_persons
            GROUP BY household
        )
        SELECT
            CAST(h.household AS BIGINT) AS household_id,
            CAST(ROUND(
                CASE
                    WHEN COALESCE(h.income, 0.0) > 0 THEN h.income * {income_deflator}
                    ELSE COALESCE(pi.sum_income, 0.0) * {income_deflator}
                END
            ) AS BIGINT) AS income
        FROM demos_households h
        LEFT JOIN p_income pi ON h.household = pi.household
        ORDER BY household_id ASC
    """).to_arrow_table()

    # 7. Step 12: Household Location (Preserve prior spatial assignment for surviving households)
    location_table = con.execute("""
        SELECT
            CAST(h.household AS BIGINT) AS household_id,
            CAST(COALESCE(prior_loc.latitude, 0.0) AS DOUBLE) AS latitude,
            CAST(COALESCE(prior_loc.longitude, 0.0) AS DOUBLE) AS longitude,
            CAST(COALESCE(prior_loc.tract, CAST(COALESCE(h.block_id, 0) / 10000 AS BIGINT), 0) AS BIGINT) AS tract,
            CAST(COALESCE(prior_loc.block_group, CAST(COALESCE(h.block_id, 0) % 1000 AS INTEGER), 0) AS INTEGER) AS block_group,
            CAST(COALESCE(prior_loc.taz, 0) AS INTEGER) AS taz
        FROM demos_households h
        LEFT JOIN prior_household_location prior_loc ON h.household = prior_loc.household_id
        ORDER BY household_id ASC
    """).to_arrow_table()

    facets: dict[str, pa.Table] = {
        "households": households_table,
        "people": people_table,
        "household_membership": membership_table,
        "person_demographics": demographics_table,
        "household_location": location_table,
        "household_income": income_table,
    }

    # 8. Optionally save Parquet files
    file_paths: dict[str, Path] = {}
    if output_dir is not None:
        out_p = Path(output_dir)
        out_p.mkdir(parents=True, exist_ok=True)
        for name, table in facets.items():
            fpath = out_p / f"{name}.parquet"
            pq.write_table(table, fpath)
            file_paths[name] = fpath

    # 9. Compute canonical tabular digests using core_facet_table/v1 profile
    digests: dict[str, str] = {}
    for name, table in facets.items():
        digest = compute_tabular_digest(
            source=table,
            columns=CORE_FACET_COLUMNS[name],
            key_columns=CORE_FACET_KEY_COLUMNS[name],
            profile="core_facet_table/v1",
        )
        digests[name] = digest

    return {
        "facets": facets,
        "file_paths": file_paths,
        "classification": classification,
        "digests": digests,
    }
