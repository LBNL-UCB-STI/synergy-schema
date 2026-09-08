# DEMOS contract review

The supplied DEMOS artifacts are mapped household and person exports labeled
`POLARIS_mapped`. They are provisional model contracts, not raw DEMOS input
files or a claim of a shared POLARIS ingest handoff.

| Physical example role | Provisional class | Review first |
| --- | --- | --- |
| Mapped household export | [DemosPolarisMappedHouseholdExampleV1](../schema/observed-examples/DemosPolarisMappedHouseholdExampleV1.md) | Field definitions, head/household codebooks, `is_reorg_household`, and whether rows are complete output. |
| Mapped person export | [DemosPolarisMappedPersonExampleV1](../schema/observed-examples/DemosPolarisMappedPersonExampleV1.md) | `person` and `household` scope, blank/nonunique `id`, and relationship/status code meanings. |

No native DEMOS input row class is declared yet: the delivery includes a
workbook description but not representative raw input payloads or the
versioned transform that produces these exports. Those artifacts are required
before a native input contract or DEMOS-to-POLARIS mapping is promoted.
