"""Deterministic canonical tabular content digests (canonical_tabular_digest/v1)."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
import math
from pathlib import Path
from typing import Any, Sequence
import unicodedata

import duckdb
import pyarrow as pa

_DELIMITER_FIELD = b"\x1f"
_DELIMITER_RECORD = b"\x1e"
_SENTINEL_NULL = b"\x00"


def normalize_scalar(val: Any) -> bytes:
    """Normalize a scalar value to canonical UTF-8 bytes."""
    if val is None:
        return _SENTINEL_NULL

    if isinstance(val, bool):
        return b"true" if val else b"false"

    if isinstance(val, int):
        return str(val).encode("utf-8")

    if isinstance(val, float):
        if math.isnan(val):
            return b"nan"
        if val == 0.0:
            return b"0.0"
        return str(val).encode("utf-8")

    if isinstance(val, str):
        return unicodedata.normalize("NFC", val).encode("utf-8")

    if isinstance(val, bytes):
        return val

    # Fallback to string representation normalized to NFC
    return unicodedata.normalize("NFC", str(val)).encode("utf-8")


def compute_tabular_digest(
    source: Path | str | pa.Table | duckdb.DuckDBPyRelation,
    columns: Sequence[str],
    key_columns: Sequence[str],
    profile: str = "core_facet_table/v1",
    sqlite_table: str | None = None,
) -> str:
    """Compute a canonical SHA-256 tabular digest over normalized, sorted rows.

    Args:
        source: A Parquet path, SQLite DB path, PyArrow Table, or DuckDB relation.
        columns: List of columns to extract in strict schema order.
        key_columns: Primary key / unique columns to sort rows by.
        profile: Profile identifier ('core_facet_table/v1' or 'view_table/v1').
        sqlite_table: Table name if source is a SQLite database file.

    Returns:
        Hex-encoded SHA-256 digest string prefixed with 'sha256:'.
    """
    for key in key_columns:
        if key not in columns:
            raise ValueError(
                f"Key column '{key}' must be in declared columns: {columns}"
            )

    con = duckdb.connect(":memory:")

    if isinstance(source, (str, Path)):
        source_path = Path(source)
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        if sqlite_table is not None:
            # Query SQLite file directly via DuckDB sqlite scanner or attach
            con.execute(f"ATTACH '{source_path}' AS sqlite_db (TYPE SQLITE)")
            table_ref = f"sqlite_db.{sqlite_table}"
        else:
            # Parquet file
            table_ref = f"read_parquet('{source_path}')"
    elif isinstance(source, pa.Table):
        con.register("arrow_table", source)
        table_ref = "arrow_table"
    elif isinstance(source, duckdb.DuckDBPyRelation):
        con.register("rel_table", source)
        table_ref = "rel_table"
    else:
        raise TypeError(f"Unsupported tabular data source type: {type(source)}")

    cols_sql = ", ".join(f'"{col}"' for col in columns)
    order_sql = ", ".join(f'"{col}" ASC NULLS FIRST' for col in key_columns)
    query = f"SELECT {cols_sql} FROM {table_ref} ORDER BY {order_sql}"

    result_table = con.execute(query).arrow()

    hasher = sha256()

    # Write canonical header
    header_parts = [profile.encode("utf-8")] + [col.encode("utf-8") for col in columns]
    hasher.update(_DELIMITER_FIELD.join(header_parts) + _DELIMITER_RECORD)

    # Stream batches through the hasher
    for batch in result_table:
        batch_dict = batch.to_pydict()
        num_rows = batch.num_rows
        for row_idx in range(num_rows):
            row_bytes = [normalize_scalar(batch_dict[col][row_idx]) for col in columns]
            hasher.update(_DELIMITER_FIELD.join(row_bytes) + _DELIMITER_RECORD)

    con.close()
    return f"sha256:{hasher.hexdigest()}"


def compute_state_digest(
    facets: Sequence[Mapping[str, Any]] | Mapping[str, str],
    *,
    profile: str = "core_state/v1",
) -> str:
    """Compute canonical StateDigest under core_state/v1.

    A Merkle tree hash over the sorted (facet, facet_content_digest) pairs.
    """
    if profile != "core_state/v1":
        raise ValueError(f"Unsupported state digest profile: {profile}")

    pairs: list[tuple[str, str]] = []
    if isinstance(facets, Mapping):
        pairs = sorted((str(k), str(v)) for k, v in facets.items())
    else:
        for entry in facets:
            pairs.append((str(entry["facet"]), str(entry["digest"])))
        pairs.sort()

    hasher = sha256()
    hasher.update(profile.encode("utf-8") + _DELIMITER_RECORD)
    for facet, digest in pairs:
        hasher.update(
            facet.encode("utf-8")
            + _DELIMITER_FIELD
            + digest.encode("utf-8")
            + _DELIMITER_RECORD
        )

    return f"sha256:{hasher.hexdigest()}"
