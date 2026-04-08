---
phase: 08-non-historized-entities
plan: "01"
subsystem: model
tags: [domain-model, resolver, nhsat, nhlink, pydantic, tdd]
dependency_graph:
  requires: []
  provides: [NhSat domain class, NhLink domain class, nhsat/nhlink resolver loops, nhsat parent validation]
  affects: [src/dmjedi/model/core.py, src/dmjedi/model/resolver.py, tests/test_model.py]
tech_stack:
  added: []
  patterns: [Pydantic model_validator for NhLink 2-hub minimum, resolver loop pattern matching existing sat/link loops]
key_files:
  created: []
  modified:
    - src/dmjedi/model/core.py
    - src/dmjedi/model/resolver.py
    - tests/test_model.py
decisions:
  - NhSat and NhLink are standalone classes (not subclasses of Satellite/Link) per plan D-01
  - NhLink validation message uses same format as Link: "must reference at least 2 hubs"
  - NhSat parent validation mirrors satellite parent validation pattern (checks hubs and links, qualified and unqualified)
metrics:
  duration: "~2 minutes"
  completed_date: "2026-04-08"
  tasks_completed: 2
  files_modified: 3
requirements_fulfilled:
  - ENTITY-03
  - ENTITY-04
---

# Phase 08 Plan 01: NhSat and NhLink Domain Model and Resolver Summary

NhSat/NhLink Pydantic domain classes added to core.py with resolver loops, duplicate detection, and nhsat parent validation — 10 new tests, all 121 tests passing.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Add failing tests for NhSat/NhLink domain classes | 271151b | tests/test_model.py |
| 1 (GREEN) | Add NhSat and NhLink domain classes, extend DataVaultModel | 6bd5e94 | src/dmjedi/model/core.py |
| 2 (RED) | Add failing tests for nhsat/nhlink resolver loops | 8b84110 | tests/test_model.py |
| 2 (GREEN) | Extend resolver with nhsat/nhlink loops and nhsat parent validation | af8d8ac | src/dmjedi/model/resolver.py |

## What Was Built

### NhSat domain class (core.py)
- Fields: `name: str`, `namespace: str = ""`, `parent_ref: str`, `columns: list[Column] = []`
- Property: `qualified_name` returning `"ns.Name"` or `"Name"`
- Standalone class, not a subclass of Satellite

### NhLink domain class (core.py)
- Fields: `name: str`, `namespace: str = ""`, `hub_references: list[str] = []`, `columns: list[Column] = []`
- `@model_validator(mode="after")` enforcing minimum 2 hub references
- Property: `qualified_name`
- Standalone class, not a subclass of Link

### DataVaultModel extensions (core.py)
- `nhsats: dict[str, NhSat] = {}`
- `nhlinks: dict[str, NhLink] = {}`

### Resolver extensions (resolver.py)
- Import of `NhSat, NhLink` from `dmjedi.model.core`
- nhsat resolution loop inside `for module in modules:` block with duplicate detection
- nhlink resolution loop inside `for module in modules:` block with duplicate detection
- Post-resolution nhsat parent validation checking against `model.hubs` and `model.links`

## Tests Added (10 new)

| Test | Description |
|------|-------------|
| test_nhlink_requires_two_refs | ValidationError raised for NhLink with <2 refs |
| test_nhsat_qualified_name | NhSat qualified_name format with namespace |
| test_nhlink_qualified_name | NhLink qualified_name format with namespace |
| test_data_vault_model_has_nhsats_nhlinks | DataVaultModel construction with nhsats/nhlinks |
| test_resolve_nhsat | nhsat parsed and resolved with correct fields |
| test_resolve_nhlink | nhlink parsed and resolved with correct hub_references |
| test_nhsat_invalid_parent_raises | ResolverErrors raised for unknown parent |
| test_nhsat_parent_ref_to_link_valid | nhsat can reference a link entity as parent |
| test_duplicate_nhsat_raises | ResolverErrors raised for duplicate nhsat |
| test_duplicate_nhlink_raises | ResolverErrors raised for duplicate nhlink |

## Deviations from Plan

None — plan executed exactly as written.

## Threat Model Coverage

| Threat | Mitigation | Status |
|--------|-----------|--------|
| T-08-01: NhLink hub_references tampering | model_validator enforces 2-hub minimum | Implemented |
| T-08-02: NhSat parent_ref tampering | Resolver validates parent against model.hubs/links | Implemented |
| T-08-03: Duplicate entity names DoS | Resolver detects duplicates and raises ResolverErrors | Implemented |

## Known Stubs

None.

## Self-Check: PASSED

- src/dmjedi/model/core.py: FOUND (contains NhSat, NhLink, nhsats/nhlinks fields)
- src/dmjedi/model/resolver.py: FOUND (contains nhsat/nhlink loops and parent validation)
- tests/test_model.py: FOUND (contains all 10 new test functions)
- Commits: 271151b, 6bd5e94, 8b84110, af8d8ac all present
- Full test suite: 121 passed (was 111)
