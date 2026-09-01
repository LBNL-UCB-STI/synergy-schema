# Workflow structures

Shared definitions become useful at concrete handoff boundaries. A
[workflow profile](../shared-structure/glossary.md#workflow-profile) combines
the shared scenario, population, and file-identity records with the
[model-native records](../shared-structure/glossary.md#native-record) needed for
one exchange.

Profiles do not replace native tables or prove that a runtime already enforces
the documented boundary. They describe what a complete exchange would contain
and give checkers a stable structure to evaluate.

Ownership follows the boundary. Model teams decide what native fields mean;
workflow teams maintain orchestration and translation behavior; Synergy
maintains the shared vocabulary and cross-document checks. [Ownership and
authority](../shared-structure/glossary.md#ownership-and-authority) separates
those responsibilities in more detail.
