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

The root schema covers the current PILATES population handoff, partial
UrbanSim, ActivitySim, and POLARIS identity/join records, and mappings for the
observed PILATES population path. It also includes a staged-assembly slice for
immutable DEMOS and ATLAS contributions to one partial population snapshot.
The repository does not claim complete native-table coverage, runtime
validation, model-owner approval, or production artifact integrity.

### Provisional model contracts

[`observed_examples.yaml`](src/synergy_schema/schema/observed_examples.yaml)
separately describes provisional DEMOS, ATLAS, and POLARIS row shapes from
local examples. It is outside `synergy_schema.yaml` because those examples do
not establish a shared handoff, mapping, scenario, or trajectory.

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

Preview the generated schema documentation:

```sh
scripts/preview-schema-docs
```

The command regenerates the ignored `docs/schema/` directory, including a
separate observed-example reference, and starts a Zensical development server
at <http://127.0.0.1:8000/>. To generate the reference and verify a static
site build without starting a server, run `scripts/preview-schema-docs build`.
Set `ZENSICAL_DEV_ADDR`, for example to `127.0.0.1:8001`, when the default
preview port is already in use.

Build the Python package and confirm that it includes the root schema:

```sh
uv build
unzip -l dist/synergy_schema-*.whl | rg 'synergy_schema/schema/synergy_schema.yaml'
```

## See a complete synthetic handoff

The [post-ATLAS population bundle example](examples/post_atlas_population_bundle/)
walks through native ATLAS rows, their snapshot-scoped population state, and
the PILATES bundle that composes the three corresponding artifacts.

For a staged rather than complete handoff, see the
[core-population assembly example](examples/core_population_assembly/). It
shows separate DEMOS and ATLAS contributions, explicit column authority, and
the command that validates their shared snapshot.

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
