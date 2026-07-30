# POLARIS population identity projections

`polaris_population.yaml` describes POLARIS-owned household, person, and
vehicle identity fields observed in translated population artifacts. It is an
identity-bearing partial projection, not a complete POLARIS schema or a claim
that its physical names belong in a shared kernel.

ATLAS vehicle identity includes `(household_id, vehicle_id, year)`, but the
translation emits only `hhold` and `vehicle_id`. The translated pair is scoped
to the enclosing `PopulationSnapshot` artifact whose `simulation_year` agrees
with the ATLAS vehicle year; `vehicle_id` is not a globally stable identifier.
The required `hhold` household alias remains explicit so the current physical
representation is reviewable.
