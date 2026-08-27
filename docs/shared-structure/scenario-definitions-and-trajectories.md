# Scenario definitions and trajectories

A [scenario definition](glossary.md#scenario-definition) records the shared
assumptions that distinguish one scenario revision from another. It does not
try to include every native model setting. A content digest identifies the
exact revision being discussed.

A [population trajectory](glossary.md#population-trajectory) organizes the
population snapshots requested and produced for one scenario and stochastic
realization. It records completed years and deliberately skipped years so that
an absent output is not silently interpreted as either a failure or an
intentional gap.

[Scenario bindings](glossary.md#what-a-binding-means-here) connect each shared
assumption to the native setting that represents it in a model. A binding can
record direct coverage, a documented gap, an intentional override, or a
conflict requiring resolution. It names the interface without taking ownership
of the native setting.
