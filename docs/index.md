# Synergy Schema

Synergy Schema describes data exchanged between integrated transportation
modeling tools. It gives model teams shared semantic contracts for explaining
what their records mean and how independently owned representations relate,
without requiring those tools to use LinkML at runtime.

The documentation combines maintained conceptual guides with reference pages
generated directly from the LinkML source. The guides explain how the pieces
fit together; the generated pages provide class- and field-level detail.

## Schema organization

The schema separates definitions according to who owns their meaning and where
they are used:

1. **Core concepts** describe ideas whose meaning can remain consistent across
   modeling tools, such as a [population snapshot](schema/PopulationSnapshot.md)
   or a [physical artifact](schema/PhysicalArtifactReference.md).
2. **Model schemas** describe native records owned by individual model teams,
   including the current UrbanSim, ActivitySim, ATLAS, and POLARIS population
   projections.
3. **Workflow profiles** compose core and model-owned definitions into a
   concrete exchange contract, such as the PILATES post-ATLAS handoff.
4. **Mappings** state semantic relationships between independently owned
   representations without copying or redefining either representation.

This separation lets the schema describe shared meaning while preserving model
ownership and physical field names.

## Cross-model population identity

The [cross-model population identity map](schema/cross-model-population-identity.md)
shows how household, person, membership, geography, and vehicle identifiers
relate across UrbanSim, ActivitySim, ATLAS, POLARIS, and the core
snapshot-scoped population model. It distinguishes preserved identifiers from
renamed, derived, composite, and artifact-scoped values.

Semantic population identity answers which household, person, or membership a
record represents. Physical artifact identity answers which exact file bytes
carry those records. Provenance records which workflow run produced or consumed
those artifacts. The schema connects these concerns without treating them as
the same kind of identity.

## Post-ATLAS population handoff

The [post-ATLAS population bundle](pilates/post-atlas-population-bundle.md)
explains the current PILATES handoff profile: its population snapshot, native
ATLAS records, snapshot-scoped household and person state, physical artifact
members, and Consist provenance.

The handoff is the most complete worked example of how the core, model,
profile, mapping, and provenance layers compose into one exchange contract.

## Schema reference

The [complete generated schema reference](schema/index.md) lists every class,
slot, enumeration, and type reachable from the root schema. Useful class-level
entry points include:

- [PopulationSnapshot](schema/PopulationSnapshot.md) for scenario, year, and
  stochastic-realization scope;
- [HouseholdState](schema/HouseholdState.md),
  [PersonState](schema/PersonState.md), and
  [HouseholdMembership](schema/HouseholdMembership.md) for population
  occurrences within a snapshot;
- [PopulationSnapshotBundle](schema/PopulationSnapshotBundle.md) for the
  post-ATLAS PILATES exchange;
- [PopulationRepresentationMapping](schema/PopulationRepresentationMapping.md)
  for cross-representation semantics; and
- [ConsistProvenanceDocument](schema/ConsistProvenanceDocument.md) for portable
  run and artifact lineage.

Primitive LinkML types and individual slot pages are included for complete
lookup coverage. Most conceptual questions are better answered by the guides
above or by class pages.

## Validation boundary

LinkML validates document shape, required fields, value types, and declared
class relationships. It does not by itself open Parquet files, verify content
digests, resolve references across separate artifacts, or prove that a complete
population is referentially consistent. This repository uses focused tests for
the cross-record invariants demonstrated by its synthetic examples; production
artifact and population validation remain separate workflow responsibilities.
