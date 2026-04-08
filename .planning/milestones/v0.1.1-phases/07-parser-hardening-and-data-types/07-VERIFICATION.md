---
phase: 07-parser-hardening-and-data-types
verified: 2026-04-08T12:03:42Z
status: passed
score: 6/6 must-haves verified
overrides_applied: 0
re_verification: null
gaps: []
deferred: []
human_verification: []
---

# Phase 7: Parser Hardening and Data Types — Verification Report

**Phase Goal:** The parser is fast, gives clear errors, and supports an expanded type system ready for new entities
**Verified:** 2026-04-08T12:03:42Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Parsing the same file twice reuses a cached Lark instance (no per-call construction) | VERIFIED | `_parser: Lark \| None = None` module singleton at `parser.py:29`; `_get_parser()` at line 32 uses `global _parser; if _parser is None: _parser = Lark(...)` |
| 2 | A syntax error in a .dv file reports the source file path, line number, column, and a human-readable hint | VERIFIED | `ParseError` dataclass at `parser.py:45` has `file`, `line`, `column`, `hint` fields; `DVMLParseError` at line 55 formats as `{file}:{line}:{column}: {hint}`; `cli/main.py` catches `DVMLParseError` and calls `format_parse_error()` |
| 3 | User can declare fields with bigint, float, varchar, and binary types and they parse without error | VERIFIED | `grammar.lark:110-113` has `type_bigint`, `type_float`, `type_varchar`, `type_binary` terminal aliases; `data_type` rule includes optional `("(" type_params ")")` for parameterized types; 111 tests pass |
| 4 | dmjedi generate with SQL Jinja produces correct SQL type mappings for new types across all dialects | VERIFIED | `model/types.py` `_TYPE_MAP` covers bigint/float/varchar/binary across `default`, `postgres`, `spark` dialects; `sql_jinja/types.py` re-exports `map_type` from `model/types.py`; `sql_jinja/generator.py` imports from the shim; all 11 `test_types.py` tests pass |
| 5 | dmjedi generate with Spark Declarative produces correct PySpark type mappings for new types | VERIFIED | `model/types.py` `_PYSPARK_MAP` maps bigint→LongType(), float→FloatType(), varchar→StringType(), binary→BinaryType(); `spark_declarative/generator.py:5` imports `map_pyspark_type` directly from `model.types`; `test_map_pyspark_type_new_types` passes |
| 6 | All 6 new entity types (nhsat, nhlink, effsat, samlink, bridge, pit) parse without grammar ambiguity | VERIFIED | All 6 `*_decl` grammar rules present in `grammar.lark:65-96`; all 6 `Decl` classes in `ast.py:64-120`; all 6 transformer methods in `parser.py`; `DVMLModule` has 6 new list fields; `test_parse_all_entity_types` confirms all 9 entity types parse in one file; 29 parser tests pass |

**Score:** 6/6 truths verified

Note: Truth 6 is derived from requirement PARSE-03 (mapped to Phase 7 in REQUIREMENTS.md) and from Phase 7's stated requirements. It is not listed as a roadmap success criterion, but the PLAN files claim it and it is traceable to this phase.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/dmjedi/lang/parser.py` | Module-level cached Lark singleton and ParseError dataclass | VERIFIED | `_parser: Lark \| None = None` at line 29; `class ParseError` at line 45; `class DVMLParseError` at line 55 |
| `src/dmjedi/lang/grammar.lark` | Extended grammar with 4 new types and optional type parameters | VERIFIED | `type_bigint` at line 110; `("(" type_params ")")?` in `data_type` rule |
| `src/dmjedi/model/types.py` | Shared type mapping module with parameter-aware map_type() | VERIFIED | File exists (3.2 KB); exports `map_type`, `map_pyspark_type`, `SUPPORTED_DIALECTS`; `_PARAM_RE` regex for parameter handling |
| `src/dmjedi/cli/errors.py` | Updated error formatting consuming ParseError | VERIFIED | Imports `DVMLParseError` from `lang.parser`; `format_parse_error()` accepts `DVMLParseError` and renders structured output |
| `tests/test_types.py` | Tests for shared type mapping module | VERIFIED | 11 tests covering all new types, all dialects, parameterized types, backward compat |
| `src/dmjedi/lang/ast.py` | 6 new Pydantic AST node classes | VERIFIED | `NhSatDecl`, `NhLinkDecl`, `EffSatDecl`, `SamLinkDecl`, `BridgeDecl`, `PitDecl` at lines 64-120; DVMLModule fields at lines 128-133 |
| `tests/test_parser.py` | Tests for parsing all 6 new entity types | VERIFIED | 12 new test functions including `test_parse_all_entity_types` at line 300 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/dmjedi/generators/sql_jinja/generator.py` | `src/dmjedi/model/types.py` | `sql_jinja/types.py` re-export shim | VERIFIED | `generator.py:10` imports from `sql_jinja/types.py`; `types.py:5` re-exports from `model.types` — documented decision in summary |
| `src/dmjedi/generators/sql_jinja/types.py` | `src/dmjedi/model/types.py` | re-export | VERIFIED | `from dmjedi.model.types import SUPPORTED_DIALECTS, map_type` at line 5 |
| `src/dmjedi/generators/spark_declarative/generator.py` | `src/dmjedi/model/types.py` | direct import | VERIFIED | `from dmjedi.model.types import map_pyspark_type` at line 5 |
| `src/dmjedi/lang/parser.py` | `src/dmjedi/cli/errors.py` | DVMLParseError created in parser, consumed by errors | VERIFIED | `cli/errors.py:9` imports `DVMLParseError`; `cli/main.py:163` catches `DVMLParseError` and calls `format_parse_error(e)` |
| `src/dmjedi/lang/grammar.lark` | `src/dmjedi/lang/parser.py` | grammar rule names match transformer method names | VERIFIED | `nhsat_decl`, `nhlink_decl`, `effsat_decl`, `samlink_decl`, `bridge_decl`, `pit_decl` present in both grammar and transformer |
| `src/dmjedi/lang/parser.py` | `src/dmjedi/lang/ast.py` | Transformer creates AST node instances | VERIFIED | `NhSatDecl`, `NhLinkDecl`, `EffSatDecl`, `SamLinkDecl`, `BridgeDecl`, `PitDecl` all instantiated in transformer methods |
| `src/dmjedi/lang/ast.py` | `DVMLModule` | 6 new entity list fields | VERIFIED | `nhsats`, `nhlinks`, `effsats`, `samlinks`, `bridges`, `pits` all defined on `DVMLModule` at lines 128-133 |

### Data-Flow Trace (Level 4)

Not applicable for this phase. All artifacts are parser/grammar/type-mapping infrastructure — no UI components, dashboards, or user-facing dynamic data rendering. Type mappings are pure functions (input: type string → output: SQL/PySpark string), verified by test suite passing.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All 111 tests pass (parser, types, generators, integration) | `uv run pytest tests/ -x -q` | 111 passed in 0.44s | PASS |
| Parser tests (29 tests, includes all 6 new entity types) | `uv run pytest tests/test_parser.py -x -q` | 29 passed in 0.10s | PASS |
| Type mapping tests (11 tests, all dialects and new types) | `uv run pytest tests/test_types.py -v` | 11 passed in 0.01s | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PARSE-01 | 07-01 | Parser caches Lark instance as singleton instead of creating per call | SATISFIED | `_parser: Lark \| None = None` module singleton; `_get_parser()` lazy-initializes once per process |
| PARSE-02 | 07-01 | Parse errors include source file, line, column, and contextual hint | SATISFIED | `ParseError` dataclass with `file`, `line`, `column`, `hint` fields; `DVMLParseError` wraps it; `_HINTS` catalog provides context-aware messages |
| PARSE-03 | 07-02 | Parser handles all new entity keywords without grammar ambiguity | SATISFIED | 6 new grammar rules added to `statement` alternatives; `test_parse_all_entity_types` parses all 9 entity types in one file without ambiguity |
| TYPE-01 | 07-01 | User can use bigint, float, varchar, binary data types in field declarations | SATISFIED | Grammar terminals at `grammar.lark:110-113`; optional parameter syntax via `type_params`; tests confirm parsing works |
| TYPE-02 | 07-01 | SQL Jinja generator maps new data types correctly per dialect (default, postgres, spark) | SATISFIED | `_TYPE_MAP` in `model/types.py` covers all 4 new types × 3 dialects; `test_map_type_bigint_all_dialects`, `test_map_type_float_all_dialects`, etc. pass |
| TYPE-03 | 07-01 | Spark Declarative generator maps new data types to PySpark types | SATISFIED | `_PYSPARK_MAP` in `model/types.py`; `spark_declarative/generator.py` imports `map_pyspark_type`; `test_map_pyspark_type_new_types` passes |

No orphaned requirements: REQUIREMENTS.md traceability maps PARSE-01, PARSE-02, PARSE-03, TYPE-01, TYPE-02, TYPE-03 all to Phase 7 — all 6 are claimed by Phase 7 plans and all 6 are verified.

### Anti-Patterns Found

None. Scanned `parser.py`, `grammar.lark`, `model/types.py`, `cli/errors.py`, `ast.py`, `spark_declarative/generator.py` for TODO/FIXME/PLACEHOLDER/stub patterns. Zero matches.

### Human Verification Required

None. All truths are verifiable programmatically through the test suite and code inspection. No visual UI, real-time behavior, or external service integration is present in this phase.

### Gaps Summary

No gaps. All 6 roadmap truths (5 explicit success criteria + PARSE-03 from requirements) are fully implemented, wired, and tested. 111 tests pass. No stubs, no orphaned artifacts, no missing key links.

---

_Verified: 2026-04-08T12:03:42Z_
_Verifier: Claude (gsd-verifier)_
