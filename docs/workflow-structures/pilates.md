# PILATES post-ATLAS population

## Current

The [one-year mapping handshake](../bring-an-existing-mapping/one-year-mapping-handshake.md)
describes a PILATES handoff: the point after ATLAS has updated which
vehicles each household owns. In the population ledger, ATLAS executes as a model
step that consumes land-use and demographic facets, records its producing run,
and derives the vehicle fleet facet.

## Proposed

Snapshots are organized into a versioned ledger for one scenario definition and
stochastic realization. Annual checkpoints tag the designated snapshot that counts
as the official population for each simulation year.

## Out of scope

This repository doesn't deploy or change PILATES. A valid manifest or ledger shows
that the records agree with each other; it doesn't show that PILATES produces them
automatically.
