from __future__ import annotations

from pathlib import Path
import csv
import yaml

from synergy_schema.conformance.review import (
    diff_mappings,
    import_mapping,
    render_mapping,
)
from tests.test_mapping_conformance import _release


def test_mapping_review_round_trips_semantic_digest_without_approval(
    tmp_path: Path,
) -> None:
    release = _release(tmp_path)
    review = tmp_path / "review"
    render_mapping(release, review)
    assert (review / "contract-at-a-glance.md").exists()
    assert (review / "field-mappings.csv").exists()
    assert (review / "residues.csv").exists()
    assert (review / "reviews.csv").exists()
    assert (review / "release-metadata.yaml").exists()
    imported = tmp_path / "imported"
    import_mapping(review, imported)
    assert diff_mappings(release, imported)["semantic"] == []
    assert "draft" in (review / "contract-at-a-glance.md").read_text(encoding="utf-8")


def test_mapping_review_import_preserves_review_evidence_without_approving(
    tmp_path: Path,
) -> None:
    release = _release(tmp_path)
    review = tmp_path / "review"
    render_mapping(release, review)
    columns = next(csv.reader((review / "reviews.csv").open(encoding="utf-8")))
    with (review / "reviews.csv").open("a", encoding="utf-8", newline="") as handle:
        csv.DictWriter(handle, fieldnames=columns).writerow(
            {
                "reviewer_role": "source_owner",
                "reviewing_team": "ATLAS",
                "review_date": "2026-08-13",
                "decision": "accept",
                "assessed_semantic_content_digest_algorithm": "sha256",
                "assessed_semantic_content_digest": "x" * 64,
                "team_contact": "",
                "rationale": "synthetic review evidence",
            }
        )
    imported = tmp_path / "imported"
    import_mapping(review, imported)
    contract = yaml.safe_load(
        (imported / "contract/population-translation-contract.yaml").read_text()
    )
    assert contract["governance"]["lifecycle_status"] == "draft"
    assert (
        contract["governance"]["review_records"][0]["reviewer_role"] == "source_owner"
    )


def test_mapping_review_summary_shows_no_reviews_and_deterministic_review_stamp(
    tmp_path: Path,
) -> None:
    release = _release(tmp_path)
    review = tmp_path / "review"
    render_mapping(release, review)
    assert "Review stamps: no reviews recorded." in (
        review / "contract-at-a-glance.md"
    ).read_text(encoding="utf-8")
    contract_path = release / "contract/population-translation-contract.yaml"
    contract = yaml.safe_load(contract_path.read_text())
    contract["governance"]["review_records"] = [
        {
            "reviewer_role": "source_owner",
            "reviewing_team": "ATLAS",
            "review_date": "2026-08-13",
            "decision": "accept",
            "assessed_semantic_content_digest_algorithm": "sha256",
            "assessed_semantic_content_digest": contract["semantic_content_digest"],
            "rationale": "synthetic",
        }
    ]
    contract_path.write_text(yaml.safe_dump(contract), encoding="utf-8")
    render_mapping(release, review)
    assert "2026-08-13 | source_owner | ATLAS | accept" in (
        review / "contract-at-a-glance.md"
    ).read_text(encoding="utf-8")


def test_mapping_diff_classifies_nonsemantic_contract_changes(tmp_path: Path) -> None:
    old = _release(tmp_path / "old")
    new = _release(tmp_path / "new")
    old_contract = old / "contract/population-translation-contract.yaml"
    new_contract = new / "contract/population-translation-contract.yaml"
    new_contract.write_text(
        old_contract.read_text(encoding="utf-8").replace("team.csv", "new-team.csv"),
        encoding="utf-8",
    )
    diff = diff_mappings(old, new)
    assert diff["semantic"] == []
    assert diff["encoding_source"]
