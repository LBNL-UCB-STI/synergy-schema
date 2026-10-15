"""Unit tests for DEMOS to Synergy Core derivation pipeline (Stage 3 Task 3.2)."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pyarrow as pa
import pytest

from synergy_schema.conformance.tabular_digest import compute_tabular_digest
from synergy_schema.pipeline.derive import (
    CORE_FACET_COLUMNS,
    CORE_FACET_KEY_COLUMNS,
    derive_core_from_demos,
)


def _sample_prior_and_current_data():
    """Create test data for longitudinal derivation:

    - Prior Year 1:
        - HH 101: Head 1001 (age 40, race 2)
        - HH 102: Head 2001 (age 30, race 1)
    - Current Year 2 DEMOS inputs:
        - HH 101 (surviving): Head 1001 (age 41), new child 1002 (relp 2, age 0)
        - HH 102 (removed)
        - HH 103 (new): Head 3001 (relp 0, age 25, race_of_head 3), spouse 3002 (relp 1, age 24)
    """
    prior_facets = {
        "households": pa.table({"household_id": [101, 102]}),
        "people": pa.table({"person_id": [1001, 2001]}),
        "household_membership": pa.table(
            {
                "person_id": [1001, 2001],
                "household_id": [101, 102],
            }
        ),
        "person_demographics": pa.table(
            {
                "person_id": [1001, 2001],
                "age": [40, 30],
                "sex": [1, 2],
                "race": [2, 1],
                "hispanic": [0, 1],
                "relate": [0, 0],
            }
        ),
        "household_location": pa.table(
            {
                "household_id": [101, 102],
                "latitude": [30.123, 30.456],
                "longitude": [-97.123, -97.456],
                "tract": [48453000100, 48453000200],
                "block_group": [1, 2],
                "taz": [10, 20],
            }
        ),
    }

    demos_households = pa.table(
        {
            "household": [101, 103],
            "block_id": [48053960800, 48053960900],
            "lcm_county_id": [48053, 48053],
            "age_of_head": [41.0, 25.0],
            "workers": [1.0, 2.0],
            "race_of_head": [2.0, 3.0],
            "income": [60000.0, 80000.0],
            "persons": [2, 2],
            "is_reorg_household": [False, False],
        }
    )

    demos_persons = pa.table(
        {
            "person": [1001, 1002, 3001, 3002],
            "relp": [0, 2, 0, 1],
            "gender": [1, 2, 1, 2],
            "education": [21, 0, 19, 20],
            "income": [60000.0, 0.0, 40000.0, 40000.0],
            "id": [0.0, 1.0, 0.0, 1.0],
            "age": [41, 0, 25, 24],
            "household": [101, 101, 103, 103],
            "marital_status": [1, 5, 1, 1],
            "employment": [1.0, 0.0, 1.0, 1.0],
            "school_enrollment": [1.0, 0.0, 1.0, 1.0],
        }
    )

    return prior_facets, demos_households, demos_persons


def test_demos_derivation_longitudinal_transition(tmp_path):
    """Verify Step 1 classification, Step 2/7 race inheritance, Step 3 income deflation,

    and Step 12 location preservation across years.
    """
    prior_facets, demos_hh, demos_p = _sample_prior_and_current_data()

    result = derive_core_from_demos(
        demos_households=demos_hh,
        demos_persons=demos_p,
        prior_core_facets=prior_facets,
        output_dir=tmp_path / "facets",
        income_deflator=0.95,
    )

    # 1. Check classification counts
    classification = result["classification"]
    assert classification["surviving_households"] == 1
    assert classification["new_households"] == 1
    assert classification["removed_households"] == 1
    assert classification["surviving_persons"] == 1
    assert classification["new_persons"] == 3
    assert classification["removed_persons"] == 1

    # 2. Check emitted facet tables
    facets = result["facets"]
    assert set(facets.keys()) == {
        "households",
        "people",
        "household_membership",
        "person_demographics",
        "household_location",
        "household_income",
    }

    # Verify demographics:
    # 1001: surviving, race=2 preserved
    # 1002: new child in surviving HH, inherits head race=2
    # 3001: new head, race=3 from race_of_head
    # 3002: new spouse in new HH, inherits head race=3
    demo_df = facets["person_demographics"].to_pandas().set_index("person_id")
    assert demo_df.loc[1001, "race"] == 2
    assert demo_df.loc[1001, "age"] == 41
    assert demo_df.loc[1002, "race"] == 2  # Inherited from 1001
    assert demo_df.loc[1002, "age"] == 0
    assert demo_df.loc[3001, "race"] == 3  # From race_of_head
    assert demo_df.loc[3002, "race"] == 3  # Inherited from 3001

    # Verify income deflation (0.95)
    inc_df = facets["household_income"].to_pandas().set_index("household_id")
    assert inc_df.loc[101, "income"] == round(60000.0 * 0.95)
    assert inc_df.loc[103, "income"] == round(80000.0 * 0.95)

    # Verify location preservation
    loc_df = facets["household_location"].to_pandas().set_index("household_id")
    assert loc_df.loc[101, "latitude"] == 30.123
    assert loc_df.loc[101, "longitude"] == -97.123
    assert loc_df.loc[101, "taz"] == 10
    # New HH 103 has derived tract and block_group from block_id
    assert loc_df.loc[103, "tract"] == 48053960800 // 10000

    # 3. Verify digests are valid sha256 strings
    digests = result["digests"]
    for name in facets:
        assert name in digests
        assert digests[name].startswith("sha256:")
        assert len(digests[name]) == 71


def test_demos_derivation_day_zero_base_initialization():
    """Verify derivation works cleanly for Day Zero base population initialization without prior state."""
    _, demos_hh, demos_p = _sample_prior_and_current_data()

    result = derive_core_from_demos(
        demos_households=demos_hh,
        demos_persons=demos_p,
        prior_core_facets=None,  # Day zero
        income_deflator=1.0,
    )

    classification = result["classification"]
    assert classification["surviving_households"] == 0
    assert classification["new_households"] == 2
    assert classification["removed_households"] == 0
    assert classification["surviving_persons"] == 0
    assert classification["new_persons"] == 4
    assert classification["removed_persons"] == 0

    demo_df = result["facets"]["person_demographics"].to_pandas().set_index("person_id")
    # Head of HH 101 has race 2, child inherits 2
    assert demo_df.loc[1001, "race"] == 2
    assert demo_df.loc[1002, "race"] == 2
    # Head of HH 103 has race 3, spouse inherits 3
    assert demo_df.loc[3001, "race"] == 3
    assert demo_df.loc[3002, "race"] == 3


def test_demos_derivation_writes_and_recomputes_digests(tmp_path):
    """Verify saved Parquet files recompute exact same canonical tabular digests."""
    _, demos_hh, demos_p = _sample_prior_and_current_data()
    out_dir = tmp_path / "parquet_facets"

    result = derive_core_from_demos(
        demos_households=demos_hh,
        demos_persons=demos_p,
        output_dir=out_dir,
    )

    for name, fpath in result["file_paths"].items():
        assert fpath.exists()
        recomputed = compute_tabular_digest(
            source=fpath,
            columns=CORE_FACET_COLUMNS[name],
            key_columns=CORE_FACET_KEY_COLUMNS[name],
            profile="core_facet_table/v1",
        )
        assert recomputed == result["digests"][name]


def test_demos_derivation_with_real_demos_sample(tmp_path: Path) -> None:
    """Verify derivation against a sample extracted from real DEMOS CSV outputs."""
    real_hh = Path("evidence/demos_outputs/Household2018_POLARIS_mapped.csv")
    real_p = Path("evidence/demos_outputs/Person2018_POLARIS_mapped.csv")

    if not (real_hh.exists() and real_p.exists()):
        pytest.skip("Evidence DEMOS files not available")

    hh_csv = tmp_path / "real_sample_hh.csv"
    p_csv = tmp_path / "real_sample_p.csv"

    # Extract 20 households and matching persons from evidence/demos_outputs
    con = duckdb.connect()
    con.execute(f"""
        CREATE TABLE sample_hh AS
        SELECT * FROM read_csv_auto('{real_hh.as_posix()}')
        LIMIT 20;

        CREATE TABLE sample_p AS
        SELECT p.* FROM read_csv_auto('{real_p.as_posix()}') p
        WHERE p.household IN (SELECT household FROM sample_hh);
    """)

    con.execute(f"COPY sample_hh TO '{hh_csv.as_posix()}' (HEADER, DELIMITER ',');")
    con.execute(f"COPY sample_p TO '{p_csv.as_posix()}' (HEADER, DELIMITER ',');")

    result = derive_core_from_demos(
        demos_households=hh_csv,
        demos_persons=p_csv,
        output_dir=tmp_path / "core_out",
    )

    facets = result["facets"]
    assert len(facets["households"]) == 20
    assert len(facets["household_income"]) == 20
    assert len(facets["household_location"]) == 20
    assert len(facets["people"]) == len(facets["household_membership"])
    assert len(facets["people"]) == len(facets["person_demographics"])

    # Ensure no null primary keys
    for name, table in facets.items():
        key_col = CORE_FACET_KEY_COLUMNS[name][0]
        assert table[key_col].null_count == 0
