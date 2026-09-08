# UrbanSim population identity and join records

`urbansim_population.yaml` describes the UrbanSim-owned household and person
identity fields used by the current PILATES population handoff. It is a partial
set of fields for joins, not a complete UrbanSim input contract or a shared-kernel
definition of UrbanSim fields.

The work and school zone aliases are explicitly scoped to the current PILATES
ActivitySim adapter. Their presence does not establish a durable cross-model
vocabulary or validation of cross-table references.
