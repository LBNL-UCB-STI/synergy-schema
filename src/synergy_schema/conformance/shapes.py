"""Closed LinkML profile validation for public bundle commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from linkml.validator import Validator
from linkml.validator.plugins import JsonschemaValidationPlugin

from .diagnostics import CheckResult, Diagnostic


def validate_bundle_shape(
    schema_path: str | Path, bundle: Mapping[str, Any], root: str
) -> CheckResult:
    """Validate one bundle as a closed instance of its published LinkML root."""
    report = Validator(
        str(schema_path), validation_plugins=[JsonschemaValidationPlugin(closed=True)]
    ).validate(dict(bundle), root)
    messages = sorted({str(result.message) for result in report.results})
    return CheckResult(
        tuple(
            Diagnostic("BUNDLE_SHAPE_INVALID", f"{root}: {message}", "error")
            for message in messages
        )
    )
