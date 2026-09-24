# Workflow structures

Shared definitions matter most at real handoffs between models. A
[workflow profile](../shared-structure/glossary.md#workflow-profile) combines
the shared scenario, population, and file records with the
[model-native records](../shared-structure/glossary.md#native-record) needed
for one specific exchange.

A profile doesn't replace a model's tables, and it doesn't mean the runtime
already enforces it. It describes what a complete exchange should contain and
gives the checker a fixed structure to test against.

Each side of the handoff owns its own piece. Model teams decide what their
fields mean. Workflow teams maintain the orchestration and translation code.
Synergy maintains the shared vocabulary and the checks that compare files.
[Ownership and authority](../shared-structure/glossary.md#ownership-and-authority)
goes into more detail.
