# Mapping meaning, implementation, and lineage

A mapping can be reviewed correctly and still be applied by the wrong script.
A correct script can also be run against the wrong scenario or year. Synergy
keeps four questions separate so those failures do not collapse into one vague
notion of validity.

| Record | Question it answers | What makes it a different version? |
| --- | --- | --- |
| Mapping description (`PopulationTranslationContract`) | What does the ATLAS-to-POLARIS translation mean? | A source or target interface, field rule, default, unsupported field, filter, or other declared loss changes. |
| Review record | Who accepted that exact meaning, in which role? | A reviewer, decision, rationale, or accepted mapping-content digest changes. |
| [Implementation binding](../shared-structure/glossary.md#implementation-binding) | Which SQL or code claims to carry out the reviewed rules? | The executable artifact or the mapping version it claims to implement changes. |
| Receipt | What was actually applied for this scenario and year? | The run, input, output, year, implementation, or observed loss changes. |

The formal [translation contract](../shared-structure/glossary.md#translation-contract)
contains the first row of that table. Its mapping-content fingerprint is the
`semantic_content_digest` field in the schema. Reviewers accept that exact
fingerprint; the implementation binding names the SQL or code associated with
it; and the receipt records one actual use.

This chain lets the checker distinguish declared “approved rules, wrong script”
from “right script, wrong year.” It checks declaration consistency; it does not
independently establish that the named executable produced an artifact.
Fixture-byte verification and evidence from the producing and consuming
runtimes are separate results. The workflow team owns the executable, while
the source and target model teams decide what their fields mean and whether the
cross-model rule is acceptable. Synergy records and checks those decisions but
cannot create approval on either team's behalf.

When translating data between two models, not every field or filter has a direct
one-to-one match. Known defaults, filtered rows, unsupported fields, and dropped
context are recorded explicitly as [mapping residue](../shared-structure/glossary.md#mapping-residue).
Recording residue makes known translation losses and assumptions visible to
both teams, rather than hiding them inside translation scripts. Residue is
declared behavior, not an unexpected error.
