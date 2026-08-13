# A population that changes over three years

The synthetic draft proof follows baseline and ZEV branches through 2025,
2030, and 2035. It links a [ScenarioDefinition](../schema/ScenarioDefinition.md)
to a [PopulationTrajectory](../schema/PopulationTrajectory.md), snapshot
[HouseholdState](../schema/HouseholdState.md) and
[PersonState](../schema/PersonState.md), model-owned [Vehicle](../schema/PolarisVehicleRecord.md) evidence, and
[ConsistProvenanceDocument](../schema/ConsistProvenanceDocument.md). It proves
the contract shape, not a deployed PILATES or POLARIS runtime.

One person enters, a household splits, and a vehicle changes household
assignment. Age appears only in compact model-owned evidence; it is not core
population state. See [what the checker catches](check-the-showcase.md).
