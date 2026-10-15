# Scenario definitions and trajectories

A [scenario definition](glossary.md#scenario-definition) lists the shared
assumptions that make one version of a scenario different from another. It
doesn't try to capture every model setting. A fingerprint (content digest)
pins down exactly which version is meant.

A [population trajectory](glossary.md#population-trajectory) tracks the
population snapshots requested and produced for one scenario and one random
draw (stochastic realization). It records which years finished and which were
skipped on purpose, so a missing year isn't mistaken for either a failure or
an intentional gap.

[Scenario bindings](glossary.md#what-a-binding-means-here) connect each shared
assumption to the model setting that represents it. A binding can say the
model covers the assumption directly, has a known gap, deliberately overrides
it, or conflicts with it and needs to be sorted out. The binding points at the
model setting without taking ownership of it.
