# DEMOS contract review

The DEMOS files we have are household and person exports labeled
`POLARIS_mapped`. They're provisional: they aren't raw DEMOS inputs, and they
don't mean there's an agreed handoff into POLARIS.

| Physical example role | LinkML class | Review first |
| --- | --- | --- |
| Mapped household export | [DemosPolarisMappedHousehold](../schema/DemosPolarisMappedHousehold.md) | Field definitions, head/household codebooks, `is_reorg_household`, and whether rows are complete output. |
| Mapped person export | [DemosPolarisMappedPerson](../schema/DemosPolarisMappedPerson.md) | `person` and `household` scope, blank/nonunique `id`, and relationship/status code meanings. |

There's no record for raw DEMOS input yet. We received a workbook describing
it, but not sample input files or the versioned code that produces these
exports. Both are needed before a DEMOS input record or a DEMOS-to-POLARIS
mapping can move past provisional.
