# UrbanSim contract review

The UrbanSim records here cover only the ID and join fields the current
workflow uses to link households and people. They aren't a complete list of
UrbanSim inputs or outputs.

| Physical role | LinkML class | Review first |
| --- | --- | --- |
| Household population identity and location | [UrbanSimHouseholdPopulationRecord](../schema/UrbanSimHouseholdPopulationRecord.md) | Household identity and block identifier spelling/format. |
| Person population identity and household join | [UrbanSimPersonPopulationRecord](../schema/UrbanSimPersonPopulationRecord.md) | Person/household identity, member ordinal scope, and zone aliases. |

There are no provisional UrbanSim records yet.
