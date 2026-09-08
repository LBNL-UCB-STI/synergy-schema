# ActivitySim contract review

The current ActivitySim record set is a partial set of identity and join fields
used by the PILATES workflow. It is not a complete ActivitySim input or output
catalog.

| Physical role | LinkML class | Review first |
| --- | --- | --- |
| Household input identity and location | [ActivitySimHouseholdInputRecord](../schema/ActivitySimHouseholdInputRecord.md) | Household and block identifiers; optional TAZ relationship. |
| Person input identity and household join | [ActivitySimPersonInputRecord](../schema/ActivitySimPersonInputRecord.md) | Person/household identity, regenerated `member_id`, and zone aliases. |
| Land-use-zone identity | [ActivitySimLandUseZoneRecord](../schema/ActivitySimLandUseZoneRecord.md) | TAZ physical spelling and identifier scope. |

No provisional observed ActivitySim artifact family is currently documented in the
observed-example reference.
