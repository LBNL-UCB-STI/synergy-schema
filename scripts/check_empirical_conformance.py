#!/usr/bin/env python3
"""Standalone CLI script to run empirical conformance and cross-model universe join checks.

Uses vectorized single-pass DuckDB SQL queries compiled from LinkML class definitions
in ``deliverable_1_static_schema.yaml`` and computes order-invariant DuckDB XOR64 table
fingerprints and structured facet dicts ready for downstream Consist workflows.

Usage:
    uv run python scripts/check_empirical_conformance.py
    uv run python scripts/check_empirical_conformance.py --format json --out report.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from synergy_schema.conformance.empirical import (
    DEFAULT_EVIDENCE_DIR,
    DEFAULT_SCHEMA_PATH,
    render_empirical_report_markdown,
    run_empirical_conformance_audit,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run schema-driven DuckDB empirical conformance and universe join checks."
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA_PATH,
        help="Path to root LinkML schema bundle (default: deliverable_1_static_schema.yaml)",
    )
    parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=DEFAULT_EVIDENCE_DIR,
        help="Path to local empirical evidence directory (default: evidence/)",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=20,
        help="Number of rows per table to validate through LinkML JsonschemaValidationPlugin",
    )
    parser.add_argument(
        "--skip-synthfirm-2050",
        action="store_true",
        help="Skip scanning the 2050 SynthFirm scenario files",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output report format",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional path to write the rendered report",
    )
    args = parser.parse_args(argv)

    report = run_empirical_conformance_audit(
        schema_path=args.schema,
        evidence_dir=args.evidence_dir,
        sample_size=args.sample_size,
        include_synthfirm_2050=not args.skip_synthfirm_2050,
    )

    rendered = (
        json.dumps(report.to_dict(), indent=2)
        if args.format == "json"
        else render_empirical_report_markdown(report)
    )
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)

    return report.to_check_result().exit_code


if __name__ == "__main__":
    sys.exit(main())
