# How Synergy is organized

Synergy separates the facts needed to describe a shared universe from the
details that remain inside each modeling system. The boundary is intentionally
small. Shared structure covers scenario identity, time, population occurrences,
declared relationships, and exact file identity. Native settings, detailed
attributes, and model predictions stay with their owning systems.

## The agreement boundary

A core record is comparable when two workflows make the same kind of claim for
the same scenario revision, year, realization, and authority. The claim may be
absent when a model does not represent it, but two authoritative claims cannot
contradict each other and still count as the same shared universe.

Examples include the selected scenario, the simulation year, a person identity
within one snapshot, and a declared household-membership relationship. Age,
vehicle technology, and predicted travel behavior remain model-owned because
different models may legitimately represent or calculate them differently.

Shared structure does not prevent disagreement. It makes disagreement visible
and gives conformance code a precise comparison to perform.

## Exchange structure

Core classes also identify files, the schemas that interpret them, model-owned
interface elements, and groups of files passed together. These records answer
which content moved across a boundary and how it should be read. They do not
transfer ownership of native schemas or payloads.

The generated [core schema UML](../schema/core-schema-uml.md) shows the classes
and typed relationships. The [Glossary](glossary.md) defines recurring terms
and contrasts similar concepts such as scenario, trajectory, snapshot, receipt,
residue, and digest.

## A useful reading order

Start with [scenario definitions and trajectories](scenario-definitions-and-trajectories.md)
to establish the shared assumptions and timeline. Continue with
[population snapshots and artifact identity](population-snapshots-and-artifact-identity.md)
for one year's state and the exact files that carry it. The
[realization-identity specification](realization-identity.md) is the
normative technical reference for independent consumers and can be read after
the conceptual guides.
