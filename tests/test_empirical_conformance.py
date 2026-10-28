"""Tests for DuckDB + Consist empirical conformance and cross-model universe join checks."""

from __future__ import annotations


import duckdb
from linkml_runtime.utils.schemaview import SchemaView
import pytest

from synergy_schema.conformance.empirical import (
    DEFAULT_EVIDENCE_DIR,
    DEFAULT_SCHEMA_PATH,
    compile_linkml_class_audit_sql,
    render_empirical_report_markdown,
    run_empirical_conformance_audit,
)


def test_compile_linkml_class_audit_sql_single_pass() -> None:
    """Verify that LinkML class rules compile into a single vectorized DuckDB query."""
    sv = SchemaView(str(DEFAULT_SCHEMA_PATH))
    con = duckdb.connect()
    con.execute(
        """
        CREATE VIEW test_atlas_veh AS
        SELECT * FROM (
            VALUES
                (101, 1, 'car', '0~5 years', 'AEV', 12000.0, 'own'),
                (101, 2, 'suv', '6~11 years', 'ICE', 15000.0, 'lease')
        ) AS t(HOUSEID, VEHID, body_type, vintage_category, powertrain, annual_mileage, ownlease)
        """
    )
    actual_cols = {
        "HOUSEID",
        "VEHID",
        "body_type",
        "vintage_category",
        "powertrain",
        "annual_mileage",
        "ownlease",
    }
    sql, null_meta, bound_meta, enum_meta = compile_linkml_class_audit_sql(
        sv=sv,
        view_name="test_atlas_veh",
        class_name="AtlasVehicleFleetOutput",
        key_columns=["HOUSEID", "VEHID"],
        actual_col_set=actual_cols,
    )
    cursor = con.execute(sql)
    row = cursor.fetchone()
    assert row is not None
    cols = [str(d[0]) for d in cursor.description]
    res = dict(zip(cols, row))

    assert res["total_rows"] == 2
    assert res["distinct_keys"] == 2
    assert int(res["table_xor_hash"]) > 0
    for alias, _ in null_meta:
        assert res[alias] == 0
    for alias, _ in bound_meta:
        assert res[alias] == 0
    for alias, _ in enum_meta:
        assert res[alias] == 0
    con.close()


@pytest.mark.skipif(
    not DEFAULT_EVIDENCE_DIR.exists(),
    reason="Empirical evidence directory not present",
)
def test_full_empirical_conformance_and_consist_facets() -> None:
    """Run full empirical conformance + universe join checks and verify Consist-ready facets."""
    report = run_empirical_conformance_audit(
        schema_path=DEFAULT_SCHEMA_PATH,
        evidence_dir=DEFAULT_EVIDENCE_DIR,
        sample_size=5,
        include_synthfirm_2050=False,
    )

    assert report.passed, render_empirical_report_markdown(report)
    assert report.to_check_result().exit_code == 0
    assert len(report.table_checks) == 18
    assert len(report.relational_checks) == 19
    assert len(report.universe_joins) == 4

    run_facet = report.to_consist_facet()
    assert run_facet["conformance_passed"] is True
    assert run_facet["tables_checked"] == 18
    assert all(
        t.duckdb_table_fingerprint.startswith("duckdb_xor64:")
        and t.to_consist_facet()["passed"] is True
        for t in report.table_checks
    )
