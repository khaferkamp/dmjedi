---
phase: 11-output-completeness
plan: "02"
subsystem: docs
tags: [tdd, docs, mermaid, markdown, entity-coverage]
dependency_graph:
  requires: []
  provides: [DOC-01, DOC-02]
  affects: [src/dmjedi/docs/markdown.py]
tech_stack:
  added: []
  patterns: [Raw Vault / Query Assist grouping, Mermaid erDiagram generation]
key_files:
  created:
    - tests/test_docs.py
  modified:
    - src/dmjedi/docs/markdown.py
decisions:
  - Use bare entity .name (not .qualified_name) in Mermaid to avoid dots breaking erDiagram parser
  - Heading levels bumped from ### to #### for entity entries now nested under ### group headers
  - Empty entity collections produce no section headers (guard in generate_markdown)
metrics:
  duration: "~10 minutes"
  completed: "2026-04-08"
  tasks_completed: 2
  files_modified: 2
---

# Phase 11 Plan 02: Docs Generator Expansion and Mermaid ER Summary

Expanded markdown docs generator to cover all 6 new DV2.1 entity types with Raw Vault/Query Assist grouping and Mermaid erDiagram support, following TDD.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | RED - Failing tests for docs expansion and Mermaid ER | 4ea169a | tests/test_docs.py (created, 12 tests) |
| 2 | GREEN - Restructure generate_markdown with all entity sections | ebda0f2 | src/dmjedi/docs/markdown.py, tests/test_docs.py |

## What Was Built

The `generate_markdown()` function in `src/dmjedi/docs/markdown.py` was fully restructured:

- **Raw Vault grouping** (`## Raw Vault`): contains hubs, links, satellites, nhsats, nhlinks, effsats, samlinks
- **Query Assist grouping** (`## Query Assist`): contains bridges, pit tables
- **Mermaid erDiagram** at top (before entity sections per D-12): shows all relationships with correct notation
  - `||--o{` for satellites, nhsats, links, nhlinks, effsats, samlinks (D-13)
  - `||..o{` for bridge and pit (dotted lines per D-13)
- **6 new section functions**: `_nhsat_section`, `_nhlink_section`, `_effsat_section`, `_samlink_section`, `_bridge_section`, `_pit_section`
- **`_mermaid_diagram()`** function generating a single erDiagram block
- **Empty model guard**: no section headers emitted when model has no entities

## Decisions Made

1. **Bare entity names in Mermaid**: Used `.name` not `.qualified_name` to avoid dots breaking Mermaid erDiagram parser (namespace dots are invalid in entity identifiers).
2. **Heading level bump**: Entity entries changed from `###` to `####` because they are now nested under `### Hubs`, `### Satellites` etc. group subheadings within the `## Raw Vault` section.
3. **Empty guard implementation**: `raw_vault_sections` and `query_assist_sections` lists populated first; section headers only emitted if the list is non-empty.

## Test Coverage

12 tests in `tests/test_docs.py`:
- `test_docs_raw_vault_grouping` — "## Raw Vault" present
- `test_docs_query_assist_grouping` — "## Query Assist" present
- `test_docs_nhsat_section` — nhsat qualified name, parent ref, columns
- `test_docs_nhlink_section` — nhlink qualified name, hub references
- `test_docs_effsat_section` — effsat qualified name, link parent ref, columns
- `test_docs_samlink_section` — samlink qualified name, master/duplicate refs
- `test_docs_bridge_section` — bridge qualified name, path chain
- `test_docs_pit_section` — pit qualified name, anchor ref, tracked satellites
- `test_docs_mermaid_diagram` — mermaid block present before ## Raw Vault
- `test_docs_mermaid_hub_sat_relationship` — `||--o{` notation present
- `test_docs_mermaid_bridge_dotted` — `||..o{` notation present
- `test_docs_empty_model` — no section headers for empty model

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Auto-fix] Removed unused `pytest` import from test file**
- **Found during:** Task 2 verification (ruff check)
- **Issue:** `import pytest` in test_docs.py was unused
- **Fix:** Removed the import
- **Files modified:** tests/test_docs.py
- **Commit:** ebda0f2 (included in GREEN commit)

## Known Stubs

None — all entity sections are fully wired to model data.

## Threat Flags

None — no new network endpoints, auth paths, or trust boundary crossings introduced.

## Self-Check

- [x] tests/test_docs.py exists
- [x] src/dmjedi/docs/markdown.py exists
- [x] Commit 4ea169a exists (RED tests)
- [x] Commit ebda0f2 exists (GREEN implementation)
- [x] All 12 docs tests pass
- [x] Full test suite passes (175 + 12 = 187 tests, snapshot fixture error is pre-existing)
- [x] ruff check passes on docs module and test file
- [x] mypy passes on docs module

## Self-Check: PASSED
