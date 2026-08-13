# Shared Scenario Trajectory and Documentation Design

## Goal

Build an early, collaborator-facing proof of concept around a small population
that visibly evolves across three years. Extend Synergy Schema from its current
yearly post-ATLAS slice into the smallest useful shared multi-year scenario
substrate for PILATES and POLARIS. The shared layer must identify one versioned
scenario definition, its stochastic trajectories, and their yearly population
snapshots while allowing each modeling context to retain different native
attributes and outputs.

The generated Markdown and HTML documentation must also give a newcomer a
clear, navigable explanation of the project's purpose, shared data structure,
workflow-specific structures, mappings, validation boundaries, and complete
generated reference.

## Design principles

1. Synergy Schema owns canonical semantics, typed mappings, compatibility
   declarations, and provider-neutral bundle contracts.
2. PILATES retains runtime orchestration, application-output persistence and
   routing policy, adapter behavior, and production artifact validation.
   Consist retains persistence of its provenance ledger.
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
7. Delivery starts with a day-zero manifest and one-year mapping handshake,
   adds repeatable review tooling, and then builds the readable three-year
   example. Each increment adds only the schema needed for its artifacts; the
   class catalog supports the examples.
8. Existing ATLAS/DEMOS-to-POLARIS mapping work is an authoritative input, not
   work to replace. Synergy gives that work a durable, reviewed contract and
   gives each application of it a verifiable receipt.
9. Adoption remains reversible. The teams keep their payloads, source mapping,
   generated human-readable contract, and inert manifests if they stop using
   Synergy; only automated checking and generation are lost.

## Considered approaches

### Recommended: evolving-population proof of concept

Add a small core scenario and trajectory vocabulary, a source-linked POLARIS
translation bundle, and focused conformance checks. Keep existing model-owned
records intact and demonstrate the design with one compact population across
2025, 2030, and 2035, a policy variant, and deliberately broken variants.

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

### Context-dependent: flat files plus a README

For a one-off, single-year exchange between stable teams, well-named flat files
and a careful README may be sufficient. The files are still the correct data
payload for this design. They become insufficient as the durable integration
record when mappings change, scenarios and years multiply, missing years need
an explanation, or a future user must reconstruct which transformation
produced an artifact.

Synergy does not replace the files. It records the versioned transformation,
the accepted losses and defaults, and the scenario/run/artifact identities
beside them. In this sense, the mapping is the function and the bundle manifest
is the receipt for one application of that function.

## Why LinkML is the source language

This repository produces a cross-team semantic agreement, not a database or a
shared runtime library. LinkML is appropriate because its YAML source can be
reviewed independently of Python, R, C++, Scala, SQL, or any model's storage
engine, while still generating JSON Schema, SQL DDL, Python/Pydantic models,
SHACL, diagrams, and reference documentation.

Raw SQL DDL remains appropriate for a physical database but would make storage
layout look canonical and does not natively express cross-representation
mappings such as renamed, derived, or unsupported concepts. SQLModel/Pydantic
would require non-Python teams to adopt the PILATES implementation language and
would blur the boundary between shared semantics and orchestrator policy. JSON
Schema is a useful generated validation target, but it is weaker as the
authored semantic and mapping vocabulary and would require a separate
documentation model.

The project will not claim that LinkML validates everything. LinkML owns the
source contract, generated bindings, and document-shaped validation. The
focused Python conformance layer owns cross-record and cross-artifact rules.
For production-scale populations, LinkML describes the snapshot, artifact, and
row contracts; it does not inline millions of records into a manifest. The
small proof-of-concept population and a production population therefore use
the same bounded-size metadata structure.

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

The digest is calculated from a deterministic JSON projection of the semantic
definition: region, horizon, optional parent reference, and assumptions sorted
by semantic key with their value, value type, unit, and authority. The
projection excludes the digest itself, display text, and workflow bindings.
The conformance implementation publishes this projection and canonicalization
algorithm alongside the fixtures so a producer can reproduce the digest
without using a Synergy runtime library.

Each `ScenarioAssumption` has a stable semantic key, a declared value, a
required `value_type`, an optional unit, and an authority/owner. `value_type`
is one of `integer`, `number`, `boolean`, `string`, `code`, or `reference`.
Values retain a scalar string representation so the schema does not grow a
universal parameter type system; conformance checks normalize them by declared
type before comparison. Boolean normalization accepts only explicit true/false
and 1/0 spellings. Code and reference values remain exact strings.

The proof of concept uses real shared questions evidenced by a current,
validated hierarchical PILATES scenario configuration rather than inferring a
contract from the legacy flat fields still present at the root default path.
The precise native bindings are `run.region`, `run.start_year`, `run.end_year`,
the effective ATLAS policy selected by `atlas.adscen` with the documented
`atlas.scenario` fallback and alias normalization, plus `atlas.rebfactor`,
`atlas.taxfactor`, and `atlas.discIncent`. PILATES execution frequencies are not
canonical scenario assumptions; they are orchestrator policy and appear only
as operational schedule evidence in the PILATES profile.

`ScenarioDefinitionReference` is the portable reference form used at exchange
boundaries. It carries `scenario_definition_id`, `revision`, and
`content_digest`; therefore two snapshots cannot appear to share a scenario
while silently selecting different revisions. It is an inlined reference
object rather than a bare string. The existing synthetic fixtures will be
migrated to this representation as an intentional schema change.

An optional `parent_definition_ref` connects a policy variant to the definition
from which it branches. A baseline definition and a ZEV-mandate definition are
distinct immutable definitions even when they share an initial population.

### ModelScenarioBinding

`ModelScenarioBinding` declares how one workflow or model configuration binds
to a `ScenarioDefinition` revision. It contains:

- the referenced scenario definition;
- `model_name` and `binding_id`;
- one or more `ScenarioAssumptionBinding` entries;
- a `NativeContractCatalogReference` containing the upstream contract kind,
  revision, and immutable digest used to interpret native references.

Each assumption binding identifies the canonical assumption key, a typed
`NativeContractElementReference`, the resolved native value, and one of these
controlled modes:

- `direct`: the model consumes the canonical value without transformation;
- `alias`: a native label is declared equivalent to the canonical value;
- `transformed`: a documented deterministic transformation is required;
- `override`: the model intentionally uses a different value and records why;
- `unsupported`: the model does not represent the assumption.

Bindings also declare compatibility as `compatible`,
`compatible_with_gaps`, `incompatible`, or `pending_review`. A model that
explicitly marks an assumption unsupported may be compatible with gaps: it has
not made a contradictory assertion, but it also cannot claim complete coverage
of the shared definition. `incompatible` and `pending_review` are explicit
states, not ordinary successful mappings. A direct or alias binding whose
resolved value differs from the canonical value is a conflict. Transformed
bindings must record the transformation. Overrides remain visible and are not
silently treated as agreement; an override makes the binding incompatible for
a completed shared scenario. An `override` requires a non-empty rationale;
`transformed` requires a non-empty transformation description; `unsupported`
does not carry a resolved native value.

`NativeContractElementReference.kind` is one of `config_path`,
`artifact_key`, or `sql_column`. The value remains owned by its native system,
but it must resolve against a pinned, checksummed contract catalog. For the
proof of concept, Synergy vendors generated inventories—not PILATES Python
modules—from a named PILATES commit: the Pydantic configuration paths and the
constant artifact-key values explicitly declared in `artifact_keys.py`. The
initial catalog does not claim to cover registry aliases or dynamic key
families such as `vehicles_{year}`; a reference outside the declared catalog is
unsupported rather than guessed. The POLARIS catalog lists SQL output columns
and the exact translation package digest. This makes mapping references
checkable without making Synergy import PILATES or requiring POLARIS to run
LinkML.

A deterministic catalog-maintenance command accepts a local upstream checkout,
extracts those inventories, and records the source revision and catalog digest.
Synergy CI validates internal references and digests against the committed
catalogs; refreshing a catalog is an explicit reviewable upstream-version
change, not a network or cross-repository test dependency.

Scenario-assumption bindings normally select `config_path` or `sql_column`.
`artifact_key` is available to profile member and handoff mappings when a
PILATES artifact role is the native contract element; it is not used merely
because an artifact happens to carry a configured assumption.

### PopulationTranslationContract

The ATLAS/DEMOS and POLARIS teams' existing column reconciliation becomes the
input to a versioned `PopulationTranslationContract`; Synergy does not ask the
teams to redo it or change either native table. The contract contains:

- a stable ID, immutable revision, and `semantic_content_digest`;
- a required `encoding_source` `PhysicalArtifactReference` pointing to the
  team-maintained spreadsheet, script, SQL, or equivalent artifact from which
  the draft contract was transcribed, plus optional supporting sources;
- source and target `NativeContractCatalogReference` objects;
- the full reviewed `PopulationFieldMapping` entries for direct, renamed,
  converted, and derived fields;
- zero or more explicit `MappingResidueRecord` entries for defaults,
  unsupported fields, filtering, lookups, and other non-clean cases;
- `MappingGovernance` describing stewardship and review state.

The encoding source is the root of the transcription lineage. Before owner
approval, a disagreement about transcription resolves against that exact
artifact. Once both model owners approve the normalized contract, the approved
semantic digest is the exchange agreement for that revision; the original
artifact remains its attributed source rather than being overwritten or
recast as Synergy-authored work.

The semantic digest covers source/target catalog references, field mappings,
and residue declarations. It excludes encoding-source bytes, implementation
artifacts, review records, and lifecycle status. Each owner review records the
exact semantic digest it assessed, so a semantic mapping change cannot inherit
an earlier approval. Formatting-only source changes, script refactors, or
governance updates remain visible in lineage and diffs without imposing a new
dual-model semantic approval.

`TranslationImplementationBinding` is a separate workflow-owned record, not a
mutable child of the immutable semantic contract. It identifies one
implementation artifact and digest, the semantic contract digest it claims to
implement, workflow owner, status (`declared`, `conformance_checked`, or
`retired`), and validation evidence. A receipt using an unregistered digest is
an error. A newly registered `declared` implementation can support discovery
with a warning but fails production acceptance until conformance checked. This
makes implementation drift visible without treating every byte-level refactor
as a semantic change. Mapping release directories keep semantic contracts and
workflow-owned implementation bindings in visibly separate subdirectories.

The existing `PopulationRepresentationMapping` remains the focused vocabulary
for identity-bearing relationships. The translation contract can reference it
and adds complete exchange-column coverage; it does not broaden every identity
mapping into a physical-table specification.

Each `PopulationFieldMapping` uses catalog-resolved source and target element
references, a controlled transformation mode, a plain-language rule, and
implementation evidence. This general field vocabulary is distinct from
`PopulationSlotMapping`, whose extra identity role, value stability, and
cardinality semantics remain useful for identity-bearing fields.

`MappingResidueRecord` captures one intentional place where the translation is
not a clean source-to-target field mapping. Its required `residue_kind` is one
of `unmapped_source`, `required_target_default`, `lookup_or_crosswalk`,
`filtered_rows`, `aggregated_or_split`, or `dropped_context`. Each record has a
stable ID, affected native contract element references, a deterministic rule
when one exists, rationale, disposition, and implementation evidence. For
example, dropping the ATLAS vehicle output year from each POLARIS row while
retaining it in the enclosing snapshot becomes a `dropped_context` record
rather than prose hidden in a class annotation.

Coverage has one unambiguous primary disposition. Every source exchange column
is either mapped or marked `unmapped_source`/`dropped_context`; every required
target column is mapped or has a `required_target_default`. Supplemental
lookup, filtering, aggregation, and split records may attach to those primary
dispositions without pretending to be another column mapping.

Residue declarations describe expected transformation behavior. Run-specific
facts—such as how many rows a filter removed, which lookup revision was used,
and whether the declared disposition occurred—are
`MappingResidueObservation` records in the derived bundle. This preserves the
distinction between a declared contract and evidence from one application.
Each observation names the residue record and semantic digest, simulation year,
affected artifact roles, observed count or lookup digest when applicable, and
the resulting disposition.
Every translation is potentially lossy; recording accepted loss is normal
engineering evidence, not a defect finding.

`MappingGovernance` avoids a single unilateral authority field. It contains a
maintaining team, lifecycle status (`draft`, `approved`, `superseded`, or
`deprecated`), optional successor contract, and multivalued
`MappingReviewRecord` entries. Each review names the source owner, target
owner, or workflow integrator role; team; review date; decision; optional team
contact; and rationale. An `approved` ATLAS/DEMOS-to-POLARIS contract requires
`accept` decisions from both source- and target-model owners for the current
semantic digest. Synergy maintains the encoding and validation machinery; the
model teams retain authority over the meaning of their columns and whether the
mapping is accepted.

The contract lives in a mapping-specific directory whose ownership metadata
names both model teams. Repository review rules require those owners for
semantic changes when their Git identities are available. Synergy may author
the initial draft as a service, but after handoff changes arrive through that
team-owned path and validation runs in Synergy CI. If repository permissions
cannot grant merge custody directly, required owner reviews and the governance
record remain the enforceable substitute; Synergy has no model-owner `accept`
role.

| Concern | Accountable owner |
| --- | --- |
| Source and target column meaning | ATLAS/DEMOS and POLARIS model teams |
| Typed encoding and conformance tooling | Synergy Schema maintainers |
| Transformation executable and invocation | PILATES translation adapter |
| Flat-file payload bytes | Producing workflow |
| Per-application receipt | PILATES adapter, automatically in production |

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

Requested years are explicit handoff milestones, not inferred from a generic
frequency. PILATES's actual schedule depends on enabled models, interval
semantics, biannual ATLAS subyears, and special cases such as the 2010-to-2017
bridge. The PILATES profile therefore records `PilatesScheduleEvidence`: the
ordered planned execution boundaries and a status record mapping every
requested handoff year to successful export or skip reason, plus the pinned
config catalog/digest and scheduler implementation identity that produced the
evidence. The conformance checker requires the requested/successful/skipped
sets to agree with those status records. It does not require requested years to
equal every scheduler boundary, nor reimplement PILATES's scheduler in
Synergy.

### Evolving population states

The shared population vocabulary expands only enough to tell the proof-of-
concept story:

- `HouseholdState` gains optional predecessor state references so one prior
  household can have multiple successors after a split;
- `VehicleState` records snapshot-scoped vehicle identity plus an optional
  producer-preserved longitudinal vehicle reference;
- `HouseholdVehicleAssignment` relates a vehicle state to a household state in
  one snapshot and records whether the native evidence describes ownership,
  leasing, availability, assignment, or an unresolved relationship.

Demographics, vehicle technology, and model-specific household attributes stay
in native records. The shared classes identify occurrences and relationships;
they do not require two models to predict the same age, fleet technology, or
travel behavior.

## Handoff bundles and POLARIS projection

### PopulationTrajectoryBundle

`PopulationTrajectoryBundle` is a PILATES operational profile class built on
the provider-neutral `HandoffBundle`. It contains one `PopulationTrajectory`
and its successfully exported yearly `PopulationSnapshotBundle` manifests.
It cannot declare itself complete when a requested year is missing. The core
trajectory semantics remain independent of PILATES and Consist; this composed
bundle belongs in the PILATES profile because it selects PILATES's yearly
population handoff.

The bundle also carries `PilatesConsistTrajectoryEvidence`, a PILATES/Synergy
adapter-produced profile object assembled from public Consist run and artifact
records. It reuses the vendored `ConsistRunReference` for an enclosing parent
run assigned the profile role `scenario_header` and its child runs, and adds
PILATES-owned `year` and `iteration` evidence for each child because the
vendored Consist provenance release 0.1.0 does not contain those fields. When
parent evidence is declared, the checker verifies direct `parent_run`
agreement; absent parent evidence remains valid for legacy/best-effort PILATES
runs. The proof-of-concept profile requires it. The checker also verifies that
copied run year/iteration agree with each snapshot's
`simulation_year`/`equilibrium_iteration`, and that artifact associations point
to the declared child runs.

This is operational production evidence, not semantic trajectory identity.
Live Consist stores `parent_run_id`, `year`, and `iteration` as individually
indexed query fields, but they are neither a composite key nor a substitute for
`ScenarioDefinitionReference`. Direct parentage does not by itself prove that
the parent was created through `Tracker.scenario`. A maintained Consist
integration note explains the upstream query surface, the smaller vendored
0.1.0 schema boundary, and the adapter step that produces the profile object;
it does not imply that Consist currently exports this document directly.

### PolarisPopulationTranslationBundle

A separate workflow profile describes the derived POLARIS population package.
It references:

- the source `PopulationTrajectoryBundle` by stable ID plus immutable manifest
  digest;
- the same scenario definition and stochastic realization;
- the exact `PopulationTranslationContractReference` by ID, revision, and
  semantic digest, plus the source/target table shapes through
  `SchemaContractReference`;
- the exact `TranslationImplementationBinding` and copied translation
  executable/SQL `PhysicalArtifactReference`; the observed implementation
  digest must match that registered binding;
- POLARIS household, person, vehicle, vehicle-class, and vehicle-type artifact
  roles, with each member carrying its simulation year;
- any run-specific `MappingResidueObservation` records, including filter
  counts, lookup revisions, and declared dispositions;
- `receipt_generation_mode` (`manual_discovery` or `automatic_adapter`);
- the trajectory's requested, successful, and skipped years plus the bundle's
  completeness status.

A complete translated bundle has exactly one artifact for every required role
in every successful year. It cannot be complete when the trajectory has a
skipped requested year.

All five roles are per-year in the current translator. `vehicle_class` is
derived from that year's observed vehicle stock and lookups; `vehicle_type`
also uses the export year to compute vintage. They are therefore not promoted
to scenario-global members in this slice.

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
- `check-polaris-bundle --schema SCHEMA --bundle BUNDLE`;
- `check-all --schema SCHEMA --dir EXAMPLE_DIR` discovers the canonical
  example files and runs every applicable check for the first-run showcase.

`check-polaris-bundle` and `check-all` accept `--production`. That mode requires
an approved semantic contract, a `conformance_checked` implementation binding,
and an automatically emitted receipt; it rejects discovery manifests.

Adoption utilities use the same contract library:

- `create-day-zero-manifest --artifact ARTIFACT --producer-artifact PRODUCER
  --native-scenario SCENARIO --year YEAR --out MANIFEST` records one existing
  exchange without requiring field mappings;
- `render-mapping --release RELEASE_DIR --out-dir REVIEW_DIR` generates a
  one-page Markdown summary plus normalized mapping, residue, and review CSVs;
- `diff-mappings --old OLD_RELEASE --new NEW_RELEASE --format
  text|markdown|json` reports
  semantic, encoding-source, implementation-only, and governance changes
  separately;
- revision two adds `import-mapping --review-dir REVIEW_DIR --out-release
  RELEASE_DIR` and
  a round-trip test proving that the generated CSV review surface reimports to
  the same semantic digest. The Markdown summary is view-only.

The pilot intentionally starts with hand encoding rather than pretending an
importer can understand arbitrary team spreadsheets. `diff-mappings` ships with
the first typed-contract increment because it is useful even when teams adopt
no manifests or runtime integration.

Each command returns zero only when all applicable invariants pass. It writes
one actionable error per line to standard error and returns exit status 1 for
conformance failures or 2 for malformed invocation/input.

`compatible` and explicitly documented `compatible_with_gaps` bindings are
valid inputs. The latter produce a visible warning and summary entry while
preserving exit status 0. `incompatible` and `pending_review` bindings fail the
showcase `check-all`; they are never silently accepted as a completed shared
scenario. Diagnostics begin with stable identifiers such as
`SCENARIO_DIGEST_MISMATCH` and `ARTIFACT_IDENTITY_MISMATCH`, followed by the
affected object and expected/actual values.

A structurally valid `draft` translation contract may support the pilot and
synthetic showcase, but `check-all` emits `MAPPING_NOT_APPROVED`; documentation
must not describe it as team-approved. A production acceptance mode requires
`approved`: `check-mappings` and `check-all` accept
`--require-approved-mapping`, which converts that diagnostic to an exit-1
failure, and `check-all --production` implies it. `superseded` or `deprecated`
contracts cannot produce new receipts,
although historical receipts remain interpretable against their recorded
revision.

The conformance layer covers:

1. mapping paths resolve to real classes and slots through `SchemaView`;
2. each complete population snapshot bundle has exactly one household, person,
   and vehicle role;
3. each role selects its declared native contract root;
4. trajectory years are ordered, unique, scenario-consistent, and
   realization-consistent;
5. completeness status agrees with requested, successful, and skipped years;
6. each model scenario binding references a declared canonical assumption and
   has internally consistent mode/compatibility metadata;
7. native config paths, artifact keys, and SQL columns resolve against their
   pinned contract catalogs;
8. every translation contract has an immutable encoding-source identity, every
   source exchange column and required target column has one primary
   mapped-or-residue disposition, and an approved mapping has accepting source-
   and target-owner reviews for its current semantic digest;
9. residue observations select declared residues and satisfy required counts,
   lookup revisions, and dispositions;
10. the bundle's semantic digest agrees with its contract and its observed
    implementation digest selects a registered, non-retired binding; production
    mode additionally requires `conformance_checked`;
11. PILATES schedule evidence agrees with requested/successful/skipped years;
12. Consist child-run parentage and copied year/iteration agree with the
   enclosing trajectory and snapshots;
13. bundle member immutable identities agree with the corresponding Consist
    artifacts and associations;
14. each complete POLARIS translated bundle has exactly one required role per
    successful year and no skipped requested years.

Artifact-opening checks—Parquet schemas, row keys, foreign keys, per-household
member ordinals, and recalculating content digests from bytes—remain PILATES
adapter responsibilities. Synergy can and will compare two supplied immutable
digest assertions for consistency without opening the artifact.
The narrow day-zero helper is the exception for discovery: it computes a digest
for the one explicitly supplied local file and producing artifact, but does not
interpret Parquet/CSV rows or claim production observation. Recurring byte
observation remains adapter/Consist work.
The documentation states the boundary and gives PILATES concrete requirements
for its later integration. In particular, the POLARIS adapter must validate
non-null identifiers, unique `(household, id)` person ordinals, household and
vehicle foreign keys, and snapshot-scoped `(hhold, vehicle_id, year)` identity.

## Delivery sequence

This design is delivered as three separately reviewable Synergy increments
rather than one atomic change: adoption foundation, repeatable mapping
maintenance, and the three-year showcase. Automatic production receipt emission
is a later PILATES-owned integration after the portable contracts are reviewed.

### Day zero: one-file discovery manifest

The smallest meeting demonstration creates a `DayZeroExchangeManifest` beside
one existing file in roughly thirty minutes. This thin PILATES exchange-profile
object records the payload artifact/digest, producing script or SQL artifact
and digest, a required native scenario label and namespace, simulation year,
and an optional resolved `ScenarioDefinitionReference`. It requires no field
mapping, residue catalog, or owner review.

The manifest is explicitly `manual_discovery`, not a production receipt. It may
demonstrate artifact identity and expose missing context, but it cannot satisfy
production acceptance or become a hand-maintained parallel ledger. If automatic
PILATES emission is not implemented after the pilot, these discovery manifests
are shelved; the project retains the readable mapping contract rather than
curating receipts that can silently go stale.

### First increment: one-year mapping handshake

Before asking the model teams to review a three-year trajectory, run a bounded
pilot on one mutually available baseline year, initially 2025. The pilot keeps
the teams' existing Parquet/CSV tables unchanged and uses the ordinary
single-snapshot scenario/year/realization context. A one-entry trajectory bundle
is used only to reuse the exchange shape; the pilot does not claim to test
cross-year continuity and introduces no special single-year data model. It
will:

1. accept the teams' current spreadsheet, script, SQL, or notes in the form
   they already maintain;
2. have the Synergy maintainer encode the field mappings, residue records, and
   governance metadata, returning a reviewable draft within five working days
   after complete source material and native schemas are available;
3. place a manifest beside the existing files that records their digests, the
   mapping-contract revision/semantic digest, registered implementation digest,
   scenario, year, realization, and available run evidence;
4. ask source- and target-model owners to review semantics, especially defaults,
   lookups, filtered rows, and unsupported fields;
5. record encoding effort, unresolved ambiguities, coverage, and whether the
   receipt can be emitted automatically from the current translation path;
6. generate the one-page contract-at-a-glance summary and normalized review
   tables with team attribution, source-artifact lineage, review state, mapping
   counts, and residue counts.

The pilot tests whether durable encoding and review can be added at low cost.
It is not a referendum on whether provenance is valuable: one stable year is
the case in which flat files naturally look strongest, while the project goal
is repeated multi-year, multi-scenario exchange. Missing target-side Consist
instrumentation is recorded as an integration gap rather than causing the
pilot to invent POLARIS runtime support.

The checked-in one-year example is a synthetic, structurally faithful analogue.
Team-provided mappings or data that cannot be published remain external and are
referenced by digest/revision rather than copied into this repository.

Hand-authored pilot manifests are acceptable only during bounded discovery, not
as a recurring operational record. The production target is automatic receipt
emission by the workflow adapter whenever the mapping is applied; teams
maintain the mapping semantics, while PILATES owns when and how the receipt is
emitted.

### Second increment: repeatable mapping maintenance

After the hand-encoded draft establishes the teams' actual table shape, add the
generated review package importer and prove the contract-to-table-to-contract
round trip preserves the semantic digest. Keep Markdown as the one-page reading
surface and normalized CSVs as the editable/importable surface. Exercise
`diff-mappings` against at least one real revision and use its semantic versus
implementation-only classification as the review agenda.

The YAML instance remains the canonical machine record, but model teams are not
required to review or edit it; the generated tables are the durable human
interface.

This increment does not make arbitrary spreadsheets a permanent source format.
The original team artifact remains `encoding_source`; the normalized review
package is the stable low-cost maintenance interface once the first contract is
accepted.

### Third increment: three-year evolving-population showcase

The reviewed one-year translation contract and residue catalog are reused in
the 2025/2030/2035 proof of concept. The third increment adds temporal
continuity, policy branching, missing-year semantics, and the deliberately
broken lineage cases. This keeps the showcase ambitious without making the
first collaboration request depend on the entire trajectory design.

## Collaboration demonstration and cost budget

The model-team meeting starts from their work, not from LinkML. The 90-second
technical demonstration first runs the broken scenario fixture and shows the
changed-rebate/claimed-baseline error that no single table reveals. It then
creates a day-zero manifest against one real exchange file, if the team permits
local use. The Consist portion is explicitly PILATES-side lineage; missing
POLARIS run instrumentation is shown as a current gap rather than hidden.

Bring a deliberately incomplete `draft` contract. If team material is available,
encode a subset from it; otherwise start from the existing identity-bearing
ATLAS-to-POLARIS mappings. Ask participants to correct the table in their own
vocabulary. Git and `diff-mappings` retain each change; a dated
`MappingReviewRecord` captures the resulting review decision rather than
misrepresenting every edit as an approval.

The meeting asks for:

- the mapping artifact exactly as currently maintained;
- defaults, dropped rows, lookups, and unsupported fields, prompted by residue
  kind;
- one review contact per team and a review turnaround they choose;
- one real historical wrong-year, changed-script, lookup, or filtering incident
  that may be documented only after their review;
- the pilot year and scenario selected by the model owners.

Any accepted incident becomes a short, co-attributed case study using the
team's terminology, with that team retaining review over the published wording.
No synthetic anecdote is presented as their experience.

The project promises not to change payload formats, require LinkML in a model
stack, gate existing model runs on the pilot, rename native columns in generated
payloads, publish team data, or hold model-owner approval authority. The
meeting uses the rendered contract and caught-error demonstrations; **Why
LinkML** remains background documentation for interested readers rather than a
presentation topic.

Cost targets are explicit and measured during the pilot:

- day zero: no more than 30 minutes of Synergy-maintainer effort after receiving
  one file and its producing artifact;
- first draft: returned within five working days of complete mapping material;
- routine revision with no semantic change: each model team reads the generated
  diff and records one decision, targeted at 30 minutes or less;
- a revision affecting at most five semantic mapping/residue rules: targeted at
  60 minutes or less per reviewing team; broader semantic changes are planned
  reviews and are not advertised as a minutes-scale tax.

Within two weeks of receiving usable material, the target package is a draft
contract rooted at `encoding_source`, one day-zero real-file manifest, and the
review-stamped contract-at-a-glance document. Within three months—conditional
on owner review and the separately owned PILATES work—the target is a dual-owner
approved semantic digest, a diff across at least one real revision, automatic
baseline receipt emission, and the three-year showcase using the reviewed
contract with contributor credit.

If routine review exceeds those budgets, the review surface must be simplified
before wider adoption. If automatic adapter emission stalls, recurring receipts
are shelved rather than maintained by hand. The readable mapping and unchanged
payload files remain useful regardless.

## Examples and tests

The repository will add one entirely synthetic, human-readable proof of concept
with approximately six households, twelve persons, and five vehicles across
2025, 2030, and 2035. The example files are written first; the schema grows
only to support their demonstrated concepts. It contains:

- an immutable baseline scenario definition using real ATLAS policy concepts;
- a related ZEV-mandate definition that shares the initial population but has
  its own digest;
- PILATES and POLARIS bindings resolved against pinned native contract
  catalogs;
- a versioned population translation contract rooted at a synthetic
  `encoding_source`, with complete mapped-or-residue coverage, separate
  semantic and implementation identities, and non-fabricated review status;
- residue declarations and observations for at least one lookup/default, one
  filtered-row rule, one unsupported field, and the dropped per-row vehicle
  year retained by snapshot context;
- one baseline stochastic trajectory and one policy-variant trajectory;
- three population snapshots showing a birth or newly present person, a person
  aging into driving age in native records, a household split with follow-up
  successor states, and a vehicle moving between households;
- source post-ATLAS and derived POLARIS bundle manifests for every year;
- generated contract-at-a-glance Markdown and normalized review CSVs;
- a POLARIS binding that transparently declares the ZEV lever unsupported
  rather than manufacturing agreement;
- a concise Mermaid lineage diagram and small tables that let a collaborator
  inspect every state change.

The example includes two deliberately broken copies used by the CLI and docs:

1. a 2035 snapshot produced with a different rebate-factor value and scenario
   digest while the trajectory still claims the baseline definition;
2. a household member whose declared immutable digest disagrees with the
   associated Consist artifact identity.

The first demonstrates a cross-model upstream scenario conflict that no one
native table can detect. The second generalizes an invariant already covered by
the current example-specific test into the reusable conformance CLI.

Negative tests cover:

- a direct/alias scenario binding with a conflicting value;
- equivalent values such as boolean `true` and boolean `1`, or integer `01` and
  integer `1`, normalize within their declared type; boolean and integer values
  do not compare equal merely because both use the scalar string `1`;
- an unresolved mapping class or slot path;
- an unresolved native config path, artifact key, or SQL column;
- an uncovered source/required-target exchange column, ambiguous duplicate
  primary disposition, or residue observation inconsistent with its
  declaration;
- a mapping labeled approved without accepting source- and target-owner reviews;
- a translation bundle whose semantic digest differs from the referenced
  contract or whose implementation digest is unregistered/retired;
- an implementation-only revision that incorrectly invalidates semantic owner
  approvals, plus a declared-but-unchecked implementation rejected in
  production mode;
- duplicate household roles or a missing vehicle role;
- mismatched scenario definitions or realizations across trajectory snapshots;
- duplicate, unordered, missing, or incorrectly reported years;
- a PILATES schedule-evidence mismatch;
- a Consist child with the wrong parent, year, iteration, or artifact digest;
- a complete POLARIS bundle with a skipped required year;
- a `manual_discovery` manifest submitted for production acceptance.

Positive tests prove that rendering and reimporting the normalized review CSVs
preserves the semantic digest, and that `diff-mappings` distinguishes semantic,
encoding-source-only, implementation-only, and governance-only changes.

All production Python behavior follows test-driven development: each behavior
is introduced by a focused failing test, then the minimum implementation makes
it pass.

## Documentation information architecture

The maintained documentation supplies the conceptual navigation; generated
LinkML pages remain the exhaustive field-level reference.

Navigation order:

1. **Overview**
2. **Proof of concept**
   - **A population that changes over three years**
   - **What the checker catches**
3. **Bring an existing mapping**
   - **Day-zero manifest**
   - **One-year mapping handshake**
   - **Contract at a glance**
   - **Costs and exit**
4. **Design rationale**
   - **Why LinkML**
   - **Why not one big table?**
   - **Are flat files enough?**
5. **Shared structure**
   - **Schema organization**
   - **Scenario definitions and trajectories**
   - **Population snapshots and artifact identity**
6. **Workflow structures**
   - **PILATES post-ATLAS population**
   - **POLARIS translated population**
7. **Cross-model mappings**
   - **Population identity**
   - **Translation contract, residue, and lineage**
   - **Scenario compatibility**
8. **Schema reference**
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

The landing page presents two equally prominent next steps. **Bring an existing
mapping** is the model-team path and starts from a real current artifact. **A
population that changes over three years** is the conceptual showcase for
newcomers and program stakeholders. The latter prints the small population
changes, traces baseline and ZEV-mandate branches, links each semantic object to
its LinkML class, and runs `check-all` against both valid and broken examples.
It closes with the scale boundary: a six-household example and a
three-million-household run use the same bounded manifest structure because
production rows remain in declared artifacts. In a model-team meeting, the
real pilot leads and the synthetic showcase is supporting material.

The top-level **Bring an existing mapping** page uses four headings: **What we
ask**, **What we do not ask**, **What you get**, and **Timeline**. It states that
teams may provide their current spreadsheet, script, notebook, or SQL; Synergy
performs the initial encoding and returns it within the documented turnaround
target; model owners review rather than rewrite it. The do-not-ask section
explicitly says no LinkML runtime, no native schema migration, no file-format
change, no immediate multi-year commitment, and no transfer of mapping
authority.

**Day-zero manifest** shows the 30-minute discovery step and visibly labels the
result non-production. It explains the automatic-emission acceptance bar and
the kill criterion for hand-maintained receipts.

The **One-year mapping handshake** page is the lower-cost collaboration entry
point. It shows the unchanged payload files, their adjacent manifest, the
translation contract, residue catalog, and review state. It reports what the
pilot does and does not test and links forward to the three-year showcase.

**Contract at a glance** is generated from the typed contract. It displays the
source and target team names, encoding-source identity, semantic digest, review
status and dates, implementation bindings, coverage totals, and residue
summary, with links to the normalized CSV review tables. This always-current
one-page artifact is part of **What you get**, suitable for technical review or
program reporting without reading YAML.

**Costs and exit** publishes the initial and steady-state time budgets from the
pilot. It also states the reversible outcome plainly: if a team stops using
Synergy, it keeps unchanged payload files, its source mapping, generated
human-readable tables, and manifests as inert YAML; it loses automated
generation, validation, and cross-run checks. Historical receipts remain
readable without a Synergy service.

**What the checker catches** shows the exact diagnostics for the changed
scenario digest and mismatched Consist artifact identity. It also distinguishes
an unsupported assumption, which is a visible compatibility gap, from a
contradictory assertion, which is a conflict.

The **Scenario compatibility** page includes a compact decision table grounded
in the fixtures: an unmapped tool-local output is not a conflict; an unsupported
shared assumption is a compatible gap; an explicit override is visible but not
agreement; and a direct value mismatch is a conflict. The table names the
scenario revision, concept, scope, and authority that make the comparison
meaningful.

**Why LinkML** presents the source-language argument from this design in
newcomer-facing terms: one readable semantic source generates multiple target
representations, while focused conformance code handles rules that cross
records or artifacts. **Why not one big table?** explains that a shared kernel
preserves common identity and meaning without making PILATES and POLARIS adopt
each other's fields, requiredness, or predicted outputs.

The LinkML rationale remains available in the documentation but is not part of
the model-team adoption pitch; teams interact with their existing artifact,
generated tables, diffs, and receipts.

**Are flat files enough?** begins by stating the bounded case in which the
answer can be yes. It then answers the repeated-integration questions a payload
alone cannot: which mapping revision and executable produced it, which years
were intentionally absent, which scenario/run it belongs to, and what defaults
or losses were accepted. It describes the manifest as an adjacent receipt, not
a replacement file format.

**Translation contract, residue, and lineage** starts with a six-months-later
question: if person counts look wrong, which mapping and lookup revisions
produced the file, what rows were filtered, and who reviewed those rules? It
walks from the bundle's semantic digest and residue observations to the
reviewed contract and implementation artifact. It treats residue as a normal
property of translation and avoids presenting the page as an audit of either
team. When a model team supplies and approves a historical incident, the page
includes it as a co-attributed case study in that team's vocabulary.

A maintained Mermaid diagram provides the complete canonical structure at a
glance. Workflow pages use the same headings—purpose, inputs, shared context,
native records, outputs, mappings, validation boundary, and reference links—so
readers can compare PILATES and POLARIS without learning a new page structure.
Each workflow page begins with a consistently styled **Current / proposed / out
of scope** callout. In particular, the POLARIS page states that the current path
is an offline translation/export package and that runtime workflow integration
is proposed, not already deployed.

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
top-level sections. They also check that the proof-of-concept page links to the
scenario, trajectory, household, person, vehicle, and provenance reference
pages and includes copyable `check-all` commands for the valid and broken
fixtures. The commands use distinct fixture directories and state their
expected exit codes: 0 for the valid example and 1 for each broken example.
Tests assert the documented stable diagnostic identifier for each failure. The
adoption-page tests also assert both landing-page actions, the day-zero warning,
contract-at-a-glance fields, stated time budgets, and exit guarantees. The
static build remains the final HTML-level check.

## Scope boundaries

This slice does not:

- migrate PILATES runtime schemas or registry behavior;
- modify the PILATES or Consist repositories; native catalogs are generated
  from named upstream revisions and vendored into Synergy for validation;
- execute POLARIS as part of PILATES;
- replace or independently reinterpret the ATLAS/DEMOS and POLARIS teams'
  existing column reconciliation;
- require LinkML in either model runtime or require either team to change its
  native tables or flat-file payloads;
- treat a manually produced day-zero manifest as production provenance;
- define a universal household/person/vehicle attribute record;
- claim complete POLARIS native-schema coverage;
- interpret production Parquet/CSV contents or validate production foreign
  keys; the day-zero helper only hashes explicitly supplied bytes;
- implement skim/OMX/Zarr conformance;
- define canonical longitudinal birth/death identity beyond existing optional
  references;
- change the vendored Consist provenance release.

## Acceptance criteria

The work is complete when:

- the root schema exposes typed scenario, binding, trajectory, trajectory
  bundle, day-zero manifest, population translation-contract/reference,
  implementation-binding, residue/observation/governance, and POLARIS
  translation-bundle classes;
- every draft contract references the original team-maintained
  `encoding_source` by immutable artifact identity, while unpublished material
  remains external;
- `create-day-zero-manifest` hashes only the explicitly supplied payload and
  producer artifacts, labels the result discovery-only, and production mode
  rejects it;
- the one-year pilot package preserves the existing payload format, records the
  semantic digest and registered implementation digest, covers every exchange
  column by a mapping or residue, and displays its actual review state without
  fabricating owner approval;
- model-owner approvals bind the semantic digest; implementation-only changes
  remain visible and require a registered, conformance-checked workflow binding
  for production, but do not invalidate semantic approval;
- `render-mapping` produces the review-stamped contract-at-a-glance document
  and normalized CSVs, `diff-mappings` classifies four change categories, and
  revision two round-trips those CSVs without changing the semantic digest;
- team ownership metadata and repository review rules protect mapping-contract
  custody, with Synergy lacking a model-owner accept role;
- the documented ownership model assigns initial encoding and validation
  tooling to Synergy, semantic review to both model teams, and production
  receipt emission to the PILATES adapter;
- the three-year fixture validates and demonstrates person, household, and
  vehicle evolution, including the displayed birth/new presence, aging,
  household split and successor states, and vehicle transfer;
- the proof page renders both baseline and ZEV-mandate trajectories with their
  distinct immutable definition references/digests, all yearly handoff
  manifests, and a POLARIS `compatible_with_gaps` binding for the unsupported
  ZEV assumption;
- native contract references resolve against pinned PILATES and POLARIS
  catalogs without importing either runtime;
- PILATES schedule evidence and Consist scenario-header/child-run evidence are
  validated at the operational profile boundary without becoming core scenario
  identity;
- focused negative tests prove scenario conflicts, digest disagreement,
  incomplete mapping/residue coverage, false approval, mapping/implementation
  digest disagreement, bundle-role errors, unresolved mapping/native-contract
  paths, schedule disagreement, and trajectory completeness failures are
  rejected;
- `check-all` validates the showcase directory in one command, while granular
  subcommands remain available for CI and debugging; the valid directory exits
  0 with its documented compatibility-gap and, when applicable,
  `MAPPING_NOT_APPROVED` warnings, production mode rejects unapproved mapping
  contracts, and each broken directory exits 1 with its documented stable
  diagnostic identifier;
- the documentation landing page clearly states the repository's purpose and
  presents **Bring an existing mapping** and the three-year proof as co-equal
  actions;
- maintained pages explain why LinkML is the source language and why the shared
  model is not one universal table, and Scenario compatibility renders the
  tool-local/gap/override/conflict decision table;
- maintained pages concede when flat files plus a README are adequate, explain
  the adjacent-manifest value without disparaging the existing mapping work,
  document day zero and the one-year handshake, make residue/lineage
  inspectable, publish honest cost budgets and exit guarantees, and label the
  synthetic showcase as supporting evidence for a real model-team pilot;
- the generated contract-at-a-glance page displays team attribution,
  encoding-source lineage, review stamps, semantic/implementation identities,
  coverage, and residue totals;
- Zensical renders the eight top-level labels in the specified order, every
  named leaf has a maintained target, both Overview actions reach their intended
  pages, and pages cross-link to relevant generated class references;
- PILATES and POLARIS workflow pages render the **Current / proposed / out of
  scope** callout;
- the POLARIS workflow page clearly labels partial projections and future
  runtime enforcement boundaries;
- schema lint, the complete pytest suite, the documentation build, and
  whitespace checks pass.
