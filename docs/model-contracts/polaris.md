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

| Physical table role | Provisional class | Owner question |
| --- | --- | --- |
| Household seed-shaped table | [PolarisDemandDatabaseV1Household](../schema/observed-examples/PolarisDemandDatabaseV1Household.md) | What does non-unique raw `hhold` mean, and which table roles are inputs? |
| Person seed-shaped table | [PolarisDemandDatabaseV1Person](../schema/observed-examples/PolarisDemandDatabaseV1Person.md) | Confirm person/household key scope and importer semantics. |
| Vehicle seed-shaped table | [PolarisDemandDatabaseV1Vehicle](../schema/observed-examples/PolarisDemandDatabaseV1Vehicle.md) | Confirm vehicle type/codebook version and demand/supply dependency. |

The provisional records make no shared release, snapshot, or round-trip claim
until POLARIS supplies the corresponding manifest and importer/exporter
context. Their source revision, owner-review status, and runtime-validation
status are not recorded.
