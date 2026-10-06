"""Tests for artifact reference validation and canonical JCS serialization."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest

from synergy_schema.conformance.artifacts import (
    artifact_digest,
    is_sha256_digest,
    jcs_json_bytes,
    validate_file_artifact_digest,
)


def test_is_sha256_digest() -> None:
    assert is_sha256_digest("a" * 64) is True
    assert is_sha256_digest("0123456789abcdef" * 4) is True
    assert is_sha256_digest("A" * 64) is False
    assert is_sha256_digest("a" * 63) is False
    assert is_sha256_digest("g" * 64) is False
    assert is_sha256_digest(123) is False
    assert is_sha256_digest(None) is False


def test_artifact_digest_extracts_lowercase_sha256() -> None:
    ref = {
        "artifact_identity": {
            "digest_algorithm": "sha256",
            "content_digest": "a" * 64,
        },
        "locator": "path/to/file.parquet",
    }
    assert artifact_digest(ref) == "a" * 64

    # Invalid cases
    assert artifact_digest({}) is None
    assert artifact_digest({"artifact_identity": "not-a-mapping"}) is None
    assert artifact_digest({"artifact_identity": {"content_digest": "invalid"}}) is None
    assert artifact_digest(None) is None


def test_validate_file_artifact_digest(tmp_path: Path) -> None:
    sample_file = tmp_path / "data.csv"
    sample_file.write_text("hello,world\n", encoding="utf-8")
    expected_digest = sha256(sample_file.read_bytes()).hexdigest()

    valid_ref = {
        "locator": "data.csv",
        "artifact_identity": {
            "digest_algorithm": "sha256",
            "content_digest": expected_digest,
        },
    }
    assert validate_file_artifact_digest(valid_ref, base_dir=tmp_path) == []

    # File not found
    missing_ref = {
        "locator": "missing.csv",
        "artifact_identity": {
            "digest_algorithm": "sha256",
            "content_digest": expected_digest,
        },
    }
    diags = validate_file_artifact_digest(missing_ref, base_dir=tmp_path)
    assert len(diags) == 1
    assert diags[0].code == "ARTIFACT_FILE_NOT_FOUND"

    # Digest mismatch
    mismatch_ref = {
        "locator": "data.csv",
        "artifact_identity": {
            "digest_algorithm": "sha256",
            "content_digest": "b" * 64,
        },
    }
    diags = validate_file_artifact_digest(mismatch_ref, base_dir=tmp_path)
    assert len(diags) == 1
    assert diags[0].code == "ARTIFACT_DIGEST_MISMATCH"


@pytest.mark.parametrize(
    "value",
    [-9007199254740991, 0, 9007199254740991],
)
def test_jcs_accepts_interoperable_integer_boundaries(value: int) -> None:
    assert jcs_json_bytes({"value": value}) == f'{{"value":{value}}}'.encode()


@pytest.mark.parametrize("value", [-9007199254740992, 9007199254740992])
def test_jcs_rejects_integers_outside_interoperable_range(value: int) -> None:
    with pytest.raises(ValueError, match="outside JCS safe range"):
        jcs_json_bytes({"value": value})


def test_jcs_orders_object_keys_as_rfc8785_utf16_code_units() -> None:
    # Emoji \U0001f600 is surrogate pair \ud83d\ude00, which sorts before \ufffd
    assert jcs_json_bytes({"\U0001f600": 1, "\ufffd": 2}) == (
        '{"\U0001f600":1,"\ufffd":2}'.encode("utf-8")
    )


def test_jcs_rejects_unicode_surrogates() -> None:
    with pytest.raises(ValueError, match="surrogate"):
        jcs_json_bytes({"value": "\ud800"})
