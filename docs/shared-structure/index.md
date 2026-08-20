# Schema organization

Shared structure separates scenario definitions, population snapshots,
workflow bundles, model-native records, and mappings. The split keeps a shared
meaning without pretending that all tools own the same physical fields.

## What belongs in core

Core classes hold shared assertions that are allowed to be absent but not
contradictory when two implementations make them for the same scenario
revision, year, realization, and authority. Examples include the selected
scenario identity, the simulation year, a snapshot-scoped person identity, and
a declared household-membership relationship.

Putting an assertion in core does not make disagreement impossible. It makes
the assertion comparable and gives conformance code a place to report a
conflict. Attributes that may legitimately differ between PILATES and POLARIS,
such as a predicted age, vehicle technology, or travel behavior, remain in
model-owned records instead of being promoted to core.

Core also contains provider-neutral exchange machinery—artifact identities,
schema references, native-contract references, and handoff bundles. Those
classes make shared claims traceable; they do not transfer ownership of native
schemas or payloads.

See the generated [core schema UML](../schema/core-schema-uml.md) for every core
class and typed relationship on one page.

Use the [Glossary](glossary.md) for plain-language definitions and comparisons
of terms such as scenario, trajectory, profile, receipt, residue, and digest.
