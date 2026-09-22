# Core population assembly example

This synthetic example shows how two models can contribute different parts of
one `2030` population snapshot without producing a universal replacement
table. It describes `synthetic-region` with two immutable contributions:

* DEMOS supplies households, people, and household membership.
* ATLAS adds vehicles and household--vehicle assignments.

The DEMOS contribution also classifies `will_move_next_iteration` as a
`model_view`: useful model-owned information about a household, not a change to
the shared population structure.

`assembly.yaml` is deliberately `partial`. It names the two contribution
identities and its resolved facet index answers where the authoritative value
for each supplied facet lives. The contributions retain their native artifact
roles, mappings, and column classifications.

## Run the check

From the repository root, validate the assembly and its two contribution
manifests together:

```sh
uv run python -m synergy_schema.conformance check-population-assembly \
  --schema src/synergy_schema/schema/synergy_schema.yaml \
  --assembly examples/core_population_assembly/assembly.yaml \
  --contribution examples/core_population_assembly/demos-contribution.yaml \
  --contribution examples/core_population_assembly/atlas-contribution.yaml
```

The artifact and schema digests are synthetic values included to make identity
checks deterministic. This is a schema-gated proof of the declarations, not a
claim that an external model run produced, consumed, or scientifically
validated these files.

The two `invalid-*.yaml` files are intentional checker fixtures:

* `invalid-overlapping-assertions.yaml` has DEMOS and ATLAS both assert the
  same core household `income` field without a field resolution.
* `invalid-missing-carried-through-upstream.yaml` marks a copied
  `household_id` as `carried_through` but does not name the upstream asserted
  field.

These fixtures test that authority cannot be inferred from contribution order
or from a matching native column name.
