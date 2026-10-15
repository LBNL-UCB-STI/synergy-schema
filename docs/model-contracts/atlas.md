# ATLAS contract review

The established ATLAS records are the three tables used in today's
post-ATLAS handoff. Review these fields first, before looking at the PILATES
handoff profile or any cross-model mapping.

## Established current-workflow records

| Physical role | LinkML class | Review first |
| --- | --- | --- |
| Household row consumed by ATLAS | [AtlasHouseholdInput](../schema/AtlasHouseholdInput.md) | Field spelling, household identifiers, code meanings, types, and nullability. |
| Person row consumed by ATLAS | [AtlasPersonInput](../schema/AtlasPersonInput.md) | Field spelling, person and household identity scope, and demographic/status codes. |
| Vehicle row produced by ATLAS | [AtlasVehicleOutput](../schema/AtlasVehicleOutput.md) | Field spelling, `(household_id, vehicle_id, year)` identity, and output-year semantics. |

## Provisional fleet-output records

These are separate from the established records above. They're a first
attempt at describing the paired fleet-output CSVs we were given. The ATLAS
team still needs to confirm where the files come from and what the fields
mean.

| Physical example role | LinkML class | Owner question |
| --- | --- | --- |
| Household fleet summary | [AtlasHouseholdFleetOutput](../schema/AtlasHouseholdFleetOutput.md) | Is this a native export, and what release/export context produced it? |
| Vehicle fleet rows | [AtlasVehicleFleetOutput](../schema/AtlasVehicleFleetOutput.md) | Confirm export status, `annual_mileage` units, and omitted year/geography semantics. |

Don't use aliases for a rename done by an adapter or for a mapping that's
still being proposed. Only add an alias once ATLAS confirms it's an exact,
permanent synonym for the same record or field.
