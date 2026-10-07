# Cross-model mappings

Sharing concepts doesn't make translation unnecessary. The same household,
person, policy assumption, or vehicle can show up under different names and
shapes in different models. A mapping records how those versions relate,
without declaring either model's format to be the "real" one.

Synergy handles three kinds of mapping:

- **Identity mapping:** do two records refer to the same household, person, or
  vehicle, or are the IDs just local row numbers?
- **Field mapping:** renames, unit conversions, derived values, defaults,
  unsupported fields, and anything lost in translation.
- **Scenario compatibility:** does a model represent a shared assumption
  directly, leave a visible gap, deliberately override it, or contradict it?

What a mapping means, who reviewed it, the code that runs it, and the evidence
from one run are all kept separate. That's what lets a checker tell the
difference between a disagreement about the rules and someone running the
wrong script or the wrong year's files.

## Conceptual guides

- [Mapping meaning, implementation, and lineage](mapping-lineage.md) explains the four records that keep rules, reviews, code, and receipts separate.
- [Population identity](population-identity.md) covers matching and tracking agents across models.
- [Scenario compatibility](scenario-compatibility.md) defines the four compatibility states for policy assumptions.

## Piloting an existing mapping

When formalizing a mapping that already exists as a spreadsheet, SQL query, or script, the [adoption pilot](../bring-an-existing-mapping/index.md) provides a structured path:

1. [Three-step pilot](../bring-an-existing-mapping/index.md): Summary of the pilot scope, inputs, and boundaries.
2. [Day-zero manifest](../bring-an-existing-mapping/day-zero-manifest.md): Inventory the exchange file and record its fingerprint.
3. [Mapping at a glance](../bring-an-existing-mapping/contract-at-a-glance.md): Write down the translation rules in a reviewable contract table.
4. [One-year mapping handshake](../bring-an-existing-mapping/one-year-mapping-handshake.md): Run the check against real model exchange files.
5. [Costs and exit](../bring-an-existing-mapping/costs-and-exit.md): Recognize when flat files are enough and when to back out.
