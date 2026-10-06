"""Generate authentic multi-year simulation artifacts and population ledger.

Constructs an authentic multi-year simulation sequence (2025 -> 2026) in
`examples/ledger/austin_multiyear/` with genuine Consist run tracking in
DuckDB, canonical tabular content digests (`core_facet_table/v1`), and
Merkle tree state digests (`core_state/v1`), emitting:
`examples/ledger/austin_multiyear_simulation.yaml`.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import tempfile
import yaml

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

try:
    from consist import ExecutionOptions, Tracker

    HAS_CONSIST = True
except ImportError:
    HAS_CONSIST = False

from synergy_schema.conformance.tabular_digest import (
    compute_state_digest,
    compute_tabular_digest,
)
from synergy_schema.pipeline.derive import (
    CORE_FACET_COLUMNS,
    CORE_FACET_KEY_COLUMNS,
)

ROOT = Path(__file__).parents[1]
LEDGER_DIR = ROOT / "examples" / "ledger"
DATA_DIR = LEDGER_DIR / "austin_multiyear"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate_multiyear_ledger(data_dir: Path | None = None) -> Path:
    if not HAS_CONSIST:
        raise RuntimeError("Consist is required to generate authentic multiyear ledger")

    target_data_dir = data_dir or DATA_DIR
    if target_data_dir.exists():
        shutil.rmtree(target_data_dir)
    target_data_dir.mkdir(parents=True, exist_ok=True)

    tracker = Tracker(
        run_dir=target_data_dir / "consist_runs",
        db_path=target_data_dir / "provenance.duckdb",
    )

    # 1. Base input tables for 2025 (UrbanSim)
    urbansim_dir = target_data_dir / "urbansim" / "2025"
    urbansim_dir.mkdir(parents=True, exist_ok=True)
    u_hh_path = urbansim_dir / "households.parquet"
    u_p_path = urbansim_dir / "persons.parquet"

    u_hh_tbl = pa.table({"household_id": [101, 102]})
    pq.write_table(u_hh_tbl, u_hh_path)

    u_p_tbl = pa.table(
        {
            "person_id": [1001, 1002, 2001],
            "household_id": [101, 101, 102],
        }
    )
    pq.write_table(u_p_tbl, u_p_path)

    def _run_urbansim(hh_p: Path, p_p: Path) -> dict[str, Path]:
        return {"households": hh_p, "persons": p_p}

    r_urbansim = tracker.run(
        fn=_run_urbansim,
        inputs={"hh_p": u_hh_path, "p_p": u_p_path},
        config={"year": 2025},
        outputs=["households", "persons"],
        execution_options=ExecutionOptions(input_binding="paths"),
    )

    hh_core_tbl = pa.table({"household_id": [101, 102]})
    p_core_tbl = pa.table({"person_id": [1001, 1002, 2001]})
    m_core_tbl = pa.table(
        {
            "person_id": [1001, 1002, 2001],
            "household_id": [101, 101, 102],
        }
    )

    hh_digest = compute_tabular_digest(
        hh_core_tbl,
        CORE_FACET_COLUMNS["households"],
        CORE_FACET_KEY_COLUMNS["households"],
    )
    p_digest_2025_u = compute_tabular_digest(
        p_core_tbl,
        CORE_FACET_COLUMNS["people"],
        CORE_FACET_KEY_COLUMNS["people"],
    )
    m_digest = compute_tabular_digest(
        m_core_tbl,
        CORE_FACET_COLUMNS["household_membership"],
        CORE_FACET_KEY_COLUMNS["household_membership"],
    )

    s0_facets = [
        {"facet": "households", "digest": hh_digest},
        {"facet": "people", "digest": p_digest_2025_u},
        {"facet": "household_membership", "digest": m_digest},
    ]
    s0_state_digest = compute_state_digest(s0_facets)

    # 2. DEMOS 2025 Step
    demos_2025_dir = target_data_dir / "demos" / "2025" / "output"
    demos_2025_dir.mkdir(parents=True, exist_ok=True)
    d_hh_path = demos_2025_dir / "households.parquet"
    d_p_path = demos_2025_dir / "persons.parquet"
    d_deaths_path = demos_2025_dir / "deaths.parquet"

    d_hh_tbl = pa.table(
        {
            "household_id": [101, 102],
            "latitude": [30.2672, 30.2700],
            "longitude": [-97.7431, -97.7400],
            "tract": [48453000100, 48453000200],
            "block_group": [1, 2],
            "taz": [10, 20],
            "income": [120000.0, 65000.0],
        }
    )
    pq.write_table(d_hh_tbl, d_hh_path)

    d_p_tbl = pa.table(
        {
            "person_id": [1001, 2001],
            "age": [45, 32],
            "sex": [1, 2],
            "race": [1, 3],
            "hispanic": [0, 0],
            "relate": [0, 0],
            "household_id": [101, 102],
        }
    )
    pq.write_table(d_p_tbl, d_p_path)

    d_deaths_tbl = pa.table({"person_id": [1002]})
    pq.write_table(d_deaths_tbl, d_deaths_path)

    def _run_demos_2025(in_hh: Path, in_p: Path) -> dict[str, Path]:
        return {
            "households_output": d_hh_path,
            "persons_output": d_p_path,
            "deaths_output": d_deaths_path,
        }

    r_demos_2025 = tracker.run(
        fn=_run_demos_2025,
        inputs={"in_hh": u_hh_path, "in_p": u_p_path},
        config={"year": 2025},
        outputs=["households_output", "persons_output", "deaths_output"],
        execution_options=ExecutionOptions(input_binding="paths"),
    )

    demo_tbl = pa.table(
        {
            "person_id": [1001, 2001],
            "age": [45, 32],
            "sex": [1, 2],
            "race": [1, 3],
            "hispanic": [0, 0],
            "relate": [0, 0],
        }
    )
    loc_tbl = pa.table(
        {
            "household_id": [101, 102],
            "latitude": [30.2672, 30.2700],
            "longitude": [-97.7431, -97.7400],
            "tract": [48453000100, 48453000200],
            "block_group": [1, 2],
            "taz": [10, 20],
        }
    )
    inc_tbl = pa.table(
        {
            "household_id": [101, 102],
            "income": [120000.0, 65000.0],
        }
    )
    p_core_2025_d = pa.table({"person_id": [1001, 2001]})

    core_dir_2025 = target_data_dir / "synergy" / "2025" / "core"
    core_dir_2025.mkdir(parents=True, exist_ok=True)
    p_stored_path_2025 = core_dir_2025 / "people.parquet"
    pq.write_table(p_core_2025_d, p_stored_path_2025)

    demo_digest = compute_tabular_digest(
        demo_tbl,
        CORE_FACET_COLUMNS["person_demographics"],
        CORE_FACET_KEY_COLUMNS["person_demographics"],
    )
    loc_digest = compute_tabular_digest(
        loc_tbl,
        CORE_FACET_COLUMNS["household_location"],
        CORE_FACET_KEY_COLUMNS["household_location"],
    )
    inc_digest = compute_tabular_digest(
        inc_tbl,
        CORE_FACET_COLUMNS["household_income"],
        CORE_FACET_KEY_COLUMNS["household_income"],
    )
    p_digest_2025_d = compute_tabular_digest(
        p_core_2025_d,
        CORE_FACET_COLUMNS["people"],
        CORE_FACET_KEY_COLUMNS["people"],
    )

    s1_facets = [
        {"facet": "households", "digest": hh_digest},
        {
            "facet": "people",
            "digest": p_digest_2025_d,
            "stored_object": {
                "artifact_identity": {
                    "digest_algorithm": "sha256",
                    "content_digest": sha256_file(p_stored_path_2025),
                },
                "locator": p_stored_path_2025.relative_to(target_data_dir).as_posix(),
            },
        },
        {"facet": "household_membership", "digest": m_digest},
        {"facet": "person_demographics", "digest": demo_digest},
        {"facet": "household_location", "digest": loc_digest},
        {"facet": "household_income", "digest": inc_digest},
    ]
    s1_state_digest = compute_state_digest(s1_facets)

    # 3. ATLAS 2025 Step
    atlas_2025_dir = target_data_dir / "atlas" / "2025" / "output"
    atlas_2025_dir.mkdir(parents=True, exist_ok=True)
    v_path_2025 = atlas_2025_dir / "vehicles.parquet"
    v_tbl_2025 = pa.table(
        {
            "vehicle_id": [1, 2],
            "household_id": [101, 102],
            "type_id": [1, 2],
        }
    )
    pq.write_table(v_tbl_2025, v_path_2025)

    def _run_atlas_2025(in_hh: Path) -> dict[str, Path]:
        return {"vehicles_output": v_path_2025}

    r_atlas_2025 = tracker.run(
        fn=_run_atlas_2025,
        inputs={"in_hh": d_hh_path},
        config={"year": 2025},
        outputs=["vehicles_output"],
        execution_options=ExecutionOptions(input_binding="paths"),
    )

    v_digest_2025 = compute_tabular_digest(
        v_tbl_2025,
        CORE_FACET_COLUMNS["vehicles"],
        CORE_FACET_KEY_COLUMNS["vehicles"],
    )
    s2_facets = list(s1_facets) + [{"facet": "vehicles", "digest": v_digest_2025}]
    s2_state_digest = compute_state_digest(s2_facets)

    # 4. DEMOS 2026 Step
    demos_2026_dir = target_data_dir / "demos" / "2026" / "output"
    demos_2026_dir.mkdir(parents=True, exist_ok=True)
    d_hh_path_2026 = demos_2026_dir / "households.parquet"
    d_p_path_2026 = demos_2026_dir / "persons.parquet"
    d_deaths_path_2026 = demos_2026_dir / "deaths.parquet"

    d_hh_tbl_2026 = pa.table(
        {
            "household_id": [101, 102],
            "latitude": [30.2672, 30.2700],
            "longitude": [-97.7431, -97.7400],
            "tract": [48453000100, 48453000200],
            "block_group": [1, 2],
            "taz": [10, 20],
            "income": [125000.0, 68000.0],
        }
    )
    pq.write_table(d_hh_tbl_2026, d_hh_path_2026)

    d_p_tbl_2026 = pa.table(
        {
            "person_id": [1001, 2001],
            "age": [46, 33],
            "sex": [1, 2],
            "race": [1, 3],
            "hispanic": [0, 0],
            "relate": [0, 0],
            "household_id": [101, 102],
        }
    )
    pq.write_table(d_p_tbl_2026, d_p_path_2026)

    d_deaths_tbl_2026 = pa.table({"person_id": pa.array([], type=pa.int64())})
    pq.write_table(d_deaths_tbl_2026, d_deaths_path_2026)

    def _run_demos_2026(in_hh: Path, in_p: Path) -> dict[str, Path]:
        return {
            "households_output": d_hh_path_2026,
            "persons_output": d_p_path_2026,
            "deaths_output": d_deaths_path_2026,
        }

    r_demos_2026 = tracker.run(
        fn=_run_demos_2026,
        inputs={"in_hh": d_hh_path, "in_p": d_p_path},
        config={"year": 2026},
        outputs=["households_output", "persons_output", "deaths_output"],
        execution_options=ExecutionOptions(input_binding="paths"),
    )

    demo_tbl_2026 = pa.table(
        {
            "person_id": [1001, 2001],
            "age": [46, 33],
            "sex": [1, 2],
            "race": [1, 3],
            "hispanic": [0, 0],
            "relate": [0, 0],
        }
    )
    inc_tbl_2026 = pa.table(
        {
            "household_id": [101, 102],
            "income": [125000.0, 68000.0],
        }
    )
    demo_digest_2026 = compute_tabular_digest(
        demo_tbl_2026,
        CORE_FACET_COLUMNS["person_demographics"],
        CORE_FACET_KEY_COLUMNS["person_demographics"],
    )
    inc_digest_2026 = compute_tabular_digest(
        inc_tbl_2026,
        CORE_FACET_COLUMNS["household_income"],
        CORE_FACET_KEY_COLUMNS["household_income"],
    )

    core_dir_2026 = target_data_dir / "synergy" / "2026" / "core"
    core_dir_2026.mkdir(parents=True, exist_ok=True)
    p_stored_path_2026 = core_dir_2026 / "people.parquet"
    pq.write_table(p_core_2025_d, p_stored_path_2026)

    s3_facets = [
        {"facet": "households", "digest": hh_digest},
        {
            "facet": "people",
            "digest": p_digest_2025_d,
            "stored_object": {
                "artifact_identity": {
                    "digest_algorithm": "sha256",
                    "content_digest": sha256_file(p_stored_path_2026),
                },
                "locator": p_stored_path_2026.relative_to(target_data_dir).as_posix(),
            },
        },
        {"facet": "household_membership", "digest": m_digest},
        {"facet": "person_demographics", "digest": demo_digest_2026},
        {"facet": "household_location", "digest": loc_digest},
        {"facet": "household_income", "digest": inc_digest_2026},
        {"facet": "vehicles", "digest": v_digest_2025},
    ]
    s3_state_digest = compute_state_digest(s3_facets)

    # 5. ATLAS 2026 Step
    atlas_2026_dir = target_data_dir / "atlas" / "2026" / "output"
    atlas_2026_dir.mkdir(parents=True, exist_ok=True)
    v_path_2026 = atlas_2026_dir / "vehicles.parquet"
    v_tbl_2026 = pa.table(
        {
            "vehicle_id": [1, 2, 3],
            "household_id": [101, 102, 101],
            "type_id": [1, 2, 3],
        }
    )
    pq.write_table(v_tbl_2026, v_path_2026)

    def _run_atlas_2026(in_hh: Path) -> dict[str, Path]:
        return {"vehicles_output": v_path_2026}

    r_atlas_2026 = tracker.run(
        fn=_run_atlas_2026,
        inputs={"in_hh": d_hh_path_2026},
        config={"year": 2026},
        outputs=["vehicles_output"],
        execution_options=ExecutionOptions(input_binding="paths"),
    )

    v_digest_2026 = compute_tabular_digest(
        v_tbl_2026,
        CORE_FACET_COLUMNS["vehicles"],
        CORE_FACET_KEY_COLUMNS["vehicles"],
    )
    s4_facets = [
        {"facet": "households", "digest": hh_digest},
        {
            "facet": "people",
            "digest": p_digest_2025_d,
            "stored_object": {
                "artifact_identity": {
                    "digest_algorithm": "sha256",
                    "content_digest": sha256_file(p_stored_path_2026),
                },
                "locator": p_stored_path_2026.relative_to(target_data_dir).as_posix(),
            },
        },
        {"facet": "household_membership", "digest": m_digest},
        {"facet": "person_demographics", "digest": demo_digest_2026},
        {"facet": "household_location", "digest": loc_digest},
        {"facet": "household_income", "digest": inc_digest_2026},
        {"facet": "vehicles", "digest": v_digest_2026},
    ]
    s4_state_digest = compute_state_digest(s4_facets)

    # Compact the DuckDB file
    db_file = target_data_dir / "provenance.duckdb"
    with tempfile.TemporaryDirectory() as tmp_dump:
        con = duckdb.connect(str(db_file))
        con.execute(f"EXPORT DATABASE '{tmp_dump}'")
        con.close()

        compacted = target_data_dir / "compacted.duckdb"
        con_new = duckdb.connect(str(compacted))
        con_new.execute(f"IMPORT DATABASE '{tmp_dump}'")
        con_new.close()

        shutil.move(str(compacted), str(db_file))

    ledger = {
        "ledger_id": "population-ledger:austin-regional:baseline:r1",
        "scenario_definition_ref": {
            "scenario_definition_id": "scenario:austin-regional:baseline",
            "revision": "2026.10",
            "content_digest": "0000000000000000000000000000000000000000000000000000000000000000",
        },
        "stochastic_realization_id": "r1",
        "facet_digest_form": "core_facet_table/v1",
        "state_digest_form": "core_state/v1",
        "mapping_catalog": "mapping-catalog:synthetic-region/v1",
        "snapshots": [
            {
                "snapshot_id": "snapshot:2025:urbansim",
                "simulation_year": 2025,
                "step": {
                    "model": "urbansim",
                    "producing_run": {
                        "provider": "consist",
                        "run_id": r_urbansim.run.id,
                    },
                    "output_views": [
                        {
                            "view_id": "view:urbansim/households_output:2025",
                            "view_kind": "urbansim/households_output",
                            "artifact": {
                                "artifact_identity": {
                                    "digest_algorithm": "sha256",
                                    "content_digest": sha256_file(u_hh_path),
                                },
                                "locator": u_hh_path.relative_to(
                                    target_data_dir
                                ).as_posix(),
                            },
                        },
                        {
                            "view_id": "view:urbansim/persons_output:2025",
                            "view_kind": "urbansim/persons_output",
                            "artifact": {
                                "artifact_identity": {
                                    "digest_algorithm": "sha256",
                                    "content_digest": sha256_file(u_p_path),
                                },
                                "locator": u_p_path.relative_to(
                                    target_data_dir
                                ).as_posix(),
                            },
                        },
                    ],
                    "derivations": [
                        {
                            "facet": "households",
                            "mapping": "mapping:urbansim-core/v1#households",
                            "views": ["view:urbansim/households_output:2025"],
                        },
                        {
                            "facet": "people",
                            "mapping": "mapping:urbansim-core/v1#people",
                            "views": ["view:urbansim/persons_output:2025"],
                        },
                        {
                            "facet": "household_membership",
                            "mapping": "mapping:urbansim-core/v1#household_membership",
                            "views": ["view:urbansim/persons_output:2025"],
                        },
                    ],
                },
                "core_state": {
                    "state_digest": s0_state_digest,
                    "facets": s0_facets,
                },
            },
            {
                "snapshot_id": "snapshot:2025:demos",
                "parent_snapshots": ["snapshot:2025:urbansim"],
                "simulation_year": 2025,
                "step": {
                    "model": "demos",
                    "producing_run": {
                        "provider": "consist",
                        "run_id": r_demos_2025.run.id,
                    },
                    "input_views": [
                        {
                            "view_id": "view:demos/persons_input:2025",
                            "view_kind": "demos/persons_input",
                            "artifact": {
                                "artifact_identity": {
                                    "digest_algorithm": "sha256",
                                    "content_digest": sha256_file(u_p_path),
                                },
                                "locator": u_p_path.relative_to(
                                    target_data_dir
                                ).as_posix(),
                            },
                            "prepared_from_state": s0_state_digest,
                        }
                    ],
                    "output_views": [
                        {
                            "view_id": "view:demos/households_output:2025",
                            "view_kind": "demos/households_output",
                            "artifact": {
                                "artifact_identity": {
                                    "digest_algorithm": "sha256",
                                    "content_digest": sha256_file(d_hh_path),
                                },
                                "locator": d_hh_path.relative_to(
                                    target_data_dir
                                ).as_posix(),
                            },
                        },
                        {
                            "view_id": "view:demos/persons_output:2025",
                            "view_kind": "demos/persons_output",
                            "artifact": {
                                "artifact_identity": {
                                    "digest_algorithm": "sha256",
                                    "content_digest": sha256_file(d_p_path),
                                },
                                "locator": d_p_path.relative_to(
                                    target_data_dir
                                ).as_posix(),
                            },
                        },
                        {
                            "view_id": "view:demos/deaths_output:2025",
                            "view_kind": "demos/deaths_output",
                            "artifact": {
                                "artifact_identity": {
                                    "digest_algorithm": "sha256",
                                    "content_digest": sha256_file(d_deaths_path),
                                },
                                "locator": d_deaths_path.relative_to(
                                    target_data_dir
                                ).as_posix(),
                            },
                        },
                    ],
                    "reads": ["households", "people", "household_membership"],
                    "derivations": [
                        {
                            "facet": "people",
                            "mapping": "mapping:demos-core/v1#people",
                            "views": ["view:demos/deaths_output:2025"],
                        },
                        {
                            "facet": "person_demographics",
                            "mapping": "mapping:demos-core/v1#person_demographics",
                            "views": ["view:demos/persons_output:2025"],
                        },
                        {
                            "facet": "household_location",
                            "mapping": "mapping:demos-core/v1#household_location",
                            "views": ["view:demos/households_output:2025"],
                        },
                        {
                            "facet": "household_income",
                            "mapping": "mapping:demos-core/v1#household_income",
                            "views": ["view:demos/households_output:2025"],
                        },
                    ],
                },
                "core_state": {
                    "state_digest": s1_state_digest,
                    "facets": s1_facets,
                },
            },
            {
                "snapshot_id": "snapshot:2025:atlas",
                "parent_snapshots": ["snapshot:2025:demos"],
                "simulation_year": 2025,
                "step": {
                    "model": "atlas",
                    "producing_run": {
                        "provider": "consist",
                        "run_id": r_atlas_2025.run.id,
                    },
                    "input_views": [
                        {
                            "view_id": "view:atlas/household_input:2025",
                            "view_kind": "atlas/household_input",
                            "artifact": {
                                "artifact_identity": {
                                    "digest_algorithm": "sha256",
                                    "content_digest": sha256_file(d_hh_path),
                                },
                                "locator": d_hh_path.relative_to(
                                    target_data_dir
                                ).as_posix(),
                            },
                            "prepared_from_state": s1_state_digest,
                        }
                    ],
                    "output_views": [
                        {
                            "view_id": "view:atlas/vehicles_output:2025",
                            "view_kind": "atlas/vehicles_output",
                            "artifact": {
                                "artifact_identity": {
                                    "digest_algorithm": "sha256",
                                    "content_digest": sha256_file(v_path_2025),
                                },
                                "locator": v_path_2025.relative_to(
                                    target_data_dir
                                ).as_posix(),
                            },
                        }
                    ],
                    "reads": ["households", "household_membership"],
                    "derivations": [
                        {
                            "facet": "vehicles",
                            "mapping": "mapping:atlas-core/v1#vehicles",
                            "views": ["view:atlas/vehicles_output:2025"],
                        },
                    ],
                },
                "core_state": {
                    "state_digest": s2_state_digest,
                    "facets": s2_facets,
                },
            },
            {
                "snapshot_id": "snapshot:2026:demos",
                "parent_snapshots": ["snapshot:2025:atlas"],
                "simulation_year": 2026,
                "step": {
                    "model": "demos",
                    "producing_run": {
                        "provider": "consist",
                        "run_id": r_demos_2026.run.id,
                    },
                    "input_views": [
                        {
                            "view_id": "view:demos/households_input:2026",
                            "view_kind": "demos/households_input",
                            "artifact": {
                                "artifact_identity": {
                                    "digest_algorithm": "sha256",
                                    "content_digest": sha256_file(d_hh_path),
                                },
                                "locator": d_hh_path.relative_to(
                                    target_data_dir
                                ).as_posix(),
                            },
                            "prepared_from_state": s2_state_digest,
                        }
                    ],
                    "output_views": [
                        {
                            "view_id": "view:demos/households_output:2026",
                            "view_kind": "demos/households_output",
                            "artifact": {
                                "artifact_identity": {
                                    "digest_algorithm": "sha256",
                                    "content_digest": sha256_file(d_hh_path_2026),
                                },
                                "locator": d_hh_path_2026.relative_to(
                                    target_data_dir
                                ).as_posix(),
                            },
                        },
                        {
                            "view_id": "view:demos/persons_output:2026",
                            "view_kind": "demos/persons_output",
                            "artifact": {
                                "artifact_identity": {
                                    "digest_algorithm": "sha256",
                                    "content_digest": sha256_file(d_p_path_2026),
                                },
                                "locator": d_p_path_2026.relative_to(
                                    target_data_dir
                                ).as_posix(),
                            },
                        },
                        {
                            "view_id": "view:demos/deaths_output:2026",
                            "view_kind": "demos/deaths_output",
                            "artifact": {
                                "artifact_identity": {
                                    "digest_algorithm": "sha256",
                                    "content_digest": sha256_file(d_deaths_path_2026),
                                },
                                "locator": d_deaths_path_2026.relative_to(
                                    target_data_dir
                                ).as_posix(),
                            },
                        },
                    ],
                    "reads": [
                        "households",
                        "people",
                        "household_membership",
                        "person_demographics",
                        "household_location",
                        "household_income",
                    ],
                    "derivations": [
                        {
                            "facet": "people",
                            "mapping": "mapping:demos-core/v1#people",
                            "views": ["view:demos/deaths_output:2026"],
                        },
                        {
                            "facet": "person_demographics",
                            "mapping": "mapping:demos-core/v1#person_demographics",
                            "views": ["view:demos/persons_output:2026"],
                        },
                        {
                            "facet": "household_income",
                            "mapping": "mapping:demos-core/v1#household_income",
                            "views": ["view:demos/households_output:2026"],
                        },
                    ],
                },
                "core_state": {
                    "state_digest": s3_state_digest,
                    "facets": s3_facets,
                },
            },
            {
                "snapshot_id": "snapshot:2026:atlas",
                "parent_snapshots": ["snapshot:2026:demos"],
                "simulation_year": 2026,
                "step": {
                    "model": "atlas",
                    "producing_run": {
                        "provider": "consist",
                        "run_id": r_atlas_2026.run.id,
                    },
                    "input_views": [
                        {
                            "view_id": "view:atlas/household_input:2026",
                            "view_kind": "atlas/household_input",
                            "artifact": {
                                "artifact_identity": {
                                    "digest_algorithm": "sha256",
                                    "content_digest": sha256_file(d_hh_path_2026),
                                },
                                "locator": d_hh_path_2026.relative_to(
                                    target_data_dir
                                ).as_posix(),
                            },
                            "prepared_from_state": s3_state_digest,
                        }
                    ],
                    "output_views": [
                        {
                            "view_id": "view:atlas/vehicles_output:2026",
                            "view_kind": "atlas/vehicles_output",
                            "artifact": {
                                "artifact_identity": {
                                    "digest_algorithm": "sha256",
                                    "content_digest": sha256_file(v_path_2026),
                                },
                                "locator": v_path_2026.relative_to(
                                    target_data_dir
                                ).as_posix(),
                            },
                        }
                    ],
                    "reads": ["households", "household_membership"],
                    "derivations": [
                        {
                            "facet": "vehicles",
                            "mapping": "mapping:atlas-core/v1#vehicles",
                            "views": ["view:atlas/vehicles_output:2026"],
                        },
                    ],
                },
                "core_state": {
                    "state_digest": s4_state_digest,
                    "facets": s4_facets,
                },
            },
        ],
        "checkpoints": [
            {
                "simulation_year": 2025,
                "snapshot": "snapshot:2025:atlas",
            },
            {
                "simulation_year": 2026,
                "snapshot": "snapshot:2026:atlas",
            },
        ],
    }

    class IndentedYamlDumper(yaml.SafeDumper):
        def increase_indent(self, flow=False, indentless=False):
            return super().increase_indent(flow, False)

    out_ledger_path = LEDGER_DIR / "austin_multiyear_simulation.yaml"
    out_ledger_path.write_text(
        yaml.dump(ledger, Dumper=IndentedYamlDumper, sort_keys=False)
    )
    return out_ledger_path


if __name__ == "__main__":
    path = generate_multiyear_ledger()
    print(f"Generated multiyear ledger at {path}")
