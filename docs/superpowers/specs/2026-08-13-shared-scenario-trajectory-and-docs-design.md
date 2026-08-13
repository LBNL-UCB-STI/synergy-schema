# Shared Scenario Trajectory and Documentation Design

## Goal

Extend Synergy Schema from its current yearly post-ATLAS population slice into
the smallest useful shared multi-year scenario substrate for PILATES and
POLARIS. The shared layer must identify one versioned scenario definition, its
stochastic trajectories, and their yearly population snapshots while allowing
each modeling context to retain different native attributes and outputs.

The generated Markdown and HTML documentation must also give a newcomer a
clear, navigable explanation of the project's purpose, shared data structure,
workflow-specific structures, mappings, validation boundaries, and complete
generated reference.

## Design principles

1. Synergy Schema owns canonical semantics, typed mappings, compatibility
   declarations, and provider-neutral bundle contracts.
2. PILATES retains runtime orchestration, artifact routing, persistence,
   adapter behavior, and production artifact validation.
3. POLARIS retains its native records, codes, execution behavior, and output
   semantics. Its Synergy profile describes exchange boundaries rather than
   replacing POLARIS runtime schemas.
4. The shared kernel is not a universal wide agent table. Native attributes may
   differ across tools without conflict when they are not mapped to the same
   canonical assertion.
5. Different model outputs are expected. A conflict exists only when two
   declarations make incompatible assertions about the same canonical concept,
   scenario revision, entity/snapshot scope, and authority.
6. Ordinary LinkML validation remains responsible for document shape. Explicit
   Python conformance checks handle cross-record, cross-role, and mapping-path
   invariants that LinkML cannot express.

## Considered approaches

### Recommended: incremental shared scenario vertical slice

Add a small core scenario and trajectory vocabulary, a source-linked POLARIS
translation bundle, and focused conformance checks. Keep existing model-owned
records intact and demonstrate the design with a compact multi-year fixture.

This approach directly addresses the missing shared semantics without turning
the repository into a copy of PILATES or a universal agent schema. It also
produces a complete, reviewable path through the documentation.

### Rejected: universal normalized agent record

Combining PILATES and POLARIS attributes into one shared household/person/
vehicle record would make tool-local requiredness, codes, and outputs appear
canonical. It would create false conflicts and undermine model ownership.

### Rejected: documentation-only expansion

Adding explanatory POLARIS and trajectory pages without typed schema objects
or conformance checks would improve navigation but leave scenario equivalence
and upstream conflicts unenforceable.

## Canonical scenario structure

### ScenarioDefinition

`ScenarioDefinition` identifies the shared policy/assumption definition that
multiple workflows implement.

Required fields:

- `id`: stable semantic identifier.
- `revision`: immutable revision or release label.
- `content_digest`: SHA-256 digest of the canonical scenario-definition
  document.
- `region_ref`: identifier for the modeled region/domain.
- `start_year` and `end_year`: inclusive scenario horizon.
- `assumptions`: one or more typed `ScenarioAssumption` declarations.

Each `ScenarioAssumption` has a stable semantic key, a declared value, an
optional unit, and an authority/owner. Values use a scalar string
representation in this slice so booleans, numbers, codes, and external
references can be carried without prematurely designing a universal parameter
type system. The semantic key and optional unit provide interpretation.

`ScenarioDefinitionReference` is the portable reference form used at exchange
boundaries. It carries `scenario_definition_id`, `revision`, and
`content_digest`; therefore two snapshots cannot appear to share a scenario
while silently selecting different revisions. It is an inlined reference
object rather than a bare string. The existing synthetic fixtures will be
migrated to this representation as an intentional schema change.

### ModelScenarioBinding

`ModelScenarioBinding` declares how one workflow or model configuration binds
to a `ScenarioDefinition` revision. It contains:

- the referenced scenario definition;
- `model_name` and `binding_id`;
- one or more `ScenarioAssumptionBinding` entries;
- the source contract revision or digest used to interpret model paths.

Each assumption binding identifies the canonical assumption key, the native
model path, the resolved native value, and one of these controlled modes:

- `direct`: the model consumes the canonical value without transformation;
- `alias`: a native label is declared equivalent to the canonical value;
- `transformed`: a documented deterministic transformation is required;
- `override`: the model intentionally uses a different value and records why;
- `unsupported`: the model does not represent the assumption.

Bindings also declare compatibility as `compatible`, `incompatible`, or
`pending_review`. `incompatible` and `pending_review` are explicit states, not
ordinary successful mappings. A direct or alias binding whose resolved value
differs from the canonical value is a conflict. Transformed bindings must
record the transformation. Overrides remain visible and are not silently
treated as agreement. An `override` requires a non-empty rationale;
`transformed` requires a non-empty transformation description; `unsupported`
does not carry a resolved native value.

### PopulationTrajectory

`PopulationTrajectory` groups the ordered yearly snapshots for one scenario
definition and stochastic realization. It requires:

- a stable trajectory ID;
- an inlined `ScenarioDefinitionReference`;
- one stochastic realization ID;
- ordered, inlined `PopulationSnapshot` metadata records;
- requested years, successful years, skipped years, and completeness status.

Snapshots remain occurrences rather than a timeless fixed population. A
trajectory validator checks that snapshot years are ordered and unique, every
snapshot uses the same scenario definition and realization, parent references
follow the declared order when supplied, and completeness agrees with the
requested/successful/skipped year sets.

`PopulationSnapshot.scenario_definition_ref` becomes an inlined
`ScenarioDefinitionReference`. Successful years are derived from the inlined
snapshot records. Skipped years are typed records with a year and reason.

## Handoff bundles and POLARIS projection

### PopulationTrajectoryBundle

`PopulationTrajectoryBundle` is a PILATES operational profile class built on
the provider-neutral `HandoffBundle`. It contains one `PopulationTrajectory`
and its successfully exported yearly `PopulationSnapshotBundle` manifests.
It cannot declare itself complete when a requested year is missing. The core
trajectory semantics remain independent of PILATES and Consist; this composed
bundle belongs in the PILATES profile because it selects PILATES's yearly
population handoff.

### PolarisPopulationTranslationBundle

A separate workflow profile describes the derived POLARIS population package.
It references:

- the source `PopulationTrajectoryBundle` by stable ID plus immutable manifest
  digest;
- the same scenario definition and stochastic realization;
- the exact mapping contract through `SchemaContractReference` and the copied
  translation executable/SQL package through `PhysicalArtifactReference`;
- POLARIS household, person, vehicle, vehicle-class, and vehicle-type artifact
  roles, with each member carrying its simulation year;
- the trajectory's requested, successful, and skipped years plus the bundle's
  completeness status.

A complete translated bundle has exactly one artifact for every required role
in every successful year. It cannot be complete when the trajectory has a
skipped requested year.

The existing `PolarisHouseholdRecord`, `PolarisPersonRecord`, and
`PolarisVehicleRecord` remain explicitly partial identity projections. This
slice does not claim full native POLARIS field coverage.

## Conformance checks

A focused Python module and CLI provide checks beyond LinkML shape validation.
The CLI uses explicit subcommands so each input contract remains clear:

- `check-mappings --schema SCHEMA --mappings MAPPINGS`;
- `check-scenario --schema SCHEMA --definition DEFINITION --bindings BINDINGS
  --trajectory TRAJECTORY`;
- `check-population-bundle --schema SCHEMA --bundle BUNDLE`;
- `check-polaris-bundle --schema SCHEMA --bundle BUNDLE`.

Each command returns zero only when all applicable invariants pass. It writes
one actionable error per line to standard error and returns exit status 1 for
conformance failures or 2 for malformed invocation/input.

The first checker covers:

1. mapping paths resolve to real classes and slots through `SchemaView`;
2. each complete population snapshot bundle has exactly one household, person,
   and vehicle role;
3. each role selects its declared native contract root;
4. trajectory years are ordered, unique, scenario-consistent, and
   realization-consistent;
5. completeness status agrees with requested, successful, and skipped years;
6. each model scenario binding references a declared canonical assumption and
   has internally consistent mode/compatibility metadata;
7. each complete POLARIS translated bundle has exactly one required role per
   successful year and no skipped requested years.

Artifact-opening checks—Parquet schemas, row keys, foreign keys, per-household
member ordinals, and content digests—remain PILATES adapter responsibilities.
The documentation states the boundary and gives PILATES concrete requirements
for its later integration. In particular, the POLARIS adapter must validate
non-null identifiers, unique `(household, id)` person ordinals, household and
vehicle foreign keys, and snapshot-scoped `(hhold, vehicle_id, year)` identity.

## Examples and tests

The repository will add one entirely synthetic two-year scenario example. It
contains:

- one immutable scenario definition;
- PILATES and POLARIS model bindings;
- one stochastic trajectory;
- two population snapshots with a deliberate membership change;
- source post-ATLAS and derived POLARIS bundle manifests.

Negative tests cover:

- a direct/alias scenario binding with a conflicting value;
- an unresolved mapping class or slot path;
- duplicate household roles or a missing vehicle role;
- mismatched scenario definitions or realizations across trajectory snapshots;
- duplicate, unordered, missing, or incorrectly reported years;
- a complete POLARIS bundle with a skipped required year.

All production Python behavior follows test-driven development: each behavior
is introduced by a focused failing test, then the minimum implementation makes
it pass.

## Documentation information architecture

The maintained documentation supplies the conceptual navigation; generated
LinkML pages remain the exhaustive field-level reference.

Navigation order:

1. **Overview**
2. **Shared structure**
   - **Schema organization**
   - **Scenario definitions and trajectories**
   - **Population snapshots and artifact identity**
3. **Workflow structures**
   - **PILATES post-ATLAS population**
   - **POLARIS translated population**
4. **Cross-model mappings**
   - **Population identity**
   - **Scenario compatibility**
5. **Schema reference**
   - **Complete generated reference**

The overview begins with a compact purpose statement:

> Synergy Schema defines the shared meaning and exchange contracts that let
> different transportation-modeling workflows describe the same scenarios and
> population states without forcing their native data structures or outputs to
> be identical.

The overview then answers, in order:

1. what this repository owns;
2. what remains owned by model runtimes;
3. how scenario, trajectory, snapshot, native records, handoff artifacts, and
   provenance relate;
4. where PILATES and POLARIS currently participate;
5. what validation is and is not enforced.

A maintained Mermaid diagram provides the complete canonical structure at a
glance. Workflow pages use the same headings—purpose, inputs, shared context,
native records, outputs, mappings, validation boundary, and reference links—so
readers can compare PILATES and POLARIS without learning a new page structure.

Generated reference pages remain ignored build products. Model source READMEs
do not serve as the only explanation of a model because they are not part of
the Zensical navigation.

## Documentation verification

The existing `scripts/preview-schema-docs build` command remains the canonical
generation path. CI adds this command after schema lint and tests so broken
navigation targets, generated references, custom diagrams, and static-site
build failures block changes.

Tests check that every maintained navigation target exists after generation
and that the Overview contains the required purpose summary and links to all
top-level sections. The static build remains the final HTML-level check.

## Scope boundaries

This slice does not:

- migrate PILATES runtime schemas or registry behavior;
- execute POLARIS as part of PILATES;
- define a universal household/person/vehicle attribute record;
- claim complete POLARIS native-schema coverage;
- open production Parquet files or validate production foreign keys;
- implement skim/OMX/Zarr conformance;
- define canonical longitudinal birth/death identity beyond existing optional
  references;
- change the vendored Consist provenance release.

## Acceptance criteria

The work is complete when:

- the root schema exposes typed scenario, binding, trajectory, trajectory
  bundle, and POLARIS translation-bundle classes;
- the two-year fixture validates and demonstrates changing membership;
- focused negative tests prove scenario conflicts, bundle-role errors,
  unresolved mapping paths, and trajectory completeness failures are rejected;
- the conformance CLI reports actionable errors and a nonzero exit status;
- the documentation landing page clearly states the repository's purpose;
- all maintained documentation sections are reachable through Zensical
  navigation and cross-link to relevant generated class pages;
- the POLARIS workflow page clearly labels partial projections and future
  runtime enforcement boundaries;
- schema lint, the complete pytest suite, the documentation build, and
  whitespace checks pass;
- existing user-owned untracked files remain untouched.
