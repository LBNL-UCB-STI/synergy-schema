# Shared concepts

This directory is for concepts that mean the same thing across two or more
models. Likely examples include identifiers, units, time periods, and
geographic references, once their meaning has been agreed.

Keep this area small. A field should not move here just because two models use
the same name. The teams involved should agree that the field represents the
same idea, uses compatible values, and can be described without favoring one
model's implementation.

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
