from __future__ import annotations

from pathlib import Path

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
