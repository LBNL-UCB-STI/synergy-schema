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

The main schema and tooling cover:

- the multi-year population ledger (`schema/core/population_ledger.yaml`) and
  conformance / pipeline orchestration (`synergy_schema.ledger`,
  `synergy_schema.pipeline`, `synergy_schema.conformance`);
- the Deliverable #1 static single-year cross-model schema
  ([`deliverable_1_static_schema.yaml`](src/synergy_schema/schema/deliverable_1_static_schema.yaml))
  spanning UrbanSim, DEMOS, ATLAS, POLARIS, ActivitySim, BEAM, SynthFirm, and
  OMX network skims;
- the PILATES population handoff after ATLAS; and
- cross-model mappings, translation contracts, and provenance receipts.

### Provisional and static model contracts

[`observed_examples.yaml`](src/synergy_schema/schema/observed_examples.yaml)
and [`deliverable_1_static_schema.yaml`](src/synergy_schema/schema/deliverable_1_static_schema.yaml)
hold model table descriptions and single-year handoff contracts across DEMOS,
ATLAS, POLARIS, UrbanSim, ActivitySim, BEAM, SynthFirm, and OMX network skims.

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

The command regenerates the ignored `docs/schema/` directory, including
Deliverable #1 UML and ER diagrams and the observed-example reference, and
starts a Zensical development server at <http://127.0.0.1:8000/>. To generate
the reference and verify a static site build without starting a server, run
`scripts/preview-schema-docs build`. Set `ZENSICAL_DEV_ADDR`, for example to
`127.0.0.1:8001`, when the default preview port is already in use.

Export the standalone Deliverable #1 static schema package:

```sh
uv run python scripts/export_deliverable1.py
```

Build the Python package and confirm that it includes the root schema:

```sh
uv build
unzip -l dist/synergy_schema-*.whl | rg 'synergy_schema/schema/synergy_schema.yaml'
```

## Examples

- [`examples/ledger/`](examples/ledger/) demonstrates multi-year population
  ledger runs across DEMOS, ATLAS, and POLARIS.
- [`examples/one_year_mapping_handshake/`](examples/one_year_mapping_handshake/)
  walks through a one-year cross-model mapping handshake, review tables, and
  conformance checks.
- [`examples/day_zero_exchange/`](examples/day_zero_exchange/) illustrates a
  lightweight day-zero manifest for existing file exchanges.

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
