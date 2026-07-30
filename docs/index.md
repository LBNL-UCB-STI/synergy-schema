# Synergy Schema

Synergy Schema describes data exchanged between integrated modeling tools. It
gives model teams a shared place to explain what their records mean without
requiring them to use LinkML at runtime.

This preview combines a short introduction with reference pages generated
directly from the current LinkML source. The generated pages are useful for
exploring the schema, but their organization and wording are still evolving.

## Where to start

- [PopulationSnapshot](schema/PopulationSnapshot.md) identifies one
  scenario-specific population state, including its simulation year and
  stochastic realization.
- [HandoffBundle](schema/HandoffBundle.md) describes a collection of physical
  artifacts produced together for a particular purpose.
- [PopulationSnapshotBundle](schema/PopulationSnapshotBundle.md) specializes
  that bundle for the PILATES post-ATLAS population handoff.
- [AtlasHouseholdInput](schema/AtlasHouseholdInput.md),
  [AtlasPersonInput](schema/AtlasPersonInput.md), and
  [AtlasVehicleOutput](schema/AtlasVehicleOutput.md) describe the three native
  ATLAS records currently used by that handoff.
- [ConsistProvenanceDocument](schema/ConsistProvenanceDocument.md) records the
  run and artifact lineage attached by the PILATES profile.

## How the schema is organized

The source definitions have four layers:

1. **Core concepts** describe ideas that can keep the same meaning across
   modeling tools, such as a population snapshot or a physical artifact.
2. **Model schemas** describe records owned by a particular model team. The
   first example is the ATLAS population schema.
3. **Workflow profiles** combine core and model-owned definitions for a
   particular consumer. The current profile describes what PILATES expects
   after ATLAS.
4. **Mappings** will explain relationships between independently owned
   definitions without copying either one.

## Browse the complete reference

The [generated schema reference](schema/index.md) lists every class, slot,
enumeration, and type currently reachable from the root schema. That includes
the pinned Consist provenance module used by the PILATES profile.

Primitive LinkML types and individual slot pages are included for completeness.
Most readers will find the class pages above more useful as an entry point.

## About validation

LinkML can validate whether a document has the expected fields and value types.
Some important bundle checks cross record boundaries—for example, confirming
that a Consist artifact digest agrees with the corresponding handoff member.
Those checks are tested by this repository but are not implied by every
generated reference page.
