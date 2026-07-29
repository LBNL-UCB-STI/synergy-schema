# Synergy Schema

This repository is the shared home for descriptions of the data used by
Synergy transportation models. It gives us one place to explain what each
dataset means, how different models represent it, and what PILATES expects at
the boundaries between models.

The schemas are written in [LinkML](https://linkml.io/). LinkML lets us describe
data in readable YAML and later use those descriptions to generate
documentation and validation tools.

## How the repository is organized

The schema is split into a few areas so that shared ideas do not get mixed up
with model-specific details:

- [`schema/core/`](src/synergy_schema/schema/core/) is for concepts that have
  the same meaning across multiple models.
- [`schema/models/`](src/synergy_schema/schema/models/) is for descriptions
  owned by individual modeling systems, such as ActivitySim, ATLAS, BEAM,
  POLARIS, and UrbanSim.
- [`schema/profiles/`](src/synergy_schema/schema/profiles/) describes the
  collections of data a real workflow uses. PILATES will be the first workflow
  supported here.
- [`schema/mappings/`](src/synergy_schema/schema/mappings/) explains how fields
  and concepts relate across the other areas.

In this repository, a *profile* is simply a named collection of schema pieces
used for a particular purpose. A *mapping* records a relationship such as a
renamed field, a unit conversion, or a value derived from other fields.

Keeping these areas separate means a model team can describe its own data
without having to adopt LinkML in its runtime. It also helps us avoid copying
the same definition into several places.

## Current status

The first two vertical slices define population-snapshot context and a
provider-neutral handoff bundle, then compose them into a PILATES yearly
population profile. The profile now binds its three population artifacts to
ATLAS-owned household/person input and vehicle-output record contracts. Native
code vocabularies, mappings, and broader cross-table validation remain to come.

## Getting started

The project uses [uv](https://docs.astral.sh/uv/) to manage Python and its
dependencies. From the repository root, install the development environment:

```sh
uv sync --group dev
```

Check that the LinkML schema is valid:

```sh
uv run linkml-lint src/synergy_schema/schema/synergy_schema.yaml
```

Run the tests:

```sh
uv run pytest -q
```

Build the Python package and confirm that it includes the root schema:

```sh
uv build
unzip -l dist/synergy_schema-*.whl | rg 'synergy_schema/schema/synergy_schema.yaml'
```

## See a complete synthetic handoff

The [post-ATLAS population bundle example](examples/post_atlas_population_bundle/)
walks through native ATLAS rows, their snapshot-scoped population state, and
the PILATES bundle that composes the three corresponding artifacts.

## Contributing a schema

Start by deciding who owns the definition:

1. Put a model's native fields and codes under `schema/models/`.
2. Move a concept into `schema/core/` only when it has the same agreed meaning
   across multiple models.
3. Use `schema/profiles/` to describe what PILATES or another workflow actually
   requires.
4. Use `schema/mappings/` to explain how two existing definitions relate
   instead of copying either definition.

It is fine to begin with questions or incomplete details about meaning. Mark
what is not yet known clearly so it can be reviewed with the people who own the
data.
