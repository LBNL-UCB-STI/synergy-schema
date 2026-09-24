# Post-ATLAS population bundle

This page goes into detail on the current PILATES handoff. For a quick
overview, see [PILATES post-ATLAS population](../workflow-structures/pilates.md).

The post-ATLAS population bundle is the PILATES workflow profile in Synergy
Schema today. It describes one yearly population handoff after ATLAS has
updated which vehicles each household owns. It covers three things: the
population being described, the three files delivered together, and a record
of the run that produced them.

It is different from a
[staged core-population assembly](../workflow-structures/core-population-assembly.md).
An assembly can collect partial contributions before any consumer is ready for
them. This bundle describes the complete three-file handoff that PILATES
expects.

## Population snapshot

A [PopulationSnapshot](../schema/PopulationSnapshot.md) identifies the
population for one scenario, year, and random draw. It can point to the
previous year's snapshot without implying that every record or ID stayed the
same.

[HouseholdState](../schema/HouseholdState.md) and
[PersonState](../schema/PersonState.md) describe a household or person as they
are in that snapshot. A [HouseholdMembership](../schema/HouseholdMembership.md)
links a person to a household in the same snapshot. Because membership belongs
to a specific year, people can join, leave, or move between households as the
scenario plays out.

Optional longitudinal references let the producing model keep a household's or
person's ID across years. These are separate from the per-snapshot IDs used
for each year's records.

## Native ATLAS records

The profile uses three record definitions owned by ATLAS:

- [AtlasHouseholdInput](../schema/AtlasHouseholdInput.md), a household row
  read by ATLAS;
- [AtlasPersonInput](../schema/AtlasPersonInput.md), a person row read by
  ATLAS; and
- [AtlasVehicleOutput](../schema/AtlasVehicleOutput.md), a vehicle row
  written by ATLAS.

ATLAS still owns these fields and codes. The PILATES profile references them
in the handoff without redefining them.

## Physical handoff

A [PopulationSnapshotBundle](../schema/PopulationSnapshotBundle.md) is a
specific kind of [HandoffBundle](../schema/HandoffBundle.md). Its members
identify the household, person, and vehicle files, the role of each file, and
the ATLAS schema used to read its rows.

Locators tell consumers where to find each file. Fingerprints pin down its
exact contents. These file identities are separate from the household and
person IDs inside the files.

## Realization identity and receipt

A trajectory has its own fingerprint, separate from the fingerprints of its
files and from any receipt evidence that can change over time. It covers the
scenario version, random draw, ordered snapshots, required file roles, file
fingerprints, and the schemas used to read them. The
[realization-identity specification](../shared-structure/realization-identity.md)
covers the exact bytes, validation rules, test vector, and trust boundary.

## Provenance

The bundle includes a
[ConsistProvenanceDocument](../schema/ConsistProvenanceDocument.md) listing the
runs, the files, and which files each run read or wrote. A run's identity comes
from its Consist ledger namespace plus its local ID. Where the ledger or files
happen to be stored can change, so those locations are treated as operational
details, not identity.

## Cross-model mappings

The mapping manifest relates UrbanSim, ActivitySim, ATLAS, POLARIS, and shared
population fields. At the post-ATLAS handoff, ATLAS household and person IDs
can fill in the optional longitudinal references, and the snapshot supplies
the year. Composite rules then build the per-snapshot IDs for
`HouseholdState`, `PersonState`, and `HouseholdMembership`.

These rules describe how IDs are built; they aren't extra files in the
handoff. The [cross-model population identity map](../schema/cross-model-population-identity.md)
shows which IDs are kept, renamed, derived, or combined.

## Example and detailed reference

The repository includes a
[complete synthetic bundle example](https://github.com/LBNL-UCB-STI/synergy-schema/tree/main/examples/post_atlas_population_bundle)
with sample ATLAS rows, shared population records, the bundle manifest,
Consist provenance, and the cross-model mapping manifest. It shows the shape
of the exchange but isn't production data or a full population validator.

For field-level details, see the
[complete generated schema reference](../schema/index.md). The generated class
pages are the authority on required fields, types, cardinality, and
relationships.
