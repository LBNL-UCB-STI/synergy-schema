# One-year mapping handshake

Use the reviewed synthetic analogue as a small, reversible pilot:

```sh
.venv/bin/python -m synergy_schema.conformance check-all --schema src/synergy_schema/schema/synergy_schema.yaml --dir examples/one_year_mapping_handshake
```

The [receipt](../shared-structure/glossary.md#receipt) is
[draft](../shared-structure/glossary.md#draft) by design. It continues to warn
until both model-owner roles accept the exact same mapping content: the field
rules, pinned source and target catalogs, defaults, unsupported fields, and
other declared translation losses. The semantic digest is a fingerprint of
that content, so the checker can tell whether both approvals refer to the same
agreement.

This approval concerns what the translation means. It does not approve the SQL
implementation by implication, and it does not require either team to change
its payload format. The pilot returns four separately inspectable things:

1. the mapping agreement;
2. its explicit residue ledger;
3. the SQL or code registered to implement it; and
4. the model-owner review records.
