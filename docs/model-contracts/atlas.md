# ATLAS contract review

ATLAS (Automotive Technology Life-cycle and Allocation Simulation) models
household vehicle ownership, vehicle retirement, and vehicle technology
adoption over multi-year simulation horizons.

The established ATLAS module defines the three table structures used in the
PILATES pipeline handoff after ATLAS updates household vehicle fleets. Review
the native fields here before considering the PILATES handoff profile or any
cross-model mapping.

## Established current-workflow records

| Exchange file / Table role | LinkML class | Review first |
| --- | --- | --- |
| Household row consumed by ATLAS | [AtlasHouseholdInput](../schema/AtlasHouseholdInput.md) | Field spelling, household identifiers, code meanings, types, and nullability. |
| Person row consumed by ATLAS | [AtlasPersonInput](../schema/AtlasPersonInput.md) | Field spelling, person and household identity scope, and demographic/status codes. |
| Vehicle row produced by ATLAS | [AtlasVehicleOutput](../schema/AtlasVehicleOutput.md) | Field spelling, `(household_id, vehicle_id, year)` identity, and output-year semantics. |

## Provisional fleet-output records

These are separate from the established records above. They provisionally model
the supplied paired CSV structure as an ATLAS fleet-output contract, while the
owner confirms its release/export context and field semantics.

| Exchange file / Table role | Provisional class | Owner question |
| --- | --- | --- |
| Household fleet summary | [AtlasHouseholdFleetOutputExampleV1](../schema/observed-examples/AtlasHouseholdFleetOutputExampleV1.md) | Is this a native export, and what release/export context produced it? |
| Vehicle fleet rows | [AtlasVehicleFleetOutputExampleV1](../schema/observed-examples/AtlasVehicleFleetOutputExampleV1.md) | Confirm export status, `annual_mileage` units, and omitted year/geography semantics. |

Do not use aliases to represent an adapter rename or a prospective mapping.
An alias is appropriate only after ATLAS confirms that it is an exact, durable
synonym for the same native record or field.
