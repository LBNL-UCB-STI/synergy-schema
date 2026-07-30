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
- [`polaris/`](polaris/), the translated POLARIS household, person, and
  vehicle identity projections.
- [`urbansim/`](urbansim/), the UrbanSim household and person join projections.

Each remains owned by its model. PILATES binds the relevant artifacts to an
operational profile without copying model fields into a shared kernel.
