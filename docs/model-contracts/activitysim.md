# ActivitySim contract review

ActivitySim is an open-source activity-based travel demand modeling platform.
It simulates daily activity schedules, tour generation, destination choices, and
travel modes for synthetic persons and households.

The current ActivitySim record set in Synergy describes the key identity and join
fields used when connecting ActivitySim to the PILATES workflow. It is not a
complete catalog of all ActivitySim inputs or outputs.

| Exchange file / Table role | LinkML class | Review first |
| --- | --- | --- |
| Household input identity and location | [ActivitySimHouseholdInputRecord](../schema/ActivitySimHouseholdInputRecord.md) | Household and block identifiers; optional TAZ relationship. |
| Person input identity and household join | [ActivitySimPersonInputRecord](../schema/ActivitySimPersonInputRecord.md) | Person/household identity, regenerated `member_id`, and zone aliases. |
| Land-use-zone identity | [ActivitySimLandUseZoneRecord](../schema/ActivitySimLandUseZoneRecord.md) | TAZ physical spelling and identifier scope. |

No provisional observed ActivitySim artifact family is currently documented in the
observed-example reference.
