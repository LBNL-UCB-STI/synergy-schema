# What the checker catches

The checker compares declarations across the scenario, trajectory, model
bindings, bundles, mapping description, and exchange receipts. The tables
below display the important rows from the actual synthetic fixtures; the
source filename above each table links to the complete executable document.

=== "Population evolution"

    Source:
    [`core-population-evolution.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/expand-schema/examples/evolving_population/core-population-evolution.yaml)

    Every person record in this synthetic fixture is shown below. This is an
    exhaustive display of the tiny fixture, not a sample of a real population.
    The fixture does not declare person-to-household membership, so the tables
    do not infer it.

    #### Snapshot summary

    “Household state records” counts the household identities described in that
    year's lineage evidence. It should not be read as a count of active occupied
    households.

{{ showcase_snapshot_summary_table(4) }}

    #### Person history

    Each row is one declared person in one year. Age is shown as model-owned
    evidence; it is not part of the shared identity kernel.

{{ showcase_person_history_table(4) }}

    #### Household lineage

    This table shows predecessor and successor declarations without implying
    that a predecessor record is still an active household.

{{ showcase_household_lineage_table(4) }}

    #### Vehicle assignment history

{{ showcase_vehicle_history_table(4) }}

=== "Scenario bindings"

    Sources:
    [`zev-scenario-definition.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/expand-schema/examples/evolving_population/zev-scenario-definition.yaml)
    and
    [`zev-model-bindings.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/expand-schema/examples/evolving_population/zev-model-bindings.yaml)

    Every shared assumption is shown. Every assumption binding declared by this
    synthetic fixture is shown as well. An absent model-assumption pair is not
    silently treated as a binding; only explicit declarations appear.

    #### Shared scenario assumptions

{{ showcase_scenario_assumptions_table(4) }}

    #### Model binding declarations

    Each row is one explicit connection from a shared assumption to a native
    model element. “Not declared” means the binding supplies no native value;
    here, POLARIS records an unsupported but non-conflicting gap.

{{ showcase_bindings_table(4) }}

=== "Broken checks"

    All digest values below come directly from the valid and broken fixtures;
    compact prefixes are displayed for readability. These tables expose the
    cross-document comparisons instead of showing only the final errors.

    #### Scenario identity mismatch

    Sources: valid
    [`zev-scenario-definition.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/expand-schema/examples/evolving_population/zev-scenario-definition.yaml)
    and altered
    [`broken-scenario-definition.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/expand-schema/examples/evolving_population_broken_scenario/broken-scenario-definition.yaml).

{{ showcase_broken_scenario_table(4) }}

    #### Implementation artifact identity mismatch

    Sources: valid
    [`zev-polaris-translation-bundle.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/expand-schema/examples/evolving_population/zev-polaris-translation-bundle.yaml)
    and altered
    [`broken-polaris-bundle.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/expand-schema/examples/evolving_population_broken_artifact_identity/broken-polaris-bundle.yaml).

{{ showcase_broken_artifact_table(4) }}

The population ages in the first table are deliberately labeled model-owned:
different workflows may produce different attributes without conflicting. The
checker focuses on shared assertions, declared relationships, mapping
coverage, and immutable identities.

## Run the checks

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
