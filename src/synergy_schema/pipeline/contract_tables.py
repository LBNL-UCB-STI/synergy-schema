"""Compile population translation contract defaults and crosswalks into DuckDB tables.

Ensures the YAML PopulationTranslationContract is the single source of truth
for target default constants and lookup/crosswalk tables used by the DuckDB
projection pipeline.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import duckdb

from synergy_schema.conformance.documents import load_mapping
from synergy_schema.conformance.mappings import (
    _lookup_table_projection,
    mapping_digest,
)

DEFAULT_MAPPING_RELEASE_DIR = (
    Path(__file__).resolve().parents[3]
    / "mappings"
    / "releases"
    / "atlas-demos-to-polaris"
    / "revision-1"
)

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_ALLOWED_SQL_TYPES = {
    "INTEGER",
    "BIGINT",
    "DOUBLE",
    "REAL",
    "VARCHAR",
    "TEXT",
    "BOOLEAN",
}

_TARGET_TABLE_VIEW_NAMES: dict[str, str] = {
    "polaris_households": "_contract_defaults_household",
    "polaris_persons": "_contract_defaults_person",
    "polaris_vehicles": "_contract_defaults_vehicle",
}


def _validate_identifier(name: str, context: str) -> str:
    if not _IDENTIFIER_RE.match(name):
        raise ValueError(f"Invalid SQL identifier for {context}: {name!r}")
    return name


def _sql_literal(value: Any, sql_type: str | None = None) -> str:
    normalized_type = sql_type.upper() if sql_type is not None else None
    if normalized_type is not None and normalized_type not in _ALLOWED_SQL_TYPES:
        raise ValueError(f"Unsupported SQL type: {sql_type!r}")

    if normalized_type == "BOOLEAN" or (
        normalized_type is None and isinstance(value, bool)
    ):
        if not isinstance(value, bool):
            raise ValueError(f"Expected BOOLEAN literal, got {value!r}")
        return "TRUE" if value else "FALSE"

    if normalized_type in {"INTEGER", "BIGINT"} or (
        normalized_type is None
        and isinstance(value, int)
        and not isinstance(value, bool)
    ):
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(
                f"Expected {normalized_type or 'INTEGER'} literal, got {value!r}"
            )
        target_type = normalized_type or "INTEGER"
        return f"CAST({value} AS {target_type})"

    if normalized_type in {"DOUBLE", "REAL"} or (
        normalized_type is None and isinstance(value, float)
    ):
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
        ):
            raise ValueError(
                f"Expected finite {normalized_type or 'DOUBLE'} literal, got {value!r}"
            )
        target_type = normalized_type or "DOUBLE"
        return f"CAST({float(value)!r} AS {target_type})"

    if normalized_type in {"VARCHAR", "TEXT"} or (
        normalized_type is None and isinstance(value, str)
    ):
        if not isinstance(value, str):
            raise ValueError(
                f"Expected {normalized_type or 'VARCHAR'} literal, got {value!r}"
            )
        escaped = value.replace("'", "''")
        target_type = normalized_type or "VARCHAR"
        return f"CAST('{escaped}' AS {target_type})"

    raise ValueError(f"Unsupported scalar value for SQL compilation: {value!r}")


def compile_contract_tables_from_mapping(
    con: duckdb.DuckDBPyConnection,
    contract: Mapping[str, Any],
    *,
    verify_digest: bool = True,
    required_default_tables: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Compile target defaults and lookup tables from a loaded contract mapping into DuckDB."""
    if verify_digest:
        expected = mapping_digest(contract)
        if (
            contract.get("semantic_content_digest_algorithm") != "sha256"
            or contract.get("semantic_content_digest") != expected
        ):
            raise ValueError(
                "Contract semantic_content_digest does not match canonical projection: "
                f"expected {expected}, got {contract.get('semantic_content_digest')!r}"
            )

    defaults_by_table: dict[str, dict[str, Any]] = {}
    default_rows: list[tuple[str, str, str, str]] = []
    registered_lookup_tables: dict[str, int] = {}

    for residue in contract.get("residue_records", []):
        residue_id = str(residue["id"])
        residue_kind = str(residue["residue_kind"])

        if (
            residue_kind == "required_target_default"
            and residue.get("default_value") is not None
        ):
            default_val = residue["default_value"]
            for element in residue.get("affected_elements", []):
                path = str(element.get("path", ""))
                if "." not in path:
                    continue
                target_table, target_col = path.split(".", 1)
                _validate_identifier(target_table, f"{residue_id} table")
                _validate_identifier(target_col, f"{residue_id} column")
                defaults_by_table.setdefault(target_table, {})[target_col] = default_val
                default_rows.append(
                    (
                        residue_id,
                        target_table,
                        target_col,
                        json.dumps(default_val),
                    )
                )

        if residue.get("lookup_table") is not None:
            lookup = _lookup_table_projection(residue["lookup_table"], residue_id)
            table_name = _validate_identifier(
                lookup["table_name"], f"{residue_id} lookup table_name"
            )
            col_defs: list[str] = []
            col_types: list[str] = []
            for col in lookup["columns"]:
                col_name = _validate_identifier(
                    col["name"], f"{residue_id} lookup column"
                )
                sql_type = col["sql_type"].upper()
                if sql_type not in _ALLOWED_SQL_TYPES:
                    raise ValueError(
                        f"Unsupported SQL type {sql_type!r} in {residue_id}"
                    )
                col_defs.append(f'"{col_name}" {sql_type}')
                col_types.append(sql_type)

            con.execute(
                f'CREATE OR REPLACE TEMP TABLE "{table_name}" ({", ".join(col_defs)});'
            )
            value_tuples: list[str] = []
            for row in lookup["rows"]:
                rendered_cells = [
                    _sql_literal(val, col_types[idx])
                    for idx, val in enumerate(row["values"])
                ]
                value_tuples.append(f"({', '.join(rendered_cells)})")
            con.execute(f'INSERT INTO "{table_name}" VALUES {", ".join(value_tuples)};')
            registered_lookup_tables[table_name] = len(lookup["rows"])

    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE "_contract_target_defaults" (
            residue_id VARCHAR,
            target_table VARCHAR,
            target_column VARCHAR,
            default_value_json VARCHAR
        );
        """
    )
    if default_rows:
        rendered_defaults = [
            f"({_sql_literal(r_id)}, {_sql_literal(t_tbl)}, {_sql_literal(t_col)}, {_sql_literal(val_json)})"
            for r_id, t_tbl, t_col, val_json in sorted(default_rows)
        ]
        con.execute(
            f'INSERT INTO "_contract_target_defaults" VALUES {", ".join(rendered_defaults)};'
        )

    if required_default_tables is not None:
        missing_tables = [
            tbl for tbl in required_default_tables if not defaults_by_table.get(tbl)
        ]
        if missing_tables:
            raise ValueError(
                f"Contract is missing required target default values for tables: {', '.join(missing_tables)}"
            )

    registered_default_tables: dict[str, list[str]] = {}
    for target_table, col_map in sorted(defaults_by_table.items()):
        view_name = _TARGET_TABLE_VIEW_NAMES.get(
            target_table, f"_contract_defaults_{target_table}"
        )
        _validate_identifier(view_name, f"defaults view for {target_table}")
        select_exprs = [
            f'{_sql_literal(val)} AS "{col}"' for col, val in sorted(col_map.items())
        ]
        con.execute(
            f'CREATE OR REPLACE TEMP TABLE "{view_name}" AS SELECT {", ".join(select_exprs)};'
        )
        registered_default_tables[view_name] = sorted(col_map.keys())

    return {
        "contract_id": str(contract.get("id", "")),
        "revision": str(contract.get("revision", "")),
        "semantic_content_digest": str(contract.get("semantic_content_digest", "")),
        "lookup_tables": registered_lookup_tables,
        "default_tables": registered_default_tables,
    }


def load_and_register_contract_tables(
    con: duckdb.DuckDBPyConnection,
    release_dir: Path | str | None = None,
    *,
    verify_digest: bool = True,
) -> dict[str, Any]:
    """Load PopulationTranslationContract from release_dir and compile its tables into DuckDB."""
    resolved_dir = (
        Path(release_dir) if release_dir is not None else DEFAULT_MAPPING_RELEASE_DIR
    )
    contract_path = resolved_dir / "contract" / "population-translation-contract.yaml"
    contract = load_mapping(contract_path)
    return compile_contract_tables_from_mapping(
        con,
        contract,
        verify_digest=verify_digest,
        required_default_tables=tuple(_TARGET_TABLE_VIEW_NAMES.keys()),
    )
