# One-year mapping handshake

The handshake turns an existing mapping into four separately inspectable
parts: the rules, the known losses, the executable code, and the model-owner
review decisions. Keeping them separate matters because any one of them can
change without the others.

The synthetic analogue can be checked from the repository root:

```sh
uv run python -m synergy_schema.conformance check-all --schema src/synergy_schema/schema/synergy_schema.yaml --dir examples/one_year_mapping_handshake
```

The [receipt](../shared-structure/glossary.md#receipt) is
[draft](../shared-structure/glossary.md#draft) by design. It continues to warn
until both model-owner roles accept the exact same mapping content: the field
rules, pinned source and target interface catalogs, defaults, unsupported
fields, and other declared translation losses.

The schema calls the fingerprint of that content a `semantic_content_digest`.
The technical name distinguishes it from a file checksum; in these guides it
is described as the **mapping-content digest**. The digest lets the checker
confirm that both reviews refer to the same version.

Review of the mapping meaning does not silently approve the SQL implementation,
and it does not require either team to change its payload format. The returned
pilot contains:

1. the mapping description;
2. its explicit residue ledger;
3. the SQL or code registered to implement it; and
4. the model-owner review records.
