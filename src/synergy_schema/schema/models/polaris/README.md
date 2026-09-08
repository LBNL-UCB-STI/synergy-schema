# POLARIS population identity and join records

`polaris_population.yaml` describes POLARIS-owned household, person, and
vehicle identity fields observed in translated population artifacts. It is an
partial set of identity and join fields, not a complete POLARIS schema or a claim
that its physical names belong in a shared kernel.

ATLAS identifies vehicles by `(household_id, vehicle_id, year)`, but the
translation emits `hhold` and `vehicle_id`. That pair is scoped to its
`PopulationSnapshot`, whose `simulation_year` matches the ATLAS year;
`vehicle_id` is not globally stable. `hhold` remains explicit to expose the
physical representation.

`polaris_demand_database_v1.yaml` is a separate provisional description of
selected population tables in a model-associated demand database. Its raw
`hhold` field is intentionally distinct from the translated-output alias above
and is neither unique nor an identifier in that provisional surface.
