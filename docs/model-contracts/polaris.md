# POLARIS contract review

The aggregate schema contains a partial translated-population record set
labeled `PILATES-observed`. It supports synthetic exchange examples; this
repository does not establish a completed POLARIS runtime integration or
model-owner approval. The source revision is not recorded here.

The provisional demand-database table description covers a separate set of
physical database tables. Its raw `hhold` field is not interchangeable with the
translated-output alias. Select the applicable record set or table description
using the specific exporter/importer context.

## Existing translated-output records

| Physical role | LinkML class | Review first |
| --- | --- | --- |
| Household translated record | [PolarisHouseholdRecord](../schema/PolarisHouseholdRecord.md) | `household`/`hhold` relationship and location semantics. |
| Person translated record | [PolarisPersonRecord](../schema/PolarisPersonRecord.md) | Person key, household join, and within-household `id` semantics. |
| Vehicle translated record | [PolarisVehicleRecord](../schema/PolarisVehicleRecord.md) | Snapshot-scoped vehicle identity and household join. |

## Provisional demand-database population rows

| Physical table role | LinkML class | Owner question |
| --- | --- | --- |
| Household seed-shaped table | [PolarisDemandDatabaseHousehold](../schema/PolarisDemandDatabaseHousehold.md) | What does non-unique raw `hhold` mean, and which table roles are inputs? |
| Person seed-shaped table | [PolarisDemandDatabasePerson](../schema/PolarisDemandDatabasePerson.md) | Confirm person/household key scope and importer semantics. |
| Vehicle seed-shaped table | [PolarisDemandDatabaseVehicle](../schema/PolarisDemandDatabaseVehicle.md) | Confirm vehicle type/codebook version and demand/supply dependency. |
| Vehicle_Class dimension table | [PolarisDemandDatabaseVehicleClass](../schema/PolarisDemandDatabaseVehicleClass.md) | Confirm passenger and commercial vehicle class definitions (`class_id` 1..8+). |
| Vehicle_Type dimension table | [PolarisDemandDatabaseVehicleType](../schema/PolarisDemandDatabaseVehicleType.md) | Confirm composite key (`vehicle_class`, `connectivity_type`, `powertrain_type`, `automation_type`, `fuel_type`, `vintage_type`) lookup (`X-V5`). |

The provisional records make no shared release, snapshot, or round-trip claim
until POLARIS supplies the corresponding manifest and importer/exporter
context. Their source revision, owner-review status, and runtime-validation
status are not recorded.
