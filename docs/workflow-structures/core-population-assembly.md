# Staged core-population assembly

Use a staged assembly when different models supply different structural facts
about the same single-year population state. It lets each model keep its native
tables while making the selected authority for a shared facet explicit.

For example, a DEMOS contribution can supply households, people, and household
membership for 2030. An ATLAS contribution can later supply vehicles and
household--vehicle assignments for that same snapshot. The assembly names both
immutable contributions and provides a resolved facet index, so a consumer can
find the authoritative artifact and native-to-core binding without relying on
file names or contribution order.

## What the check establishes

The checker confirms that the contributions target the same snapshot, their
artifact and semantic digests match the assembly references, core assertions
do not silently overlap, carried-through columns name their upstream
assertion, and declared vehicle-to-household relationships are well formed.

It does not merge files, prove that a join succeeded from row data, or show
that a receiving model accepted the result. Those are later evidence gates.

## Try the synthetic example

The [core-population assembly example](../../examples/core_population_assembly/)
contains a partial 2030 DEMOS + ATLAS assembly and two intentionally invalid
contributions. Run its check from the repository root:

```sh
uv run python -m synergy_schema.conformance check-population-assembly \
  --schema src/synergy_schema/schema/synergy_schema.yaml \
  --assembly examples/core_population_assembly/assembly.yaml \
  --contribution examples/core_population_assembly/demos-contribution.yaml \
  --contribution examples/core_population_assembly/atlas-contribution.yaml
```

The example is a schema-gated proof of the declarations, not a real
producer-to-consumer exchange.
