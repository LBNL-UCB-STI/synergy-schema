# UrbanSim contract review

The current UrbanSim surface is an identity-bearing partial projection used to
join household and person population records in the current workflow. It is
not a complete UrbanSim input or output catalog.

| Physical role | LinkML class | Review first |
| --- | --- | --- |
| Household population identity and location | [UrbanSimHouseholdPopulationRecord](../schema/UrbanSimHouseholdPopulationRecord.md) | Household identity and block identifier spelling/format. |
| Person population identity and household join | [UrbanSimPersonPopulationRecord](../schema/UrbanSimPersonPopulationRecord.md) | Person/household identity, member ordinal scope, and zone aliases. |

No provisional observed UrbanSim artifact family is currently documented in the
observed-example reference.
