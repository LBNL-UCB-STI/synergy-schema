# ATLAS native population records

This directory contains ATLAS-owned record contracts. `atlas_population.yaml`
describes the household and person rows ATLAS receives, plus the vehicle rows
ATLAS produces. It deliberately does not contain PILATES artifact keys, run
identifiers, paths, or snapshot metadata; the PILATES population profile owns
that operational context.

The first slice uses the current exporter spellings as explicit physical
bindings. That keeps the contract reviewable against today's tables without
claiming those spellings belong in the shared kernel. Legacy code values remain
primitive values until the ATLAS owner confirms their vocabularies.
