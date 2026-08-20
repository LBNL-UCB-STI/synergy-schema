# Translation contract, residue, and lineage

The handoff keeps four questions separate:

| Document | Question it answers | What makes it a different version? |
| --- | --- | --- |
| Translation contract | What does the ATLAS-to-POLARIS translation mean? | A source or target catalog, field rule, default, unsupported field, filter, or other declared residue changes. |
| Review record | Who accepted that exact meaning? | A reviewer, decision, rationale, or accepted semantic digest changes. |
| [Implementation binding](../shared-structure/glossary.md#implementation-binding) | Which SQL or code claims to carry out that meaning? | The executable artifact or the contract digest it claims to implement changes. |
| Receipt | What was actually applied for this scenario and year? | The run, input, output, year, implementation, or observed residue changes. |

The semantic digest is the contract's fingerprint: it is calculated from the
pinned source and target catalogs, field rules, and declared residue. Reviewers
accept that fingerprint. The implementation binding names the SQL or code that
claims to implement it, and the receipt records one actual use. This chain lets
the checker detect “approved rules, wrong script” and “right script, wrong
year” without treating those as the same problem.

The workflow team owns the executable. The source and target model teams retain
authority over the mapping's meaning. Synergy records and checks their decisions
but cannot manufacture their approval.

See the glossary for the difference between the reviewed
[translation contract](../shared-structure/glossary.md#translation-contract)
and its explicit [mapping residue](../shared-structure/glossary.md#mapping-residue).
