"""POLARIS Demand Database projection module.

Executes 'Core-In, POLARIS-Out' projection from Synergy core population facets
to POLARIS Demand.sqlite tables (Household, Person, Vehicle) using DuckDB SQL.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa

from synergy_schema.conformance.tabular_digest import compute_tabular_digest
from synergy_schema.pipeline.contract_tables import load_and_register_contract_tables

POLARIS_DEMAND_DDL: dict[str, str] = {
    "Household": """
CREATE TABLE Household (
    household INTEGER PRIMARY KEY,
    hhold INTEGER NOT NULL,
    location INTEGER NOT NULL,
    persons INTEGER NOT NULL,
    workers INTEGER NOT NULL,
    vehicles INTEGER NOT NULL,
    type INTEGER NOT NULL,
    income INTEGER NOT NULL,
    bikes INTEGER NOT NULL,
    housing_unit_type INTEGER NOT NULL,
    ecom INTEGER NOT NULL,
    delRat REAL,
    dispose_veh INTEGER,
    Has_Residential_Charging INTEGER NOT NULL,
    num_groceries INTEGER NOT NULL,
    num_meals INTEGER NOT NULL,
    time_in_home REAL
);
""",
    "Person": """
CREATE TABLE Person (
    person INTEGER PRIMARY KEY,
    household INTEGER NOT NULL,
    id INTEGER NOT NULL,
    school_location_id INTEGER NOT NULL,
    work_location_id INTEGER NOT NULL,
    age INTEGER NOT NULL,
    worker_class INTEGER NOT NULL,
    education INTEGER NOT NULL,
    industry INTEGER NOT NULL,
    employment INTEGER NOT NULL,
    gender INTEGER NOT NULL,
    income INTEGER NOT NULL,
    journey_to_work_arrival_time INTEGER NOT NULL,
    journey_to_work_mode INTEGER NOT NULL,
    journey_to_work_travel_time INTEGER NOT NULL,
    journey_to_work_vehicle_occupancy INTEGER NOT NULL,
    marital_status INTEGER NOT NULL,
    race INTEGER NOT NULL,
    school_enrollment INTEGER NOT NULL,
    school_grade_level INTEGER NOT NULL,
    work_hours INTEGER NOT NULL,
    telecommute_level INTEGER NOT NULL,
    transit_pass INTEGER,
    disability INTEGER NOT NULL,
    time_in_job REAL,
    is_long_term_chooser INTEGER,
    escooter_use_level INTEGER NOT NULL
);
""",
    "Vehicle": """
CREATE TABLE Vehicle (
    vehicle_id INTEGER PRIMARY KEY,
    hhold INTEGER NOT NULL,
    parking INTEGER NOT NULL,
    L3_wtp INTEGER NOT NULL,
    L4_wtp INTEGER NOT NULL,
    type INTEGER,
    fleet INTEGER,
    subtype INTEGER NOT NULL
);
""",
}

POLARIS_DEMAND_COLUMNS: dict[str, list[str]] = {
    "Household": [
        "household",
        "hhold",
        "location",
        "persons",
        "workers",
        "vehicles",
        "type",
        "income",
        "bikes",
        "housing_unit_type",
        "ecom",
        "delRat",
        "dispose_veh",
        "Has_Residential_Charging",
        "num_groceries",
        "num_meals",
        "time_in_home",
    ],
    "Person": [
        "person",
        "household",
        "id",
        "school_location_id",
        "work_location_id",
        "age",
        "worker_class",
        "education",
        "industry",
        "employment",
        "gender",
        "income",
        "journey_to_work_arrival_time",
        "journey_to_work_mode",
        "journey_to_work_travel_time",
        "journey_to_work_vehicle_occupancy",
        "marital_status",
        "race",
        "school_enrollment",
        "school_grade_level",
        "work_hours",
        "telecommute_level",
        "transit_pass",
        "disability",
        "time_in_job",
        "is_long_term_chooser",
        "escooter_use_level",
    ],
    "Vehicle": [
        "vehicle_id",
        "hhold",
        "parking",
        "L3_wtp",
        "L4_wtp",
        "type",
        "fleet",
        "subtype",
    ],
}

POLARIS_DEMAND_KEY_COLUMNS: dict[str, list[str]] = {
    "Household": ["household"],
    "Person": ["person"],
    "Vehicle": ["vehicle_id"],
}


HOUSEHOLD_PROJECTION_SQL = """
WITH hh_members AS (
    SELECT
        m.household_id,
        count(m.person_id) AS persons,
        sum(coalesce(x_p2.is_at_work, 0)) AS workers,
        max(CASE WHEN coalesce(d.relate, 99) = 1 THEN 1 ELSE 0 END) AS has_spouse,
        max(CASE WHEN coalesce(d.relate, 99) BETWEEN 2 AND 10 THEN 1 ELSE 0 END) AS has_other_relative,
        max(CASE WHEN coalesce(d.relate, 99) = 0 THEN coalesce(d.sex, 1) ELSE NULL END) AS head_gender
    FROM household_membership m
    LEFT JOIN person_demographics d ON m.person_id = d.person_id
    LEFT JOIN person_employment e ON m.person_id = e.person_id
    LEFT JOIN _contract_crosswalk_x_p2 x_p2 ON coalesce(e.employment_status, 0) = x_p2.employment_status
    GROUP BY m.household_id
),
hh_vehicles AS (
    SELECT
        household_id,
        count(vehicle_id) AS vehicles
    FROM vehicles
    GROUP BY household_id
),
hh_composition AS (
    SELECT
        h.household_id,
        loc.taz,
        dw.housing_unit_type,
        dw.tenure,
        dw.has_residential_charging,
        dw.time_in_home,
        inc.income,
        mem.persons,
        mem.workers,
        veh.vehicles,
        CASE
            WHEN coalesce(dw.housing_unit_type, def.housing_unit_type) = 5 THEN 1
            ELSE 0
        END AS is_gq,
        CASE
            WHEN coalesce(dw.housing_unit_type, def.housing_unit_type) = 5 THEN 0
            WHEN coalesce(dw.tenure, 1) IN (1, 3) THEN 1
            ELSE 0
        END AS is_owner,
        CASE
            WHEN coalesce(dw.housing_unit_type, def.housing_unit_type) = 5 THEN 0
            WHEN coalesce(mem.has_spouse, 0) = 1 THEN 1
            WHEN coalesce(mem.has_other_relative, 0) = 1 THEN
                CASE WHEN coalesce(mem.head_gender, 1) = 1 THEN 2 ELSE 3 END
            WHEN coalesce(mem.persons, 1) = 1 THEN 4
            ELSE 5
        END AS hht
    FROM households h
    CROSS JOIN _contract_defaults_household def
    LEFT JOIN household_location loc ON h.household_id = loc.household_id
    LEFT JOIN household_dwelling dw ON h.household_id = dw.household_id
    LEFT JOIN household_income inc ON h.household_id = inc.household_id
    LEFT JOIN hh_members mem ON h.household_id = mem.household_id
    LEFT JOIN hh_vehicles veh ON h.household_id = veh.household_id
)
SELECT
    c.household_id AS household,
    c.household_id AS hhold,
    coalesce(c.taz, def.location) AS location,
    coalesce(c.persons, 0) AS persons,
    coalesce(c.workers, 0) AS workers,
    coalesce(c.vehicles, 0) AS vehicles,
    x_h2.polaris_type AS type,
    coalesce(c.income, 0) AS income,
    def.bikes AS bikes,
    coalesce(c.housing_unit_type, def.housing_unit_type) AS housing_unit_type,
    def.ecom AS ecom,
    def.delRat AS delRat,
    def.dispose_veh AS dispose_veh,
    coalesce(c.has_residential_charging, def.Has_Residential_Charging) AS Has_Residential_Charging,
    def.num_groceries AS num_groceries,
    def.num_meals AS num_meals,
    coalesce(c.time_in_home, def.time_in_home) AS time_in_home
FROM hh_composition c
CROSS JOIN _contract_defaults_household def
LEFT JOIN _contract_crosswalk_x_h2 x_h2
    ON c.is_gq = x_h2.is_gq
    AND c.is_owner = x_h2.is_owner
    AND c.hht = x_h2.hht
ORDER BY c.household_id ASC
"""

PERSON_PROJECTION_SQL = """
SELECT
    p.person_id AS person,
    m.household_id AS household,
    (ROW_NUMBER() OVER (
        PARTITION BY m.household_id
        ORDER BY
            coalesce(d.relate, 99) ASC,
            coalesce(d.age, 0) DESC,
            p.person_id ASC
    ) - 1) AS id,
    coalesce(s.school_location_id, def.school_location_id) AS school_location_id,
    coalesce(e.work_location_id, def.work_location_id) AS work_location_id,
    coalesce(d.age, 0) AS age,
    coalesce(e.worker_type, def.worker_class) AS worker_class,
    coalesce(s.education_level, 0) AS education,
    coalesce(e.industry, def.industry) AS industry,
    coalesce(e.employment_status, 0) AS employment,
    coalesce(d.sex, 1) AS gender,
    coalesce(e.income, 0) AS income,
    CASE
        WHEN coalesce(x_p2.is_at_work, 0) = 1 THEN x_p2.default_arrival_time
        ELSE def.journey_to_work_arrival_time
    END AS journey_to_work_arrival_time,
    coalesce(e.commute_mode, def.journey_to_work_mode) AS journey_to_work_mode,
    def.journey_to_work_travel_time AS journey_to_work_travel_time,
    CASE
        WHEN coalesce(x_p2.is_at_work, 0) = 1 THEN x_p2.default_vehicle_occupancy
        ELSE def.journey_to_work_vehicle_occupancy
    END AS journey_to_work_vehicle_occupancy,
    CASE
        WHEN coalesce(d.relate, 99) = 1 THEN 1
        WHEN coalesce(d.age, 0) < 15 THEN 5
        WHEN coalesce(d.relate, 99) = 0 THEN 1
        ELSE 5
    END AS marital_status,
    coalesce(d.race, def.race) AS race,
    coalesce(s.school_status, 1) AS school_enrollment,
    coalesce(s.school_grade_level, def.school_grade_level) AS school_grade_level,
    coalesce(e.hours_worked, def.work_hours) AS work_hours,
    def.telecommute_level AS telecommute_level,
    def.transit_pass AS transit_pass,
    def.disability AS disability,
    def.time_in_job AS time_in_job,
    def.is_long_term_chooser AS is_long_term_chooser,
    def.escooter_use_level AS escooter_use_level
FROM people p
CROSS JOIN _contract_defaults_person def
JOIN household_membership m ON p.person_id = m.person_id
LEFT JOIN person_demographics d ON p.person_id = d.person_id
LEFT JOIN person_schooling s ON p.person_id = s.person_id
LEFT JOIN person_employment e ON p.person_id = e.person_id
LEFT JOIN _contract_crosswalk_x_p2 x_p2 ON coalesce(e.employment_status, 0) = x_p2.employment_status
ORDER BY p.person_id ASC
"""

VEHICLE_PROJECTION_SQL = """
SELECT
    ROW_NUMBER() OVER (ORDER BY v.household_id ASC, v.vehicle_id ASC) AS vehicle_id,
    v.household_id AS hhold,
    def.parking AS parking,
    def.L3_wtp AS L3_wtp,
    def.L4_wtp AS L4_wtp,
    coalesce(v.type_id, def.type) AS type,
    def.fleet AS fleet,
    def.subtype AS subtype
FROM vehicles v
CROSS JOIN _contract_defaults_vehicle def
ORDER BY vehicle_id ASC
"""


def _register_facet(
    con: duckdb.DuckDBPyConnection,
    facet_name: str,
    source: Path | str | pa.Table | duckdb.DuckDBPyRelation,
) -> None:
    """Register a core facet in DuckDB connection."""
    if isinstance(source, (Path, str)):
        p = Path(source)
        if not p.exists():
            raise FileNotFoundError(f"Facet {facet_name} file not found: {p}")
        con.execute(
            f"CREATE OR REPLACE VIEW {facet_name} AS SELECT * FROM read_parquet('{p.as_posix()}');"
        )
    elif isinstance(source, pa.Table):
        con.register(facet_name, source)
    elif isinstance(source, duckdb.DuckDBPyRelation):
        con.register(facet_name, source.to_arrow_table())
    else:
        raise TypeError(
            f"Unsupported source type for facet {facet_name}: {type(source)}"
        )


def project_core_to_polaris(
    core_facets: Mapping[str, Path | str | pa.Table | duckdb.DuckDBPyRelation],
    output_sqlite_path: Path | str,
    duckdb_con: duckdb.DuckDBPyConnection | None = None,
    *,
    release_dir: Path | str | None = None,
    verify_contract_digest: bool = True,
) -> dict[str, Any]:
    """Project Synergy core facets into a POLARIS Demand.sqlite database.

    Args:
        core_facets: Mapping from facet names to Parquet path, PyArrow table, or DuckDB relation.
            Required facets:
              - households
              - people
              - household_membership
              - vehicles
              - household_location
              - person_demographics
              - household_dwelling
              - person_schooling
              - person_employment
              - household_income
        output_sqlite_path: Path to target SQLite database.
        duckdb_con: Optional existing DuckDB connection. If omitted, a fresh in-memory connection is used.
        release_dir: Optional path to mapping release directory containing population-translation-contract.yaml.
        verify_contract_digest: Whether to verify semantic_content_digest of the translation contract.

    Returns:
        Dict with table counts, digests, contract_tables metadata, and validation summaries.
    """
    out_path = Path(output_sqlite_path)
    if out_path.exists():
        out_path.unlink()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Initialize SQLite schema with exact POLARIS Demand DDL
    with sqlite3.connect(out_path) as s_con:
        s_cur = s_con.cursor()
        for ddl in POLARIS_DEMAND_DDL.values():
            s_cur.execute(ddl)
        s_con.commit()

    # 2. Connect DuckDB, compile contract lookup/default tables, and register core facets
    con = duckdb_con or duckdb.connect()
    contract_tables_meta = load_and_register_contract_tables(
        con, release_dir=release_dir, verify_digest=verify_contract_digest
    )
    for facet_name, source in core_facets.items():
        _register_facet(con, facet_name, source)

    if "vehicles" not in core_facets:
        con.execute("""
            CREATE OR REPLACE TEMP TABLE vehicles (
                vehicle_id BIGINT,
                household_id BIGINT,
                type_id INTEGER
            );
        """)

    # 3. Attach SQLite database
    con.execute(f"ATTACH '{out_path.as_posix()}' AS polaris (TYPE SQLITE);")

    # 4. Execute projections into polaris tables
    con.execute(f"INSERT INTO polaris.Household {HOUSEHOLD_PROJECTION_SQL};")
    con.execute(f"INSERT INTO polaris.Person {PERSON_PROJECTION_SQL};")
    con.execute(f"INSERT INTO polaris.Vehicle {VEHICLE_PROJECTION_SQL};")

    # Detach sqlite
    con.execute("DETACH polaris;")

    # 5. Conformance verification and tabular digest computation
    with sqlite3.connect(out_path) as s_con:
        s_cur = s_con.cursor()
        hh_count = s_cur.execute("SELECT count(*) FROM Household;").fetchone()[0]
        person_count = s_cur.execute("SELECT count(*) FROM Person;").fetchone()[0]
        vehicle_count = s_cur.execute("SELECT count(*) FROM Vehicle;").fetchone()[0]

        # Verify foreign keys
        orphan_persons = s_cur.execute(
            "SELECT count(*) FROM Person WHERE household NOT IN (SELECT household FROM Household);"
        ).fetchone()[0]
        orphan_vehicles = s_cur.execute(
            "SELECT count(*) FROM Vehicle WHERE hhold NOT IN (SELECT household FROM Household);"
        ).fetchone()[0]

    if orphan_persons > 0:
        raise ValueError(
            f"Referential integrity failure: {orphan_persons} orphan persons."
        )
    if orphan_vehicles > 0:
        raise ValueError(
            f"Referential integrity failure: {orphan_vehicles} orphan vehicles."
        )

    # 6. Compute canonical tabular digests
    digests = {}
    for table_name in ["Household", "Person", "Vehicle"]:
        digest = compute_tabular_digest(
            source=out_path,
            columns=POLARIS_DEMAND_COLUMNS[table_name],
            key_columns=POLARIS_DEMAND_KEY_COLUMNS[table_name],
            profile="view_table/v1",
            sqlite_table=table_name,
        )
        digests[table_name] = digest

    return {
        "output_path": out_path,
        "row_counts": {
            "Household": hh_count,
            "Person": person_count,
            "Vehicle": vehicle_count,
        },
        "digests": digests,
        "contract_tables": contract_tables_meta,
    }
