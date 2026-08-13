"""Creation and validation of deliberately non-production discovery receipts."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

from .diagnostics import CheckResult, Diagnostic, InputError


def _artifact(path: Path) -> dict[str, object]:
    try:
        digest = sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise InputError(f"cannot read explicit artifact {path}: {error}") from error
    return {
        "artifact_identity": {"digest_algorithm": "sha256", "content_digest": digest},
        "locator": str(path),
    }


def create_day_zero_manifest(
    artifact: Path | str,
    producer_artifact: Path | str,
    native_scenario_namespace: str,
    native_scenario: str,
    year: int,
) -> dict[str, object]:
    """Make a receipt from exactly the two explicitly named byte streams."""
    return {
        "generation_mode": "manual_discovery",
        "native_scenario_label": native_scenario,
        "native_scenario_namespace": native_scenario_namespace,
        "payload_artifact": _artifact(Path(artifact)),
        "producer_artifact": _artifact(Path(producer_artifact)),
        "simulation_year": int(year),
    }


def validate_day_zero_manifest(
    manifest: Mapping[str, Any], *, production: bool = False
) -> CheckResult:
    diagnostics: list[Diagnostic] = []
    if manifest.get("generation_mode") != "manual_discovery":
        diagnostics.append(
            Diagnostic(
                "DAY_ZERO_MODE_INVALID",
                "day-zero manifests must use manual_discovery",
                "error",
            )
        )
    for name in ("payload_artifact", "producer_artifact"):
        identity = (
            (manifest.get(name) or {}).get("artifact_identity")
            if isinstance(manifest.get(name), Mapping)
            else None
        )
        if (
            not isinstance(identity, Mapping)
            or identity.get("digest_algorithm") != "sha256"
            or not identity.get("content_digest")
        ):
            diagnostics.append(
                Diagnostic(
                    "ARTIFACT_IDENTITY_MISMATCH",
                    f"{name} lacks a SHA-256 byte identity",
                    "error",
                )
            )
    if production:
        diagnostics.append(
            Diagnostic(
                "PRODUCTION_RECEIPT_REQUIRED",
                "manual discovery manifests cannot be production receipts",
                "error",
            )
        )
    return CheckResult(tuple(diagnostics))
