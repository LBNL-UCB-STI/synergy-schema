from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import yaml

from synergy_schema.conformance.day_zero import validate_day_zero_manifest


ROOT = Path(__file__).parents[1]


def test_day_zero_example_is_a_byte_accurate_discovery_receipt() -> None:
    example = ROOT / "examples/day_zero_exchange"
    manifest = yaml.safe_load(
        (example / "day-zero-manifest.yaml").read_text(encoding="utf-8")
    )
    assert (
        manifest["payload_artifact"]["artifact_identity"]["content_digest"]
        == sha256((example / "payload.csv").read_bytes()).hexdigest()
    )
    assert (
        manifest["producer_artifact"]["artifact_identity"]["content_digest"]
        == sha256((example / "producer.sql").read_bytes()).hexdigest()
    )
    assert manifest["native_scenario_namespace"] == "synthetic.atlas"
    assert manifest["native_scenario_label"] == "day-zero-demo"
    assert manifest["simulation_year"] == 2025
    assert manifest["generation_mode"] == "manual_discovery"
    assert [
        item.code
        for item in validate_day_zero_manifest(manifest, production=True).diagnostics
    ] == ["PRODUCTION_RECEIPT_REQUIRED"]
