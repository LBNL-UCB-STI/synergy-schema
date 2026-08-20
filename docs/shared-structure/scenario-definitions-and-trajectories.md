# Scenario definitions and trajectories

A [ScenarioDefinition](../schema/ScenarioDefinition.md) has an immutable
content digest. A [PopulationTrajectory](../schema/PopulationTrajectory.md)
names requested years and ordered snapshots for one scenario and realization.
[Scenario bindings](glossary.md#what-a-binding-means-here) say how each model's
native settings represent the shared assumptions. They can record compatible
coverage, a documented gap, an intentional override, or a conflict that needs
resolution; they do not transfer ownership of the native setting.

The glossary explains the plain-language distinction between a
[scenario definition](glossary.md#scenario-definition) and a
[population trajectory](glossary.md#population-trajectory).
