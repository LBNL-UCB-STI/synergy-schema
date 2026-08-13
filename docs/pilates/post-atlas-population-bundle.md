# Post-ATLAS population bundle

This is the detailed current-workflow explanation. For a short newcomer view,
see [PILATES post-ATLAS population](../workflow-structures/pilates.md).

The post-ATLAS population bundle is the current PILATES workflow profile in
Synergy Schema. It describes one yearly population handoff after ATLAS has
updated household vehicle ownership: the population state being represented,
the three physical table artifacts delivered together, and the provenance of
the run that produced them.

## Population snapshot

A [PopulationSnapshot](../schema/PopulationSnapshot.md) identifies one
scenario-specific population at a simulation year and stochastic realization.
An optional parent snapshot can connect successive states without implying that
all records or identifiers remain unchanged.

[HouseholdState](../schema/HouseholdState.md) and
[PersonState](../schema/PersonState.md) represent household and person
occurrences inside that snapshot. A
[HouseholdMembership](../schema/HouseholdMembership.md) connects a person state
to a household state in the same snapshot. This makes membership temporal:
people can enter, leave, or move between households as a scenario evolves.

Optional longitudinal references can preserve producer-defined household and
person identity across snapshots. They are distinct from the composite
snapshot-scoped identifiers used for individual state occurrences.

## Native ATLAS records

The profile selects three model-owned record contracts:

- [AtlasHouseholdInput](../schema/AtlasHouseholdInput.md) describes a household
  row consumed by ATLAS;
- [AtlasPersonInput](../schema/AtlasPersonInput.md) describes a person row
  consumed by ATLAS; and
- [AtlasVehicleOutput](../schema/AtlasVehicleOutput.md) describes the vehicle
  row produced by ATLAS.

ATLAS retains ownership of these physical fields and code systems. The PILATES
profile composes the contracts into a handoff without redefining their native
representations.

## Physical handoff

A [PopulationSnapshotBundle](../schema/PopulationSnapshotBundle.md) specializes
the general [HandoffBundle](../schema/HandoffBundle.md) for this exchange. Its
members identify the household, person, and vehicle artifacts, the semantic
role of each artifact, and the native schema contract selected for its rows.

Artifact locators help consumers find files. Immutable digests identify the
selected bytes. These artifact identities are separate from household and
person identities carried by rows inside the artifacts.

## Provenance

The bundle carries a
[ConsistProvenanceDocument](../schema/ConsistProvenanceDocument.md) containing
portable run references, artifact references, and input/output associations.
Together, the ledger namespace and local identifiers establish portable
Consist identity. Mutable ledger or artifact locations remain operational
evidence rather than identity.

## Cross-model mappings

The mapping manifest relates UrbanSim, ActivitySim, ATLAS, POLARIS, and core
population fields. At the post-ATLAS boundary, ATLAS household and person
identifiers can populate optional longitudinal references, while the enclosing
snapshot supplies temporal scope. Composite constructions then describe the
snapshot-scoped `HouseholdState`, `PersonState`, and `HouseholdMembership`
identifiers.

These are semantic construction contracts, not additional physical tables in
the handoff. The [cross-model population identity map](../schema/cross-model-population-identity.md)
shows the preserved, renamed, derived, and composite relationships.

## Example and detailed reference

The repository contains a
[complete synthetic bundle example](https://github.com/LBNL-UCB-STI/synergy-schema/tree/main/examples/post_atlas_population_bundle)
with representative ATLAS rows, core population states, the bundle manifest,
Consist provenance, and the cross-model mapping manifest. It illustrates the
contracts but is not a production dataset or a complete population validator.

For field-level lookup, use the
[complete generated schema reference](../schema/index.md). The generated class
pages are authoritative for required fields, ranges, cardinality, and declared
LinkML relationships.
