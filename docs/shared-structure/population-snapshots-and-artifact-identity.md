# Population snapshots and artifact identity

A population snapshot is a commit in the population ledger. It describes the
state of the population after a specific model step executes: it records the
model step that produced it, the parent snapshot(s) it was built from, and the
resulting core state.

In Synergy's ledger model:
- A `PopulationSnapshot` is a commit naming its producing model step and parent snapshots.
- A `CoreState` is the commit's tree: a map from each established core facet to a canonical content digest.
- A `PopulationCheckpoint` is a tag designating a snapshot as the official population for a given simulation year.

The [core schema UML](../schema/core-schema-uml.md#core-entity-tables) shows how core entity tables
define key-only identities for households, persons, and vehicles, with explicit
membership relationships. Models read and write model-owned views, and Synergy
facet mappings derive core facets from those views.

Artifact identity answers a different question: which exact file carried the
records? A content digest stays the same when a file moves and changes when
its contents change. Provenance then records which run produced or used that
file.

Keeping population identity, facet content identity, and artifact provenance
separate means no single row ID, filename, or run record is asked to prove more
than it can.
