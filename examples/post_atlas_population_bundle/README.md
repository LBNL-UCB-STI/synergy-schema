# Post-ATLAS population bundle example

This self-contained, entirely synthetic example shows one 2025 population
snapshot after ATLAS: the native ATLAS household, person, and vehicle rows;
the shared snapshot-scoped state records; and the PILATES handoff bundle that
describes the three real artifacts. It is an example of the current contracts,
not a real dataset or a complete population validator.

## Read these files in this order

1. [`atlas_population_records.yaml`](atlas_population_records.yaml) shows one
   representative native ATLAS household input, person input, and vehicle
   output row.
2. [`core_population_states.yaml`](core_population_states.yaml) gives that
   household and person their identities within one population snapshot and
   records the household membership relationship.
3. [`population_snapshot_bundle.yaml`](population_snapshot_bundle.yaml)
   composes the snapshot and its household, person, and vehicle artifacts into
   one PILATES handoff.

## What each layer means

The native records are owned by ATLAS. `AtlasHouseholdInput` and
`AtlasPersonInput` are inputs ATLAS receives; `AtlasVehicleOutput` is an output
ATLAS produces. Their physical field names and code values remain ATLAS
concerns. PILATES does not own or copy those row definitions. Instead, its
profile selects those three native contracts and composes their artifacts into
the handoff.

A `PopulationSnapshot` is one scenario-specific population at one simulation
year and one stochastic realization. The `stochastic_realization_id` belongs
to the snapshot because the same scenario can branch into different simulated
outcomes. `HouseholdState` and `PersonState` are occurrences within that
snapshot, while `HouseholdMembership` is also snapshot-scoped: people can be
born, die, or move households as a scenario evolves. The optional longitudinal
references show a producer's link across snapshots without assuming every
producer can preserve it.

The bundle is the artifact-level handoff. Its members point to the three
Parquet artifacts, state the native LinkML contract selected for each role, and
record a synthetic immutable SHA-256 content digest. The small YAML rows in
the first file illustrate those contracts only; they are not the Parquet
members and do not produce the displayed digests.

The same bundle carries a Consist provenance document. Its namespace and local
run or artifact identifier together provide portable Consist identity. The
document records the producing run, one Consist artifact reference for each
member, and three output associations. The Consist identities repeat each
member digest only as a trusted assertion about the same bytes; the focused
checks reject disagreement between those assertions.

`year` on the vehicle is the ATLAS forecast/output year that participates in
the vehicle's natural key. `modelyear` is the year the vehicle model was made;
it is intentionally a different fact.

## Identity, evidence, and validation

Domain meaning includes the household/person/vehicle roles, each selected
native contract, and the snapshot's scenario, realization, and simulation
year. The artifact digest algorithm and content digest identify immutable bytes
once an artifact is selected. The Consist ledger namespace participates in run
and artifact reference identity; the ledger locator does not. Artifact
locators, the producing-run locator, row counts, and observed columns are
operational evidence: useful for finding and checking an artifact, but not
portable identity. A canonical digest for the complete bundle itself is
deliberately not defined yet.

Ordinary LinkML validation of the bundle checks declaration shape and required
fields. It does not enforce that a role's `selected_root` is the contract named
for that role, or that a Parquet member conforms to that contract. The native
row excerpts validate only when they are separately validated against the
named native class. LinkML also does not open a Parquet file, verify a digest,
resolve a locator, prove that a reference exists, or enforce a complete
cross-table population story. The focused tests add only the identifier and
snapshot consistency checks needed by this small example. They also check that
Consist output associations agree with artifact producers and that trusted
Consist identities agree with the corresponding Synergy member identities.
Those are cross-record checks rather than ordinary LinkML shape validation;
production-level completeness and referential validation remain separate work.

## Connected UrbanSim to POLARIS identity story

[`cross_model_population_records.yaml`](cross_model_population_records.yaml)
adds one synthetic path from UrbanSim through ActivitySim and ATLAS to
POLARIS. It is intentionally a row-level identity illustration, not an
artifact handoff or a claim that these are complete model inputs.

| Semantic concept | Physical fields in this example | Status | Ordinary LinkML boundary |
| --- | --- | --- | --- |
| Household identity | UrbanSim/ActivitySim/ATLAS `household_id`; POLARIS `household` and `hhold` | Preserved; `hhold` is an alias | Each row's required fields and types validate. |
| Person identity | UrbanSim/ActivitySim/ATLAS `person_id`; POLARIS `person` | Preserved under a renamed field | It does not prove records in different files refer to the same person. |
| Household membership | Person `household_id`; POLARIS person `household` and vehicle `hhold` | Preserved; POLARIS fields are renamed | It does not resolve or verify the referenced household row. |
| Within-household ordinal | UrbanSim/ActivitySim/ATLAS `member_id`; POLARIS person `id` | Preserved through ATLAS; transformed to POLARIS's zero-based local ordinal | It cannot establish that the two ordinal conventions represent the same member. |
| Home and destination geography | UrbanSim/ActivitySim `block_id`, `taz`, `work_zone_id`/`workplace_taz`, and `school_zone_id`/`school_taz`; POLARIS `location` | Block identity is preserved into ActivitySim; zone aliases are explicit; POLARIS location is platform-specific | It validates physical fields but does not perform geographic lookup or conversion. |
| Vehicle identity | ATLAS `(household_id, vehicle_id, year)`; POLARIS `(hhold, vehicle_id)`; enclosing snapshot `simulation_year` | The translation drops ATLAS `year`; the remaining POLARIS pair is meaningful only inside the matching snapshot artifact | It does not establish vehicle identity outside the selected artifact. |

The ordinary LinkML boundary ends at validating each excerpt against its named
row class. The focused tests additionally make this single synthetic path
checkable across files. They do not validate a complete population, open model
artifacts, execute UrbanSim-to-ActivitySim or ATLAS-to-POLARIS transforms, or
prove referential completeness in production data.

## Check the example

From the repository root, run:

```sh
/Users/zaneedell/miniforge3/bin/uv run linkml-lint \
  src/synergy_schema/schema/synergy_schema.yaml
/Users/zaneedell/miniforge3/bin/uv run pytest -q \
  tests/test_schema.py tests/test_population_projections.py
```
