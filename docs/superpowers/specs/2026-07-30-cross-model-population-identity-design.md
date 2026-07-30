# Cross-Model Population Identity and Mapping Design

Date: 2026-07-30

## Purpose

Expand the first PILATES LinkML vertical slice beyond the post-ATLAS handoff
without attempting to translate the complete PILATES schema. The expansion
will demonstrate how one semantic repository can describe identity-preserving
joins, renamed fields, derived keys, and artifact-scoped identities across
UrbanSim, ActivitySim, ATLAS, and POLARIS.

The result should be useful to collaborators reviewing the model even when
their software does not use LinkML at runtime.

## Existing architecture

The approved federated architecture remains unchanged:

- `core` owns agreed semantic concepts and stable relationships.
- model directories own native or explicitly observed representations.
- PILATES profiles compose model contracts with snapshot, artifact, and
  provenance context.
- PILATES retains runtime joins, transformations, registry routing, recovery,
  and validation policy.

The existing `PopulationSnapshot`, `HouseholdState`, `PersonState`, and
`HouseholdMembership` classes remain the complete shared population kernel for
this slice. No producer-specific columns move into `core`.

## Evidence from the PILATES loop

PILATES preserves `household_id` and `person_id` through the UrbanSim to
ActivitySim preprocessing and ActivitySim to UrbanSim writeback paths.
Persons refer to households through `household_id`, forming a many-to-one
relationship.

Other similar-looking keys have different semantics:

- ActivitySim preprocessing regenerates `member_id` after filtering persons.
- The POLARIS translation converts `member_id` to a zero-based, within-household
  `id`.
- ActivitySim derives home `TAZ` from a household's `block_id` through a
  configured crosswalk.
- Work and school zone columns have adapter-specific aliases.
- ATLAS vehicle identity includes household, vehicle, and year, while the
  POLARIS translation emits only household and vehicle keys. The translated
  vehicle identity is therefore safe only within its enclosing snapshot
  artifact.

These differences are the main value of the expanded demonstration: the
schema should expose them rather than treating equal-looking values or similar
names as universal equivalence.

## Considered approaches

### Complete native-table translations

Translating complete UrbanSim, ActivitySim, and POLARIS tables would produce
broader documentation, but it would also promote many uncertain optionality,
code, unit, and ownership details before they have been reviewed.

### Mapping-only catalog

A mapping catalog without native record classes would be quick to create, but
collaborators could not validate or inspect representative model records.

### Identity-bearing native projections plus typed mappings

This is the selected approach. Small model-owned projections will contain only
the fields needed to demonstrate identity, membership, geography joins, and
known transformations. Typed mapping records will describe how those
projections relate.

## Model schemas

Each new class must be labeled as an identity-bearing projection rather than a
complete native table contract. Its annotations and documentation must identify
the owning representation, physical source, direction, and partial coverage.

### UrbanSim population projection

Add `models/urbansim/urbansim_population.yaml` with:

- `UrbanSimHouseholdPopulationRecord`
  - `household_id`: producer household identifier.
  - `block_id`: household location in the UrbanSim block geography.
- `UrbanSimPersonPopulationRecord`
  - `person_id`: producer person identifier.
  - `household_id`: reference to
    `UrbanSimHouseholdPopulationRecord.household_id`.
  - `member_id`: within-household position supplied by the population table.
  - `work_zone_id`: work location in the UrbanSim zone geography.
  - `school_zone_id`: school location in the UrbanSim zone geography.

The identifiers and person-to-household reference are required by this
projection. Location fields remain optional. `member_id` must be documented as
a local ordinal, not a person identifier.

### ActivitySim population projection

Add `models/activitysim/activitysim_population.yaml` with:

- `ActivitySimHouseholdInputRecord`
  - `household_id`
  - `block_id`
  - `taz`, physically represented as `TAZ`
- `ActivitySimPersonInputRecord`
  - `person_id`
  - `household_id`
  - `member_id`
  - `taz`, physically represented as `TAZ`
  - `work_zone_id`
  - `workplace_taz`
  - `school_zone_id`
  - `school_taz`
- `ActivitySimLandUseZoneRecord`
  - `taz`, physically represented as `TAZ`

The household and person identifiers and the person-to-household reference are
required. Location fields remain optional because the adapter can filter,
reassign, or clear invalid locations. `member_id` is required in the
ActivitySim projection but must be marked as regenerated during preprocessing.

The work and school aliases are equivalent only within the current PILATES
adapter. They are not universal synonyms in the shared kernel.

### POLARIS translation projection

Add `models/polaris/polaris_population.yaml` with:

- `PolarisHouseholdRecord`
  - `household`
  - `hhold`
  - `location`
- `PolarisPersonRecord`
  - `person`
  - `household`
  - `id`
- `PolarisVehicleRecord`
  - `vehicle_id`
  - `hhold`

These records describe the current output of the generated PILATES SQL
translation rather than a complete POLARIS database schema. `household` and
`hhold` are equal aliases in the translated household row. Person `id` is a
zero-based position within the household and is not equivalent to `person`.
The vehicle key is scoped to the enclosing translated snapshot artifact.

### ATLAS reuse

The existing `AtlasHouseholdInput`, `AtlasPersonInput`, and
`AtlasVehicleOutput` classes remain the ATLAS authority. They must be imported
and referenced by the mappings rather than copied.

## Typed mapping vocabulary

Add `mappings/population_identity.yaml` containing:

- `PopulationRepresentationMapping`: a named mapping between two
  representations, containing one or more slot mappings.
- `PopulationSlotMapping`: one source-to-target semantic relationship.
- `PopulationMappingStatus`: `direct`, `renamed`,
  `unit_or_enum_converted`, `derived`, `unsupported`, or
  `platform_specific`.
- `PopulationIdentityRole`: `entity_identifier`,
  `relationship_foreign_key`, `within_parent_ordinal`,
  `geographic_identifier`, or `artifact_scoped_identifier`.
- `PopulationValueStability`: `preserved`, `derived`, `regenerated`,
  `alias`, or `artifact_scoped`.

Each slot mapping must contain:

- a stable mapping identifier;
- source and target class-slot paths;
- mapping status;
- identity role;
- value stability;
- a plain-language relationship or transformation description;
- cardinality where the mapping expresses a relationship;
- an evidence reference to a PILATES code or test path.

Built-in LinkML mapping metadata may additionally link slots when exact or
related meaning is well supported. The typed mapping records remain necessary
because built-in mappings alone do not express transformation behavior,
stability, cardinality, or implementation evidence.

## Initial mapping coverage

The first mapping dataset must cover:

1. UrbanSim `household_id` to ActivitySim `household_id`: direct and
   identity-preserving.
2. UrbanSim `person_id` to ActivitySim `person_id`: direct and
   identity-preserving.
3. UrbanSim and ActivitySim person `household_id` fields to their household
   identifiers: many-to-one relationship projections corresponding to
   `HouseholdMembership`.
4. ATLAS `household_id` to POLARIS `household` and `hhold`: renamed and
   identity-preserving.
5. ATLAS `person_id` to POLARIS `person`: renamed and identity-preserving.
6. UrbanSim `member_id` to ActivitySim `member_id`: regenerated after person
   filtering and ordering.
7. ATLAS `member_id` to POLARIS `id`: derived by conversion to a zero-based
   within-household ordinal.
8. UrbanSim household `block_id` to ActivitySim household `TAZ`: derived
   through the configured block-to-zone crosswalk.
9. ActivitySim work and school location aliases: adapter-specific aliases with
   their physical spellings recorded.
10. ATLAS vehicle `(household_id, vehicle_id, year)` to POLARIS vehicle
    `(hhold, vehicle_id)`: identity narrowed to the enclosing translated
    snapshot artifact.

No mapping may classify `member_id`, POLARIS person `id`, or `vehicle_id`
alone as a globally stable entity identifier.

## Example

Extend `examples/post_atlas_population_bundle/` rather than creating a second,
disconnected population fixture. Add:

- representative UrbanSim records;
- their ActivitySim identity projections;
- the resulting POLARIS household, person, and vehicle records;
- a mapping manifest containing the initial mapping records.

The example must retain the existing synthetic household, person, snapshot,
and ATLAS vehicle identities. It should make the following transformations
visible:

- household and person identities remain unchanged across projections;
- the person continues to refer to the same household;
- a one-based source `member_id` becomes POLARIS person `id` zero;
- a household block is mapped to an ActivitySim `TAZ`;
- the POLARIS vehicle key is interpreted within the example's population
  snapshot rather than globally.

The existing example remains canonical test data. Tests must load it directly
rather than maintain separate fixture copies.

## Validation

Validation has three explicit levels:

1. LinkML validation checks each native projection and mapping record against
   its declared shape and required fields.
2. Mapping coverage tests require each initial relationship to have a status,
   identity role, stability classification, transformation description, and
   evidence.
3. Cross-file example tests verify the shared household/person values,
   person-to-household membership, alias agreement, ordinal conversion,
   block-to-zone example, snapshot context, and vehicle identity scope.

Ordinary LinkML validation does not prove that referenced rows are co-present,
that source and target artifacts share a snapshot, or that a transformation
was executed correctly. The focused example tests provide evidence for this
slice without claiming to be a general runtime conformance engine.

## Documentation

Update the model, mapping, profile, and example READMEs to explain:

- why these classes are partial identity projections;
- which system owns each physical representation;
- which identifiers are preserved and which values are regenerated;
- how mappings relate physical fields to shared population semantics;
- which integrity checks require higher-level validation.

Update the internal PILATES transition ledger with the implemented scope,
evidence, remaining owner-review questions, and a decision recording that
identity-bearing projections plus typed mappings are the selected incremental
expansion strategy.

## Non-goals

This slice will not:

- add producer-specific attributes to the shared population kernel;
- claim complete UrbanSim, ActivitySim, or POLARIS schema coverage;
- change PILATES adapters, generated SQL, schema registry behavior, or runtime
  validation;
- modify the ActivitySim repository;
- model OMX adapter ordinals or general skim-coordinate contracts;
- infer requiredness, units, or enumerations from nullable SQLModel stubs;
- treat mapping declarations as proof of cross-artifact referential integrity.

OMX ordering and canonical zone-domain conformance remain part of the planned
labeled-skim workstream.

## Verification

Implementation is complete only after fresh runs of:

- LinkML lint for the canonical schema import closure;
- the complete `synergy-schema` test suite;
- focused validation of every new example record and mapping;
- `scripts/preview-schema-docs build`;
- `git diff --check`;
- a review confirming that no PILATES or ActivitySim files changed.
