"""Offline, checksummed inventories of native model contract elements."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

import yaml


class CatalogValidationError(ValueError):
    """Raised when a native contract catalog is malformed or altered."""


_KINDS = frozenset({"config_path", "artifact_key", "sql_column"})


class _CatalogDumper(yaml.SafeDumper):
    """Use the repository's indented sequence YAML style."""

    def increase_indent(self, flow: bool = False, indentless: bool = False) -> Any:
        return super().increase_indent(flow, False)


def canonical_catalog_projection(document: Mapping[str, Any]) -> dict[str, Any]:
    """Return the stable content addressed by a catalog digest."""
    required = ("catalog_id", "catalog_kind", "revision", "upstream", "elements")
    missing = [field for field in required if field not in document]
    if missing:
        raise CatalogValidationError(
            f"catalog missing required fields: {', '.join(missing)}"
        )
    upstream = document["upstream"]
    elements = document["elements"]
    if not isinstance(upstream, Mapping) or not isinstance(elements, list):
        raise CatalogValidationError(
            "catalog upstream must be a mapping and elements must be a list"
        )
    return {
        "catalog_id": str(document["catalog_id"]),
        "catalog_kind": str(document["catalog_kind"]),
        "revision": str(document["revision"]),
        "upstream": {str(key): upstream[key] for key in sorted(upstream)},
        "elements": sorted(
            [
                {"kind": str(item["kind"]), "path": str(item["path"])}
                for item in elements
            ],
            key=lambda item: (item["kind"], item["path"]),
        ),
    }


def canonical_catalog_json(document: Mapping[str, Any]) -> str:
    """Encode a catalog's semantic projection as deterministic JSON."""
    return json.dumps(
        canonical_catalog_projection(document), sort_keys=True, separators=(",", ":")
    )


def catalog_digest(document: Mapping[str, Any]) -> str:
    """Return the SHA-256 digest of a catalog semantic projection."""
    return sha256(canonical_catalog_json(document).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class NativeCatalog:
    """A validated catalog that resolves native references without runtime imports."""

    document: Mapping[str, Any]

    def resolve(self, kind: str, path: str) -> bool:
        return (kind, path) in {
            (str(element["kind"]), str(element["path"]))
            for element in self.document["elements"]
        }


def _validate(document: Mapping[str, Any]) -> None:
    projection = canonical_catalog_projection(document)
    if document.get("digest_algorithm") != "sha256":
        raise CatalogValidationError("catalog digest_algorithm must be sha256")
    seen: set[tuple[str, str]] = set()
    for element in document["elements"]:
        if (
            not isinstance(element, Mapping)
            or "kind" not in element
            or "path" not in element
        ):
            raise CatalogValidationError("native elements must contain kind and path")
        identity = (str(element["kind"]), str(element["path"]))
        if identity in seen:
            raise CatalogValidationError(
                f"duplicate native element: {identity[0]}:{identity[1]}"
            )
        seen.add(identity)
    digest = document.get("content_digest")
    if not isinstance(digest, str) or digest != catalog_digest(document):
        raise CatalogValidationError(
            "catalog content digest does not match canonical content"
        )
    elements = projection["elements"]
    for element in elements:
        kind, path = element["kind"], element["path"]
        if kind not in _KINDS:
            raise CatalogValidationError(f"unknown native element kind: {kind}")
        if not path:
            raise CatalogValidationError("native element paths must be non-empty")


def load_catalog(path: Path | str) -> NativeCatalog:
    """Load and verify one committed catalog document."""
    source = Path(path)
    try:
        document = yaml.safe_load(source.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise CatalogValidationError(
            f"cannot load catalog {source}: {error}"
        ) from error
    if not isinstance(document, Mapping):
        raise CatalogValidationError("catalog document root must be a mapping")
    _validate(document)
    return NativeCatalog(document=document)


def write_catalog(document: Mapping[str, Any], path: Path | str) -> None:
    """Write a catalog with sorted elements and a recomputed content digest."""
    normalized = canonical_catalog_projection(document)
    normalized["digest_algorithm"] = "sha256"
    normalized["content_digest"] = catalog_digest(normalized)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        yaml.dump(
            normalized, Dumper=_CatalogDumper, sort_keys=False, allow_unicode=True
        ),
        encoding="utf-8",
    )
