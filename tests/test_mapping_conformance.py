from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

from synergy_schema.conformance.mappings import (
    mapping_digest,
    semantic_mapping_projection,
    validate_mapping_release,
)
from synergy_schema.native_catalog import load_catalog, write_catalog


def _catalog(path: Path, catalog_id: str, columns: list[str]) -> dict[str, object]:
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
    document = load_catalog(path).document
    return {
        key: document[key]
        for key in (
            "catalog_id",
            "catalog_kind",
            "revision",
            "digest_algorithm",
            "content_digest",
        )
    }


def _release(tmp_path: Path, lifecycle: str = "draft") -> Path:
    source = _catalog(
        tmp_path / "catalogs/source/r1/catalog.yaml", "source", ["household", "persons"]
    )
    target = _catalog(
        tmp_path / "catalogs/target/r1/catalog.yaml", "target", ["hhold", "workers"]
    )
    contract: dict[str, object] = {
        "id": "mapping:demo",
        "revision": "r1",
        "semantic_content_digest_algorithm": "sha256",
        "semantic_content_digest": "",
        "encoding_source": {"locator": "team.csv"},
        "supporting_sources": [{"locator": "notes.md"}],
        "source_catalog": source,
        "target_catalog": target,
        "source_schema_contract": {
            "language": "linkml",
            "schema_digest_algorithm": "sha256",
            "schema_digest": "a" * 64,
            "selected_root": "AtlasHouseholdInput",
        },
        "target_schema_contract": {
            "language": "linkml",
            "schema_digest_algorithm": "sha256",
            "schema_digest": "b" * 64,
            "selected_root": "PolarisHouseholdRecord",
        },
        "field_mappings": [
            {
                "id": "household",
                "source_element": {
                    "catalog": source,
                    "kind": "sql_column",
                    "path": "household",
                },
                "target_element": {
                    "catalog": target,
                    "kind": "sql_column",
                    "path": "hhold",
                },
                "transformation_mode": "renamed",
                "rule": "rename",
                "implementation_evidence": ["sql"],
            }
        ],
        "residue_records": [
            {
                "id": "persons",
                "residue_kind": "unmapped_source",
                "affected_elements": [
                    {"catalog": source, "kind": "sql_column", "path": "persons"}
                ],
                "rationale": "not exchanged",
                "disposition": "dropped",
                "implementation_evidence": ["sql"],
            },
            {
                "id": "workers",
                "residue_kind": "required_target_default",
                "affected_elements": [
                    {"catalog": target, "kind": "sql_column", "path": "workers"}
                ],
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
        "source_schema_contract",
        "target_schema_contract",
        "field_mappings",
        "residue_records",
    }
    changed = deepcopy(contract)
    changed["encoding_source"] = {"locator": "different.csv"}
    changed["governance"]["lifecycle_status"] = "approved"
    changed["field_mappings"][0]["implementation_evidence"] = ["different.sql"]
    assert mapping_digest(changed) == contract["semantic_content_digest"]


def test_mapping_release_requires_schema_contract_identities(tmp_path: Path) -> None:
    release = _release(tmp_path)
    contract_path = release / "contract/population-translation-contract.yaml"
    contract = yaml.safe_load(contract_path.read_text())
    contract.pop("source_schema_contract")
    contract["target_schema_contract"] = "not-a-mapping"
    contract_path.write_text(yaml.safe_dump(contract), encoding="utf-8")
    assert [
        item.code
        for item in validate_mapping_release(
            release, catalog_root=tmp_path / "catalogs"
        ).diagnostics
    ] == ["MAPPING_DOCUMENT_INVALID"]


def test_mapping_checks_catalogs_coverage_and_digest(tmp_path: Path) -> None:
    release = _release(tmp_path)
    assert (
        validate_mapping_release(release, catalog_root=tmp_path / "catalogs")
        .diagnostics[0]
        .code
        == "MAPPING_NOT_APPROVED"
    )
    contract_path = release / "contract/population-translation-contract.yaml"
    contract = yaml.safe_load(contract_path.read_text())
    contract["semantic_content_digest"] = "0" * 64
    contract["residue_records"] = []
    contract_path.write_text(yaml.safe_dump(contract), encoding="utf-8")
    codes = [
        item.code
        for item in validate_mapping_release(
            release, catalog_root=tmp_path / "catalogs"
        ).diagnostics
    ]
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
        for item in validate_mapping_release(
            release, require_approved=True, catalog_root=tmp_path / "catalogs"
        ).diagnostics
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
        for item in validate_mapping_release(
            release, new_receipt=True, catalog_root=tmp_path / "catalogs"
        ).diagnostics
    ]
    assert codes == [
        "MAPPING_IMPLEMENTATION_UNREGISTERED",
        "MAPPING_NOT_APPROVED",
        "MAPPING_NOT_RECEIPT_ELIGIBLE",
    ]


def test_approval_requires_named_owners_not_spoofed_roles(tmp_path: Path) -> None:
    release = _release(tmp_path, lifecycle="approved")
    contract_path = release / "contract/population-translation-contract.yaml"
    contract = yaml.safe_load(contract_path.read_text())
    digest = contract["semantic_content_digest"]
    contract["governance"]["review_records"] = [
        {
            "reviewer_role": "source_owner",
            "reviewing_team": "Synergy",
            "decision": "accept",
            "assessed_semantic_content_digest": digest,
            "assessed_semantic_content_digest_algorithm": "sha256",
        },
        {
            "reviewer_role": "target_owner",
            "reviewing_team": "POLARIS",
            "decision": "accept",
            "assessed_semantic_content_digest": digest,
            "assessed_semantic_content_digest_algorithm": "sha256",
        },
    ]
    contract_path.write_text(yaml.safe_dump(contract), encoding="utf-8")
    assert [
        item.code
        for item in validate_mapping_release(
            release, catalog_root=tmp_path / "catalogs"
        ).diagnostics
    ] == ["MAPPING_FALSE_APPROVAL"]
    contract["governance"]["review_records"][0]["reviewing_team"] = "ATLAS"
    contract_path.write_text(yaml.safe_dump(contract), encoding="utf-8")
    assert (
        validate_mapping_release(
            release, catalog_root=tmp_path / "catalogs"
        ).diagnostics
        == ()
    )


def test_native_element_catalog_identity_must_match_its_contract_side(
    tmp_path: Path,
) -> None:
    release = _release(tmp_path)
    contract_path = release / "contract/population-translation-contract.yaml"
    contract = yaml.safe_load(contract_path.read_text())
    contract["field_mappings"][0]["source_element"]["catalog"]["content_digest"] = (
        "0" * 64
    )
    contract_path.write_text(yaml.safe_dump(contract), encoding="utf-8")
    assert [
        item.code
        for item in validate_mapping_release(
            release, catalog_root=tmp_path / "catalogs"
        ).diagnostics
    ] == [
        "MAPPING_DIGEST_MISMATCH",
        "MAPPING_NOT_APPROVED",
        "NATIVE_ELEMENT_UNRESOLVED",
    ]


def test_atlas_demos_to_polaris_revision_1_conformance() -> None:
    release_dir = Path("mappings/releases/atlas-demos-to-polaris/revision-1")
    result = validate_mapping_release(release_dir)
    assert not any(d.severity == "error" for d in result.diagnostics)
    assert [d.code for d in result.diagnostics] == ["MAPPING_NOT_APPROVED"]
