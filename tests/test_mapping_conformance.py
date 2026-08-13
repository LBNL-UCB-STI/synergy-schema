from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

from synergy_schema.conformance.mappings import (
    mapping_digest,
    semantic_mapping_projection,
    validate_mapping_release,
)
from synergy_schema.native_catalog import write_catalog


def _catalog(path: Path, catalog_id: str, columns: list[str]) -> Path:
    write_catalog(
        {
            "catalog_id": catalog_id,
            "catalog_kind": "polaris",
            "revision": "r1",
            "upstream": {"revision": "r1", "source_paths": ["translation.sql"]},
            "elements": [{"kind": "sql_column", "path": column} for column in columns],
        },
        path,
    )
    return path


def _release(tmp_path: Path, lifecycle: str = "draft") -> Path:
    source = _catalog(tmp_path / "source.yaml", "source", ["household", "persons"])
    target = _catalog(tmp_path / "target.yaml", "target", ["hhold", "workers"])
    contract: dict[str, object] = {
        "id": "mapping:demo",
        "revision": "r1",
        "semantic_content_digest_algorithm": "sha256",
        "semantic_content_digest": "",
        "encoding_source": {"locator": "team.csv"},
        "supporting_sources": [{"locator": "notes.md"}],
        "source_catalog": {"catalog_path": str(source)},
        "target_catalog": {"catalog_path": str(target)},
        "field_mappings": [
            {
                "id": "household",
                "source_element": {"kind": "sql_column", "path": "household"},
                "target_element": {"kind": "sql_column", "path": "hhold"},
                "transformation_mode": "renamed",
                "rule": "rename",
                "implementation_evidence": ["sql"],
            }
        ],
        "residue_records": [
            {
                "id": "persons",
                "residue_kind": "unmapped_source",
                "affected_elements": [{"kind": "sql_column", "path": "persons"}],
                "rationale": "not exchanged",
                "disposition": "dropped",
                "implementation_evidence": ["sql"],
            },
            {
                "id": "workers",
                "residue_kind": "required_target_default",
                "affected_elements": [{"kind": "sql_column", "path": "workers"}],
                "rationale": "default",
                "disposition": "zero",
                "implementation_evidence": ["sql"],
            },
        ],
        "governance": {
            "maintaining_team": "Synergy",
            "lifecycle_status": lifecycle,
            "review_records": [],
        },
    }
    contract["semantic_content_digest"] = mapping_digest(contract)
    release = tmp_path / "release"
    (release / "contract").mkdir(parents=True)
    (release / "implementation").mkdir()
    (release / "contract/population-translation-contract.yaml").write_text(
        yaml.safe_dump(contract), encoding="utf-8"
    )
    (release / "ownership.yaml").write_text(
        "source_owner: ATLAS\ntarget_owner: POLARIS\n", encoding="utf-8"
    )
    return release


def test_semantic_digest_excludes_lineage_implementation_and_governance(
    tmp_path: Path,
) -> None:
    release = _release(tmp_path)
    contract = yaml.safe_load(
        (release / "contract/population-translation-contract.yaml").read_text()
    )
    projection = semantic_mapping_projection(contract)
    assert set(projection) == {
        "source_catalog",
        "target_catalog",
        "field_mappings",
        "residue_records",
    }
    changed = deepcopy(contract)
    changed["encoding_source"] = {"locator": "different.csv"}
    changed["governance"]["lifecycle_status"] = "approved"
    changed["field_mappings"][0]["implementation_evidence"] = ["different.sql"]
    assert mapping_digest(changed) == contract["semantic_content_digest"]


def test_mapping_checks_catalogs_coverage_and_digest(tmp_path: Path) -> None:
    release = _release(tmp_path)
    assert (
        validate_mapping_release(release).diagnostics[0].code == "MAPPING_NOT_APPROVED"
    )
    contract_path = release / "contract/population-translation-contract.yaml"
    contract = yaml.safe_load(contract_path.read_text())
    contract["semantic_content_digest"] = "0" * 64
    contract["residue_records"] = []
    contract_path.write_text(yaml.safe_dump(contract), encoding="utf-8")
    codes = [item.code for item in validate_mapping_release(release).diagnostics]
    assert codes == [
        "MAPPING_COVERAGE_MISSING",
        "MAPPING_DIGEST_MISMATCH",
        "MAPPING_NOT_APPROVED",
    ]


def test_approval_and_implementation_are_independent(tmp_path: Path) -> None:
    release = _release(tmp_path, lifecycle="approved")
    contract_path = release / "contract/population-translation-contract.yaml"
    contract = yaml.safe_load(contract_path.read_text())
    digest = contract["semantic_content_digest"]
    contract["governance"]["review_records"] = [
        {
            "reviewer_role": "workflow_integrator",
            "decision": "accept",
            "assessed_semantic_content_digest": digest,
            "assessed_semantic_content_digest_algorithm": "sha256",
        }
    ]
    contract_path.write_text(yaml.safe_dump(contract), encoding="utf-8")
    impl = {
        "id": "impl:demo",
        "implemented_semantic_content_digest": digest,
        "implemented_semantic_content_digest_algorithm": "sha256",
        "status": "declared",
    }
    (release / "implementation/translation.yaml").write_text(
        yaml.safe_dump(impl), encoding="utf-8"
    )
    codes = [
        item.code
        for item in validate_mapping_release(release, require_approved=True).diagnostics
    ]
    assert codes == ["MAPPING_FALSE_APPROVAL", "MAPPING_IMPLEMENTATION_NOT_CHECKED"]


def test_unregistered_and_ineligible_new_receipts_are_errors(tmp_path: Path) -> None:
    release = _release(tmp_path, lifecycle="superseded")
    (release / "implementation/translation.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "impl:bad",
                "implemented_semantic_content_digest": "0" * 64,
                "implemented_semantic_content_digest_algorithm": "sha256",
                "status": "conformance_checked",
            }
        ),
        encoding="utf-8",
    )
    codes = [
        item.code
        for item in validate_mapping_release(release, new_receipt=True).diagnostics
    ]
    assert codes == [
        "MAPPING_IMPLEMENTATION_UNREGISTERED",
        "MAPPING_NOT_APPROVED",
        "MAPPING_NOT_RECEIPT_ELIGIBLE",
    ]
