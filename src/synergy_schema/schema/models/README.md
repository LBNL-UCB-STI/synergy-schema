# Model-owned schemas

This directory is where each modeling system can describe its own data in its
own terms. ActivitySim, ATLAS, BEAM, POLARIS, and UrbanSim may have different
field names, codes, table shapes, or ideas about what is required. Those
differences should be visible here rather than hidden behind a forced common
model.

The team that knows a model's data should remain the authority for its
definitions. Contributors can review generated tables and diagrams without
using LinkML in the model's runtime.

When two model-owned definitions are related, record that relationship in
[`../mappings/`](../mappings/). Move a concept to
[`../core/`](../core/) only after the participating teams agree that its
meaning is genuinely shared.

The model-owned population slices are:

- [`activitysim/`](activitysim/), the ActivitySim household, person, and
  land-use-zone join projections observed by the current PILATES adapter.
- [`atlas/`](atlas/), the ATLAS household and person inputs plus vehicle output
  used by the post-ATLAS population handoff.
- [`atlas/atlas_fleet_observed_example_v1.yaml`](atlas/atlas_fleet_observed_example_v1.yaml),
  a provisional model-contract shape for observed fleet-output tables; it is
  not a shared-handoff profile.
- [`demos/`](demos/), provisional row contracts for observed DEMOS
  `POLARIS_mapped` exports; their publisher and target-ingest status remain
  unconfirmed.
- [`polaris/`](polaris/), the translated POLARIS household, person, and
  vehicle identity projections.
- [`polaris/polaris_demand_database_v1.yaml`](polaris/polaris_demand_database_v1.yaml),
  a selected population-table projection from an observed demand database;
  it is neither a complete database schema nor a confirmed seed-input contract.
- [`urbansim/`](urbansim/), the UrbanSim household and person join projections.

The established projections remain model-owned. The provisional surfaces record
their observed model association while maintainers review their semantics.
PILATES binds relevant approved artifacts to an operational profile without
copying model fields into a shared kernel.

## Provisional-contract entry point

[`../observed_examples.yaml`](../observed_examples.yaml) assembles the three
provisional surfaces for local review and focused validation. It deliberately
is not imported by `synergy_schema.yaml`: the examples are separate model
contexts, not a shared handoff, approved mapping, or aggregate release.
