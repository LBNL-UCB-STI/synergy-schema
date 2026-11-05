"""Deterministic review surfaces for mapping releases."""

from __future__ import annotations

import csv
from copy import deepcopy
import json
from pathlib import Path

import yaml

from .documents import load_mapping, load_mapping_release
from .mappings import mapping_digest, semantic_mapping_projection


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            sorted(rows, key=lambda row: tuple(row[column] for column in columns))
        )


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def render_mapping(release: Path | str, out_dir: Path | str) -> None:
    """Render canonical YAML release facts into stable, editable review files."""
    contract, implementations, ownership = load_mapping_release(release)
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    fields = [
        {
            "id": str(item["id"]),
            "source_kind": str(item["source_element"]["kind"]),
            "source_path": str(item["source_element"]["path"]),
            "target_kind": str(item["target_element"]["kind"]),
            "target_path": str(item["target_element"]["path"]),
            "transformation_mode": str(item["transformation_mode"]),
            "rule": str(item["rule"]),
            "implementation_evidence": _json(item.get("implementation_evidence", [])),
        }
        for item in contract.get("field_mappings", [])
    ]
    _write_csv(
        output / "field-mappings.csv",
        [
            "id",
            "source_kind",
            "source_path",
            "target_kind",
            "target_path",
            "transformation_mode",
            "rule",
            "implementation_evidence",
        ],
        fields,
    )
    residues = [
        {
            "id": str(item["id"]),
            "residue_kind": str(item["residue_kind"]),
            "affected_elements": _json(item.get("affected_elements", [])),
            "deterministic_rule": str(item.get("deterministic_rule") or ""),
            "default_value": _json(item["default_value"])
            if item.get("default_value") is not None
            else "",
            "lookup_table": _json(item["lookup_table"])
            if item.get("lookup_table") is not None
            else "",
            "rationale": str(item["rationale"]),
            "disposition": str(item["disposition"]),
            "implementation_evidence": _json(item.get("implementation_evidence", [])),
        }
        for item in contract.get("residue_records", [])
    ]
    _write_csv(
        output / "residues.csv",
        [
            "id",
            "residue_kind",
            "affected_elements",
            "deterministic_rule",
            "default_value",
            "lookup_table",
            "rationale",
            "disposition",
            "implementation_evidence",
        ],
        residues,
    )
    reviews = [
        {key: str(value) for key, value in item.items()}
        for item in contract.get("governance", {}).get("review_records", [])
    ]
    review_columns = [
        "reviewer_role",
        "reviewing_team",
        "review_date",
        "decision",
        "assessed_semantic_content_digest_algorithm",
        "assessed_semantic_content_digest",
        "team_contact",
        "rationale",
    ]
    _write_csv(
        output / "reviews.csv",
        review_columns,
        [{column: row.get(column, "") for column in review_columns} for row in reviews],
    )
    metadata = {
        "contract": {
            key: contract[key]
            for key in (
                "id",
                "revision",
                "semantic_content_digest_algorithm",
                "semantic_content_digest",
                "source_catalog",
                "target_catalog",
                "source_schema_contract",
                "target_schema_contract",
                "encoding_source",
                "supporting_sources",
                "governance",
            )
            if key in contract
        },
        "ownership": ownership,
        "implementations": implementations,
    }
    (output / "release-metadata.yaml").write_text(
        yaml.safe_dump(metadata, sort_keys=True), encoding="utf-8"
    )
    governance = contract.get("governance", {})
    review_stamps = sorted(
        (
            str(item.get("review_date", "")),
            str(item.get("reviewer_role", "")),
            str(item.get("reviewing_team", "")),
            str(item.get("decision", "")),
        )
        for item in governance.get("review_records", [])
        if isinstance(item, dict)
    )
    review_summary = (
        "Review stamps: no reviews recorded."
        if not review_stamps
        else "Review stamps:\n"
        + "\n".join(f"- {' | '.join(stamp)}" for stamp in review_stamps)
    )
    rendered_summary = (
        "# Contract at a glance\n\n"
        f"- Contract: `{contract.get('id')}` revision `{contract.get('revision')}`\n"
        f"- Semantic identity: `{contract.get('semantic_content_digest_algorithm')}:{contract.get('semantic_content_digest')}`\n"
        f"- Lifecycle: `{governance.get('lifecycle_status')}`\n"
        f"- Teams: source `{ownership.get('source_owner')}`, target `{ownership.get('target_owner')}`\n"
        f"- Encoding source: `{(contract.get('encoding_source') or {}).get('locator', '')}`\n"
        f"- Coverage: {len(fields)} mappings; {len(residues)} residues\n"
        f"- Implementations: {len(implementations)}\n\n" + review_summary + "\n"
    )
    (output / "contract-at-a-glance.md").write_text(rendered_summary, encoding="utf-8")


def import_mapping(review_dir: Path | str, out_release: Path | str) -> None:
    """Import the normalized CSV package; Markdown is intentionally ignored."""
    review = Path(review_dir)
    metadata = load_mapping(review / "release-metadata.yaml")
    contract = deepcopy(metadata["contract"])
    with (review / "field-mappings.csv").open(encoding="utf-8", newline="") as handle:
        contract["field_mappings"] = [
            {
                "id": row["id"],
                "source_element": {
                    "catalog": contract["source_catalog"],
                    "kind": row["source_kind"],
                    "path": row["source_path"],
                },
                "target_element": {
                    "catalog": contract["target_catalog"],
                    "kind": row["target_kind"],
                    "path": row["target_path"],
                },
                "transformation_mode": row["transformation_mode"],
                "rule": row["rule"],
                "implementation_evidence": json.loads(row["implementation_evidence"]),
            }
            for row in csv.DictReader(handle)
        ]
    with (review / "residues.csv").open(encoding="utf-8", newline="") as handle:
        residue_records = []
        for row in csv.DictReader(handle):
            record: dict[str, object] = {
                "id": row["id"],
                "residue_kind": row["residue_kind"],
                "affected_elements": json.loads(row["affected_elements"]),
                "deterministic_rule": row["deterministic_rule"] or None,
                "rationale": row["rationale"],
                "disposition": row["disposition"],
                "implementation_evidence": json.loads(row["implementation_evidence"]),
            }
            if row.get("default_value"):
                parsed_default = json.loads(row["default_value"])
                if parsed_default is not None:
                    record["default_value"] = parsed_default
            if row.get("lookup_table"):
                parsed_lookup = json.loads(row["lookup_table"])
                if parsed_lookup is not None:
                    record["lookup_table"] = parsed_lookup
            residue_records.append(record)
        contract["residue_records"] = residue_records
    with (review / "reviews.csv").open(encoding="utf-8", newline="") as handle:
        contract.setdefault("governance", {})["review_records"] = [
            {key: value for key, value in row.items() if value}
            for row in csv.DictReader(handle)
        ]
    # CSV evidence does not choose or promote the lifecycle; metadata remains authoritative.
    contract["semantic_content_digest"] = mapping_digest(contract)
    output = Path(out_release)
    (output / "contract").mkdir(parents=True, exist_ok=True)
    (output / "implementation").mkdir(exist_ok=True)
    (output / "contract/population-translation-contract.yaml").write_text(
        yaml.safe_dump(contract, sort_keys=True), encoding="utf-8"
    )
    (output / "ownership.yaml").write_text(
        yaml.safe_dump(metadata["ownership"], sort_keys=True), encoding="utf-8"
    )
    for implementation in metadata.get("implementations", []):
        (
            output / "implementation" / f"{implementation['id'].replace(':', '-')}.yaml"
        ).write_text(yaml.safe_dump(implementation, sort_keys=True), encoding="utf-8")


def diff_mappings(old: Path | str, new: Path | str) -> dict[str, list[str]]:
    """Classify intentional mapping-release changes without conflating identities."""
    old_contract, old_impl, old_ownership = load_mapping_release(old)
    new_contract, new_impl, new_ownership = load_mapping_release(new)
    result = {
        "semantic": [],
        "encoding_source": [],
        "implementation_only": [],
        "governance_only": [],
    }
    if semantic_mapping_projection(old_contract) != semantic_mapping_projection(
        new_contract
    ):
        result["semantic"].append("canonical semantic projection changed")
    if old_contract.get("encoding_source") != new_contract.get("encoding_source"):
        result["encoding_source"].append("encoding source changed")
    if old_impl != new_impl:
        result["implementation_only"].append("implementation registration changed")
    if (
        old_contract.get("governance") != new_contract.get("governance")
        or old_ownership != new_ownership
    ):
        result["governance_only"].append("governance or ownership changed")
    return result
