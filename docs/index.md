# Synergy Schema

Transportation modeling studies often combine several tools maintained by
different teams. Those tools may be intended to use the same scenario and the
same evolving population, even though they organize their inputs, settings,
and outputs differently. Synergy provides a clear, checkable description of
what is shared and how files move between those tools.

## Why this project exists

The immediate use case is coordination between the PILATES modeling pipeline
and POLARIS. Both may run a common multi-year scenario, but they do not need to
store every household, person, vehicle, or policy setting in the same way. They
may also legitimately produce different model-specific results.

Passing CSV or Parquet files is still part of the exchange, but the files alone
do not answer questions such as:

- Which exact scenario assumptions does this file represent?
- Was this year intentionally skipped, or is an output missing?
- Is this population connected to the preceding modeled year?
- Which version of the ATLAS-to-POLARIS mapping was used?
- Which translation script produced these rows?
- Did both model teams review the same field rules, defaults, and known losses?

Synergy records those answers beside the existing payload files so they remain
available to people and automated checks later.

## What Synergy adds

The project defines a small shared layer for the facts that must have one
coherent meaning across participating workflows: scenario identity, simulation
year, population snapshot, stable entity references, declared relationships,
and exact file identity.

It also provides documents for:

- connecting shared scenario assumptions to each model's native settings;
- describing how source fields become target fields;
- recording defaults, unsupported fields, filtered rows, and other known
  translation losses;
- grouping related files and recording which run produced them; and
- checking that scenario, year, mapping, implementation, and file identities
  agree across a handoff.

LinkML is the language used to maintain these definitions and generate the
reference documentation. PILATES, POLARIS, ATLAS, and other participating tools
do not need to use LinkML in their runtime systems.

## What it does not replace

The participating tools keep their own schemas, terminology, and runtime
systems. Synergy does not create one universal population table, take ownership
of model-defined columns, or require tool-specific predictions to agree. It
only treats a difference as a conflict when two authoritative records make
incompatible claims about something they explicitly agreed to share.

The current POLARIS material describes a proposed and tested exchange boundary,
not a completed POLARIS runtime integration. The documentation labels current,
proposed, and out-of-scope behavior where that distinction matters.

## What is in these docs

| Documentation area | What you will find |
| --- | --- |
| [Proof of concept](proof-of-concept/index.md) | A small population followed through three modeled years, plus examples of errors the checker catches. |
| [Bring an existing mapping](bring-an-existing-mapping/index.md) | A low-risk path for turning an existing spreadsheet, SQL script, or column mapping into a reviewed and checkable handoff. |
| [Shared structure](shared-structure/index.md) | The common scenario, population, relationship, file, and handoff concepts, including readable UML diagrams. |
| [Workflow structures](workflow-structures/index.md) | The additional records used specifically at the PILATES and proposed POLARIS boundaries. |
| [Cross-model mappings](cross-model-mappings/index.md) | How identities, fields, assumptions, and known translation losses connect across independently owned models. |
| [Design rationale](design-rationale/index.md) | Why the project uses separate shared and model-owned structures, and when flat files may already be enough. |
| [Glossary](shared-structure/glossary.md) | Plain-language definitions of recurring terms and distinctions. |
| [Generated schema reference](schema/index.md) | The complete field-level reference generated from the LinkML source. |

## Where to start

If your team already has an ATLAS, DEMOS, or POLARIS mapping, start with
[Bring an existing mapping](bring-an-existing-mapping/index.md). It preserves
the existing files and begins from the team's current spreadsheet, SQL, or
script.

If you want to evaluate the approach first, inspect the
[three-year proof](proof-of-concept/index.md) and the accompanying
[checker examples](proof-of-concept/check-the-showcase.md). They show both the
data being described and the cross-file mistakes that become detectable.

For implementation details, use the [core UML
page](schema/core-schema-uml.md), then open the
[generated schema reference](schema/index.md) for exact fields and validation
rules.
