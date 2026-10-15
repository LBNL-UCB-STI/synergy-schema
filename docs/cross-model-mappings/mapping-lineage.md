# Mapping meaning, implementation, and lineage

A mapping can be reviewed and correct, and still be applied by the wrong
script. A correct script can still be run on the wrong scenario or year.
Synergy keeps four questions apart so those different failures don't blur
into a vague "is it valid?"

| Record | Question it answers | What counts as a new version? |
| --- | --- | --- |
| Mapping description (`PopulationTranslationContract`) | What does the ATLAS-to-POLARIS translation mean? | Any change to a source or target interface, field rule, default, unsupported field, filter, or other known loss. |
| Review record | Who accepted that exact version, and in what role? | A different reviewer, decision, rationale, or mapping-content digest. |
| [Implementation binding](../shared-structure/glossary.md#implementation-binding) | Which SQL or code is supposed to carry out the reviewed rules? | A different script, or a different mapping version it claims to implement. |
| Receipt | What was actually run for this scenario and year? | A different run, input, output, year, script, or observed loss. |

The formal [translation contract](../shared-structure/glossary.md#translation-contract)
is the first row of that table. Its fingerprint is the
`semantic_content_digest` field in the schema. Reviewers accept that exact
fingerprint, the implementation binding names the SQL or code for it, and the
receipt records one actual run.

This chain lets the checker tell "approved rules, wrong script" apart from
"right script, wrong year," based on what the records declare. It doesn't
independently confirm that the named script really produced a given file.
Checking the actual file bytes, and collecting evidence from the runs that
produced and consumed them, are separate steps.

Responsibility is split, too. The workflow team owns the script. The source
and target model teams decide what their fields mean and whether the
cross-model rule is acceptable. Synergy records and checks those decisions,
but it can't approve anything on either team's behalf.

Known defaults, dropped rows, unsupported fields, and lost context are
recorded as [mapping residue](../shared-structure/glossary.md#mapping-residue).
Residue is translation behavior that's out in the open, not automatically an
error.
