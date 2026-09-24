# Glossary

This glossary explains the project's recurring terms in plain language.
Where the schema uses a formal name, that name is kept here even if the guides
usually say something shorter. For exact fields, types, and required values,
the [generated schema reference](../schema/index.md) is the authority.

## Shared scenarios and changing populations

### Scenario definition

The versioned list of shared assumptions that all the participating models
are meant to follow. Its fingerprint tells one version apart from another. It
doesn't include every model-specific setting.

### Scenario binding

A statement of how one model's settings represent one shared scenario
assumption. The model might use the value directly, under another name, after
a conversion, deliberately override it, or not support it at all.

### Population trajectory

The series of yearly population snapshots for one scenario and one random
draw. It also records which years were requested, finished, or skipped on
purpose.

### Population snapshot

The population as it stands in one simulation year, for one scenario and
random draw. It describes a moment in time, not a permanent master list.

### Stochastic realization

One run of a model that makes random choices. Two runs of the same scenario
can turn out differently, so each gets its own realization ID to keep the
results apart.

### Core population state

The shared record of a household, person, vehicle, or relationship in one
snapshot. It deliberately leaves out model-specific details like demographics,
vehicle technology, and predicted behavior.

### Core population contribution

One model's piece of a shared snapshot, such as DEMOS supplying households
and people, or ATLAS supplying vehicles. It can't be changed once published.
A contribution points to its own files and mappings; it never rewrites another
model's records.

### Core population assembly

The list of contributions that make up one snapshot, each pinned by its
fingerprint. Its index tells a consumer which contribution is the authority for
each part (households, vehicles, and so on). An assembly can be partial.

### Column authority classification

A label on each model column in an assembly saying what role it plays: a
shared fact, a model-specific view, a value copied from an earlier
contribution (which must be named), or an unclassified model field. This stops
a copied column, or one that happens to share a name, from quietly becoming a
new source of truth.

## What a binding means here

A **binding** is a written-down, checkable link between something shared and
the model-specific thing that stands for it. It answers "where, and how, does
this shared idea show up in this model?" A binding doesn't copy data, require
models to produce the same output, or hand control of a model's field to
Synergy. It also doesn't prove compatibility on its own; it records enough for
the checker and the relevant owners to decide.

| Binding or relationship | Connects | Maintained by | What it establishes |
| --- | --- | --- | --- |
| Scenario binding | A shared scenario assumption to a model setting or value | The team that configures the model | How that model represents, leaves out, or overrides the assumption |
| Field mapping | A field in one model to a field in another | The teams that own each side | What one translation rule means, as reviewed |
| Schema contract reference | A file to a specific version of a schema and its top-level class | Whoever produces the file | Exactly which structure should be used to read the file |
| Implementation binding | A reviewed mapping description to SQL or code | The workflow team that runs the translation | Which code is supposed to carry out that mapping version |

So "binding" means more than "related to." It names both sides and how they
connect. A scenario binding is about shared assumptions; an implementation
binding is about code.

## Schemas, contracts, profiles, and native records

### Schema

A formal description of how data is structured: which fields are allowed,
their types, which are required, and how records relate. This repository
writes its schemas in LinkML.

### Contract

A versioned agreement used for one exchange. The word shows up in schema
class names like `PopulationTranslationContract` and
`SchemaContractReference`. Elsewhere, the guides use the more specific
"mapping description" or "schema reference." A schema can describe a broad,
reusable vocabulary; a contract picks out the part used at one handoff.

### Schema contract reference

The schema language, schema fingerprint, and top-level class used to read a
file. An optional URI and version label help people find the schema, but they
don't identify it.

### Profile

A bundle of shared and model-owned definitions put together for one workflow
or exchange. A profile picks what that workflow needs without taking ownership
of the definitions it borrows.

### Workflow profile

A profile for a specific handoff in a workflow, such as the PILATES
post-ATLAS population handoff or the proposed POLARIS translation. Having a
profile doesn't mean the workflow already enforces it at runtime.

### Interface

The parts of a model or workflow that other systems are meant to use, such
as a setting, a file key, a table column, or a file role. An interface
description points at these without trying to describe the model's full
internals.

### Native record

A row or data structure whose fields and meanings belong to the model that
produces it, such as an ATLAS household row or a POLARIS person row. Shared
definitions point at native records instead of replacing them with one
universal table.

### Native contract

A model's own list of the settings, file keys, and table columns other
workflows may refer to, with their exact spellings. "Contract" here just means
these names are deliberately published and versioned for others to use. It is
not a Synergy-owned replacement for the
model's schema, runtime objects, or files.

### Native contract catalog

A pinned version of one [native contract](#native-contract). The catalog
reference records its ID, kind, version, and fingerprint, which together
answer "exactly which version of this model's list are we using?" without
copying the model's whole schema into Synergy.

### Native contract element reference

A pointer to one item in a pinned catalog. It combines the catalog, the kind
of item (such as `config_path`, `artifact_key`, or `sql_column`), and the
item's name in the model. For example, a scenario binding might point to the
`polaris_households.persons` SQL column in a particular version of the POLARIS
catalog.

The structural chain is **catalog → element → binding**:

1. The catalog pins which version of the model's list is in use.
2. The element points to one item in that list.
3. A scenario or translation binding explains how that item relates to a
   shared concept.

Synergy can check that the item exists in the pinned catalog. The model team
still decides what it means and how their model uses it.

### Shared core

The intentionally small set of concepts that mean the same thing across
models, such as scenario version, simulation year, who is in the population,
and file identity. It doesn't include every attribute every model produces.

## Files, bundles, manifests, receipts, and provenance

### Artifact

An input or output, usually a file, identified by its exact contents. A CSV
of households and the SQL script that created it are two different
artifacts.

### Artifact identity

A hashing algorithm plus the resulting fingerprint, which together identify
a file's exact contents. The file's path or URI can change without changing
its identity.

### Canonical representation

A freshly built, consistently ordered set of selected fields, used as the
input when calculating a stable fingerprint. It isn't a set of model records,
a database view, or the source document with some fields deleted. Some schema
fields and Python functions still say `projection` (for example,
`projection_version` and `canonical_realization_projection`); the guides call
it the "canonical representation."

### Evidence

A record that backs up a specific factual claim. A file fingerprint backs up
a claim about exact contents; provenance backs up which run produced a file; a
receipt backs up what happened in one exchange. Evidence
supports a bounded claim. On its own it doesn't show that a model is scientifically sound, that
a mapping is approved, or who owns a definition.

### Handoff

The point where files pass from one model or workflow step to the next.

### Bundle

A named group of related files delivered together. A bundle lists the files
and their roles; it doesn't copy their rows into the manifest.

### Manifest

A document describing a bundle or exchange: its metadata, the files in it,
their fingerprints, and whether it's complete. The data files themselves are
kept separately.

### Receipt

A record of what was actually used or produced in one run: scenario, year,
mapping description, translation code, files, and residue observed. It's
evidence about one run, not the reusable mapping itself.

### Day-zero manifest

A first-pass receipt for one existing file and the code that produced it. It
records what the file is and where it came from before any field mapping
exists. It doesn't count as production provenance.

### Provenance

Evidence about where data came from and how it was produced or used,
including runs, files, and which runs read or wrote which files. Provenance
doesn't define what a scenario or field means.

### Lineage

The full history from source files and runs, through mappings and
transformations, to the files derived from them. Provenance records are the
evidence used to piece lineage together.

## Mappings, implementations, and residue

### Mapping

A written-down relationship between data owned by different models, such as
a renamed ID, a code conversion, a derived value, or an unsupported field.

### Translation contract

The schema's name for a versioned mapping description. It records how source
columns map to target columns, including residue. It's separate from the code
that actually does the translation.

### Field mapping

One rule in a translation contract that connects a source field to a target
field. It says what kind of transformation it is and what it means.

### Mapping residue

Anything in a translation that isn't a clean one-to-one field mapping: a
default value, a lookup table, rows that get filtered out, source fields the
target can't hold, or context that gets dropped. In plain terms, it's a
documented exception or data loss. Residue isn't automatically an error;
writing it down just makes it reviewable.

### Review record

A named team's decision, made in a named role, about one exact version of a
mapping (identified by its mapping-content digest). The decision can be
accept, request changes, or reject. The two model-side roles are
`source_owner` and `target_owner`. The workflow integrator has a separate role
and can't sign off in place of either model team.

### Residue observation

Evidence of how a piece of residue played out in one run, such as how many
rows were filtered or which lookup table was used in a given year.

### Implementation binding

A record, kept by the workflow team, linking a translation script or SQL
file to the mapping version it's supposed to implement. The script and the
mapping stay separate, so either can change without silently changing the
other.

### Encoding source

The original spreadsheet, SQL, script, or other file a team used to maintain
a mapping, before it was copied into Synergy. Its fingerprint keeps credit
with the original and lets reviewers check the Synergy version against it if
there's a question.

## Ownership and authority

In this project, **ownership** means being responsible for, and having the
final say on, what something means or how it behaves. It doesn't necessarily
mean holding the file. Synergy can write down, check, and document a model
team's definitions, but referencing or copying them
does not transfer authority over meaning.

| Responsibility | Decision authority |
| --- | --- |
| Meaning of ATLAS/DEMOS or POLARIS native fields and codes | The corresponding model team |
| Meaning of shared scenario assumptions and identity concepts | The participating teams through the shared definition and its named authorities |
| Meaning of an ATLAS-to-POLARIS translation rule | The named source- and target-model meaning owners |
| PILATES orchestration, translation code, and automatic receipt emission | The PILATES workflow maintainers |
| Synergy vocabulary, schema composition, conformance rules, and generated documentation | The Synergy maintainers, within the limits of model-owner approval |
| Run and artifact evidence recorded through Consist | The producing workflow; Consist supplies the provenance mechanism |

Several roles may apply to the same artifact:

- A **meaning owner** decides what a field, code, assumption, or mapping
  means. In mapping reviews, this is the `source_owner` or `target_owner`
  role.
- An **implementation owner** maintains the code that applies that meaning.
- A **producer** creates the file and records its receipt.
- A **custodian** stores or publishes the files.
- A **reviewer or approver** signs off on a specific version of a mapping, in
  a named role.

These roles are kept separate on purpose. For example, PILATES might maintain
the SQL for an ATLAS-to-POLARIS mapping, while ATLAS and POLARIS keep the final
say on what their own fields mean and approve the mapping between them.
Synergy can reject a malformed or unapproved mapping description, but it can't
approve a mapping on either team's behalf.

## Digests, review states, and compatibility

### Content digest

A fingerprint calculated from some content, usually with SHA-256. The same
content always gives the same fingerprint. The schema says which content is
included.

### Semantic digest

A fingerprint of just the parts of a scenario or mapping that affect its
meaning. The mapping field is called `semantic_content_digest`; the guides call
it the **mapping-content digest**. File locations, review details, and
implementation evidence are left out, so changing them doesn't look like a
change to the reviewed rules.

### Draft

Complete enough to explore and review, but not yet accepted by every team
whose sign-off is required.

### Approved

Accepted by both the source and target model teams, for the same version of
the mapping. Synergy can't approve on their behalf.

### Production-ready

An approved mapping, plus code that passes the checks, plus receipts that
are produced automatically. "Approved" and "production-ready" are not the same
thing.

### Compatible

The model represents the relevant shared assumptions, with no known
contradictions.

### Compatible with gaps

The model doesn't support one or more shared assumptions, but doesn't
contradict them either. The gap stays visible.

### Override

A model setting that deliberately differs from the shared assumption. It's
documented, but it isn't agreement with the shared scenario.

### Conflict

Two authoritative records disagree about the same shared fact, for the same
version, scope, and authority.

## Terms that are easy to confuse

| Often confused | How they differ |
| --- | --- |
| Scenario definition / trajectory / snapshot | A definition lists the assumptions; a trajectory tracks the population across years; a snapshot is the population in one year. |
| Schema / contract / profile | A schema defines reusable structure; a contract is the agreement used for one exchange; a profile bundles definitions for one handoff. |
| Native record / core population state | A native record holds a model's own attributes; core state holds only the shared IDs and relationships for one snapshot. |
| Native contract / Synergy schema | A native contract lists what a model exposes; the Synergy schema defines the shared structure around it. |
| Catalog / element / binding | A catalog pins a version of that list; an element points to one item in it; a binding connects that item to a shared idea. |
| Artifact / manifest / bundle / receipt | An artifact is a file; a manifest describes an exchange; a bundle groups files by role; a receipt records what was used in one run. |
| Artifact digest / semantic digest | An artifact digest fingerprints a file's exact contents; a semantic digest fingerprints only the parts that affect meaning. |
| Translation contract / implementation binding | The translation contract is the mapping the model teams review; the implementation binding names the code that carries it out. |
| Ownership / file custody | Ownership is the final say on meaning or behavior; custody is holding or publishing the file. |
| Mapping residue / validation error | Residue is translation behavior that's been written down for review; an error is something undeclared or inconsistent. |
| Provenance / scenario definition | Provenance is the history of runs and files; the scenario definition lists the shared assumptions. |
| Draft / approved / production-ready | Draft is ready for review; approved has sign-off from the required teams; production-ready also needs checked code and automatic receipts. |
| Compatible with gaps / conflict | A gap means unsupported but not contradicted; a conflict means two records disagree about the same shared fact. |

## Where to go next

- [Scenario definitions and trajectories](scenario-definitions-and-trajectories.md)
- [Population snapshots and artifact identity](population-snapshots-and-artifact-identity.md)
- [Mapping meaning, implementation, and lineage](../cross-model-mappings/mapping-lineage.md)
- [Workflow structures](../workflow-structures/index.md)
- [Complete generated reference](../schema/index.md)
