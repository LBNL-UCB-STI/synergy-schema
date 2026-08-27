# A population that changes over three years

The smallest useful demonstration of a shared universe must include change.
This synthetic proof follows baseline and ZEV branches through 2025, 2030, and
2035. One person enters, a household splits, and a vehicle changes household
assignment.

The example connects a [ScenarioDefinition](../schema/ScenarioDefinition.md)
to a [PopulationTrajectory](../schema/PopulationTrajectory.md), then describes
each year with [HouseholdState](../schema/HouseholdState.md) and
[PersonState](../schema/PersonState.md) records. Compact model-owned
[Vehicle](../schema/PolarisVehicleRecord.md) data demonstrates that model
attributes can differ without changing the shared population identity. A
[ConsistProvenanceDocument](../schema/ConsistProvenanceDocument.md) records the
runs and files behind the exchange.

This is a test of the documented exchange shape and cross-file checks. It is
not a deployed PILATES or POLARIS runtime. [What the checker
catches](check-the-showcase.md) shows both the valid declarations and two
deliberately broken variants.
