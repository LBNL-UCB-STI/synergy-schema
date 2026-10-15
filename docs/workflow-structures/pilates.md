# PILATES post-ATLAS population

## Current

The [one-year mapping handshake](../bring-an-existing-mapping/one-year-mapping-handshake.md)
describes a PILATES handoff: the point after ATLAS has updated which
vehicles each household owns.

In the [population ledger architecture](../shared-structure/population-snapshots-and-artifact-identity.md),
PILATES executes as an explicit sequence of model steps:
1. **UrbanSim**: Establishes land-use base states, residential locations, and household structures.
2. **DEMOS**: Simulates demographic transitions, aging, employment, and schooling.
3. **ATLAS**: Refines vehicle fleets, vehicle ownership, and charging access.

Snapshots form a versioned DAG within the ledger (`PopulationLedger`) for one scenario
definition and stochastic realization. Annual checkpoints (`PopulationCheckpoint`) tag the
designated snapshot that represents the official population state for each simulation year.
Every step records its execution run in Consist (`producing_run.run_id`).

The repository includes a canonical multi-year simulation example at
`examples/ledger/austin_multiyear_simulation.yaml`. It can be verified with:

```sh
synergy-conformance check-ledger \
  --ledger examples/ledger/austin_multiyear_simulation.yaml \
  --data-root examples/ledger \
  --verify-consist-provenance \
  --consist-db examples/ledger/austin_multiyear/provenance.duckdb \
  --verify-state-digest
```

## Proposed

Automated emission of ledger snapshots directly from the PILATES orchestrator
runtime is planned as an upstream workflow adapter. Ledger checks can then
run continuously across distributed simulation pipelines.


## Out of scope

This repository does not deploy or mutate the live PILATES runtime. A valid
ledger demonstrates that the documented records, physical artifact digests,
and Consist provenance traces agree; it does not claim that PILATES emits them
without orchestration tooling.
