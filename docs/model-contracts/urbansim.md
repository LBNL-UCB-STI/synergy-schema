# UrbanSim contract review

UrbanSim is an urban simulation platform that models land use, real estate
markets, parcel development, and location choices of households and jobs over
time.

The current UrbanSim record set in Synergy describes the key identity and join
fields used to connect household and person population records within the
PILATES workflow. It is not a complete UrbanSim input or output catalog.

| Exchange file / Table role | LinkML class | Review first |
| --- | --- | --- |
| Household population identity and location | [UrbanSimHouseholdPopulationRecord](../schema/UrbanSimHouseholdPopulationRecord.md) | Household identity and block identifier spelling/format. |
| Person population identity and household join | [UrbanSimPersonPopulationRecord](../schema/UrbanSimPersonPopulationRecord.md) | Person/household identity, member ordinal scope, and zone aliases. |

No provisional observed UrbanSim artifact family is currently documented in the
observed-example reference.
