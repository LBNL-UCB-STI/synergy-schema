# PILATES post-ATLAS population

In the PILATES simulation pipeline, UrbanSim simulates land use and ActivitySim
generates travel activity schedules. ATLAS then models household vehicle
choice—updating vehicle ownership, vehicle retirement, and EV technology
adoption.

## Current

The [post-ATLAS population bundle](../pilates/post-atlas-population-bundle.md)
describes one documented PILATES handoff after ATLAS updates vehicle ownership.
It groups household, person, and vehicle files (artifacts) with their roles,
exact file identities (cryptographic hashes), population snapshot (year-specific
state), and Consist run evidence.

## Proposed

Yearly manifests can connect those handoffs into a population trajectory for
one scenario and stochastic realization. Explicit completed and skipped years
make trajectory completeness checkable.

## Out of scope

This repository does not deploy or modify PILATES runtime behavior. A valid
manifest demonstrates that the documented records agree; it does not show that
PILATES emits them automatically.
