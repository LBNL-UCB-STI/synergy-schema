# Following the proof from claim to file

The proof is intentionally small enough to inspect in full. Its files describe
one changing population, two scenario branches, the model settings that receive
shared assumptions, the translation between native records, and the exact
artifacts delivered by each step. The tables on this page are generated from
those files during the documentation build.

## The population over time

The canonical timeline follows the ZEV scenario. The shared records identify
households, people, vehicles, and their relationships at each simulation year.
Every person state has an explicit household membership, and every vehicle
state has an explicit household assignment.

Source:
[`core-population-evolution.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/main/examples/evolving_population/core-population-evolution.yaml)

{{ showcase_population_timeline_table() }}

The 2025 household is the predecessor of two household states in 2030. Alex
remains identifiable across all three snapshots. A new child first appears in
2030. The vehicle keeps its longitudinal identity while its household
assignment moves to one of the successor households.

Age is absent from the shared records because it belongs to the native
population evidence. The shared layer carries the identity needed to compare
records; it does not take ownership of every attribute held by a model.

## Shared identity and model-owned results

The baseline and ZEV receipts use the same shared vehicle identity. Their
native POLARIS evidence assigns different vehicle types. This is an intended
model result, not a disagreement about which vehicle exists.

{{ showcase_branch_comparison_table() }}

The distinction matters because forcing all native attributes into a common
record would erase useful model detail. Leaving identity entirely implicit
would create the opposite problem: similar-looking outputs could no longer be
shown to refer to the same population.

## From a shared assumption to an exact file

A scenario assumption becomes useful only when its path through each workflow
is visible. The scenario records the shared value. A model binding names the
native configuration element that receives it or records that the model does
not support it.

Sources:
[`zev-scenario-definition.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/main/examples/evolving_population/zev-scenario-definition.yaml)
and
[`zev-model-bindings.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/main/examples/evolving_population/zev-model-bindings.yaml)

### Shared assumptions

{{ showcase_scenario_assumptions_table(4) }}

### Model interfaces

{{ showcase_bindings_table(4) }}

The ZEV policy binding records a compatibility gap for POLARIS. That gap is
more informative than treating an absent value as agreement: the scenario is
still identifiable, while the unsupported interface remains visible.

The next table follows that assumption through the mapping release and receipt
to one exact evidence file.

{{ showcase_evidence_trace_table() }}

Evidence is included because names and schema validation cannot answer every
reproducibility question. File identities establish which bytes were used.
Run records connect those bytes to producing work. Review records show whether
the mapping rules have received the intended scrutiny. In this proof, the
mapping remains a draft and has no review records, so that limitation is part
of the result rather than a detail hidden behind a successful schema check.

## What the proof establishes

Several checks contribute different kinds of confidence. Passing one level
does not imply that the later levels have been reached.

{{ showcase_status_ladder_table() }}

The shared records conform to their LinkML shapes. The checker can compare the
scenario, trajectory, bindings, mapping release, bundles, and receipts. The
mapping is still marked draft, the ZEV binding still contains a compatibility
gap, and the receipt was assembled through manual discovery. Production
integration, scientific approval, and validation of a full population are not
claimed.

## Deliberately broken exchanges

All digest values below come directly from the valid and broken fixtures;
compact prefixes are displayed for readability. The readable fields remain
plausible in both cases, which is why immutable identities are checked as well.

### Scenario identity mismatch

Sources: valid
[`zev-scenario-definition.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/main/examples/evolving_population/zev-scenario-definition.yaml)
and altered
[`broken-scenario-definition.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/main/examples/evolving_population_broken_scenario/broken-scenario-definition.yaml).

{{ showcase_broken_scenario_table(4) }}

The altered file carries a scenario identity that no longer matches the
scenario body. The checker reports `SCENARIO_DIGEST_MISMATCH`.

### Implementation artifact identity mismatch

Sources: valid
[`zev-polaris-translation-bundle.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/main/examples/evolving_population/zev-polaris-translation-bundle.yaml)
and altered
[`broken-polaris-bundle.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/main/examples/evolving_population_broken_artifact_identity/broken-polaris-bundle.yaml).

{{ showcase_broken_artifact_table(4) }}

The altered receipt names a different implementation artifact from the one in
its implementation binding. The checker reports
`ARTIFACT_IDENTITY_MISMATCH`.

## Run the checks

The baseline and ZEV branches are checked independently from the repository
root:

```sh
.venv/bin/python -m synergy_schema.conformance check-all --schema src/synergy_schema/schema/synergy_schema.yaml --dir examples/evolving_population/baseline
.venv/bin/python -m synergy_schema.conformance check-all --schema src/synergy_schema/schema/synergy_schema.yaml --dir examples/evolving_population/zev
```

Both valid branches exit 0. The baseline branch reports
`MAPPING_NOT_APPROVED`; the ZEV branch also reports
`SCENARIO_COMPATIBILITY_GAP`. These warnings are expected because the proof
retains its draft review state and unsupported POLARIS policy interface.

The deliberately broken exchanges exit 1:

```sh
.venv/bin/python -m synergy_schema.conformance check-all --schema src/synergy_schema/schema/synergy_schema.yaml --dir examples/evolving_population_broken_scenario
# SCENARIO_DIGEST_MISMATCH
.venv/bin/python -m synergy_schema.conformance check-all --schema src/synergy_schema/schema/synergy_schema.yaml --dir examples/evolving_population_broken_artifact_identity
# ARTIFACT_IDENTITY_MISMATCH
```

The checker catches the mismatched scenario and artifact identities. It does
not claim full population validation or runtime enforcement.
