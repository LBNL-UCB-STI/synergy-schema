# Cross-model mappings

Shared concepts do not remove the need for translation. The same household,
person, policy assumption, or vehicle can appear under different names and
structures in different models. A mapping records how those representations
relate without declaring either model's native form to be the universal one.

Synergy distinguishes three mapping problems:

- **Identity mapping** determines whether records refer to the same entity or
  to local occurrences and row positions.
- **Field mapping** records renames, conversions, derived values, defaults,
  unsupported fields, and information lost during translation.
- **Scenario compatibility** records whether a model represents a shared
  assumption directly, leaves a visible gap, intentionally overrides it, or
  contradicts it.

The mapping meaning, its review, the executable implementation, and evidence
from one application remain separate. That separation is what allows a checker
to distinguish a disagreement about rules from the use of the wrong script or
the wrong year's files.
