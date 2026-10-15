# One-year mapping handshake

The handshake splits an existing mapping into four parts that can each be
checked on their own: the rules, what gets lost, the code, and the sign-off
from each model team. They're kept separate because any one of them can
change without the others.

To check the synthetic example, run this from the repository root:

```sh
uv run python -m synergy_schema.conformance check-all --schema src/synergy_schema/schema/synergy_schema.yaml --dir examples/one_year_mapping_handshake
```

The example [receipt](../shared-structure/glossary.md#receipt) is a
[draft](../shared-structure/glossary.md#draft) on purpose. It keeps warning
until both model teams accept the exact same mapping content: the field rules,
the pinned source and target interface catalogs, defaults, unsupported fields,
and anything else the translation drops.

The schema calls the fingerprint of that content `semantic_content_digest`.
These guides call it the **mapping-content digest**, to make clear it isn't a
file checksum. It lets the checker confirm that both reviews are looking at
the same version.

Review of the mapping meaning doesn't quietly approve the SQL that implements
it, and neither team has to change its file format. The finished pilot
contains:

1. the mapping description;
2. a list of what the translation drops or fills in (the residue);
3. the SQL or code registered to carry it out; and
4. each model team's review record.
