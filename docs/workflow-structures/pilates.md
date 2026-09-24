# PILATES post-ATLAS population

## Current

The [post-ATLAS population bundle](../pilates/post-atlas-population-bundle.md)
describes one PILATES handoff: the point after ATLAS has updated which
vehicles each household owns. It groups the household, person, and vehicle
files together with each file's role, its fingerprint, the population snapshot
it belongs to, and the Consist record of the run that produced it.

## Proposed

Yearly manifests can link those handoffs into a population trajectory for one
scenario and one random draw. Listing which years finished and which were
skipped makes it possible to check whether the trajectory is complete.

## Out of scope

This repository doesn't deploy or change PILATES. A valid manifest shows that
the records agree with each other; it doesn't show that PILATES produces them
automatically.
