# ATLAS contract review

The established ATLAS module keeps the three current post-ATLAS record shapes
together. Review the native fields here before considering the PILATES handoff
profile or any cross-model mapping.

## Established current-workflow records

| Physical role | LinkML class | Review first |
| --- | --- | --- |
| Household row consumed by ATLAS | [AtlasHouseholdInput](../schema/AtlasHouseholdInput.md) | Field spelling, household identifiers, code meanings, types, and nullability. |
| Person row consumed by ATLAS | [AtlasPersonInput](../schema/AtlasPersonInput.md) | Field spelling, person and household identity scope, and demographic/status codes. |
| Vehicle row produced by ATLAS | [AtlasVehicleOutput](../schema/AtlasVehicleOutput.md) | Field spelling, `(household_id, vehicle_id, year)` identity, and output-year semantics. |

## Provisional fleet-output records

These are separate from the established records above. They provisionally model
the supplied paired CSV structure as an ATLAS fleet-output contract, while the
owner confirms its release/export context and field semantics.

| Physical example role | LinkML class | Owner question |
| --- | --- | --- |
| Household fleet summary | [AtlasHouseholdFleetOutput](../schema/AtlasHouseholdFleetOutput.md) | Is this a native export, and what release/export context produced it? |
| Vehicle fleet rows | [AtlasVehicleFleetOutput](../schema/AtlasVehicleFleetOutput.md) | Confirm export status, `annual_mileage` units, and omitted year/geography semantics. |

Do not use aliases to represent an adapter rename or a prospective mapping.
An alias is appropriate only after ATLAS confirms that it is an exact, durable
synonym for the same native record or field.
