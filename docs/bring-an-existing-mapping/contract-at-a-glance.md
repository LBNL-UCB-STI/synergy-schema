# Mapping at a glance

The generated [one-page review summary](../schema/contract-at-a-glance.md)
collects the source and target owners, original mapping source, mapping-content
digest, implementation identity, field coverage, known losses (residue), and
review state in a single concise view.

This page exists because review quality drops when important decisions are
scattered across YAML files, SQL queries, and meeting notes. It is a generated
summary from the structured records, not a second source of truth. The
documentation build copies the summary from the synthetic one-year example.

### Example summary structure

An example review summary presents the key exchange facts at a glance:

```yaml
- Contract: mapping:atlas-demo-to-polaris (revision-1)
- Semantic identity: sha256:02ae76d67869ec8cee8ca138288e44907cd86ba31db81b66fa6d2e845e798663
- Lifecycle: draft
- Participating teams: ATLAS (source), POLARIS (target)
- Original mapping source: encoding-source/team-mapping.csv
- Coverage: 3 field mappings, 4 documented residues (known losses / defaults)
- Registered implementations: 1 executable script
- Review stamps: Pending review
```

This compact format allows model owners to inspect and confirm the exchange
rules before investing time in implementation code or test runs.
