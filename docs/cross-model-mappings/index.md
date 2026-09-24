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
