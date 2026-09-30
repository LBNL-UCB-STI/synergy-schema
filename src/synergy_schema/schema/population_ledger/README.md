# Population ledger (provisional)

A draft for review with ANL. It runs alongside `../core/` and `../assembly/`
and is not imported by `../synergy_schema.yaml`. Design notes:
`docs-internal/2026-09-23-within-year-population-transitions.md`.

It borrows from git:

| Git | Ledger |
|---|---|
| Commit | `PopulationSnapshot`: one model step, its parent snapshot(s), and the full core state afterward |
| Tree | `CoreState`: a map from each core facet to a `FacetContentDigest`, identified by a `StateDigest` |
| Tag | `PopulationCheckpoint`: the snapshot that counts as a given year's population |
| Branch | `PopulationLedger`: one scenario and one stochastic realization |

**Models read and write views, not core tables.** A `ModelView` is a
model-owned artifact, such as the ATLAS household input or the DEMOS persons
output. Synergy derives each core facet from output views through a mapping.
For input views, the ledger records which core state they were prepared from;
that state must be a parent snapshot's state. This records population
provenance, but does not by itself establish that every model input is current.
Model-owned values such as income or location may change without changing a
core facet. Reuse decisions need explicit dependencies on the input artifacts
or their contracts, in addition to any core-state dependencies.

Each facet has a core table class (`CoreHousehold`, `CorePerson`,
`CoreHouseholdMembership`, `CoreVehicle`, `CoreHouseholdVehicleAssignment`).
These are Synergy's canonical form, not files that models exchange. The core
table's attributes are exactly what `core_facet_table/v1` hashes.

A `CoreFacetMapping` is declared once per ledger. It says which kinds of
output view a facet is derived from, binds view columns to core fields
(`CoreFieldFromView`), and can pin a reviewed `PopulationTranslationContract`.
Its inputs can include the parent's content for some facets, for steps whose
views are partial (for example a deaths-only delta).

Each `CoreFacetEntry` in a state names its mapping and the actual inputs
used: output views of this step (`derived_from_views`) and parent facet
content pinned by digest (`derived_from_facets`). An entry either repeats the
parent's entry unchanged or is produced by this step, so history comes from
following parent snapshots. `stored_object` is a materialized core table (byte
identity plus an optional locator) so rebuilding doesn't have to replay a
chain of deltas. A checkpoint requires it for entries derived from parent
facets. Looking tables up by digest alone, without a locator, is left for a
later shared store.

Order comes from the parent links, not from a stored number, so a year can
contain several snapshots (UrbanSim, then DEMOS, then ATLAS). See
`examples/population_ledger/urbansim_demos_atlas_2025.yaml`.

A snapshot can have several parents when independent steps are joined (for
example DEMOS on membership and ATLAS on vehicles, run from the same state).
The join takes each facet from the parent that changed it since their latest
common ancestor; if more than one parent changed the same facet, the join is
rejected. Most ledgers will be linear.

## Three kinds of hash

- `ImmutableArtifactIdentity`: bytes of a file (a view, or a stored core
  table). Answers "is this the exact file?"
- `FacetContentDigest` (`core_facet_table/vN`): normalized rows of a core
  table, however they were produced. Answers "is this the same population
  fact?" Used for `CoreFacetEntry.digest` and pinned `derived_from_facets`.
- `StateDigest` (`core_state/vN`): hash over a state's (facet, facet digest)
  pairs; no file is read. Used for `CoreState.state_digest` and a view's
  `prepared_from_state`.

## Validation

Validation runs in three layers, from cheapest to most thorough.

**1. LinkML shape validation (done).** Checks structure, required fields, the
closed facet list, and a few conditional `rules:`:
- a mapping with `field_bindings` must list `input_view_kinds`;
- an entry with no `derived_from_facets` must cite `derived_from_views`.

The JSON Schema validator enforces these rules. Rules that compare a field
against a set held in another field, or that follow a reference, can't be
expressed this way; LinkML's SHACL generator converts only a few rule patterns.

**2. Ledger conformance plugin (first version done).**
`synergy_schema.conformance.ledger.LedgerConformancePlugin` is a LinkML
`ValidationPlugin`, so it runs through the same `Validator` call as the shape
checks:

```python
from linkml.validator import Validator
from linkml.validator.plugins import JsonschemaValidationPlugin
from synergy_schema.conformance.ledger import LedgerConformancePlugin

Validator(schema, validation_plugins=[
    JsonschemaValidationPlugin(closed=True),
    LedgerConformancePlugin(),
]).validate(ledger, "PopulationLedger")
```

It checks the metadata in one ledger document:
- IDs are unique, there is one root, parents appear before children, and
  years don't run backward;
- joined parents don't change the same facet since their common ancestor;
- reads are established in a parent, and established facets aren't dropped;
- input views were prepared from a parent's state;
- changed digests are declared in `writes`;
- entries use a mapping for their facet and cite only this step's output
  views;
- pinned facet digests match the mapping's `input_facets` and the parent's
  digests;
- checkpoint targets exist and are in the right year, checkpoint entries
  built from parent facets have a `stored_object`, and checkpoint years are
  unique and increasing.

It doesn't yet recompute `state_digest`, check `view_column` against a view's
schema contract, or check coverage of core fields.

**3. Data checks (planned).** These read the actual tables:
- *Canonical facet hashing.* Define `core_facet_table/v1`: the core table
  class's columns in declared order, rows sorted by key, fixed types and null
  handling, then SHA-256. The plugin can then recompute facet and state
  digests, and compare a repeated column against the current facet digest.
- *DDL for core tables.* `gen-sqlddl` on this module gives DuckDB or SQLite
  tables whose primary keys, `unique_keys` (one household per person or
  vehicle), and foreign keys (membership → households, people) are enforced
  on load. The JSON Schema validator ignores `unique_keys`, so this is where
  they take effect. It also matches the Consist/DuckDB index plans.
- *View contracts.* Check view parquet columns against each view's
  `schema_contract`, and the mapping's `view_column`s against those columns,
  so a mapping can't cite a column that doesn't exist. `gen-pydantic` covers
  row-level checks when a pipeline wants them in Python.
- *Plan checks.* Check a planned workflow (steps with reads and writes)
  ahead of a run for read-before-write, conflicting writes, and
  write-after-read. The plugin's per-snapshot rules carry over.
- *Input freshness and reuse.* To skip re-preparing an input after an
  unrelated change, treat it as current if every facet in `step.reads` has
  the same digest now as in its `prepared_from_state`. This covers core facts
  only: the ledger does not version model-owned attributes such as income or
  location, so their staleness is out of scope here (Consist provenance, or a
  later model-facet extension).

Not yet defined: canonical hashing details (row order, type and null
normalization), entity-lineage row structure, a global vehicle identity
(vehicles are keyed by household for now), and the data checks above. Until the
hashing and data checks exist, example digests are illustrative metadata, not
verified identities for population tables.
