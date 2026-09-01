# A population that changes over three years

Two modeling workflows can use the same scenario name and simulation year yet
still describe different worlds. A household may split in one workflow but not
the other. A person may lose a stable identity between years. A policy may
reach one model through a configuration value while another model silently
ignores it. Comparing the final indicators does not reveal which of these
differences caused the result.

Synergy Schema provides a shared language for the parts of the world that need
to agree. This synthetic proof follows one small population through 2025, 2030,
and 2035. One person enters, one household becomes two, and one vehicle moves
with a successor household. Baseline and ZEV branches begin with the same
population identities while POLARIS retains a branch-specific vehicle type.
The models can therefore differ in what they own without losing the same shared
universe.

The records that support this comparison are deliberately explicit. A
[ScenarioDefinition](../schema/ScenarioDefinition.md) identifies the scenario
revision. A [PopulationTrajectory](../schema/PopulationTrajectory.md) orders
the yearly snapshots. [HouseholdState](../schema/HouseholdState.md),
[PersonState](../schema/PersonState.md), and vehicle relationship records say
which entities and connections persist. [VehicleState](../schema/VehicleState.md)
keeps the shared vehicle identity separate from native vehicle attributes. A
[ConsistProvenanceDocument](../schema/ConsistProvenanceDocument.md) connects the
exchange to exact runs and files.

Evidence, interfaces, and review records address different ways that a model
comparison can become ambiguous:

- Evidence identifies the files and runs behind a claim, so a result can be
  checked against the material that produced it.
- Model interfaces show where a shared assumption enters each model's native
  configuration, including cases that are unsupported.
- Mapping review records distinguish a proposed translation from one that has
  received the intended technical and scientific review.

These records focus on the difficult boundaries because those boundaries are
where two otherwise reasonable workflows can stop representing the same world.
They do not require the workflows to use identical internal tables.

This is a test of the documented exchange shape and cross-file checks. It is
not a deployed PILATES or POLARIS runtime, and it does not establish that a
full regional population is valid. [Following the proof from claim to
file](check-the-showcase.md) presents the records, the evidence trail, the
current review status, and two deliberately broken exchanges.
