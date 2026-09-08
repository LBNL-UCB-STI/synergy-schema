# Glossary

This glossary explains the project’s recurring terms in plain language. Formal
names are retained where they appear in schema classes or fields, even when the
guides use a shorter phrase. The [generated schema
reference](../schema/index.md) remains authoritative for exact fields, types,
requiredness, and cardinality.

## Why these records exist

No single file can establish that several workflows simulated the same shared
universe. A scenario definition states the common assumptions. An interface
reference locates those assumptions in a model-owned system. A mapping states
how representations relate. A review record records a named role's decision on
one exact mapping version. An implementation binding names the code associated
with that version, and a receipt records one actual use of the code and files.

These records are separate because the underlying facts change independently.
The separation also limits each claim: evidence that a file came from a named
run is not proof that the mapping was approved, and an approved mapping is not
proof that the expected code ran.

## Shared scenarios and changing populations

### Scenario definition

The versioned set of shared assumptions that multiple modeling workflows
intend to represent. Its digest distinguishes one exact revision from
another; it does not contain every model-specific setting.

### Scenario binding

A statement of how a model’s native configuration represents one shared
scenario assumption. A binding can be direct, an alias, transformed,
intentionally overridden, or unsupported.

## What a binding means here

A **binding** is a declared, checkable connection between something shared
and the model-specific representation that is meant to stand for it. It
answers “where and how does this shared meaning show up in this model?” A
binding does not copy the underlying data, require identical model outputs,
or transfer control of a model-owned field to Synergy. It also does not prove
compatibility by itself: the binding records enough information for a checker
and the relevant owners to make that decision.

| Binding or relationship | Connects | Maintained by | What it establishes |
| --- | --- | --- | --- |
| Scenario binding | A shared scenario assumption to a native setting or value | The model or workflow team that configures the model | How that model represents, omits, or overrides the assumption |
| Field mapping | A source native element to a target native element | Source and target meaning owners | The reviewed meaning of one translation rule |
| Schema contract reference | An artifact to an immutable schema and root class | The exchange producer | Which exact structure interprets the artifact |
| Implementation binding | A reviewed mapping description to executable SQL or code | The workflow team that runs the translation | Which implementation claims to carry out that mapping version |

“Binding” is therefore more specific than “related to.” It names both sides
of a boundary and the nature of their connection. A scenario binding concerns
shared assumptions; an implementation binding concerns executable code.

### Population trajectory

An ordered sequence of population snapshots for one scenario definition and
stochastic realization. It also records which years were requested,
completed, or deliberately skipped.

### Population snapshot

The population state at one simulation year for one scenario and
realization. It is an occurrence in time, not a timeless master population.

### Stochastic realization

One repeat of a model run whose random choices may produce different results
even under the same scenario definition. The realization identifier keeps
those parallel outcomes separate.

### Core population state

A shared, snapshot-scoped identity for a household, person, vehicle, or
relationship. Core state records intentionally omit model-specific
demographics, technologies, and predicted behavior.

## Schemas, contracts, profiles, and native records

### Schema

A formal description of data structure: allowed fields, types, required
values, and relationships. LinkML is the source language used for schemas in
this repository.

### Contract

A formal schema name for a versioned agreement selected for an exchange. The
repository uses this word in classes such as `PopulationTranslationContract`
and `SchemaContractReference`; the maintained guides otherwise prefer the more
specific phrases “mapping description” or “schema reference.” A schema can
describe a broad reusable vocabulary, while the selected agreement identifies
the part used at one boundary.

### Schema contract reference

The language, immutable schema digest, and selected root class used to
interpret an artifact. Optional URI and version labels help people find the
schema but are not its identity.

### Profile

A composition of shared and model-owned definitions for a particular
workflow or exchange. A profile selects what that workflow requires without
taking ownership of every imported definition.

### Workflow profile

A profile owned at a workflow boundary—for example, the PILATES post-ATLAS
population handoff or the proposed POLARIS translation package. It is not
automatically proof that the workflow already enforces the profile at
runtime.

### Interface

The deliberately exposed part of a model or workflow that another system can
name or use, such as a configuration path, artifact key, table column, or file
role. An interface description identifies this boundary without claiming to
describe the model's full internal schema or behavior.

### Native record

A row or data structure whose fields and meanings remain owned by its source
model, such as an ATLAS household row or a POLARIS person row. Shared
definitions refer to native records rather than replacing them with one
universal table.

### Native contract

A model-owned description of the interface surfaces that another workflow may
refer to: configuration paths, artifact keys, or table columns and their exact
spellings. In Synergy, “contract” means that these surfaces are deliberately
named and versioned for exchange. It is not a Synergy-owned replacement for the
model's schema, runtime objects, or payload files.

### Native contract catalog

A pinned inventory of elements from one
[native contract](#native-contract). The catalog reference records the model's
catalog identifier, kind, revision, and content digest. Those values answer
“which exact version of the model-owned inventory are we using?” without
copying the full model schema into Synergy.

### Native contract element reference

One typed address inside a pinned native contract catalog. It combines the
catalog identity with an element kind—such as `config_path`, `artifact_key`, or
`sql_column`—and the model-owned path itself. For example, a scenario binding
may point to the `polaris_households.persons` SQL column in a particular
POLARIS catalog revision.

The structural chain is **catalog → element → binding**:

1. The catalog reference pins the version of the model-owned inventory.
2. The element reference identifies one address within that inventory.
3. A scenario or translation binding explains how that element relates to a
   shared concept.

Synergy can check that the address exists in the pinned catalog. The model team
still owns what the address means and how its runtime produces or consumes it.

### Shared core

The deliberately small set of concepts whose meaning can be shared across
tools, such as scenario revision, simulation year, population occurrence,
and artifact identity. It does not contain every attribute produced by every
model.

## Files, bundles, manifests, receipts, and provenance

### Artifact

A physical output or input, usually a file, identified by its bytes. A CSV
of households and the SQL script that created it are different artifacts.

### Artifact identity

An algorithm plus content digest that identifies exact bytes. A path or URI
can change while the artifact identity remains the same.

### Canonical representation

A newly constructed, ordered set of selected fields used to calculate a stable
digest. It is not a model record set, a database view, or a copy of the source
document with fields removed. For compatibility, some schema fields and Python
functions retain `projection` in their names, such as `projection_version` and
`canonical_realization_projection`; in the guides, “canonical representation”
is the preferred name for this hashing input.

### Evidence

A record that supports a limited factual claim. A file digest can support a
claim about exact bytes; provenance can support a claim about which run
produced them; a receipt can support a claim about one exchange. Evidence
supports a bounded claim. It does not, by itself, establish scientific
validity, mapping approval, or authority over a model-owned definition.

### Handoff

The act and boundary of passing artifacts from one workflow step or model to
another.

### Bundle

A named collection of related artifact members delivered together. A bundle
describes the members and their roles; it does not copy all rows into the
manifest.

### Manifest

A document listing a bundle or exchange and its declared metadata, members,
identities, and completeness. The payload files remain separate.

### Receipt

A per-application record of what was actually used or produced: scenario,
year, mapping description, translation implementation, artifacts, and observed
residue. It is evidence of one application, not the reusable mapping
agreement itself.

### Day-zero manifest

A discovery-only receipt for one existing payload and its producer artifact.
It records identity and context before a full field mapping exists; it is not
accepted as production provenance.

### Provenance

Evidence about where data came from and how it was produced or consumed,
including runs, artifacts, and their associations. Provenance does not by
itself define the meaning of a scenario or model field.

### Lineage

The connected history from source artifacts and runs through mappings,
transformations, and derived artifacts. Provenance records are evidence used
to reconstruct lineage.

## Mappings, implementations, and residue

### Mapping

A declared relationship between independently owned representations, such as
a renamed identifier, code conversion, derived value, or unsupported field.

### Translation contract

The formal schema name for the versioned mapping description. It records how
source exchange columns map to target columns, including explicit residue. It
is distinct from the code that performs the translation.

### Field mapping

One rule within a translation contract connecting source and target native
elements. It states the transformation mode and meaning of the rule.

### Mapping residue

An intentional case that is not a clean source-to-target field mapping—for
example, a required default, lookup table, filtered row, unsupported source
field, or context dropped from each output row. Residue is not automatically
an error; it makes accepted translation loss or extra behavior reviewable.

### Review record

A decision made by a named team and accountable role about one exact
mapping-content digest. The decision may accept, request changes, or reject.
The formal source and target roles are `source_owner` and `target_owner`; the
workflow integrator has a separate role and cannot substitute for either model
owner's acceptance.

### Residue observation

Evidence about one application of a declared residue, such as the number of
rows filtered or the lookup digest used in a particular simulation year.

### Implementation binding

A workflow-owned registration connecting a translation script or SQL artifact
to the mapping-content digest it claims to implement. Script identity and
mapping meaning remain separate.

### Encoding source

The team-maintained spreadsheet, SQL, script, or other artifact from which a
typed mapping description was transcribed. Its digest preserves attribution
and lets reviewers resolve transcription disputes against the original work.

## Ownership and authority

In this project, **ownership** means responsibility and decision authority for
meaning or behavior. It does not necessarily mean exclusive custody of a file.
Synergy can encode, validate, and document a model team's definitions, but
referencing or transcribing them does not transfer authority over meaning.

| Responsibility | Decision authority |
| --- | --- |
| Meaning of ATLAS/DEMOS or POLARIS native fields and codes | The corresponding model team |
| Meaning of shared scenario assumptions and identity concepts | The participating teams through the shared definition and its named authorities |
| Meaning of an ATLAS-to-POLARIS translation rule | The named source- and target-model meaning owners |
| PILATES orchestration, translation code, and automatic receipt emission | The PILATES workflow maintainers |
| Synergy vocabulary, schema composition, conformance rules, and generated documentation | The Synergy maintainers, within the limits of model-owner approval |
| Run and artifact evidence recorded through Consist | The producing workflow; Consist supplies the provenance mechanism |

Several roles may apply to the same artifact:

- A **meaning owner** decides what a field, code, assumption, or mapping means.
  Mapping review records represent this authority with the `source_owner` and
  `target_owner` roles.
- An **implementation owner** maintains the code that applies that meaning.
- A **producer** creates the payload and records its receipt.
- A **custodian** stores or publishes the physical files.
- A **reviewer or approver** accepts a particular mapping-content digest in a named
  role.

These roles are deliberately separate. For example, PILATES may maintain the
SQL that implements an ATLAS-to-POLARIS mapping, while ATLAS and POLARIS retain
authority over their native meanings and approve the cross-model mapping.
Synergy can reject a malformed or unapproved mapping description, but it cannot
approve that mapping on either model team's behalf.

## Digests, review states, and compatibility

### Content digest

A deterministic fingerprint calculated from content, usually with SHA-256.
The relevant schema definition specifies which content is included.

### Semantic digest

The formal term for a digest calculated from the meaning-bearing parts of a
scenario or mapping. The mapping field is `semantic_content_digest`; the guides
call it a **mapping-content digest**. Locations, review metadata, and
implementation-only evidence are excluded, so changes to them do not appear to
change the reviewed rules.

### Draft

Structurally usable for discovery and review, but not accepted by all required
meaning owners.

### Approved

Accepted by the required source- and target-model owner roles for the same
mapping-content digest. Synergy cannot supply those approvals on their behalf.

### Production-ready

Approved mapping description, conformance-checked implementation binding, and
automatically emitted receipt. “Approved” and “production-ready” are not
synonyms.

### Compatible

The model binding represents the relevant shared assumptions without a
known contradiction.

### Compatible with gaps

The model does not represent one or more shared assumptions but also does not
contradict them. The missing coverage remains visible.

### Override

An intentional native value that differs from the shared assumption. It is
documented, but it is not agreement with the shared scenario.

### Conflict

Two authoritative declarations make incompatible claims about the same
shared concept at the same revision, scope, and authority.

## Terms that are easy to confuse

| Often confused | How they differ |
| --- | --- |
| Scenario definition / trajectory / snapshot | A definition states assumptions; a trajectory organizes change across years; a snapshot is one population state in one year. |
| Schema / contract / profile | A schema defines reusable structure; a contract selects an agreement for an exchange; a profile composes definitions for one workflow boundary. |
| Native record / core population state | A native record carries model-owned attributes; core state carries only shared snapshot-scoped identity and relationships. |
| Native contract / Synergy schema | A native contract inventories a model-owned interface; the Synergy schema defines shared references and exchange structure around it. |
| Catalog / element / binding | A catalog pins an interface inventory; an element identifies one address in it; a binding connects that address to shared meaning. |
| Artifact / manifest / bundle / receipt | An artifact is physical content; a manifest describes an exchange; a bundle groups artifact roles; a receipt records one application of scenario, mapping, implementation, and artifacts. |
| Artifact digest / semantic digest | An artifact digest identifies exact bytes; the formally named semantic digest identifies normalized meaning-bearing content. |
| Translation contract / implementation binding | The translation contract is the formally named, model-owner-reviewed mapping description; the binding identifies workflow code that implements it. |
| Ownership / file custody | Ownership is authority over meaning or behavior; custody is possession or publication of the bytes. |
| Mapping residue / validation error | Residue is declared and reviewable translation behavior; an error is an undeclared or inconsistent violation. |
| Provenance / scenario definition | Provenance describes execution and artifact history; the scenario definition states shared assumptions. |
| Draft / approved / production-ready | Draft supports review; approved has required meaning-owner acceptance; production-ready additionally requires checked code and automatic receipts. |
| Compatible with gaps / conflict | A gap means unsupported but non-contradictory; a conflict is an incompatible assertion about the same shared concept. |

## Where to go next

- [Scenario definitions and trajectories](scenario-definitions-and-trajectories.md)
- [Population snapshots and artifact identity](population-snapshots-and-artifact-identity.md)
- [Mapping meaning, implementation, and lineage](../cross-model-mappings/mapping-lineage.md)
- [Workflow structures](../workflow-structures/index.md)
- [Complete generated reference](../schema/index.md)
