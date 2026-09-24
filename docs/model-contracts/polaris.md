# POLARIS contract review

The schema includes a partial set of translated population records labeled
`PILATES-observed`. They support the synthetic examples, but they don't mean
POLARIS integration is finished or that the POLARIS team has approved them.
Which POLARIS version they came from isn't recorded.

The provisional demand-database records describe a different set of database
tables. Their raw `hhold` field is not the same thing as the `hhold` alias in
the translated output. Pick the right set based on which exporter or importer
is involved.

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

The provisional records don't claim a shared release, snapshot, or round
trip until POLARIS provides the matching manifest and importer/exporter
details. Their source version, review status, and runtime validation status
aren't recorded yet.
