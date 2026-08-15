# User-Friendly Glossary Design

## Goal

Give newcomers one plain-language place to understand Synergy Schema terms and
the distinctions among concepts that currently sound similar.

## Structure

Add `docs/shared-structure/glossary.md` as a maintained guide, not generated
schema reference. Group definitions by the questions a reader is likely to
have:

- shared scenarios and changing populations;
- schemas, contracts, profiles, and native records;
- files, bundles, manifests, receipts, and provenance;
- mappings, implementation bindings, and residue;
- digests, identity, review state, and compatibility.

Each entry uses a bold term, one plain-language definition, and at most one
short clarification. A final “terms that are easy to confuse” table compares
the most important neighboring concepts.

## Navigation and links

Add **Glossary** under **Shared structure**, link it prominently from the
Overview and Schema organization pages, and add selective first-use links from
the scenario, workflow, mapping-lineage, and one-year-handshake guides. Do not
link every repeated term; excessive links would make the prose harder to read.

## Boundaries

- The glossary explains concepts; generated LinkML pages remain authoritative
  for field names, types, requiredness, and cardinality.
- Definitions preserve the distinction between shared semantics, model-native
  structures, workflow behavior, and physical artifact evidence.
- A mapping residue is described as an explicit accepted translation case,
  not automatically as an error.
- Draft, approved, and production-ready remain separate states.
- The glossary must not imply deployed POLARIS runtime integration or complete
  native-schema coverage.

## Verification

Documentation tests require the navigation entry, landing-page link, topic
groups, core term coverage, and the comparison table. The canonical static-site
build verifies navigation targets and generated-reference links.
