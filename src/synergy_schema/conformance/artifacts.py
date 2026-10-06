"""Artifact reference and digest validation helpers."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

import json

from .diagnostics import Diagnostic

_SHA256_HEX_LENGTH = 64
_MAX_SAFE_JCS_INTEGER = 9007199254740991


def jcs_json_bytes(value: object) -> bytes:
    """Encode the restricted JSON value set with RFC 8785 key ordering."""

    def encode(item: object) -> str:
        if item is None:
            raise ValueError("null is not permitted in canonical JCS encoding")
        if isinstance(item, bool):
            return "true" if item else "false"
        if isinstance(item, int):
            if abs(item) > _MAX_SAFE_JCS_INTEGER:
                raise ValueError("integer is outside JCS safe range")
            return str(item)
        if isinstance(item, str):
            if any(0xD800 <= ord(character) <= 0xDFFF for character in item):
                raise ValueError("strings cannot contain surrogates")
            return json.dumps(item, ensure_ascii=False, separators=(",", ":"))
        if isinstance(item, list):
            return "[" + ",".join(encode(child) for child in item) + "]"
        if isinstance(item, Mapping):
            if not all(isinstance(key, str) for key in item):
                raise ValueError("object keys must be strings")
            ordered_keys = sorted(item, key=lambda key: key.encode("utf-16be"))
            return (
                "{"
                + ",".join(f"{encode(key)}:{encode(item[key])}" for key in ordered_keys)
                + "}"
            )
        raise ValueError(f"unsupported type for canonical JCS: {type(item)}")

    return encode(value).encode("utf-8")


def is_sha256_digest(value: object) -> bool:
    """Return True if value is a 64-character lowercase hex string."""
    return (
        isinstance(value, str)
        and len(value) == _SHA256_HEX_LENGTH
        and all(c in "0123456789abcdef" for c in value)
    )


def artifact_digest(reference: object) -> str | None:
    """Extract lowercase hex content digest from a PhysicalArtifactReference."""
    if not isinstance(reference, Mapping):
        return None
    identity = reference.get("artifact_identity")
    if not isinstance(identity, Mapping):
        return None
    digest = identity.get("content_digest")
    if isinstance(digest, str) and is_sha256_digest(digest):
        return digest
    return None


def validate_file_artifact_digest(
    reference: Mapping[str, Any], base_dir: Path | None = None
) -> list[Diagnostic]:
    """Verify that a referenced file exists and matches its declared content digest."""
    diagnostics: list[Diagnostic] = []
    locator = reference.get("locator")
    if not isinstance(locator, str):
        diagnostics.append(
            Diagnostic(
                "ARTIFACT_LOCATOR_INVALID", "missing or non-string locator", "error"
            )
        )
        return diagnostics

    path = Path(locator) if base_dir is None else base_dir / locator
    if not path.is_file():
        diagnostics.append(
            Diagnostic(
                "ARTIFACT_FILE_NOT_FOUND",
                f"referenced artifact file not found: {locator}",
                "error",
            )
        )
        return diagnostics

    declared = artifact_digest(reference)
    if declared is None:
        diagnostics.append(
            Diagnostic(
                "ARTIFACT_DIGEST_INVALID",
                "missing or invalid declared sha256 content_digest",
                "error",
            )
        )
        return diagnostics

    actual = sha256(path.read_bytes()).hexdigest()
    if actual != declared:
        diagnostics.append(
            Diagnostic(
                "ARTIFACT_DIGEST_MISMATCH",
                f"computed sha256 {actual} does not match declared {declared}",
                "error",
            )
        )
    return diagnostics
