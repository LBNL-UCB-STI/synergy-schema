# Cross-Model Population Identity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add small UrbanSim, ActivitySim, and POLARIS identity projections plus typed, evidence-backed mappings that demonstrate preserved and transformed population keys across the PILATES loop.

**Architecture:** Keep the snapshot-scoped shared population kernel unchanged. Add explicitly partial model-owned projections, a typed mapping vocabulary, and one connected example that reuses the existing post-ATLAS identities. LinkML validates declaration shape; focused Python tests validate the cross-file semantic story.

**Tech Stack:** LinkML YAML, `linkml-runtime`, LinkML validator with closed JSON Schema validation, pytest, YAML, Zensical.

## Global Constraints

- Do not add producer-specific attributes to `core`.
- Every new model class must be labeled as an identity-bearing partial projection, not a complete native table.
- `household_id` and `person_id` may be identity-preserving; `member_id`, POLARIS person `id`, and `vehicle_id` alone must not be presented as globally stable identity.
- Keep PILATES runtime joins, adapters, registry routing, generated SQL, recovery, and validation policy unchanged.
- Do not modify `/Users/zaneedell/git/PILATES` or `/Users/zaneedell/git/activitysim`.
- Do not infer units, enums, or broad requiredness from nullable SQLModel stubs.
- Reuse `examples/post_atlas_population_bundle/` as canonical example data.
- Tests must exercise LinkML validation and cross-file behavior, not grep schema text.
- Follow test-driven development: add a focused failing test and observe the expected failure before adding each schema or example behavior.

---

### Task 1: Add model-owned identity projections

**Files:**
- Create: `src/synergy_schema/schema/models/urbansim/urbansim_population.yaml`
- Create: `src/synergy_schema/schema/models/urbansim/README.md`
- Create: `src/synergy_schema/schema/models/activitysim/activitysim_population.yaml`
- Create: `src/synergy_schema/schema/models/activitysim/README.md`
- Create: `src/synergy_schema/schema/models/polaris/polaris_population.yaml`
- Create: `src/synergy_schema/schema/models/polaris/README.md`
- Modify: `src/synergy_schema/schema/models/README.md`
- Modify: `src/synergy_schema/schema/synergy_schema.yaml`
- Create: `tests/test_population_projections.py`

**Interfaces:**
- Consumes: the canonical root at `src/synergy_schema/schema/synergy_schema.yaml` and existing ATLAS classes.
- Produces: `UrbanSimHouseholdPopulationRecord`, `UrbanSimPersonPopulationRecord`, `ActivitySimHouseholdInputRecord`, `ActivitySimPersonInputRecord`, `ActivitySimLandUseZoneRecord`, `PolarisHouseholdRecord`, `PolarisPersonRecord`, and `PolarisVehicleRecord`.

- [ ] **Step 1: Write projection discovery and shape tests**

Create `tests/test_population_projections.py` with local schema and validation helpers:

```python
from copy import deepcopy
from pathlib import Path

from linkml.validator import Validator
from linkml.validator.plugins import JsonschemaValidationPlugin
from linkml_runtime.utils.schemaview import SchemaView


SCHEMA_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "synergy_schema"
    / "schema"
    / "synergy_schema.yaml"
)


def _messages(instance: dict[str, object], target_class: str) -> list[str]:
    report = Validator(
        SCHEMA_PATH,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    ).validate(instance, target_class)
    return [result.message for result in report.results]


def test_root_exposes_cross_model_population_identity_projections() -> None:
    schema_view = SchemaView(str(SCHEMA_PATH))
    assert {
        "UrbanSimHouseholdPopulationRecord",
        "UrbanSimPersonPopulationRecord",
        "ActivitySimHouseholdInputRecord",
        "ActivitySimPersonInputRecord",
        "ActivitySimLandUseZoneRecord",
        "PolarisHouseholdRecord",
        "PolarisPersonRecord",
        "PolarisVehicleRecord",
    }.issubset(schema_view.all_classes())


def test_population_projection_shapes_expose_only_identity_join_fields() -> None:
    schema_view = SchemaView(str(SCHEMA_PATH))
    expected = {
        "UrbanSimHouseholdPopulationRecord": {"household_id", "block_id"},
        "UrbanSimPersonPopulationRecord": {
            "person_id",
            "household_id",
            "member_id",
            "work_zone_id",
            "school_zone_id",
        },
        "ActivitySimHouseholdInputRecord": {"household_id", "block_id", "taz"},
        "ActivitySimPersonInputRecord": {
            "person_id",
            "household_id",
            "member_id",
            "taz",
            "work_zone_id",
            "workplace_taz",
            "school_zone_id",
            "school_taz",
        },
        "ActivitySimLandUseZoneRecord": {"taz"},
        "PolarisHouseholdRecord": {"household", "hhold", "location"},
        "PolarisPersonRecord": {"person", "household", "id"},
        "PolarisVehicleRecord": {"vehicle_id", "hhold"},
    }
    for class_name, fields in expected.items():
        assert set(schema_view.induced_class(class_name).attributes) == fields
```

- [ ] **Step 2: Run the focused tests and observe the missing-class failure**

Run:

```bash
uv run pytest -q tests/test_population_projections.py
```

Expected: failure because the eight projection classes are absent.

- [ ] **Step 3: Add the three model schemas and root imports**

Use a separate schema ID and import of `linkml:types` in each file. Apply these contracts:

- All classes have annotations:
  - `owner`: `UrbanSim`, `ActivitySim`, or `POLARIS`;
  - `coverage`: `identity-bearing partial projection`;
  - `enforcement_status`: `PILATES-observed`.
- All entity IDs are `integer`, required, and identifiers in their own record.
- Person `household_id` fields are required and carry `relationship_target`.
- UrbanSim `member_id` is optional and annotated
  `identity_role: within-household ordinal`.
- ActivitySim `member_id` is required and annotated
  `value_stability: regenerated by PILATES ActivitySim preprocessing`.
- `ActivitySimLandUseZoneRecord.taz` is its required identifier and has
  `physical_name: TAZ`.
- ActivitySim household/person `taz` slots have `physical_name: TAZ` and a
  relationship target of `ActivitySimLandUseZoneRecord`.
- Work/school aliases are optional and carry
  `mapping_scope: current PILATES ActivitySim adapter`.
- POLARIS `household`, `person`, and `vehicle_id` are identifiers for their
  respective records. Household `hhold` is a required alias annotated
  `alias_of: household`. Person `household` and vehicle `hhold` are required
  relationship references to `PolarisHouseholdRecord`.
- POLARIS person `id` is required and annotated
  `identity_role: zero-based within-household ordinal`.
- POLARIS vehicle class is annotated
  `identity_scope: enclosing translated population snapshot artifact`.

Add these imports to the canonical root:

```yaml
  - models/urbansim/urbansim_population
  - models/activitysim/activitysim_population
  - models/polaris/polaris_population
```

- [ ] **Step 4: Add behavior tests for required IDs, relationships, and physical names**

Append tests that validate one minimal record of each class and verify:

```python
def test_projection_identifiers_and_relationships_are_explicit() -> None:
    schema_view = SchemaView(str(SCHEMA_PATH))
    cases = {
        "UrbanSimHouseholdPopulationRecord": ({"household_id": 101}, "household_id"),
        "UrbanSimPersonPopulationRecord": (
            {"person_id": 1001, "household_id": 101},
            "person_id",
        ),
        "ActivitySimHouseholdInputRecord": ({"household_id": 101}, "household_id"),
        "ActivitySimPersonInputRecord": (
            {"person_id": 1001, "household_id": 101, "member_id": 1},
            "person_id",
        ),
        "ActivitySimLandUseZoneRecord": ({"taz": 5001}, "taz"),
        "PolarisHouseholdRecord": (
            {"household": 101, "hhold": 101},
            "household",
        ),
        "PolarisPersonRecord": (
            {"person": 1001, "household": 101, "id": 0},
            "person",
        ),
        "PolarisVehicleRecord": ({"vehicle_id": 1, "hhold": 101}, "vehicle_id"),
    }
    for class_name, (record, identifier) in cases.items():
        assert _messages(record, class_name) == []
        induced = schema_view.induced_class(class_name)
        assert induced.attributes[identifier].identifier is True
        missing = deepcopy(record)
        del missing[identifier]
        assert _messages(missing, class_name)

    assert (
        schema_view.induced_slot("taz", "ActivitySimLandUseZoneRecord")
        .annotations["physical_name"]
        .value
        == "TAZ"
    )
    assert (
        schema_view.induced_slot("household_id", "ActivitySimPersonInputRecord")
        .annotations["relationship_target"]
        .value
        == "ActivitySimHouseholdInputRecord"
    )
```

- [ ] **Step 5: Run focused tests and lint**

Run:

```bash
uv run pytest -q tests/test_population_projections.py
uv run linkml-lint src/synergy_schema/schema/synergy_schema.yaml
```

Expected: all focused tests pass and lint reports no problems.

- [ ] **Step 6: Commit Task 1**

```bash
git add src/synergy_schema/schema/models src/synergy_schema/schema/synergy_schema.yaml tests/test_population_projections.py
git commit -m "feat: add cross-model population identity projections"
```

---

### Task 2: Add the typed mapping vocabulary and mapping manifest

**Files:**
- Create: `src/synergy_schema/schema/mappings/population_identity.yaml`
- Modify: `src/synergy_schema/schema/mappings/README.md`
- Modify: `src/synergy_schema/schema/synergy_schema.yaml`
- Create: `examples/post_atlas_population_bundle/population_identity_mappings.yaml`
- Modify: `tests/test_population_projections.py`

**Interfaces:**
- Consumes: all projection classes from Task 1 plus existing ATLAS classes.
- Produces: `PopulationRepresentationMapping`, `PopulationSlotMapping`, `PopulationMappingStatus`, `PopulationIdentityRole`, and `PopulationValueStability`.

- [ ] **Step 1: Write failing mapping-vocabulary tests**

Append:

```python
MAPPINGS_PATH = (
    Path(__file__).parents[1]
    / "examples"
    / "post_atlas_population_bundle"
    / "population_identity_mappings.yaml"
)


def _mapping_fixture() -> dict[str, dict[str, object]]:
    import yaml

    return yaml.safe_load(MAPPINGS_PATH.read_text(encoding="utf-8"))


def test_mapping_vocabulary_is_imported_with_controlled_classifications() -> None:
    schema_view = SchemaView(str(SCHEMA_PATH))
    assert {
        "PopulationRepresentationMapping",
        "PopulationSlotMapping",
    }.issubset(schema_view.all_classes())
    assert set(schema_view.get_enum("PopulationMappingStatus").permissible_values) == {
        "direct",
        "renamed",
        "unit_or_enum_converted",
        "derived",
        "unsupported",
        "platform_specific",
    }
    assert set(schema_view.get_enum("PopulationIdentityRole").permissible_values) == {
        "entity_identifier",
        "relationship_foreign_key",
        "within_parent_ordinal",
        "geographic_identifier",
        "artifact_scoped_identifier",
    }
    assert set(schema_view.get_enum("PopulationValueStability").permissible_values) == {
        "preserved",
        "derived",
        "regenerated",
        "alias",
        "artifact_scoped",
    }
```

- [ ] **Step 2: Run the focused test and observe the missing mapping schema**

Run:

```bash
uv run pytest -q tests/test_population_projections.py::test_mapping_vocabulary_is_imported_with_controlled_classifications
```

Expected: failure because the mapping classes and enums are absent.

- [ ] **Step 3: Implement the mapping schema**

Define:

```yaml
classes:
  PopulationRepresentationMapping:
    attributes:
      id:
        identifier: true
        required: true
      source_representation:
        required: true
      target_representation:
        required: true
      slot_mappings:
        range: PopulationSlotMapping
        multivalued: true
        inlined_as_list: true
        required: true
        minimum_cardinality: 1
  PopulationSlotMapping:
    attributes:
      id:
        identifier: true
        required: true
      source_paths:
        multivalued: true
        required: true
        minimum_cardinality: 1
      target_paths:
        multivalued: true
        required: true
        minimum_cardinality: 1
      mapping_status:
        range: PopulationMappingStatus
        required: true
      identity_role:
        range: PopulationIdentityRole
        required: true
      value_stability:
        range: PopulationValueStability
        required: true
      relationship_cardinality:
        description: Optional relationship cardinality such as one-to-one or many-to-one.
      transformation:
        required: true
      evidence:
        required: true
```

Add the three enums with the exact permissible values asserted by the test.
Import the mapping schema from the root.

- [ ] **Step 4: Add the mapping fixture and validation tests**

Create a YAML mapping keyed by stable names. It must cover:

- `urbansim_activitysim_household_identity`;
- `urbansim_activitysim_person_identity`;
- person-to-household membership in UrbanSim and ActivitySim;
- `atlas_polaris_household_identity`, including both `household` and `hhold`;
- `atlas_polaris_person_identity`;
- regenerated UrbanSim-to-ActivitySim `member_id`;
- derived ATLAS `member_id` to POLARIS `id`;
- derived UrbanSim `block_id` to ActivitySim `taz`;
- ActivitySim work and school aliases;
- artifact-scoped ATLAS-to-POLARIS vehicle identity.

Use repository-relative PILATES evidence strings such as:

```yaml
evidence: pilates/activitysim/preprocessor.py:3349
```

Append:

```python
def test_population_mapping_manifest_validates_and_is_evidence_complete() -> None:
    mappings = _mapping_fixture()
    assert set(mappings) == {
        "urbansim_activitysim_population",
        "atlas_polaris_population",
    }
    for mapping in mappings.values():
        assert _messages(mapping, "PopulationRepresentationMapping") == []
        for slot_mapping in mapping["slot_mappings"]:
            assert slot_mapping["mapping_status"]
            assert slot_mapping["identity_role"]
            assert slot_mapping["value_stability"]
            assert slot_mapping["transformation"]
            assert slot_mapping["evidence"].startswith("pilates/")


def test_unstable_local_ordinals_are_not_mapped_as_preserved_entity_ids() -> None:
    slot_mappings = [
        entry
        for mapping in _mapping_fixture().values()
        for entry in mapping["slot_mappings"]
    ]
    for entry in slot_mappings:
        if any(path.endswith((".member_id", ".id")) for path in entry["source_paths"]):
            assert entry["identity_role"] == "within_parent_ordinal"
            assert entry["value_stability"] in {"derived", "regenerated"}
```

- [ ] **Step 5: Run focused tests and lint**

```bash
uv run pytest -q tests/test_population_projections.py
uv run linkml-lint src/synergy_schema/schema/synergy_schema.yaml
```

Expected: all focused tests pass and lint reports no problems.

- [ ] **Step 6: Commit Task 2**

```bash
git add src/synergy_schema/schema/mappings src/synergy_schema/schema/synergy_schema.yaml examples/post_atlas_population_bundle/population_identity_mappings.yaml tests/test_population_projections.py
git commit -m "feat: describe cross-model population mappings"
```

---

### Task 3: Extend the canonical example with connected model records

**Files:**
- Create: `examples/post_atlas_population_bundle/cross_model_population_records.yaml`
- Modify: `examples/post_atlas_population_bundle/atlas_population_records.yaml`
- Modify: `examples/post_atlas_population_bundle/README.md`
- Modify: `tests/test_population_projections.py`

**Interfaces:**
- Consumes: Task 1 projection classes, Task 2 mapping fixture, and existing synthetic ATLAS/core/bundle examples.
- Produces: one connected UrbanSim → ActivitySim → ATLAS → POLARIS identity story.

- [ ] **Step 1: Write failing example validation and integrity tests**

Append:

```python
CROSS_MODEL_RECORDS_PATH = (
    Path(__file__).parents[1]
    / "examples"
    / "post_atlas_population_bundle"
    / "cross_model_population_records.yaml"
)
ATLAS_RECORDS_PATH = (
    Path(__file__).parents[1]
    / "examples"
    / "post_atlas_population_bundle"
    / "atlas_population_records.yaml"
)


def _yaml(path: Path) -> dict[str, object]:
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_cross_model_example_records_validate() -> None:
    records = _yaml(CROSS_MODEL_RECORDS_PATH)
    targets = {
        "urbansim_household": "UrbanSimHouseholdPopulationRecord",
        "urbansim_person": "UrbanSimPersonPopulationRecord",
        "activitysim_household": "ActivitySimHouseholdInputRecord",
        "activitysim_person": "ActivitySimPersonInputRecord",
        "activitysim_land_use": "ActivitySimLandUseZoneRecord",
        "polaris_household": "PolarisHouseholdRecord",
        "polaris_person": "PolarisPersonRecord",
        "polaris_vehicle": "PolarisVehicleRecord",
    }
    for record_name, target_class in targets.items():
        assert _messages(records[record_name], target_class) == []


def test_cross_model_example_preserves_entities_and_exposes_transformations() -> None:
    records = _yaml(CROSS_MODEL_RECORDS_PATH)
    atlas = _yaml(ATLAS_RECORDS_PATH)

    assert {
        records["urbansim_household"]["household_id"],
        records["activitysim_household"]["household_id"],
        atlas["household"]["household_id"],
        records["polaris_household"]["household"],
        records["polaris_household"]["hhold"],
        records["polaris_person"]["household"],
        records["polaris_vehicle"]["hhold"],
    } == {101}
    assert {
        records["urbansim_person"]["person_id"],
        records["activitysim_person"]["person_id"],
        atlas["person"]["person_id"],
        records["polaris_person"]["person"],
    } == {1001}
    assert records["activitysim_person"]["household_id"] == 101
    assert records["urbansim_person"]["member_id"] == 1
    assert records["activitysim_person"]["member_id"] == 1
    assert atlas["person"]["member_id"] == 1
    assert records["polaris_person"]["id"] == 0
    assert records["activitysim_household"]["taz"] == records["activitysim_land_use"]["taz"]
    assert records["polaris_vehicle"]["vehicle_id"] == atlas["vehicle"]["vehicle_id"]
```

- [ ] **Step 2: Run focused tests and observe missing example failures**

```bash
uv run pytest -q tests/test_population_projections.py::test_cross_model_example_records_validate tests/test_population_projections.py::test_cross_model_example_preserves_entities_and_exposes_transformations
```

Expected: failure because `cross_model_population_records.yaml` does not exist.

- [ ] **Step 3: Add the connected example**

Use these exact values:

```yaml
urbansim_household:
  household_id: 101
  block_id: "060750101001001"
urbansim_person:
  person_id: 1001
  household_id: 101
  member_id: 1
  work_zone_id: 5002
  school_zone_id: 5003
activitysim_household:
  household_id: 101
  block_id: "060750101001001"
  taz: 5001
activitysim_person:
  person_id: 1001
  household_id: 101
  member_id: 1
  taz: 5001
  work_zone_id: 5002
  workplace_taz: 5002
  school_zone_id: 5003
  school_taz: 5003
activitysim_land_use:
  taz: 5001
polaris_household:
  household: 101
  hhold: 101
  location: 60750101001001
polaris_person:
  person: 1001
  household: 101
  id: 0
polaris_vehicle:
  vehicle_id: 1
  hhold: 101
```

Add `member_id: 1` to the existing ATLAS person example.

- [ ] **Step 4: Document the connected story**

Update the example README with a compact table showing each semantic concept,
its physical fields, whether it is preserved or transformed, and where the
ordinary LinkML validation boundary ends.

- [ ] **Step 5: Run focused and existing example tests**

```bash
uv run pytest -q tests/test_population_projections.py tests/test_schema.py
```

Expected: all tests pass.

- [ ] **Step 6: Commit Task 3**

```bash
git add examples/post_atlas_population_bundle tests/test_population_projections.py
git commit -m "docs: demonstrate cross-model population identity"
```

---

### Task 4: Integrate documentation, record the decision, and verify the full slice

**Files:**
- Modify: `src/synergy_schema/schema/profiles/README.md`
- Modify but keep ignored/untracked: `docs-internal/pilates-linkml-transition-plan.md`
- Modify if needed for navigation: `README.md`

**Interfaces:**
- Consumes: all schemas, mappings, examples, and tests from Tasks 1–3.
- Produces: collaborator-facing explanation and an updated transition ledger.

- [ ] **Step 1: Update schema documentation**

Document:

- the identity-bearing projection pattern;
- preserved `household_id` and `person_id`;
- regenerated and derived ordinals;
- model-specific zone relationships;
- artifact-scoped POLARIS vehicle identity;
- the distinction between LinkML shape validation and cross-artifact integrity.

Do not claim complete native-table coverage or runtime enforcement.

- [ ] **Step 2: Update the internal transition ledger**

Add a new resolved decision after D25:

```text
D26 | Expand collaborator-facing coverage with identity-bearing UrbanSim, ActivitySim, and POLARIS projections plus typed mappings; keep core unchanged | population mapping slice | resolved: implemented
```

Add a dated decision/progress entry summarizing the live PILATES evidence,
files implemented, tests added, remaining model-owner review, and the deferred
OMX/skim-order work.

- [ ] **Step 3: Run full verification**

```bash
uv run linkml-lint src/synergy_schema/schema/synergy_schema.yaml
uv run pytest -q
scripts/preview-schema-docs build
git diff --check
git status --short
```

Expected:

- LinkML lint reports no problems.
- The full pytest suite passes with zero failures.
- Zensical builds successfully.
- `git diff --check` is clean.
- Status contains only the intended Task 4 documentation changes before commit.

- [ ] **Step 4: Confirm external repositories are unchanged**

```bash
git -C /Users/zaneedell/git/PILATES status --short
git -C /Users/zaneedell/git/activitysim status --short
```

Compare the output with the pre-implementation snapshot. Do not clean,
stage, or modify either repository.

- [ ] **Step 5: Commit Task 4**

```bash
git add src/synergy_schema/schema/profiles/README.md README.md
git commit -m "docs: explain population identity mapping slice"
```

The ignored `docs-internal/pilates-linkml-transition-plan.md` remains a local
progress ledger and must not be forced into the Git index.

- [ ] **Step 6: Re-run completion verification**

```bash
uv run linkml-lint src/synergy_schema/schema/synergy_schema.yaml
uv run pytest -q
scripts/preview-schema-docs build
git diff --check
git status --short --branch
```

Expected: lint, tests, and docs build pass; the worktree is clean.
