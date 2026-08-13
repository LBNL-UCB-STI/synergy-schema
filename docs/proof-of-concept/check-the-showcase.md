# What the checker catches

Run from the repository root:

```sh
.venv/bin/python -m synergy_schema.conformance check-all --schema src/synergy_schema/schema/synergy_schema.yaml --dir examples/evolving_population
```

The valid synthetic showcase exits 0 (exit 0) and reports its draft-review and compatibility-gap warnings. These two deliberately broken checks exit 1:

```sh
.venv/bin/python -m synergy_schema.conformance check-all --schema src/synergy_schema/schema/synergy_schema.yaml --dir examples/evolving_population_broken_scenario
# SCENARIO_DIGEST_MISMATCH
.venv/bin/python -m synergy_schema.conformance check-all --schema src/synergy_schema/schema/synergy_schema.yaml --dir examples/evolving_population_broken_artifact_identity
# ARTIFACT_IDENTITY_MISMATCH
```

The checker catches mismatched immutable scenario and artifact identities. It
does not claim full population validation or runtime enforcement.
