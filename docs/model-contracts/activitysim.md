# ActivitySim contract review

The ActivitySim records here cover only the ID and join fields the PILATES
workflow uses. They aren't a complete list of ActivitySim inputs or outputs.

| Physical role | LinkML class | Review first |
| --- | --- | --- |
| Household input identity and location | [ActivitySimHouseholdInputRecord](../schema/ActivitySimHouseholdInputRecord.md) | Household and block identifiers; optional TAZ relationship. |
| Person input identity and household join | [ActivitySimPersonInputRecord](../schema/ActivitySimPersonInputRecord.md) | Person/household identity, regenerated `member_id`, and zone aliases. |
| Land-use-zone identity | [ActivitySimLandUseZoneRecord](../schema/ActivitySimLandUseZoneRecord.md) | TAZ physical spelling and identifier scope. |

There are no provisional ActivitySim records yet.
