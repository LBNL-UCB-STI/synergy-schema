"""Contract tests for the provisional population ledger."""

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
import yaml
from linkml.validator import Validator
from linkml.validator.plugins import JsonschemaValidationPlugin
from linkml_runtime.utils.schemaview import SchemaView

from synergy_schema.conformance.ledger import LedgerConformancePlugin


ROOT = Path(__file__).parents[1]
SCHEMA_PATH = (
    ROOT
    / "src"
    / "synergy_schema"
    / "schema"
    / "population_ledger"
    / "population_ledger.yaml"
)
EXAMPLES = ROOT / "examples" / "population_ledger"
EXAMPLE_PATH = EXAMPLES / "urbansim_demos_atlas_2025.yaml"
CATALOG_PATH = EXAMPLES / "mapping_catalog.yaml"


def _example() -> dict[str, Any]:
    return yaml.safe_load(EXAMPLE_PATH.read_text())


def _catalog() -> dict[str, Any]:
    return yaml.safe_load(CATALOG_PATH.read_text())


def _validation_messages(
    instance: dict[str, object], root: str = "PopulationLedger"
) -> list[str]:
    report = Validator(
        SCHEMA_PATH,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    ).validate(instance, root)
    return [result.message for result in report.results]


def _ledger_messages(
    instance: dict[str, Any], catalog: dict[str, Any] | None = None
) -> list[str]:
    report = Validator(
        SCHEMA_PATH,
        validation_plugins=[
            JsonschemaValidationPlugin(closed=True),
            LedgerConformancePlugin(_catalog() if catalog is None else catalog),
        ],
    ).validate(instance, "PopulationLedger")
    return [result.message for result in report.results]


def _snapshot(ledger: dict[str, Any], name: str) -> dict[str, Any]:
    return next(
        s for s in ledger["snapshots"] if s["snapshot_id"] == f"snapshot:2025:{name}"
    )


def _entry(snapshot: dict[str, Any], facet: str) -> dict[str, Any]:
    return next(e for e in snapshot["core_state"]["facets"] if e["facet"] == facet)


# Shape validation


def test_example_and_catalog_validate() -> None:
    assert _validation_messages(_example()) == []
    assert _validation_messages(_catalog(), "CoreFacetMappingCatalog") == []


def test_snapshot_requires_step_and_core_state() -> None:
    ledger = _example()
    del ledger["snapshots"][0]["step"]
    del ledger["snapshots"][0]["core_state"]
    messages = _validation_messages(ledger)
    assert any("'step' is a required property" in m for m in messages)
    assert any("'core_state' is a required property" in m for m in messages)


def test_core_facets_are_a_closed_vocabulary() -> None:
    ledger = _example()
    ledger["snapshots"][1]["step"]["reads"] = ["household_income"]
    assert any("household_income" in m for m in _validation_messages(ledger))


def test_digests_must_be_sha256_strings() -> None:
    ledger = _example()
    _entry(ledger["snapshots"][0], "households")["digest"] = "a1a1"
    ledger["snapshots"][0]["core_state"]["state_digest"] = "md5:abc"
    messages = _validation_messages(ledger)
    assert sum("does not match '^sha256:[0-9a-f]{64}$'" in m for m in messages) == 2


def test_digest_forms_are_pinned_per_kind() -> None:
    ledger = _example()
    ledger["facet_digest_form"] = "core_state/v1"
    ledger["state_digest_form"] = "core_facet_table/v1"
    messages = _validation_messages(ledger)
    assert any("does not match '^core_facet_table/v[0-9]+$'" in m for m in messages)
    assert any("does not match '^core_state/v[0-9]+$'" in m for m in messages)


def test_mapping_bindings_require_view_kinds() -> None:
    catalog = _catalog()
    del catalog["mappings"][0]["input_view_kinds"]
    del catalog["mappings"][1]["field_bindings"][0]["view_kind"]
    messages = _validation_messages(catalog, "CoreFacetMappingCatalog")
    assert any("'input_view_kinds' is a required property" in m for m in messages)
    assert any("'view_kind' is a required property" in m for m in messages)


def _core_table_classes() -> dict[str, str]:
    schema_view = SchemaView(str(SCHEMA_PATH))
    return {
        schema_view.get_class(name).annotations["core_facet"].value: name
        for name in schema_view.all_classes()
        if "core_facet" in schema_view.get_class(name).annotations
    }


def test_every_core_facet_has_one_core_table_class() -> None:
    schema_view = SchemaView(str(SCHEMA_PATH))
    facets = set(schema_view.get_enum("CoreFacet").permissible_values)
    assert set(_core_table_classes()) == facets


def test_example_mappings_cover_each_core_table() -> None:
    schema_view = SchemaView(str(SCHEMA_PATH))
    tables = _core_table_classes()
    for mapping in _catalog()["mappings"]:
        bound = {b["core_field"] for b in mapping.get("field_bindings", [])}
        expected = set(schema_view.class_slots(tables[mapping["facet"]]))
        # Fields not bound from a view must come from an input facet.
        assert bound == expected or mapping.get("input_facets"), mapping["mapping_id"]


# Ledger conformance


def test_example_passes_ledger_conformance() -> None:
    assert _ledger_messages(_example()) == []


def test_structural_checks_run_without_a_catalog() -> None:
    report = Validator(
        SCHEMA_PATH, validation_plugins=[LedgerConformancePlugin()]
    ).validate(_example(), "PopulationLedger")
    assert list(report.results) == []


def _break_undeclared_change(ledger: dict[str, Any]) -> None:
    _entry(_snapshot(ledger, "atlas"), "household_membership")["digest"] = (
        "sha256:" + "f" * 64
    )


def _break_unsatisfied_read(ledger: dict[str, Any]) -> None:
    _snapshot(ledger, "atlas")["step"]["reads"].append("vehicles")


def _break_foreign_view_citation(ledger: dict[str, Any]) -> None:
    _snapshot(ledger, "atlas")["step"]["derivations"][0]["views"] = [
        "view:demos/persons_output:2025"
    ]


def _break_checkpoint_store(ledger: dict[str, Any]) -> None:
    del _entry(_snapshot(ledger, "atlas"), "people")["stored_object"]


def _break_stale_input_view(ledger: dict[str, Any]) -> None:
    _snapshot(ledger, "atlas")["step"]["input_views"][0]["prepared_from_state"] = (
        _snapshot(ledger, "urbansim")["core_state"]["state_digest"]
    )


def _break_missing_prepared_state(ledger: dict[str, Any]) -> None:
    del _snapshot(ledger, "demos")["step"]["input_views"][0]["prepared_from_state"]


def _break_dropped_facet(ledger: dict[str, Any]) -> None:
    del _snapshot(ledger, "atlas")["core_state"]["facets"][0]


def _break_derivation_without_entry(ledger: dict[str, Any]) -> None:
    atlas = _snapshot(ledger, "atlas")
    atlas["core_state"]["facets"] = [
        e for e in atlas["core_state"]["facets"] if e["facet"] != "vehicles"
    ]


def _break_wrong_mapping_facet(ledger: dict[str, Any]) -> None:
    _snapshot(ledger, "atlas")["step"]["derivations"][0]["mapping"] = (
        "mapping:demos-core/v1#households"
    )


def _break_unknown_mapping(ledger: dict[str, Any]) -> None:
    _snapshot(ledger, "atlas")["step"]["derivations"][0]["mapping"] = "mapping:nope"


def _break_view_kind(ledger: dict[str, Any]) -> None:
    _snapshot(ledger, "atlas")["step"]["output_views"][0]["view_kind"] = "atlas/other"


def _break_first_parent(ledger: dict[str, Any]) -> None:
    ledger["snapshots"][0]["parent_snapshots"] = ["snapshot:2025:demos"]


def _break_later_parent(ledger: dict[str, Any]) -> None:
    _snapshot(ledger, "atlas")["parent_snapshots"] = []


def _break_year(ledger: dict[str, Any]) -> None:
    _snapshot(ledger, "atlas")["simulation_year"] = 2024


@pytest.mark.parametrize(
    ("breaker", "expected"),
    [
        (
            _break_undeclared_change,
            "household_membership changed but this step has no derivation",
        ),
        (_break_unsatisfied_read, "reads vehicles, which no parent has established"),
        (_break_foreign_view_citation, "which is not an output of this step"),
        (
            _break_checkpoint_store,
            "people is derived from parent facets but has no stored_object",
        ),
        (_break_stale_input_view, "was prepared from a state no parent has"),
        (_break_missing_prepared_state, "has no prepared_from_state"),
        (_break_dropped_facet, "drops households"),
        (
            _break_derivation_without_entry,
            "derives vehicles, which is missing from core_state",
        ),
        (_break_wrong_mapping_facet, "vehicles uses a mapping for households"),
        (_break_unknown_mapping, "uses unknown mapping mapping:nope"),
        (_break_view_kind, "whose view_kind is not declared by its mapping"),
        (_break_first_parent, "the first snapshot must not have a parent"),
        (_break_later_parent, "every later snapshot must have a parent"),
        (_break_year, "simulation_year precedes parent snapshot:2025:demos"),
    ],
)
def test_ledger_conformance_catches(breaker: Any, expected: str) -> None:
    ledger = _example()
    breaker(ledger)
    assert any(expected in m for m in _ledger_messages(ledger))


def test_catalog_must_match_the_ledger() -> None:
    catalog = _catalog()
    catalog["catalog_id"] = "mapping-catalog:other"
    assert any(
        "is not the ledger's mapping-catalog:synthetic-region/v1" in m
        for m in _ledger_messages(_example(), catalog)
    )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda c: c["mappings"].append(deepcopy(c["mappings"][0])),
            "duplicate mapping_id",
        ),
        (
            lambda c: c["mappings"][0]["field_bindings"][0].update(
                view_kind="other/output"
            ),
            "binding view_kind other/output is not declared",
        ),
    ],
)
def test_catalog_problems_are_reported(mutate: Any, message: str) -> None:
    catalog = _catalog()
    mutate(catalog)
    assert any(message in m for m in _ledger_messages(_example(), catalog))


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda ledger: ledger["snapshots"].append(ledger["snapshots"][0]),
            "duplicate snapshot_id",
        ),
        (
            lambda ledger: ledger["snapshots"][0]["step"]["output_views"].append(
                ledger["snapshots"][0]["step"]["output_views"][0]
            ),
            "duplicate view_id",
        ),
    ],
)
def test_ledger_ids_must_be_unique(mutate: Any, message: str) -> None:
    ledger = _example()
    mutate(ledger)
    assert any(message in m for m in _ledger_messages(ledger))


def _joined_ledger() -> dict[str, Any]:
    """Run ATLAS from the UrbanSim state in parallel with DEMOS, then join."""
    ledger = _example()
    urbansim, demos, atlas = ledger["snapshots"]
    atlas["parent_snapshots"] = [urbansim["snapshot_id"]]
    atlas["step"]["input_views"][0]["prepared_from_state"] = urbansim["core_state"][
        "state_digest"
    ]
    atlas["core_state"]["facets"] = deepcopy(urbansim["core_state"]["facets"]) + [
        deepcopy(_entry(atlas, "vehicles"))
    ]
    join = {
        "snapshot_id": "snapshot:2025:join",
        "parent_snapshots": [demos["snapshot_id"], atlas["snapshot_id"]],
        "simulation_year": 2025,
        "step": {
            "model": "synergy",
            "producing_run": {"provider": "consist", "run_id": "join-2025"},
        },
        "core_state": {
            "state_digest": "sha256:" + "53" * 32,
            "facets": deepcopy(demos["core_state"]["facets"])
            + [deepcopy(_entry(atlas, "vehicles"))],
        },
    }
    ledger["snapshots"].append(join)
    ledger["checkpoints"][0]["snapshot"] = join["snapshot_id"]
    return ledger


def test_join_of_independent_facets_is_accepted() -> None:
    assert _ledger_messages(_joined_ledger()) == []


def test_join_of_conflicting_facets_is_rejected() -> None:
    ledger = _joined_ledger()
    atlas = _snapshot(ledger, "atlas")
    atlas["step"]["derivations"].append(
        {
            "facet": "households",
            "mapping": "mapping:urbansim-core/v1#households",
            "views": [],
        }
    )
    _entry(atlas, "households")["digest"] = "sha256:" + "f" * 64
    assert any(
        "more than one parent changed households" in m for m in _ledger_messages(ledger)
    )
