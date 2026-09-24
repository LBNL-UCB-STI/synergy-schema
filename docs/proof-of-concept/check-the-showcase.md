# Following the proof from claim to file

The example is small enough to read in full. Its files describe one changing
population, two scenario branches, the model settings that receive shared
assumptions, the translation between models, and the exact files each step
delivered. The tables on this page are generated from those files when the
docs are built.

## The population over time

The timeline below follows the ZEV scenario. For each year, the shared records
list the households, people, and vehicles, and how they relate.
Every person state has an explicit household membership, and every vehicle
state has an explicit household assignment.

Source:
[`core-population-evolution.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/main/examples/evolving_population/core-population-evolution.yaml)

{{ showcase_population_timeline_table() }}

The 2025 household splits into two households in 2030. Alex can be followed
through all three years. A new child appears in 2030. The vehicle keeps the
same ID while moving to one of the new households.

Age isn't in the shared records because it belongs to the model's own data.
The shared layer carries just enough identity to compare records; it doesn't
take over every attribute a model holds.

## Shared identity and model-owned results

The baseline and ZEV receipts refer to the same vehicle, but POLARIS gives it
a different vehicle type in each branch. That's an expected model result, not
a disagreement about which vehicle exists.

{{ showcase_branch_comparison_table() }}

This matters in both directions. Forcing every attribute into one common
record would throw away useful model detail. Leaving identity unstated would
cause the opposite problem: there would be no way to show that two similar-looking
outputs describe the same population.

## From a shared assumption to an exact file

A scenario assumption is only useful if it's clear where it goes in each
workflow. The scenario records the shared value. Each model binding names the
model setting that receives it, or records that the model doesn't support it.

Sources:
[`zev-scenario-definition.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/main/examples/evolving_population/zev-scenario-definition.yaml)
and
[`zev-model-bindings.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/main/examples/evolving_population/zev-model-bindings.yaml)

### Shared assumptions

{{ showcase_scenario_assumptions_table(4) }}

### Model interfaces

{{ showcase_bindings_table(4) }}

POLARIS can't represent the ZEV policy, so its binding records a gap. That's
more useful than treating a missing value as agreement: the scenario is still
identifiable, and the unsupported setting stays visible.

The next table follows that assumption through the mapping and the receipt to
one exact evidence file.

{{ showcase_evidence_trace_table() }}

Evidence is included because names and schema validation can't answer every
reproducibility question. File fingerprints show which bytes were used. Run
records link those bytes to the work that produced them. Review records show
whether the mapping rules have been checked by the right people. Here the
mapping is still a draft with no review records, and that gap is reported as
part of the result instead of being hidden behind a passing schema check.

## What the proof establishes

Each check below adds a different kind of confidence. Passing one doesn't mean
the later ones have passed.

{{ showcase_status_ladder_table() }}

In short: the shared records match their LinkML schemas, and the checker can
compare the scenario, trajectory, bindings, mapping, bundles, and receipts
against each other. The mapping is still a draft, the ZEV binding still has a
gap, and the receipt was put together by hand. The example doesn't claim
production integration, scientific approval, or validation of a full
population.

## Deliberately broken exchanges

All digest values below come directly from the valid and broken fixtures; only
the first few characters are shown. In both cases the human-readable fields
still look reasonable, which is exactly why the checker also compares
fingerprints.

### Scenario identity mismatch

Sources: valid
[`zev-scenario-definition.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/main/examples/evolving_population/zev-scenario-definition.yaml)
and altered
[`broken-scenario-definition.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/main/examples/evolving_population_broken_scenario/broken-scenario-definition.yaml).

{{ showcase_broken_scenario_table(4) }}

The altered file's scenario fingerprint no longer matches its contents. The
checker reports `SCENARIO_DIGEST_MISMATCH`.

### Implementation artifact identity mismatch

Sources: valid
[`zev-polaris-translation-bundle.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/main/examples/evolving_population/zev-polaris-translation-bundle.yaml)
and altered
[`broken-polaris-bundle.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/main/examples/evolving_population_broken_artifact_identity/broken-polaris-bundle.yaml).

{{ showcase_broken_artifact_table(4) }}

The altered receipt names a different translation script than the one
registered for the mapping. The checker reports `ARTIFACT_IDENTITY_MISMATCH`.

## Run the checks

From the repository root, check the baseline and ZEV branches separately:

```sh
uv run python -m synergy_schema.conformance check-all --schema src/synergy_schema/schema/synergy_schema.yaml --dir examples/evolving_population/baseline
uv run python -m synergy_schema.conformance check-all --schema src/synergy_schema/schema/synergy_schema.yaml --dir examples/evolving_population/zev
```

Both valid branches exit 0. The baseline branch warns
`MAPPING_NOT_APPROVED`, and the ZEV branch also warns
`SCENARIO_COMPATIBILITY_GAP`. Both warnings are expected: the mapping is still
a draft, and POLARIS still can't represent the ZEV policy.

The broken examples exit 1:

```sh
uv run python -m synergy_schema.conformance check-all --schema src/synergy_schema/schema/synergy_schema.yaml --dir examples/evolving_population_broken_scenario
# SCENARIO_DIGEST_MISMATCH
uv run python -m synergy_schema.conformance check-all --schema src/synergy_schema/schema/synergy_schema.yaml --dir examples/evolving_population_broken_artifact_identity
# ARTIFACT_IDENTITY_MISMATCH
```

The checker catches both mismatches. It doesn't claim to validate a full
population or enforce anything at runtime.
