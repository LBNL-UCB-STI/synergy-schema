"""Strict YAML document loading shared across conformance commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml

from .diagnostics import InputError


def load_mapping(path: Path | str) -> dict[str, Any]:
    source = Path(path)
    try:
        value = yaml.safe_load(source.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise InputError(f"cannot read YAML document {source}: {error}") from error
    if not isinstance(value, Mapping):
        raise InputError(f"YAML document root must be a mapping: {source}")
    return dict(value)


def load_list(path: Path | str) -> list[dict[str, Any]]:
    value = load_mapping(path)
    bindings = value.get("bindings", value.get("model_bindings"))
    if not isinstance(bindings, list) or not all(
        isinstance(item, Mapping) for item in bindings
    ):
        raise InputError(f"document must contain a bindings list: {path}")
    return [dict(item) for item in bindings]
