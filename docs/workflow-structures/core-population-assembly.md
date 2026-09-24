# Staged core-population assembly

Use a staged assembly when different models supply different parts of the
same year's population. Each model keeps its own tables, and the assembly
makes it explicit which model is the authority for each shared part.

For example, DEMOS might supply the 2030 households, people, and who lives
where. ATLAS might later add the vehicles and which household owns each one.
The assembly lists both contributions, which don't change once published, and
builds an index of which contribution supplies each part. A consumer can then
find the right file, and how its columns map onto the shared records, without
relying on file names or the order the contributions arrived in.

## What the check establishes

The checker confirms that:

- all contributions target the same snapshot;
- their file and content fingerprints match what the assembly lists;
- no two contributions quietly claim the same shared fact;
- columns copied from an earlier contribution say where they came from; and
- vehicle-to-household links are well formed.

It doesn't merge files, confirm that joins actually work on the row data, or
show that a receiving model accepted the result. Those are later checks.

## Try the synthetic example

The [core-population assembly example](../../examples/core_population_assembly/)
contains a partial 2030 DEMOS + ATLAS assembly and two intentionally invalid
contributions. Run the check from the repository root:

```sh
uv run python -m synergy_schema.conformance check-population-assembly \
  --schema src/synergy_schema/schema/synergy_schema.yaml \
  --assembly examples/core_population_assembly/assembly.yaml \
  --contribution examples/core_population_assembly/demos-contribution.yaml \
  --contribution examples/core_population_assembly/atlas-contribution.yaml
```

The example checks the declarations against the schema. It isn't a real
exchange between a producing and a consuming model.
