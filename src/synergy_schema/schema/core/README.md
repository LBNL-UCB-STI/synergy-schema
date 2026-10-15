# Core Population Ledger & Shared Concepts

This directory holds shared concepts with agreed meaning across models, centered on the **Population Ledger**.

The ledger is a versioned record of one population as several models edit it in turn, modeled on git:

| Git | Population Ledger |
|---|---|
| Commit | `PopulationSnapshot`: one model step, its parent snapshot(s), and the full core state afterward |
| Tree | `CoreState`: a map from each core facet to a `FacetContentDigest`, identified by a `StateDigest` |
| Tag | `PopulationCheckpoint`: the snapshot that counts as a given year's population |
| Branch | `PopulationLedger`: one scenario and one stochastic realization |

## Modules

The core schema is structured into the following modules:

1. **`core_tables.yaml`**: The four foundational key-only core table classes (`CoreHousehold`, `CorePerson`, `CoreHouseholdMembership`, `CoreVehicle`), the `CoreFacet` enum, and the content digest types (`FacetContentDigest`, `StateDigest`).
2. **`facet_mappings.yaml`**: `ModelView`, `CoreFacetMapping`, `CoreFieldFromView`, `CoreFacetMappingCatalog`, and `FacetDerivation`. Mappings specify how Synergy derives core facets from model output views and prepares model input views from core state.
3. **`population_ledger.yaml`**: The aggregate ledger structure containing `PopulationLedger`, `PopulationSnapshot`, `PopulationCheckpoint`, `ModelStep`, `CoreState`, and `CoreFacetEntry`.
4. **`handoff_bundle.yaml`**: File-byte artifact and execution references (`PhysicalArtifactReference`, `ProducingRunReference`).
5. **`native_contract.yaml`**: Native model schema contracts and column specifications.
6. **`scenario_definition.yaml`**: Cross-model scenario definitions and experiment configuration references.

## Key Principles

- **Models read and write views, not core tables.** A `ModelView` is a model-owned artifact, such as the ATLAS household input or the DEMOS persons output. Synergy derives each core facet from output views through a mapping.
- **State and derivation are separate.** A `CoreFacetEntry` is a tree entry: `facet`, `digest`, and an optional `stored_object`. How content was produced lives on `step.derivations`, recording the step's write set.
- **Mappings are fixed system knowledge.** Stored in a `CoreFacetMappingCatalog` and cited by ID. A mapping specifies which kinds of output view a facet is derived from, binds view columns to core fields, and can pin a reviewed `PopulationTranslationContract`.

## Content Identity and Hashing

- `ImmutableArtifactIdentity`: File byte identity (SHA-256). Answers: *is this the exact file?*
- `FacetContentDigest`: Normalized rows of a core table under `facet_digest_form` (`core_facet_table/v1`). Answers: *is this the same population fact?*
- `StateDigest`: Merkle tree hash over a state's sorted `(facet, facet_content_digest)` pairs under `state_digest_form` (`core_state/v1`). No files are read to compute it.

## Validation

1. **LinkML Shape Validation**: Enforces structure, required fields, closed facet vocabulary, and regex digest patterns via `JsonschemaValidationPlugin(closed=True)`.
2. **Ledger Conformance Plugin**: `synergy_schema.conformance.ledger.LedgerConformancePlugin` validates cross-snapshot DAG integrity, parent state merges, write sets, mapping catalogs, and checkpoint constraints. CLI command: `check-ledger`.
3. **Data & Consist Checks**: Verification of table content digests and Consist run receipts.
