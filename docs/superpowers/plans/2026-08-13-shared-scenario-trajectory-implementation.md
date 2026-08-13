# Shared Scenario Trajectory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to execute this plan task-by-task. Every behavior change follows superpowers:test-driven-development, and completion claims follow superpowers:verification-before-completion.

**Goal:** Turn the approved shared-scenario design into typed LinkML contracts, reusable conformance and mapping-review tools, synthetic one-year and three-year examples, and a newcomer-oriented documentation site without changing PILATES, POLARIS, or Consist runtimes.

**Architecture:** Provider-neutral scenario, native-contract, trajectory, and population-state semantics remain under `schema/core`; mapping-release semantics remain under `schema/mappings`; PILATES/Consist and POLARIS exchange compositions remain separate workflow profiles. A small standard-library-first `synergy_schema.conformance` package performs deterministic cross-document checks that LinkML cannot express. Example directories contain explicit `showcase.yaml` manifests so `check-all` discovers inputs without filename guessing, while mapping releases use one fixed `contract/` versus `implementation/` topology. Maintained guides explain intent and workflow boundaries; ignored generated schema pages remain reference detail.

**Tech Stack:** LinkML YAML, Python 3.10+, `linkml-runtime`, PyYAML already available through the existing runtime dependency, `argparse`, `hashlib`, `csv`, `pytest`, Zensical, and Mermaid.

## Global Constraints

- Do not modify `/Users/zaneedell/git/PILATES`, any POLARIS checkout, or the vendored Consist release under `src/synergy_schema/schema/vendor/consist-provenance/0.1.0/`.
- Preserve native model ownership. Never introduce a universal household, person, vehicle, or scenario-output table.
- Keep semantic mapping contracts separate from workflow-owned implementation bindings and byte-level artifacts.
- All checked-in examples are synthetic and must remain `draft`; never fabricate ATLAS/DEMOS or POLARIS owner approval.
- A manual day-zero manifest is discovery evidence only and must fail production acceptance.
- Use exact, stable diagnostic identifiers and deterministic output ordering.
- Do not touch or stage the pre-existing untracked July 31 documentation plan/spec files.
- Commit each task independently after its focused tests pass.

---

## Task 1: Add provider-neutral native-contract and scenario vocabulary

**Files:**

- Create: `src/synergy_schema/schema/core/native_contract.yaml`
- Create: `src/synergy_schema/schema/core/scenario_definition.yaml`
- Modify: `src/synergy_schema/schema/core/population_snapshot.yaml`
- Modify: `src/synergy_schema/schema/synergy_schema.yaml`
- Modify: `examples/post_atlas_population_bundle/population_snapshot_bundle.yaml`
- Modify: `tests/test_schema.py`
- Create: `tests/test_scenario_schema.py`

**Step 1: Write failing schema tests**

Add tests asserting that the root exposes:

- `NativeContractCatalogReference`, `NativeContractElementReference`, and `NativeContractElementKind` with `config_path`, `artifact_key`, and `sql_column`;
- `ScenarioDefinition`, `ScenarioDefinitionReference`, `ScenarioAssumption`, `ScenarioAssumptionBinding`, and `ModelScenarioBinding`;
- scalar value types `integer`, `number`, `boolean`, `string`, `code`, and `reference`;
- binding modes `direct`, `alias`, `transformed`, `override`, and `unsupported`;
- compatibility states `compatible`, `compatible_with_gaps`, `incompatible`, and `pending_review`;
- an inlined required `ScenarioDefinitionReference` on `PopulationSnapshot`.

Add positive fixture validation for an inlined scenario reference and negative validation for the former bare string.

Run:

```sh
.venv/bin/python -m pytest -q tests/test_schema.py tests/test_scenario_schema.py
```

Expected: FAIL because the new classes and typed snapshot reference do not exist.

**Step 2: Implement the minimal LinkML contracts**

Reuse `DigestAlgorithm` from `core/handoff_bundle.yaml`. Define immutable catalog identity by catalog ID, kind, revision, digest algorithm, and content digest. Define element references as an inlined catalog reference plus element kind/path.

Define scenario references by scenario ID, revision, and content digest. Define scenario assumptions with stable key, scalar string value, declared type, optional unit, and authority. Define scenario definitions with region, inclusive horizon, optional parent reference, and one-or-more assumptions. Define assumption bindings and model bindings with the conditional requirements documented in annotations for the conformance layer.

Migrate `PopulationSnapshot.scenario_definition_ref` to the inlined reference object and update the existing synthetic bundle.

**Step 3: Run focused verification**

```sh
.venv/bin/python -m pytest -q tests/test_schema.py tests/test_scenario_schema.py
UV_CACHE_DIR=/tmp/synergy-schema-uv-cache uv run linkml-lint src/synergy_schema/schema/synergy_schema.yaml
git diff --check
```

Expected: PASS.

**Step 4: Commit**

```sh
git add src/synergy_schema/schema/core/native_contract.yaml src/synergy_schema/schema/core/scenario_definition.yaml src/synergy_schema/schema/core/population_snapshot.yaml src/synergy_schema/schema/synergy_schema.yaml examples/post_atlas_population_bundle/population_snapshot_bundle.yaml tests/test_schema.py tests/test_scenario_schema.py
git commit -m "feat: define shared scenario contracts"
```

---

## Task 2: Add the semantic mapping-release contracts

**Files:**

- Create: `src/synergy_schema/schema/mappings/population_translation.yaml`
- Modify: `src/synergy_schema/schema/synergy_schema.yaml`
- Create: `tests/test_population_translation_schema.py`

**Step 1: Write failing shape and ownership tests**

Assert that the root exposes:

- `PopulationTranslationContract` and `PopulationTranslationContractReference`;
- `PopulationFieldMapping` with catalog-resolved source/target elements, controlled transformation mode, rule, and evidence;
- `MappingResidueRecord` and `MappingResidueObservation` with the six designed residue kinds;
- `MappingGovernance` and `MappingReviewRecord` with draft/approved/superseded/deprecated lifecycle and source-owner/target-owner/workflow-integrator roles;
- `TranslationImplementationBinding` and its reference with declared/conformance-checked/retired status.

Verify structurally that `encoding_source: PhysicalArtifactReference` is required, supporting sources are optional, the semantic contract does not embed implementation bindings, and implementation bindings identify the semantic digest they implement.

Run:

```sh
.venv/bin/python -m pytest -q tests/test_population_translation_schema.py
```

Expected: FAIL because the mapping-release vocabulary does not exist.

**Step 2: Implement the mapping contracts**

Keep `mappings/population_identity.yaml` unchanged and import it from the sibling translation module. Encode the primary-disposition rule and dual-owner approval rule as explicit annotations for later conformance checks. Make `encoding_source` the required provenance root, while excluding it, governance, and implementation details from the documented semantic digest projection.

**Step 3: Run focused verification**

```sh
.venv/bin/python -m pytest -q tests/test_population_translation_schema.py tests/test_population_projections.py
UV_CACHE_DIR=/tmp/synergy-schema-uv-cache uv run linkml-lint src/synergy_schema/schema/synergy_schema.yaml
git diff --check
```

Expected: PASS.

**Step 4: Commit**

```sh
git add src/synergy_schema/schema/mappings/population_translation.yaml src/synergy_schema/schema/synergy_schema.yaml tests/test_population_translation_schema.py
git commit -m "feat: define population translation releases"
```

---

## Task 3: Add trajectories and evolving population relationships

**Files:**

- Create: `src/synergy_schema/schema/core/population_trajectory.yaml`
- Modify: `src/synergy_schema/schema/core/population_snapshot.yaml`
- Modify: `src/synergy_schema/schema/synergy_schema.yaml`
- Modify: `examples/post_atlas_population_bundle/core_population_states.yaml`
- Create: `tests/test_population_trajectory_schema.py`
- Modify: `tests/test_schema.py`

**Step 1: Write failing trajectory/state tests**

Test `PopulationTrajectory` for a stable ID, one scenario reference, one realization, ordered inlined snapshots, requested years, skipped-year records, and completeness. Test `HouseholdState.predecessor_state_refs`, `VehicleState`, and `HouseholdVehicleAssignment` with relationship kinds ownership/leasing/availability/assignment/unresolved. Assert core classes contain only identity, snapshot scope, and relationship fields—not native demographics or vehicle technology.

Run:

```sh
.venv/bin/python -m pytest -q tests/test_population_trajectory_schema.py tests/test_schema.py
```

Expected: FAIL.

**Step 2: Implement provider-neutral trajectory vocabulary**

Add the trajectory module without Consist or PILATES imports. Keep successful years derivable from snapshot years; represent skipped years as typed records with a year and reason. Extend the existing core state fixture minimally for predecessor and vehicle-assignment shape validation.

**Step 3: Run focused verification**

```sh
.venv/bin/python -m pytest -q tests/test_population_trajectory_schema.py tests/test_schema.py
UV_CACHE_DIR=/tmp/synergy-schema-uv-cache uv run linkml-lint src/synergy_schema/schema/synergy_schema.yaml
git diff --check
```

Expected: PASS.

**Step 4: Commit**

```sh
git add src/synergy_schema/schema/core/population_trajectory.yaml src/synergy_schema/schema/core/population_snapshot.yaml src/synergy_schema/schema/synergy_schema.yaml examples/post_atlas_population_bundle/core_population_states.yaml tests/test_population_trajectory_schema.py tests/test_schema.py
git commit -m "feat: model evolving population trajectories"
```

---

## Task 4: Compose PILATES and POLARIS workflow profiles

**Files:**

- Modify: `src/synergy_schema/schema/profiles/pilates_population.yaml`
- Create: `src/synergy_schema/schema/profiles/polaris_population_translation.yaml`
- Modify: `src/synergy_schema/schema/synergy_schema.yaml`
- Create: `tests/test_workflow_profiles.py`

**Step 1: Write failing profile-boundary tests**

Assert that the PILATES profile exposes:

- `DayZeroExchangeManifest` with payload and producer artifact references, native scenario namespace/label, year, and an invariant discovery-only mode;
- `PilatesScheduleEvidence` and one status for every requested handoff year;
- `PilatesConsistTrajectoryEvidence` reusing vendored `ConsistRunReference` and adding adapter-copied child year/iteration evidence;
- `PopulationTrajectoryBundle` composing the core trajectory with successful yearly `PopulationSnapshotBundle` manifests.

Assert that the separate POLARIS profile exposes `PolarisPopulationTranslationBundle`, five per-year roles (`households`, `persons`, `vehicles`, `vehicle_class`, `vehicle_type`), mapping and implementation references, residue observations, receipt mode, requested/successful/skipped years, and completeness. Assert `models/polaris/polaris_population.yaml` remains partial native projections and the vendored Consist checksums remain unchanged.

Assert that `PopulationTrajectoryBundle` declares a deterministic immutable manifest-content digest, calculated from its canonical content projection excluding the digest field itself, and that `PopulationTrajectoryBundleReference` carries both the stable bundle ID and this digest. The POLARIS bundle must use that typed reference rather than a bare ID.

Run:

```sh
.venv/bin/python -m pytest -q tests/test_workflow_profiles.py tests/test_schema.py
```

Expected: FAIL.

**Step 2: Implement the profiles**

Keep `PopulationSnapshotBundle` as the per-year PILATES unit. Add operational scheduling and Consist evidence only to the PILATES profile. Put derived POLARIS exchange packaging in the new profile and import—but do not redefine—the partial native POLARIS records.

**Step 3: Run focused verification**

```sh
.venv/bin/python -m pytest -q tests/test_workflow_profiles.py tests/test_schema.py
UV_CACHE_DIR=/tmp/synergy-schema-uv-cache uv run linkml-lint src/synergy_schema/schema/synergy_schema.yaml
git diff --check
```

Expected: PASS, including the existing vendored checksum test.

**Step 4: Commit**

```sh
git add src/synergy_schema/schema/profiles/pilates_population.yaml src/synergy_schema/schema/profiles/polaris_population_translation.yaml src/synergy_schema/schema/synergy_schema.yaml tests/test_workflow_profiles.py
git commit -m "feat: compose trajectory exchange profiles"
```

---

## Task 5: Add pinned native-contract catalogs and deterministic refresh tooling

**Files:**

- Create: `src/synergy_schema/native_catalog.py`
- Create: `scripts/refresh-native-contract-catalog`
- Create: `catalogs/pilates/<pinned-revision>/catalog.yaml`
- Create: `catalogs/pilates/<pinned-revision>/source.json`
- Create: `catalogs/polaris/<pinned-revision>/catalog.yaml`
- Create: `catalogs/polaris/<pinned-revision>/source.json`
- Create: `tests/test_native_catalog.py`

**Step 1: Write failing catalog-format and offline-validation tests**

Specify one deterministic catalog document format containing catalog identity, kind, upstream source/revision, declared elements, and canonical content digest. Test loading and resolving `config_path`, `artifact_key`, and `sql_column` references without importing either upstream runtime. Test recomputed committed-catalog digests and reject duplicate or mismatched elements.

Run:

```sh
.venv/bin/python -m pytest -q tests/test_native_catalog.py
```

Expected: FAIL because no catalog library or committed catalog exists.

**Step 2: Implement the explicit local refresh path**

`scripts/refresh-native-contract-catalog --kind pilates --checkout CHECKOUT --out OUT` extracts Pydantic configuration paths and statically declared `artifact_keys.py` constant values from a named local PILATES checkout. It never downloads dependencies or imports PILATES. The POLARIS mode inventories explicit SQL columns and translation-package artifact identity from an explicitly supplied local source directory. Both modes sort output and record the upstream Git revision when available.

**Step 3: Commit pinned inventories**

Generate the initial PILATES inventory from `/Users/zaneedell/git/PILATES` and the structurally faithful synthetic POLARIS SQL inventory from the reviewed translation SQL available in that checkout. Record exactly which source paths and revision were used; do not imply a POLARIS runtime schema or team approval.

The test suite validates only the committed catalogs and therefore remains offline and checkout-independent. A separate refresh test uses a temporary miniature checkout, not the real external path.

**Step 4: Run focused verification and commit**

```sh
.venv/bin/python -m pytest -q tests/test_native_catalog.py
git diff --check
git add src/synergy_schema/native_catalog.py scripts/refresh-native-contract-catalog catalogs tests/test_native_catalog.py
git commit -m "feat: pin native contract catalogs"
```

---

## Task 6: Build the conformance CLI foundation and scenario checks

**Files:**

- Create: `src/synergy_schema/conformance/__init__.py`
- Create: `src/synergy_schema/conformance/__main__.py`
- Create: `src/synergy_schema/conformance/diagnostics.py`
- Create: `src/synergy_schema/conformance/documents.py`
- Create: `src/synergy_schema/conformance/scenario.py`
- Create: `src/synergy_schema/conformance/cli.py`
- Create: `tests/test_conformance_cli.py`
- Create: `tests/test_scenario_conformance.py`

**Step 1: Write failing CLI/result tests**

Specify immutable `Diagnostic(code, message, severity)`, `CheckResult`, and `InputError`. Test deterministic diagnostic ordering and exit codes: 0 for warnings/success, 1 for conformance errors, 2 for bad invocation/malformed YAML/root type, and 130 for `KeyboardInterrupt`. Test `python -m synergy_schema.conformance --help` and a parser containing every designed subcommand, even when later handlers initially report a clear not-yet-wired input error in this task.

Run:

```sh
.venv/bin/python -m pytest -q tests/test_conformance_cli.py
```

Expected: FAIL because the package does not exist.

**Step 2: Implement deterministic document and CLI primitives**

Use stdlib plus existing PyYAML. Expose `main(argv: Sequence[str] | None = None) -> int`. Keep ordinary results on stdout only for render/diff/create commands; diagnostics go to stderr. Do not import dev-only `linkml.validator`.

**Step 3: Write failing scenario conformance tests**

Test:

- the published canonical scenario projection excludes digest, display text, and workflow bindings;
- deterministic JSON and SHA-256;
- typed scalar normalization, including only explicit boolean spellings;
- direct/alias equality, required transformed descriptions, required override rationale, unsupported value absence, and compatibility status rules;
- catalog element resolution;
- ordered/unique trajectory years, consistent definition/realization, valid parents, and completeness sets;
- stable diagnostics including `SCENARIO_DIGEST_MISMATCH`, `SCENARIO_BINDING_CONFLICT`, `NATIVE_ELEMENT_UNRESOLVED`, and `TRAJECTORY_COMPLETENESS_MISMATCH`.

Run:

```sh
.venv/bin/python -m pytest -q tests/test_scenario_conformance.py
```

Expected: FAIL.

**Step 4: Implement and wire `check-scenario`**

Use explicit `--schema`, `--definition`, `--bindings`, and `--trajectory` paths. Accept `compatible_with_gaps` as a successful warning-bearing state. Reject `incompatible` and `pending_review` for completed checks.

**Step 5: Run focused verification and commit**

```sh
.venv/bin/python -m pytest -q tests/test_conformance_cli.py tests/test_scenario_conformance.py
git diff --check
git add src/synergy_schema/conformance tests/test_conformance_cli.py tests/test_scenario_conformance.py
git commit -m "feat: check shared scenario conformance"
```

---

## Task 7: Add mapping-release validation and semantic digests

**Files:**

- Create: `src/synergy_schema/conformance/mappings.py`
- Modify: `src/synergy_schema/conformance/cli.py`
- Create: `tests/test_mapping_conformance.py`

**Canonical release layout:**

```text
RELEASE_DIR/
  contract/population-translation-contract.yaml
  implementation/*.yaml
  ownership.yaml
```

`check-mappings --mappings RELEASE_DIR` and all review tools load this topology through one `load_mapping_release()` function in `documents.py`.

**Step 1: Write failing semantic-digest and coverage tests**

Test a single deterministic semantic projection covering catalog references, field mappings, and residue declarations while excluding encoding/supporting sources, implementation bindings, governance lifecycle, and reviews. Test catalog resolution, exactly one primary disposition for each source/required target column, supplementary residues, residue references, and declared semantic digest equality.

Test dual-owner approval: current-digest source and target owner accepts are required for `approved`; Synergy/workflow review cannot substitute. `MAPPING_NOT_APPROVED` is a warning normally and an error under `--require-approved-mapping`. Test implementation binding registration and status separately from semantic approval.

Test receipt eligibility independently from strict production mode: `superseded` and `deprecated` releases can interpret historical receipts but cannot authorize any newly declared translation receipt, even in discovery mode. Emit stable `MAPPING_NOT_RECEIPT_ELIGIBLE` errors.

Run:

```sh
.venv/bin/python -m pytest -q tests/test_mapping_conformance.py
```

Expected: FAIL.

**Step 2: Implement and wire `check-mappings`**

Resolve schema paths with `SchemaView` and catalog paths from committed catalog documents. Keep stable errors including `MAPPING_DIGEST_MISMATCH`, `MAPPING_COVERAGE_MISSING`, `MAPPING_FALSE_APPROVAL`, `MAPPING_IMPLEMENTATION_UNREGISTERED`, and `MAPPING_IMPLEMENTATION_NOT_CHECKED`.

**Step 3: Run focused verification and commit**

```sh
.venv/bin/python -m pytest -q tests/test_mapping_conformance.py tests/test_conformance_cli.py
git diff --check
git add src/synergy_schema/conformance/mappings.py src/synergy_schema/conformance/documents.py src/synergy_schema/conformance/cli.py tests/test_mapping_conformance.py tests/test_conformance_cli.py
git commit -m "feat: validate mapping releases"
```

---

## Task 8: Add bundle validation and `check-all`

**Files:**

- Create: `src/synergy_schema/conformance/bundles.py`
- Modify: `src/synergy_schema/conformance/cli.py`
- Modify: `src/synergy_schema/conformance/documents.py`
- Create: `tests/test_bundle_conformance.py`
- Modify: `tests/test_conformance_cli.py`

**Canonical showcase layout:**

Every directory accepted by `check-all --dir EXAMPLE_DIR` contains `showcase.yaml` with relative paths to one scenario definition, model bindings, one core trajectory, one PILATES trajectory bundle, one POLARIS translation bundle, one mapping-release directory, and any catalog documents. Broken fixture directories use their own manifest and may reference unchanged files in the valid synthetic directory explicitly.

**Step 1: Write failing bundle tests**

Generalize the existing one-year role and Consist checks into reusable validators. Test:

- exactly one required source role/root per successful year;
- member artifact versus Consist artifact/association digest identity;
- schedule status agreement with requested/successful/skipped years;
- scenario-header/child direct parentage when supplied, and required parentage for the showcase;
- copied child year/iteration against the snapshot;
- five POLARIS roles for every successful year;
- source trajectory bundle ID and canonical manifest-content digest through `PopulationTrajectoryBundleReference`, scenario, realization, mapping semantic digest, registered implementation digest, and residue observation references;
- production rejection unless the mapping is approved, implementation is conformance checked, and receipt mode is `automatic_adapter`.
- rejection of every new receipt using a `superseded` or `deprecated` mapping release, regardless of production mode.

Use stable diagnostics including `BUNDLE_ROLE_CARDINALITY`, `ARTIFACT_IDENTITY_MISMATCH`, `SCHEDULE_EVIDENCE_MISMATCH`, `CONSIST_PARENT_MISMATCH`, `POLARIS_YEAR_ROLE_MISSING`, and `PRODUCTION_RECEIPT_REQUIRED`.

Run:

```sh
.venv/bin/python -m pytest -q tests/test_bundle_conformance.py
```

Expected: FAIL.

**Step 2: Implement granular bundle commands**

Wire `check-population-bundle --schema --bundle` and `check-polaris-bundle --schema --bundle [--production]`. The `--schema` option confirms the expected profile roots exist; the cross-document checks remain pure dictionary logic.

**Step 3: Implement manifest-driven `check-all`**

Load `showcase.yaml`, call the granular validators, aggregate each diagnostic exactly once, and apply `--production` and `--require-approved-mapping` consistently. Do not duplicate invariant logic in the orchestrator.

**Step 4: Run focused verification and commit**

```sh
.venv/bin/python -m pytest -q tests/test_bundle_conformance.py tests/test_conformance_cli.py
git diff --check
git add src/synergy_schema/conformance/bundles.py src/synergy_schema/conformance/cli.py src/synergy_schema/conformance/documents.py tests/test_bundle_conformance.py tests/test_conformance_cli.py
git commit -m "feat: validate trajectory exchange bundles"
```

---

## Task 9: Add day-zero and mapping-review tools

**Files:**

- Create: `src/synergy_schema/conformance/review.py`
- Create: `src/synergy_schema/conformance/day_zero.py`
- Modify: `src/synergy_schema/conformance/cli.py`
- Create: `tests/test_day_zero_manifest.py`
- Create: `tests/test_mapping_review.py`

**Step 1: Write failing day-zero tests**

Define the exact interface:

```text
create-day-zero-manifest \
  --artifact ARTIFACT \
  --producer-artifact PRODUCER \
  --native-scenario-namespace NAMESPACE \
  --native-scenario LABEL \
  --year YEAR \
  --out MANIFEST
```

Test that only the two explicitly supplied byte streams are SHA-256 hashed, locators remain evidence, output is deterministic YAML, and mode is always `manual_discovery`. Test missing/unreadable files as exit 2 and production rejection of the emitted manifest.

**Step 2: Implement the day-zero helper**

Do not inspect CSV/Parquet contents or walk adjacent directories.

**Step 3: Write failing renderer/diff/import tests**

`render-mapping --release RELEASE_DIR --out-dir REVIEW_DIR` must generate:

- `contract-at-a-glance.md` with team attribution, encoding-source lineage, current review state/stamps, semantic and implementation identities, coverage totals, and residue totals;
- `field-mappings.csv`, `residues.csv`, and `reviews.csv` with stable column order and row sorting.

`diff-mappings --old OLD_RELEASE --new NEW_RELEASE --format text|markdown|json` must classify semantic, encoding-source, implementation-only, and governance-only changes; a non-empty diff exits 0.

`import-mapping --review-dir REVIEW_DIR --out-release RELEASE_DIR` consumes only the normalized CSV review package, never Markdown, and must round-trip the canonical semantic projection/digest. Require an existing `release-metadata.yaml` emitted by the renderer to carry non-tabular contract/catalog/source metadata.

Run:

```sh
.venv/bin/python -m pytest -q tests/test_mapping_review.py tests/test_day_zero_manifest.py
```

Expected: FAIL.

**Step 4: Implement the tools and wire the CLI**

Keep human-facing YAML as the machine record and CSV/Markdown as the model-team review surface. Ensure the importer preserves the semantic digest but creates no approval decisions on its own.

**Step 5: Run focused verification and commit**

```sh
.venv/bin/python -m pytest -q tests/test_day_zero_manifest.py tests/test_mapping_review.py tests/test_conformance_cli.py
git diff --check
git add src/synergy_schema/conformance/day_zero.py src/synergy_schema/conformance/review.py src/synergy_schema/conformance/cli.py tests/test_day_zero_manifest.py tests/test_mapping_review.py
git commit -m "feat: add mapping adoption tools"
```

---

## Task 10: Add the day-zero discovery fixture

**Files:**

- Create: `examples/day_zero_exchange/payload.csv`
- Create: `examples/day_zero_exchange/producer.sql`
- Create: `examples/day_zero_exchange/day-zero-manifest.yaml`
- Create: `examples/day_zero_exchange/README.md`
- Create: `tests/test_adoption_examples.py`

**Step 1: Write the failing checked-in receipt test**

Test that the committed manifest exactly matches recomputed payload and producer digests, records scenario namespace/label and year, remains `manual_discovery`, and is rejected for production use. The payload format and contents remain untouched.

Run:

```sh
.venv/bin/python -m pytest -q tests/test_adoption_examples.py -k day_zero
```

Expected: FAIL.

**Step 2: Generate the synthetic receipt through the public command**

Create small, clearly synthetic payload and SQL files, then invoke `create-day-zero-manifest`. The README must state that a hand-maintained receipt is a throwaway discovery instrument and automatic adapter emission is the production acceptance bar.

**Step 3: Run focused verification and commit**

```sh
.venv/bin/python -m pytest -q tests/test_day_zero_manifest.py tests/test_adoption_examples.py -k day_zero
git diff --check
git add examples/day_zero_exchange tests/test_adoption_examples.py
git commit -m "docs: add day-zero exchange example"
```

---

## Task 11: Add the one-year mapping handshake

**Files:**

- Create: `examples/one_year_mapping_handshake/showcase.yaml`
- Create: `examples/one_year_mapping_handshake/scenario-definition.yaml`
- Create: `examples/one_year_mapping_handshake/model-bindings.yaml`
- Create: `examples/one_year_mapping_handshake/trajectory.yaml`
- Create: `examples/one_year_mapping_handshake/pilates-trajectory-bundle.yaml`
- Create: `examples/one_year_mapping_handshake/polaris-translation-bundle.yaml`
- Create: `examples/one_year_mapping_handshake/mapping-release/revision-1/contract/population-translation-contract.yaml`
- Create: `examples/one_year_mapping_handshake/mapping-release/revision-1/implementation/pilates-translation.yaml`
- Create: `examples/one_year_mapping_handshake/mapping-release/revision-1/ownership.yaml`
- Create: `examples/one_year_mapping_handshake/encoding-source/team-mapping.csv`
- Create: `examples/one_year_mapping_handshake/review/*`
- Create: `examples/one_year_mapping_handshake/README.md`
- Create: `mappings/releases/atlas-demos-to-polaris/OWNERS.yaml`
- Modify: `tests/test_adoption_examples.py`

**Step 1: Write failing handshake and custody tests**

Test the one-year `check-all` package exits 0 in discovery mode, emits `MAPPING_NOT_APPROVED`, preserves payload format, covers every declared exchange column by mapping or residue, displays draft governance honestly, and records the registered implementation digest. Test the canonical manifest digest in the POLARIS source-bundle reference.

Test that the owned mapping path declares both model-team roles and requires their semantic review. When real Git handles are unavailable, do not fabricate them: `OWNERS.yaml`, mapping governance, and the checker-enforced dual-owner review rule are the documented repository enforcement substitute. If maintainers supply Git handles later, `.github/CODEOWNERS` may add them without changing semantic identity.

Run:

```sh
.venv/bin/python -m pytest -q tests/test_adoption_examples.py -k one_year
```

Expected: FAIL.

**Step 2: Build the synthetic adoption fixture through the public tools**

Use `render-mapping` for review artifacts. All identities/digests must match actual checked-in bytes and committed native catalogs. The mapping source is explicitly synthetic and governance remains draft.

**Step 3: Run focused verification and commit**

```sh
.venv/bin/python -m pytest -q tests/test_adoption_examples.py tests/test_mapping_review.py
.venv/bin/python -m synergy_schema.conformance check-all --schema src/synergy_schema/schema/synergy_schema.yaml --dir examples/one_year_mapping_handshake
git diff --check
git add examples/one_year_mapping_handshake mappings/releases/atlas-demos-to-polaris/OWNERS.yaml tests/test_adoption_examples.py
git commit -m "feat: add one-year mapping handshake"
```

---

## Task 12: Add the three-year two-branch showcase and broken fixtures

**Files:**

- Create: `examples/evolving_population/*`
- Create: `examples/evolving_population_broken_scenario/*`
- Create: `examples/evolving_population_broken_artifact_identity/*`
- Create: `tests/test_evolving_population_examples.py`

**Step 1: Write failing showcase acceptance tests**

Require 2025, 2030, and 2035 baseline and ZEV trajectories with distinct immutable scenario definition references/digests. The small population must demonstrate:

- a person absent in 2025 and present in 2030;
- aging only in model-owned attributes, not core state;
- one household split into multiple successor states;
- one vehicle transferred between household assignments;
- all yearly PILATES manifests and all five yearly POLARIS roles;
- schedule and Consist scenario-header/child evidence;
- a POLARIS `compatible_with_gaps` binding for unsupported ZEV policy;
- reuse of the one-year semantic contract and residue catalog.

Test exact commands and stable outcomes:

```sh
.venv/bin/python -m synergy_schema.conformance check-all --schema src/synergy_schema/schema/synergy_schema.yaml --dir examples/evolving_population
# exit 0 with documented compatibility-gap and draft-review warnings

.venv/bin/python -m synergy_schema.conformance check-all --schema src/synergy_schema/schema/synergy_schema.yaml --dir examples/evolving_population_broken_scenario
# exit 1 with SCENARIO_DIGEST_MISMATCH

.venv/bin/python -m synergy_schema.conformance check-all --schema src/synergy_schema/schema/synergy_schema.yaml --dir examples/evolving_population_broken_artifact_identity
# exit 1 with ARTIFACT_IDENTITY_MISMATCH
```

**Step 2: Build the valid fixture**

Keep model attributes in compact synthetic ATLAS/POLARIS evidence files. Keep core records limited to identity and relationship evolution. Reuse the same semantic mapping release by explicit relative reference rather than duplicating it.

**Step 3: Build minimal broken fixture directories**

Each broken directory has its own `showcase.yaml` and only the changed synthetic document(s); it explicitly references unchanged valid documents. Do not mutate or duplicate valid fixture bytes unnecessarily.

**Step 4: Run focused verification and commit**

```sh
.venv/bin/python -m pytest -q tests/test_evolving_population_examples.py tests/test_bundle_conformance.py tests/test_scenario_conformance.py
git diff --check
git add examples/evolving_population examples/evolving_population_broken_scenario examples/evolving_population_broken_artifact_identity tests/test_evolving_population_examples.py
git commit -m "feat: add evolving population showcase"
```

---

## Task 13: Rebuild newcomer documentation and navigation

**Files:**

- Modify: `docs/index.md`
- Modify: `zensical.toml`
- Modify: `scripts/preview-schema-docs`
- Modify: `docs/pilates/post-atlas-population-bundle.md`
- Create: `docs/proof-of-concept/index.md`
- Create: `docs/proof-of-concept/check-the-showcase.md`
- Create: `docs/bring-an-existing-mapping/index.md`
- Create: `docs/bring-an-existing-mapping/day-zero-manifest.md`
- Create: `docs/bring-an-existing-mapping/one-year-mapping-handshake.md`
- Create: `docs/bring-an-existing-mapping/contract-at-a-glance.md`
- Create: `docs/bring-an-existing-mapping/costs-and-exit.md`
- Create: `docs/design-rationale/index.md`
- Create: `docs/design-rationale/why-linkml.md`
- Create: `docs/design-rationale/why-not-one-big-table.md`
- Create: `docs/design-rationale/are-flat-files-enough.md`
- Create: `docs/shared-structure/index.md`
- Create: `docs/shared-structure/scenario-definitions-and-trajectories.md`
- Create: `docs/shared-structure/population-snapshots-and-artifact-identity.md`
- Create: `docs/workflow-structures/index.md`
- Create: `docs/workflow-structures/pilates.md`
- Create: `docs/workflow-structures/polaris.md`
- Create: `docs/cross-model-mappings/index.md`
- Create: `docs/cross-model-mappings/population-identity.md`
- Create: `docs/cross-model-mappings/mapping-lineage.md`
- Create: `docs/cross-model-mappings/scenario-compatibility.md`
- Create: `tests/test_documentation.py`
- Modify: `.github/workflows/ci.yml`

**Step 1: Write failing navigation/content tests**

Assert the exact eight top-level labels and order:

1. Overview
2. Proof of concept
3. Bring an existing mapping
4. Design rationale
5. Shared structure
6. Workflow structures
7. Cross-model mappings
8. Schema reference

Assert every leaf target exists after generation. Assert Overview starts with a plain-language purpose summary and gives co-equal primary actions to bring a mapping and inspect the three-year proof.

Assert the proof page links scenario, trajectory, household, person, vehicle, and provenance references; documents valid exit 0 and both broken exit 1 commands; and names `SCENARIO_DIGEST_MISMATCH` and `ARTIFACT_IDENTITY_MISMATCH`.

Assert adoption pages contain:

- “What we ask / What we do not ask / What you get / Timeline”;
- the generated one-page contract-at-a-glance deliverable;
- day-zero discovery-only and automatic-emission acceptance/kill criteria;
- honest minutes-not-hours steady-state cost budgets and the five-day encode-and-return target;
- an exit-cost guarantee preserving payloads, readable tables, and inert manifests;
- a request for model-team historical incidents without inventing one;
- the explicit concession that flat files plus a README can be enough for stable one-off exchange.

Assert every maintained leaf from the approved information architecture appears under its exact top-level section: **A population that changes over three years**, **What the checker catches**, **Day-zero manifest**, **One-year mapping handshake**, **Contract at a glance**, **Costs and exit**, **Why LinkML**, **Why not one big table?**, **Are flat files enough?**, **Schema organization**, **Scenario definitions and trajectories**, **Population snapshots and artifact identity**, **PILATES post-ATLAS population**, **POLARIS translated population**, **Population identity**, **Translation contract, residue, and lineage**, **Scenario compatibility**, and **Complete generated reference**.

Assert Scenario compatibility renders the no-conflict/gap/override/conflict decision table. Assert PILATES and POLARIS pages both render **Current / proposed / out of scope**, and the POLARIS page says its native records are partial and runtime adapter enforcement is future work.

Run:

```sh
.venv/bin/python -m pytest -q tests/test_documentation.py
```

Expected: FAIL.

**Step 2: Write the maintained guides and exact navigation**

Use newcomer language, short task-oriented pages, cross-links to generated class pages, and the actual commands/fixtures. Keep “Why LinkML” in design rationale—not in the model-team meeting path. Make the real one-year pilot the adoption lead and the synthetic showcase supporting evidence.

**Step 3: Extend the canonical docs build**

Have `scripts/preview-schema-docs` generate the identity diagram and a copy of the synthetic contract-at-a-glance review page under ignored `docs/schema/`, then run Zensical. Avoid cleaning maintained paths.

Add `UV_CACHE_DIR=/tmp/synergy-schema-uv-cache scripts/preview-schema-docs build` to CI after lint and pytest.

**Step 4: Run focused verification and commit**

```sh
.venv/bin/python -m pytest -q tests/test_documentation.py
UV_CACHE_DIR=/tmp/synergy-schema-uv-cache scripts/preview-schema-docs build
git diff --check
git add docs/index.md docs/pilates/post-atlas-population-bundle.md docs/proof-of-concept docs/bring-an-existing-mapping docs/design-rationale docs/shared-structure docs/workflow-structures docs/cross-model-mappings zensical.toml scripts/preview-schema-docs tests/test_documentation.py .github/workflows/ci.yml
git commit -m "docs: guide shared scenario adoption"
```

---

## Task 14: Perform full conformance and documentation verification

**Files:**

- Modify only files needed to fix verified integration defects.

**Step 1: Run the complete local gate**

```sh
UV_CACHE_DIR=/tmp/synergy-schema-uv-cache uv run linkml-lint src/synergy_schema/schema/synergy_schema.yaml
.venv/bin/python -m pytest -q
UV_CACHE_DIR=/tmp/synergy-schema-uv-cache scripts/preview-schema-docs build
.venv/bin/python -m synergy_schema.conformance check-all --schema src/synergy_schema/schema/synergy_schema.yaml --dir examples/one_year_mapping_handshake
.venv/bin/python -m synergy_schema.conformance check-all --schema src/synergy_schema/schema/synergy_schema.yaml --dir examples/evolving_population
git diff --check
git status --short
```

Expected: lint, all tests, static docs, and both valid examples pass. Only the two pre-existing untracked July 31 documentation files remain outside the planned commit set.

**Step 2: Verify the negative contracts**

Run each broken fixture without `set -e`, capture its status, and verify both return 1 with the exact documented diagnostic. Verify the valid synthetic example fails under `--production` because it truthfully remains draft/manual where applicable.

**Step 3: Request a full-branch review**

Review the complete diff from commit `375ff85` through `HEAD` for spec compliance, semantic ownership boundaries, CLI behavior, docs navigation, fixture honesty, and accidental edits to user files. Resolve every blocking issue through another test-first fix commit.

**Step 4: Record final evidence**

Update the subagent-driven-development progress ledger with final commit IDs, commands, exit codes, and any deliberately unverified external-runtime boundary. Do not claim PILATES or POLARIS runtime integration; report it as proposed/out of scope.
