"""Tests for canonical tabular content digests (canonical_tabular_digest/v1)."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from synergy_schema.conformance.tabular_digest import (
    compute_tabular_digest,
    normalize_scalar,
)


def test_scalar_normalization() -> None:
    assert normalize_scalar(None) == b"\x00"
    assert normalize_scalar(True) == b"true"
    assert normalize_scalar(False) == b"false"
    assert normalize_scalar(42) == b"42"
    assert normalize_scalar(0) == b"0"
    assert normalize_scalar(0.0) == b"0.0"
    assert normalize_scalar(-0.0) == b"0.0"
    assert normalize_scalar(float("nan")) == b"nan"
    assert normalize_scalar(3.14159) == b"3.14159"
    # Unicode NFC normalization
    e_acute_decomposed = "e\u0301"
    e_acute_composed = "\u00e9"
    assert normalize_scalar(e_acute_decomposed) == normalize_scalar(e_acute_composed)


def test_row_order_invariance() -> None:
    schema = pa.schema(
        [
            ("person_id", pa.int64()),
            ("household_id", pa.int64()),
            ("age", pa.int32()),
        ]
    )

    data1 = {
        "person_id": [101, 102, 103],
        "household_id": [1, 1, 2],
        "age": [35, 34, 12],
    }
    # Shuffled rows
    data2 = {
        "person_id": [103, 101, 102],
        "household_id": [2, 1, 1],
        "age": [12, 35, 34],
    }

    t1 = pa.Table.from_pydict(data1, schema=schema)
    t2 = pa.Table.from_pydict(data2, schema=schema)

    cols = ["person_id", "household_id", "age"]
    keys = ["person_id"]

    digest1 = compute_tabular_digest(t1, cols, keys)
    digest2 = compute_tabular_digest(t2, cols, keys)

    assert digest1 == digest2
    assert digest1.startswith("sha256:")
    assert len(digest1) == 71  # "sha256:" + 64 hex chars


def test_format_and_compression_invariance() -> None:
    schema = pa.schema(
        [
            ("household_id", pa.int64()),
            ("latitude", pa.float64()),
            ("longitude", pa.float64()),
        ]
    )

    data = {
        "household_id": [20, 10, 30],
        "latitude": [30.2672, 37.7749, 41.8781],
        "longitude": [-97.7431, -122.4194, -87.6298],
    }
    cols = ["household_id", "latitude", "longitude"]
    keys = ["household_id"]

    table = pa.Table.from_pydict(data, schema=schema)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        parquet_snappy = tmp_path / "snappy.parquet"
        parquet_zstd = tmp_path / "zstd.parquet"
        sqlite_db = tmp_path / "test.db"

        pq.write_table(table, parquet_snappy, compression="snappy")
        pq.write_table(table, parquet_zstd, compression="zstd")

        # Create SQLite table with data in different physical insertion order
        con = sqlite3.connect(sqlite_db)
        con.execute(
            "CREATE TABLE households (household_id INTEGER PRIMARY KEY, latitude REAL, longitude REAL)"
        )
        con.executemany(
            "INSERT INTO households VALUES (?, ?, ?)",
            [
                (10, 37.7749, -122.4194),
                (30, 41.8781, -87.6298),
                (20, 30.2672, -97.7431),
            ],
        )
        con.commit()
        con.close()

        d_table = compute_tabular_digest(table, cols, keys)
        d_snappy = compute_tabular_digest(parquet_snappy, cols, keys)
        d_zstd = compute_tabular_digest(parquet_zstd, cols, keys)
        d_sqlite = compute_tabular_digest(
            sqlite_db, cols, keys, sqlite_table="households"
        )

        assert d_table == d_snappy
        assert d_snappy == d_zstd
        assert d_zstd == d_sqlite


def test_value_difference_changes_digest() -> None:
    schema = pa.schema([("person_id", pa.int64()), ("age", pa.int32())])
    t1 = pa.Table.from_pydict({"person_id": [1, 2], "age": [20, 30]}, schema=schema)
    t2 = pa.Table.from_pydict({"person_id": [1, 2], "age": [20, 31]}, schema=schema)

    cols = ["person_id", "age"]
    keys = ["person_id"]

    assert compute_tabular_digest(t1, cols, keys) != compute_tabular_digest(
        t2, cols, keys
    )


def test_column_order_invariance_in_storage() -> None:
    # Stored tables with columns in different physical order should match when
    # evaluated against the same canonical column declaration.
    t1 = pa.Table.from_pydict({"a": [1, 2], "b": ["x", "y"]})
    t2 = pa.Table.from_pydict({"b": ["x", "y"], "a": [1, 2]})

    cols = ["a", "b"]
    keys = ["a"]

    assert compute_tabular_digest(t1, cols, keys) == compute_tabular_digest(
        t2, cols, keys
    )


def test_null_distinct_from_empty_string() -> None:
    t1 = pa.Table.from_pydict({"id": [1], "val": [None]})
    t2 = pa.Table.from_pydict({"id": [1], "val": [""]})

    cols = ["id", "val"]
    keys = ["id"]

    assert compute_tabular_digest(t1, cols, keys) != compute_tabular_digest(
        t2, cols, keys
    )


def test_missing_key_column_raises_error() -> None:
    table = pa.Table.from_pydict({"a": [1, 2], "b": [3, 4]})
    with pytest.raises(ValueError, match="Key column 'c' must be in declared columns"):
        compute_tabular_digest(table, columns=["a", "b"], key_columns=["c"])


def test_compute_state_digest() -> None:
    from synergy_schema.conformance.tabular_digest import compute_state_digest

    facets1 = [
        {
            "facet": "households",
            "digest": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
        },
        {
            "facet": "people",
            "digest": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
        },
    ]
    # Reordered facets
    facets2 = [
        {
            "facet": "people",
            "digest": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
        },
        {
            "facet": "households",
            "digest": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
        },
    ]
    # Dict form
    facets_dict = {
        "households": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
        "people": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
    }

    digest1 = compute_state_digest(facets1)
    digest2 = compute_state_digest(facets2)
    digest3 = compute_state_digest(facets_dict)

    assert digest1.startswith("sha256:")
    assert len(digest1) == 7 + 64
    assert digest1 == digest2 == digest3

    # Different digest
    facets_diff = [
        {
            "facet": "households",
            "digest": "sha256:3333333333333333333333333333333333333333333333333333333333333333",
        },
        {
            "facet": "people",
            "digest": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
        },
    ]
    assert compute_state_digest(facets_diff) != digest1
