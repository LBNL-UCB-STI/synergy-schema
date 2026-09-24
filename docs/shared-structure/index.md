# How Synergy is organized

Synergy draws a line between the facts every model needs to agree on and the
details that stay inside each model. That shared set is kept small on purpose:
the scenario, the year, who is in the population, how people and vehicles
relate, and exactly which files were exchanged. Model settings, detailed
attributes, and predictions stay with the model that owns them.

## The agreement boundary

Two workflows are comparable on a shared record when they're making the same
kind of claim about the same scenario version, year, random draw, and
authority. The claim may be left out when a model doesn't represent that fact,
but two authoritative claims cannot contradict each other and still count as
the same shared universe.

Shared facts include the chosen scenario, the year, a person's ID within one
year's population, and which household that person belongs to. Age, vehicle
technology, and predicted travel behavior stay with each model, because
different models can reasonably represent or calculate them differently.

The shared structure does not prevent disagreement. It makes disagreement
visible and gives the checker something precise to compare.

## Exchange structure

The shared schema also describes the files themselves: what's in them, which
schema reads them, which model settings or columns they touch, and which files
travel together. These records say what crossed a boundary and how to read
it. They don't take over ownership of any model's schema or files.

The generated [core schema UML](../schema/core-schema-uml.md) diagrams the
classes and how they connect. The [Glossary](glossary.md) defines recurring
terms and explains the ones that are easy to mix up, such as scenario,
trajectory, snapshot, receipt, residue, and digest.

## Suggested reading order

1. [Scenario definitions and trajectories](scenario-definitions-and-trajectories.md)
   covers the shared assumptions and the timeline.
2. [Population snapshots and artifact identity](population-snapshots-and-artifact-identity.md)
   covers one year's population and the files that carry it.
3. The [realization-identity specification](realization-identity.md) is the
   precise technical reference for tools that need to compute and compare
   identities. Read it after the other two.
