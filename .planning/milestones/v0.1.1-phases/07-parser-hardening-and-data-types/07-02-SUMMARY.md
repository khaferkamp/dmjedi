---
phase: 07-parser-hardening-and-data-types
plan: 02
subsystem: parser
tags: [lark, pydantic, ast, dvml, grammar, data-vault]

# Dependency graph
requires:
  - phase: 07-01
    provides: Parser caching singleton, 4 new data types (bigint/float/varchar/binary), ParseError dataclass, shared type module

provides:
  - NhSatDecl, NhLinkDecl, EffSatDecl, SamLinkDecl, BridgeDecl, PitDecl Pydantic AST node classes
  - Grammar rules for all 6 new DV 2.1 entity types in grammar.lark
  - Transformer methods for all 6 new entity types in DVMLTransformer
  - DVMLModule extended with 6 new entity list fields (nhsats, nhlinks, effsats, samlinks, bridges, pits)
  - 12 new parser tests covering all entity types including all-9-types integration test

affects:
  - phase 08 (resolver — will need to process all 9 entity types)
  - phase 09 (linter — will enforce DV 2.1 rules per entity type)
  - phase 10 (generators — will produce output for all 9 entity types)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Self-contained grammar pattern: each entity has its own *_decl, *_body, *_member rules"
    - "Discriminated tuple pattern for samlink master/duplicate refs and pit of/tracks (('key', value))"
    - "Arrow-chain grammar: qualified_ref ('->' qualified_ref)+ for bridge path traversal"

key-files:
  created: []
  modified:
    - src/dmjedi/lang/ast.py
    - src/dmjedi/lang/grammar.lark
    - src/dmjedi/lang/parser.py
    - tests/test_parser.py

key-decisions:
  - "Used discriminated tuples ('master'/'duplicate', ref) and ('of'/'tracks', ref) for samlink and pit body parsing — avoids new dataclasses for simple key-value grammar members"
  - "Bridge path_chain uses qualified_ref ('->' qualified_ref)+ so arrow separators are discarded by the grammar, leaving only node identifiers in the list"
  - "nhlink reuses references_decl rule from link (same grammar pattern) — consistent with DV 2.1 spec that nhlinks behave like links without historization"

patterns-established:
  - "Entity body pattern: *_decl -> *_body -> *_member -> individual rule, each transformer method self-contained"
  - "Dispatch in start(): isinstance checks against all AST node types, each routes to its DVMLModule list"

requirements-completed:
  - PARSE-03

# Metrics
duration: 25min
completed: 2026-04-08
---

# Phase 07 Plan 02: New DV 2.1 Entity Types Summary

**6 new DV 2.1 entity types (nhsat, nhlink, effsat, samlink, bridge, pit) fully parsed via Lark grammar into Pydantic AST nodes, extending DVMLModule to cover all 9 entity types**

## Performance

- **Duration:** 25 min
- **Started:** 2026-04-08T00:00:00Z
- **Completed:** 2026-04-08T00:25:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- All 6 new entity types have self-contained grammar rules, Pydantic AST models, transformer methods, and DVMLModule list fields
- A single .dv file with all 9 entity types (hub, sat, link, nhsat, nhlink, effsat, samlink, bridge, pit) parses without ambiguity — confirmed by `test_parse_all_entity_types`
- 12 new tests added (5 for Task 1, 7 for Task 2); full suite goes from 99 to 111 tests, all passing

## Task Commits

Each task was committed atomically:

1. **Task 1: nhsat, nhlink, effsat grammar, AST nodes, transformer** - `d87a895` (feat)
2. **Task 2: samlink, bridge, pit grammar, AST nodes, transformer** - `ae856a5` (feat)

_Note: TDD tasks — tests written first (RED), implementation added (GREEN) within same commit per task_

## Files Created/Modified

- `src/dmjedi/lang/ast.py` — Added NhSatDecl, NhLinkDecl, EffSatDecl, SamLinkDecl, BridgeDecl, PitDecl; DVMLModule extended with 6 new list fields
- `src/dmjedi/lang/grammar.lark` — Added 6 entity type rule blocks (nhsat_decl, nhlink_decl, effsat_decl, samlink_decl, bridge_decl, pit_decl) plus sub-rules (path_chain, pit_of, pit_tracks, master_ref, duplicate_ref); statement alternatives updated
- `src/dmjedi/lang/parser.py` — Added transformer methods for all 6 entity types; start() dispatch updated; imports extended with 3 new AST node classes
- `tests/test_parser.py` — 12 new test functions covering each entity type plus the all-9-types integration test

## Decisions Made

- Used discriminated tuples for samlink master/duplicate and pit of/tracks body members — keeps grammar clean without introducing extra Pydantic models for simple key-value pairs
- Bridge path_chain grammar uses `qualified_ref ("->" qualified_ref)+` so the `->` tokens are consumed by the grammar rule and the transformer receives only the node identifier strings
- nhlink reuses `references_decl` (same as link) — consistent with DV 2.1 where nhlink is a link without historization

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None. The parser singleton caching (from Plan 07-01) works correctly in test isolation — each pytest process creates a fresh singleton from the updated grammar.lark, so no test cache invalidation was needed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 9 DVML entity types are now parseable — Phases 8 (resolver), 9 (linter), 10 (generators) can proceed with a complete AST surface
- Resolver will need isinstance dispatch for all 6 new node types (currently skips unknown types as intended)
- Linter rules for new types (e.g., effsat must reference a link, samlink must have both master and duplicate) are deferred to Phase 9

---
*Phase: 07-parser-hardening-and-data-types*
*Completed: 2026-04-08*
