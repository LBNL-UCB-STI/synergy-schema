# ATLAS native population records

This directory contains ATLAS-owned record contracts. `atlas_population.yaml`
describes the household and person rows ATLAS receives, plus the vehicle rows
ATLAS produces. It deliberately does not contain PILATES artifact keys, run
identifiers, paths, or snapshot metadata; the PILATES population profile owns
that operational context.

## Owner review map

Start with the named class that corresponds to the physical ATLAS surface under
review. The established post-ATLAS records are intentionally consolidated in
[`atlas_population.yaml`](atlas_population.yaml); keeping their relationships
together makes the household/person/vehicle boundary easier to inspect.

| ATLAS surface | LinkML review block | Status | Owner review focus |
| --- | --- | --- | --- |
| Household row consumed by ATLAS | [`AtlasHouseholdInput`](atlas_population.yaml#L22) | Established native contract | Physical field inventory, descriptions, types, nullability, and household-code meanings. |
| Person row consumed by ATLAS | [`AtlasPersonInput`](atlas_population.yaml#L117) | Established native contract | Physical field inventory, person/household identity scope, and demographic/status-code meanings. |
| Vehicle row produced by ATLAS | [`AtlasVehicleOutput`](atlas_population.yaml#L224) | Established native contract | Physical field inventory, `(household_id, vehicle_id, year)` identity, output-year semantics, and vehicle-code meanings. |
| Paired household/vehicle fleet examples | [`atlas_fleet_observed_example_v1.yaml`](atlas_fleet_observed_example_v1.yaml) | Model-associated observed example | Whether the files are native ATLAS exports, the export/release context, `annual_mileage` units, and omitted year/geography semantics. |

Each established class exposes `owner`, `direction`, and `physical_binding`
annotations in the generated reference. Edit an attribute's `description` to
clarify a field; change range, requiredness, keys, or enums only when the
underlying producer behavior is confirmed.

## Naming and separation

The LinkML class names are stable review handles, while attributes preserve
the current physical spellings. Do not add aliases merely for a convenient
label: use an alias only after ATLAS confirms it is an exact, durable synonym
for the same native record or field. In particular, do not use aliases to
represent an adapter rename or a prospective cross-model mapping.

The established `atlas_population.yaml` remains one consolidated module. The
fleet example stays separate because it is evidence from an unconfirmed export
context, not a replacement or successor to the established vehicle contract.

`atlas_fleet_observed_example_v1.yaml` is separate from that established
contract. It records the exact headers of one model-associated fleet-output
example, including `HOUSEID` and `VEHID`, through explicit physical bindings,
but makes no producer-authority, year, or handoff claim.
