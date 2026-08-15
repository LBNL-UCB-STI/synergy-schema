# User-Friendly Glossary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a maintained plain-language glossary, prominent navigation, and selective first-use links for confusing Synergy Schema terminology.

**Architecture:** `docs/shared-structure/glossary.md` is the single maintained newcomer glossary. The Overview, Shared Structure navigation, and a few concept-heavy guides link to it; generated LinkML class pages remain the structural reference.

**Tech Stack:** Markdown, Zensical TOML navigation, pytest documentation assertions.

## Global Constraints

- Preserve the eight existing top-level navigation sections and their order.
- Do not duplicate a glossary on every guide page.
- Keep definitions plain-language and ownership-neutral.
- Do not imply POLARIS runtime deployment, model-team approval, or universal native records.
- Preserve the two pre-existing untracked July 31 documentation files.

---

### Task 1: Add glossary navigation and content contract

**Files:**

- Create: `docs/shared-structure/glossary.md`
- Modify: `zensical.toml`
- Modify: `docs/index.md`
- Modify: `docs/shared-structure/index.md`
- Test: `tests/test_documentation.py`

**Interfaces:**

- Consumes: the existing **Shared structure** navigation section.
- Produces: `shared-structure/glossary.md` and stable glossary anchors used by Task 2.

- [ ] **Step 1: Write the failing documentation test**

Add a test that requires the **Glossary** navigation leaf, Overview and Schema
organization links, the five topic headings, core terms, and a comparison
table headed `| Often confused | How they differ |`.

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest -q tests/test_documentation.py`

Expected: FAIL because the glossary navigation leaf and file do not exist.

- [ ] **Step 3: Write the glossary and navigation links**

Define the terms from the design in short entries and add the comparison table.
Add **Glossary** under **Shared structure** without changing top-level order.

- [ ] **Step 4: Run the documentation test**

Run: `.venv/bin/python -m pytest -q tests/test_documentation.py`

Expected: PASS.

---

### Task 2: Add selective first-use links and verify the site

**Files:**

- Modify: `docs/shared-structure/scenario-definitions-and-trajectories.md`
- Modify: `docs/workflow-structures/index.md`
- Modify: `docs/cross-model-mappings/mapping-lineage.md`
- Modify: `docs/bring-an-existing-mapping/one-year-mapping-handshake.md`
- Modify: `tests/test_documentation.py`

**Interfaces:**

- Consumes: glossary anchors from `docs/shared-structure/glossary.md`.
- Produces: four high-value first-use links without link-saturating the guides.

- [ ] **Step 1: Extend the failing test with exact first-use links**

Require links to scenario definition/trajectory, workflow profile/native record,
translation contract/residue, and receipt/review-state glossary anchors.

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest -q tests/test_documentation.py`

Expected: FAIL because the first-use links are absent.

- [ ] **Step 3: Add the four selective links**

Link only the first relevant phrase on each page. Do not replace existing links
to generated class pages.

- [ ] **Step 4: Run the complete documentation gate**

Run:

```sh
.venv/bin/python -m pytest -q tests/test_documentation.py
UV_CACHE_DIR=/tmp/synergy-schema-uv-cache scripts/preview-schema-docs build
git diff --check
```

Expected: documentation tests, static build, and whitespace checks pass.
