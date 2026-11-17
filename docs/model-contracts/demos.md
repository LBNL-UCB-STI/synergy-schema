# DEMOS contract review

DEMOS has two separate schema slices in Synergy:

1. **Core DEMOS native I/O** (`demos_core.yaml`): Derived directly from
   `NatLabRockies/DEMOS` (`demos/config.py`, `demos/datasources.py`,
   `demos/models/`, and `data/small_example/small_example_tables.h5`). These are
   the native HDF5 population tables and CSV control/calibration inputs consumed
   and emitted by the core DEMOS container (`ghcr.io/NatLabRockies/demos:latest`).
2. **Provisional `POLARIS_mapped` exports** (`demos_polaris_mapped_examples.yaml`):
   Sketched from `POLARIS_mapped` CSV examples. They remain provisional until the
   DEMOS-to-POLARIS preprocessing and postprocessing scripts are finalized.

## Core DEMOS native records

| Physical role | LinkML class | Review first |
| --- | --- | --- |
| Native HDF5 persons table | [DemosCorePerson](../schema/demos-core/DemosCorePerson.md) | Required vs. newborn/derived fields, `MAR`, `hispanic.1`, and `race_id` vs. `race`. |
| Native HDF5 households table | [DemosCoreHousehold](../schema/demos-core/DemosCoreHousehold.md) | Required `household_id`/`lcm_county_id` vs. Orca-computed/seed fields on newly formed households. |
| County income growth rates CSV | [DemosIncomeRateRow](../schema/demos-core/DemosIncomeRateRow.md) | `year` index, zero-padded `lcm_county_id`, and multiplicative `rate`. |
| Household size control totals CSV | [DemosHouseholdSizeControlRow](../schema/demos-core/DemosHouseholdSizeControlRow.md) | `hh_size` category labels and `total_number_of_households`. |
| Observed annual calibration counts CSV | [DemosObservedAnnualCountRow](../schema/demos-core/DemosObservedAnnualCountRow.md) | Shared `year`/`count` shape for employment, mortality, and birth targets. |
| Observed marital status counts CSV | [DemosObservedMaritalCountRow](../schema/demos-core/DemosObservedMaritalCountRow.md) | `MAR` code meanings and `count` targets for household reorganization. |

## Provisional `POLARIS_mapped` exports

| Physical example role | LinkML class | Review first |
| --- | --- | --- |
| Mapped household export | [DemosPolarisMappedHousehold](../schema/DemosPolarisMappedHousehold.md) | Field definitions, head/household codebooks, `is_reorg_household`, and whether rows are complete output. |
| Mapped person export | [DemosPolarisMappedPerson](../schema/DemosPolarisMappedPerson.md) | `person` and `household` scope, blank/nonunique `id`, and relationship/status code meanings. |
