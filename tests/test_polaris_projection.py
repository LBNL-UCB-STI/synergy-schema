"""Tests for Core-In, POLARIS-Out minimal projection pipeline."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pyarrow as pa
import pytest

from synergy_schema.pipeline.polaris_projection import (
    POLARIS_DEMAND_COLUMNS,
    project_core_to_polaris,
)


@pytest.fixture
def sample_core_facets() -> dict[str, pa.Table]:
    """Build a deterministic synthetic core facet extract spanning diverse household types."""
    # Households:
    # 101: Married family (head M age 40, spouse F age 38, kid M age 10), owns home, 2 cars, 2 workers
    # 102: Single mother (head F age 32, kid F age 7), rents home, 1 car, 1 worker
    # 103: Single adult (head M age 26), rents home, 0 cars, 1 worker
    # 104: Nonfamily roommates (head M age 28, roommate M age 29), rents home, 1 car, 2 workers
    # 105: Group quarters (person 501), GQ, 0 cars, 0 workers

    households = pa.table(
        {
            "household_id": [101, 102, 103, 104, 105],
        }
    )

    people = pa.table(
        {
            "person_id": [1001, 1002, 1003, 2001, 2002, 3001, 4001, 4002, 5001],
        }
    )

    household_membership = pa.table(
        {
            "person_id": [1001, 1002, 1003, 2001, 2002, 3001, 4001, 4002, 5001],
            "household_id": [101, 101, 101, 102, 102, 103, 104, 104, 105],
        }
    )

    vehicles = pa.table(
        {
            "household_id": [101, 101, 102, 104],
            "vehicle_id": [1, 2, 1, 1],
            "type_id": [12, 14, 5, 8],
        }
    )

    household_location = pa.table(
        {
            "household_id": [101, 102, 103, 104, 105],
            "latitude": [30.2672, 30.2700, 30.2800, 30.2900, 30.3000],
            "longitude": [-97.7431, -97.7400, -97.7500, -97.7600, -97.7700],
            "tract": [48453000100, 48453000200, 48453000300, 48453000400, 48453000500],
            "block_group": [1, 2, 1, 3, 1],
            "taz": [501, 502, 503, 504, 505],
        }
    )

    person_demographics = pa.table(
        {
            "person_id": [1001, 1002, 1003, 2001, 2002, 3001, 4001, 4002, 5001],
            "age": [40, 38, 10, 32, 7, 26, 28, 29, 68],
            "sex": [1, 2, 1, 2, 2, 1, 1, 1, 1],  # 1=M, 2=F
            "race": [1, 1, 1, 2, 2, 1, 3, 3, 1],
            "hispanic": [0, 0, 0, 0, 0, 1, 0, 0, 0],
            "relate": [
                0,
                1,
                2,
                0,
                2,
                0,
                0,
                12,
                16,
            ],  # 0=head, 1=spouse, 2=child, 12=roommate, 16=GQ
        }
    )

    household_dwelling = pa.table(
        {
            "household_id": [101, 102, 103, 104, 105],
            "housing_unit_type": [
                1,
                2,
                3,
                2,
                5,
            ],  # 1=Single family, 2=Small apt, 3=Large apt, 5=GQ
            "tenure": [1, 2, 2, 2, 2],  # 1=Own, 2=Rent
            "has_residential_charging": [1, 0, 0, 0, 0],
            "time_in_home": [5.5, 2.0, 1.0, 0.5, 4.0],
        }
    )

    person_schooling = pa.table(
        {
            "person_id": [1001, 1002, 1003, 2001, 2002, 3001, 4001, 4002, 5001],
            "school_status": [1, 1, 2, 1, 2, 1, 1, 1, 1],  # 1=not enrolled, 2=public
            "school_location_id": [-1, -1, 301, -1, 302, -1, -1, -1, -1],
            "education_level": [21, 21, 5, 19, 2, 20, 21, 22, 16],
            "school_grade_level": [0, 0, 5, 0, 2, 0, 0, 0, 0],
        }
    )

    person_employment = pa.table(
        {
            "person_id": [1001, 1002, 1003, 2001, 2002, 3001, 4001, 4002, 5001],
            "employment_status": [
                1,
                1,
                0,
                1,
                0,
                1,
                1,
                1,
                6,
            ],  # 1=at work, 0=under 16, 6=not in LF
            "worker_type": [1, 2, 0, 1, 0, 1, 1, 2, 0],
            "industry": [7380, 7860, 0, 6870, 0, 8190, 7290, 7380, 0],
            "work_location_id": [801, 802, -1, 803, -1, 804, 805, 806, -1],
            "hours_worked": [40, 35, 0, 40, 0, 45, 40, 50, 0],
            "commute_mode": [1, 1, 0, 1, 0, 2, 1, 1, 0],
            "income": [85000, 72000, 0, 45000, 0, 52000, 65000, 78000, 18000],
        }
    )

    household_income = pa.table(
        {
            "household_id": [101, 102, 103, 104, 105],
            "income": [157000, 45000, 52000, 143000, 18000],
        }
    )

    return {
        "households": households,
        "people": people,
        "household_membership": household_membership,
        "vehicles": vehicles,
        "household_location": household_location,
        "person_demographics": person_demographics,
        "household_dwelling": household_dwelling,
        "person_schooling": person_schooling,
        "person_employment": person_employment,
        "household_income": household_income,
    }


def test_polaris_projection_executes_and_verifies_conformance(
    sample_core_facets: dict[str, pa.Table],
) -> None:
    """Validate that project_core_to_polaris creates valid Demand.sqlite satisfying POLARIS specs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_sqlite = Path(tmp_dir) / "Demand.sqlite"

        result = project_core_to_polaris(sample_core_facets, output_sqlite)

        assert result["row_counts"]["Household"] == 5
        assert result["row_counts"]["Person"] == 9
        assert result["row_counts"]["Vehicle"] == 4

        # Verify digests
        assert "Household" in result["digests"]
        assert "Person" in result["digests"]
        assert "Vehicle" in result["digests"]
        for tbl, digest in result["digests"].items():
            assert digest.startswith("sha256:"), f"Invalid digest format for {tbl}"

        # Connect and inspect sqlite data
        with sqlite3.connect(output_sqlite) as con:
            cur = con.cursor()

            # Verify Household columns
            cur.execute("PRAGMA table_info(Household);")
            hh_cols = [r[1] for r in cur.fetchall()]
            assert hh_cols == POLARIS_DEMAND_COLUMNS["Household"]

            # Check specific household derivations:
            # 101: married couple family, owner -> type = 1, persons = 3, workers = 2, vehicles = 2
            hh101 = cur.execute(
                "SELECT persons, workers, vehicles, type, income, Has_Residential_Charging FROM Household WHERE household = 101;"
            ).fetchone()
            assert hh101 == (3, 2, 2, 1, 157000, 1)

            # 102: female head relative family, renter -> type = 8, persons = 2, workers = 1, vehicles = 1
            hh102 = cur.execute(
                "SELECT persons, workers, vehicles, type, income FROM Household WHERE household = 102;"
            ).fetchone()
            assert hh102 == (2, 1, 1, 8, 45000)

            # 103: single living alone, renter -> type = 9, persons = 1, workers = 1, vehicles = 0
            hh103 = cur.execute(
                "SELECT persons, workers, vehicles, type, vehicles FROM Household WHERE household = 103;"
            ).fetchone()
            assert hh103 == (1, 1, 0, 9, 0)

            # 104: nonfamily roommates, renter -> type = 10, persons = 2, workers = 2, vehicles = 1
            hh104 = cur.execute(
                "SELECT persons, workers, vehicles, type FROM Household WHERE household = 104;"
            ).fetchone()
            assert hh104 == (2, 2, 1, 10)

            # 105: group quarters -> type = 11
            hh105 = cur.execute(
                "SELECT type, housing_unit_type FROM Household WHERE household = 105;"
            ).fetchone()
            assert hh105 == (11, 5)

            # Verify Person columns
            cur.execute("PRAGMA table_info(Person);")
            p_cols = [r[1] for r in cur.fetchall()]
            assert p_cols == POLARIS_DEMAND_COLUMNS["Person"]

            # Check within-household person id (0..n-1)
            p_ids_101 = cur.execute(
                "SELECT id, age, person FROM Person WHERE household = 101 ORDER BY id ASC;"
            ).fetchall()
            assert [r[0] for r in p_ids_101] == [0, 1, 2]
            # Head (relate=0, age 40) is id 0, spouse (relate=1, age 38) is id 1, child (relate=2, age 10) is id 2
            assert p_ids_101[0][2] == 1001
            assert p_ids_101[1][2] == 1002
            assert p_ids_101[2][2] == 1003

            # Check Vehicle columns
            cur.execute("PRAGMA table_info(Vehicle);")
            v_cols = [r[1] for r in cur.fetchall()]
            assert v_cols == POLARIS_DEMAND_COLUMNS["Vehicle"]

            # Check vehicle rows
            v_rows = cur.execute(
                "SELECT vehicle_id, hhold, type FROM Vehicle ORDER BY vehicle_id ASC;"
            ).fetchall()
            assert len(v_rows) == 4


def test_polaris_projection_works_with_parquet_files(
    sample_core_facets: dict[str, pa.Table],
) -> None:
    """Validate that projection works when facets are supplied as Parquet files on disk."""
    import pyarrow.parquet as pq

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        parquet_facets = {}
        for facet_name, table in sample_core_facets.items():
            p = tmp_path / f"{facet_name}.parquet"
            pq.write_table(table, p)
            parquet_facets[facet_name] = p

        output_sqlite = tmp_path / "Demand.sqlite"
        result = project_core_to_polaris(parquet_facets, output_sqlite)

        assert result["row_counts"]["Household"] == 5
        assert result["row_counts"]["Person"] == 9
        assert result["row_counts"]["Vehicle"] == 4


def test_polaris_projection_detects_referential_integrity_violation(
    sample_core_facets: dict[str, pa.Table],
) -> None:
    """Ensure projection raises error if persons or vehicles belong to nonexistent households."""
    # Break referential integrity by adding a person in non-existent household 999
    bad_membership = pa.table(
        {
            "person_id": [1001, 1002, 1003, 2001, 2002, 3001, 4001, 4002, 5001, 9999],
            "household_id": [101, 101, 101, 102, 102, 103, 104, 104, 105, 999],
        }
    )
    bad_people = pa.table(
        {
            "person_id": [1001, 1002, 1003, 2001, 2002, 3001, 4001, 4002, 5001, 9999],
        }
    )

    facets = dict(sample_core_facets)
    facets["household_membership"] = bad_membership
    facets["people"] = bad_people

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_sqlite = Path(tmp_dir) / "Demand.sqlite"
        with pytest.raises(
            ValueError, match="Referential integrity failure.*orphan persons"
        ):
            project_core_to_polaris(facets, output_sqlite)


def test_projected_sqlite_matches_linkml_schema(
    sample_core_facets: dict[str, pa.Table],
) -> None:
    """Ensure projected SQLite table attributes match the LinkML schema exactly."""
    from linkml_runtime.utils.schemaview import SchemaView

    schema_path = (
        Path(__file__).parents[1]
        / "src"
        / "synergy_schema"
        / "schema"
        / "models"
        / "polaris"
        / "polaris_demand_database_v1.yaml"
    )
    view = SchemaView(str(schema_path))

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_sqlite = Path(tmp_dir) / "Demand.sqlite"
        project_core_to_polaris(sample_core_facets, output_sqlite)

        with sqlite3.connect(output_sqlite) as con:
            cur = con.cursor()
            mapping = {
                "Household": "PolarisDemandDatabaseHousehold",
                "Person": "PolarisDemandDatabasePerson",
                "Vehicle": "PolarisDemandDatabaseVehicle",
            }
            for tbl, cls_name in mapping.items():
                cur.execute(f"PRAGMA table_info({tbl});")
                db_cols = {r[1] for r in cur.fetchall()}

                induced_cls = view.induced_class(cls_name)
                schema_cols = {
                    slot.annotations["physical_name"].value
                    for slot in induced_cls.attributes.values()
                    if "physical_name" in slot.annotations
                }

                assert db_cols == schema_cols, (
                    f"Mismatch for {tbl}: {db_cols.symmetric_difference(schema_cols)}"
                )


def test_polaris_projection_with_real_austin_sample() -> None:
    """Extract 20 households from the reference Austin demand db, project them, and assert fidelity."""
    db_path = (
        Path(__file__).parents[1]
        / "evidence"
        / "demos_input_population_from_polaris"
        / "Austin-Demand_incl_relp_hh_matches_acs.sqlite"
    )
    if not db_path.exists():
        pytest.skip(f"Reference database not found at {db_path}")

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    cur.execute(
        "SELECT household, location, type, income, housing_unit_type, Has_Residential_Charging, time_in_home FROM Household LIMIT 20;"
    )
    hh_rows = cur.fetchall()
    hh_ids = [r[0] for r in hh_rows]
    hh_id_str = ",".join(str(i) for i in hh_ids)

    cur.execute(
        f"SELECT person, household, id, age, gender, relp, race, education, school_enrollment, school_grade_level, school_location_id, employment, worker_class, industry, work_location_id, work_hours, journey_to_work_mode, income FROM Person WHERE household IN ({hh_id_str});"
    )
    p_rows = cur.fetchall()

    cur.execute(
        f"SELECT vehicle_id, hhold, type FROM Vehicle WHERE hhold IN ({hh_id_str});"
    )
    v_rows = cur.fetchall()

    # Build core facets
    facets = {
        "households": pa.table({"household_id": hh_ids}),
        "people": pa.table({"person_id": [r[0] for r in p_rows]}),
        "household_membership": pa.table(
            {
                "person_id": [r[0] for r in p_rows],
                "household_id": [r[1] for r in p_rows],
            }
        ),
        "vehicles": pa.table(
            {
                "vehicle_id": [r[0] for r in v_rows],
                "household_id": [r[1] for r in v_rows],
                "type_id": [r[2] for r in v_rows],
            }
        ),
        "household_location": pa.table(
            {
                "household_id": hh_ids,
                "latitude": [0.0] * 20,
                "longitude": [0.0] * 20,
                "tract": [0] * 20,
                "block_group": [0] * 20,
                "taz": [r[1] for r in hh_rows],
            }
        ),
        "person_demographics": pa.table(
            {
                "person_id": [r[0] for r in p_rows],
                "age": [r[3] for r in p_rows],
                "sex": [r[4] for r in p_rows],
                "relate": [r[5] for r in p_rows],
                "race": [r[6] for r in p_rows],
                "hispanic": [0] * len(p_rows),
            }
        ),
        "household_dwelling": pa.table(
            {
                "household_id": hh_ids,
                "housing_unit_type": [r[4] for r in hh_rows],
                "tenure": [1 if r[2] <= 5 else 2 for r in hh_rows],
                "has_residential_charging": [r[5] for r in hh_rows],
                "time_in_home": [r[6] for r in hh_rows],
            }
        ),
        "person_schooling": pa.table(
            {
                "person_id": [r[0] for r in p_rows],
                "education_level": [r[7] for r in p_rows],
                "school_status": [r[8] for r in p_rows],
                "school_grade_level": [r[9] for r in p_rows],
                "school_location_id": [r[10] for r in p_rows],
            }
        ),
        "person_employment": pa.table(
            {
                "person_id": [r[0] for r in p_rows],
                "employment_status": [r[11] for r in p_rows],
                "worker_type": [r[12] for r in p_rows],
                "industry": [r[13] for r in p_rows],
                "work_location_id": [r[14] for r in p_rows],
                "hours_worked": [r[15] for r in p_rows],
                "commute_mode": [r[16] for r in p_rows],
                "income": [r[17] for r in p_rows],
            }
        ),
        "household_income": pa.table(
            {"household_id": hh_ids, "income": [r[3] for r in hh_rows]}
        ),
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = Path(tmp_dir) / "Demand.sqlite"
        res = project_core_to_polaris(facets, out_path)

        assert res["row_counts"]["Household"] == 20
        assert res["row_counts"]["Person"] == len(p_rows)
        assert res["row_counts"]["Vehicle"] == len(v_rows)

        proj_con = sqlite3.connect(out_path)
        proj_cur = proj_con.cursor()
        proj_cur.execute(
            "SELECT household, type, persons, workers, vehicles, income FROM Household ORDER BY household ASC;"
        )
        proj_hhs = {r[0]: r[1:] for r in proj_cur.fetchall()}

        orig_cur = con.cursor()
        orig_cur.execute(
            f"SELECT household, type, persons, workers, vehicles, income FROM Household WHERE household IN ({hh_id_str}) ORDER BY household ASC;"
        )
        orig_hhs = {r[0]: r[1:] for r in orig_cur.fetchall()}

        for hid in hh_ids:
            assert proj_hhs[hid] == orig_hhs[hid], (
                f"Household {hid} attribute divergence"
            )
