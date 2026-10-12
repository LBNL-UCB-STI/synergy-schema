# Model-owned schemas

Each model describes its data here in its own terms; differences in fields,
codes, table shapes, and requirements stay visible rather than being forced
into a common model. The model-owning team remains authoritative. Put
relationships between definitions in [`../mappings/`](../mappings/); move a
concept to [`../core/`](../core/) only after participating teams agree its
meaning is shared.

The model-owned population slices are:

- [`activitysim/`](activitysim/), the ActivitySim household, person, and
  land-use-zone identity and join records observed by the current PILATES adapter.
- [`atlas/`](atlas/), the ATLAS household and person inputs plus vehicle output
  used by the post-ATLAS population handoff.
- [`atlas/atlas_fleet_observed_example_v1.yaml`](atlas/atlas_fleet_observed_example_v1.yaml),
  a provisional model-contract shape for observed fleet-output tables; it is
  not a shared-handoff profile.
- [`beam/`](beam/), the BEAM household, person, and travel plans input classes
  plus network travel skims output observed in the PILATES reference implementation.
- [`demos/`](demos/), provisional row contracts for observed DEMOS
  `POLARIS_mapped` exports; their publisher and target-ingest status remain
  unconfirmed.
- [`polaris/`](polaris/), the translated POLARIS household, person, and
  vehicle identity records.
- [`polaris/polaris_demand_database_v1.yaml`](polaris/polaris_demand_database_v1.yaml),
  a description of selected population tables from an observed demand database;
  it is neither a complete database schema nor a confirmed seed-input contract.
- [`urbansim/`](urbansim/), the UrbanSim household and person join records.

Established record sets remain model-owned. Provisional record sets record
observed associations pending semantic review. PILATES binds approved artifacts
through an operational profile without copying fields into a shared kernel.

## Provisional-contract entry point

[`../observed_examples.yaml`](../observed_examples.yaml) assembles the three
provisional examples for local review and focused validation. It deliberately
is not imported by `synergy_schema.yaml`: the examples are separate model
contexts, not a shared handoff, approved mapping, or aggregate release.
