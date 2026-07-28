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

No model-owned schemas have been added yet.
