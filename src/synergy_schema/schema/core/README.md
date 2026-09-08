# Shared concepts

This directory holds concepts with an agreed meaning across at least two
models, such as identifiers, units, time periods, and geographic references.
Keep it small: a shared name is insufficient; teams must agree on meaning,
values, and a model-neutral description.

Details that belong to only one model should stay in
[`../models/`](../models/). Relationships between different definitions belong
in [`../mappings/`](../mappings/).

The first shared concepts are `PopulationSnapshot`, snapshot-scoped
`HouseholdState` and `PersonState` occurrences, `HouseholdMembership`, and
provider-neutral handoff/provenance references. They describe population state
and artifact context without defining native household, person, vehicle, or
zonal-land-use rows.

`HouseholdState`, `PersonState`, and `HouseholdMembership` intentionally carry
only identity, snapshot scope, and optional longitudinal identity. Native
models own demographic, economic, location, and code fields. A higher-level
bundle validator, not standard LinkML reference validation, must check that a
membership's referenced states are co-present and share its snapshot.
