---
phase: 07-parser-hardening-and-data-types
plan: "01"
subsystem: parser, type-system, generators
tags: [parser, caching, types, error-handling, spark, sql]
dependency_graph:
  requires: []
  provides:
    - parser-singleton-cache
    - structured-parse-errors
    - extended-dvml-types
    - shared-type-mapping-module
    - spark-typed-columns
  affects:
    - src/dmjedi/lang/parser.py
    - src/dmjedi/lang/grammar.lark
    - src/dmjedi/model/types.py
    - src/dmjedi/generators/sql_jinja/types.py
    - src/dmjedi/generators/spark_declarative/generator.py
    - src/dmjedi/cli/errors.py
    - src/dmjedi/cli/main.py
tech_stack:
  added:
    - "dataclasses.dataclass for ParseError"
    - "re.compile for parameter extraction in map_type()"
  patterns:
    - "Module-level singleton for Lark instance caching"
    - "Structured exception carrying dataclass payload (DVMLParseError/ParseError)"
    - "Shared type mapping module with re-export compatibility shim"
    - "TDD red-green flow for all three tasks"
key_files:
  created:
    - src/dmjedi/model/types.py
    - tests/test_types.py
  modified:
    - src/dmjedi/lang/grammar.lark
    - src/dmjedi/lang/parser.py
    - src/dmjedi/cli/errors.py
    - src/dmjedi/cli/main.py
    - src/dmjedi/generators/sql_jinja/types.py
    - src/dmjedi/generators/spark_declarative/generator.py
    - tests/test_parser.py
    - tests/test_generators.py
    - tests/snapshots/test_integration/test_spark_hub_snapshot/hub_customer.py
decisions:
  - "ParseError is a plain dataclass (not Pydantic) — renderer-agnostic per D-05"
  - "DVMLParseError wraps ParseError and extends Exception (not Lark's exception hierarchy)"
  - "sql_jinja/types.py kept as re-export shim to preserve backward-compatible import path"
  - "Spark generator .cast() added for both satellites and links column types"
  - "Pre-existing mypy errors in parser.py (type: ignore[union-attr] pattern) are out of scope — existed before this plan"
metrics:
  duration: "~25 minutes"
  completed: "2026-04-08"
  tasks_completed: 3
  files_created: 2
  files_modified: 9
  tests_added: 34
  tests_total: 99
---

# Phase 07 Plan 01: Parser Hardening and Data Types Summary

**One-liner:** Lark singleton caching, structured DVMLParseError with hint catalog, 4 new DVML types (bigint/float/varchar/binary) with optional parameters, and a shared type mapping module (`model/types.py`) consumed by SQL Jinja and Spark generators.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Parser caching tests + new type tests | 1ca43c0 | tests/test_parser.py |
| 1+2 (GREEN) | Parser caching, grammar extension, parse errors | bb19860 | grammar.lark, parser.py, errors.py, main.py, test_cli.py |
| 3 (RED) | Type module tests + Spark e2e tests | 45f2e8b | tests/test_types.py, tests/test_generators.py |
| 3 (GREEN) | Shared type module + Spark generator wiring | 77bab1d | model/types.py, sql_jinja/types.py, spark generator, snapshot |

## What Was Built

### Task 1: Parser Caching and Grammar Extension

- Added `_parser: Lark | None = None` module-level singleton to `parser.py`
- `_get_parser()` now uses `global _parser; if _parser is None: _parser = Lark(...)` — one instance per process
- Extended `grammar.lark` with `type_name` intermediate rule and 4 new terminal aliases: `type_bigint`, `type_float`, `type_varchar`, `type_binary`
- Added optional `("(" type_params ")")?` to `data_type` rule enabling `varchar(100)`, `decimal(10,4)` etc.
- Updated `DVMLTransformer.data_type()` to handle parameter pass-through: `f"{type_name}({params})"`
- Added 4 new transformer methods: `type_bigint`, `type_float`, `type_varchar`, `type_binary`

### Task 2: Structured Parse Errors

- Added `ParseError` dataclass with `file`, `line`, `column`, `hint`, `source_line` fields
- Added `DVMLParseError(Exception)` exception carrying `ParseError` instance
- Added `_HINTS` catalog mapping `frozenset[str]` of expected tokens to friendly messages
- Added `_get_hint()` function dispatching on `UnexpectedToken | UnexpectedCharacters | UnexpectedEOF`
- `parse()` now catches `UnexpectedInput` and raises `DVMLParseError` with structured data
- Updated `format_parse_error()` in `cli/errors.py` to accept `DVMLParseError` and render `{file}:{line}:{col}: error: {hint}`
- Updated `cli/main.py` to catch `DVMLParseError` instead of `UnexpectedInput`

### Task 3: Shared Type Mapping Module

- Created `src/dmjedi/model/types.py` as single source of truth for all type mappings
- `_TYPE_MAP` covers 11 DVML types (7 original + 4 new) across 3 dialects
- `_PYSPARK_MAP` provides PySpark type expressions for all 11 types
- `map_type(dvml_type, dialect)` is parameter-aware: `varchar(100)` → `VARCHAR(100)`, `decimal(10,4)` → `DECIMAL(10,4)`
- `map_pyspark_type(dvml_type)` ignores params for most types, preserves them for `decimal`
- `sql_jinja/types.py` replaced with re-export shim preserving backward compatibility
- Spark generator now imports `map_pyspark_type` and uses `.cast(LongType())` pattern in satellite/link column selects
- Updated `_IMPORTS` constant in Spark generator to include `from pyspark.sql.types import *`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed CLI catch clause for new DVMLParseError**
- **Found during:** Task 1+2 implementation (full suite regression run)
- **Issue:** `cli/main.py` was catching `UnexpectedInput` but `parse_file()` now raises `DVMLParseError` (which does not inherit from `UnexpectedInput`)
- **Fix:** Updated catch clause to `except DVMLParseError as e` and updated `format_parse_error()` call signature (no longer needs `source_file` — already in the error)
- **Files modified:** `src/dmjedi/cli/main.py`
- **Commit:** bb19860

**2. [Rule 1 - Bug] Updated test_cli.py assertions for new error format**
- **Found during:** Task 1+2 implementation
- **Issue:** `test_validate_syntax_error` asserted `"Syntax error"` in output; `test_format_parse_error` checked `isinstance(err, UnexpectedInput)`. Both outdated after format change.
- **Fix:** Updated to check `"error:"` in output (the new structured format); updated `test_format_parse_error` to catch `DVMLParseError` directly
- **Files modified:** `tests/test_cli.py`
- **Commit:** bb19860

**3. [Rule 1 - Bug] Updated integration snapshot for new PySpark types import**
- **Found during:** Task 3 implementation (full suite regression run)
- **Issue:** Spark generator `_IMPORTS` now includes `from pyspark.sql.types import *` — snapshot `hub_customer.py` became stale
- **Fix:** Ran `pytest --snapshot-update` to regenerate snapshot
- **Files modified:** `tests/snapshots/test_integration/test_spark_hub_snapshot/hub_customer.py`
- **Commit:** 77bab1d

**4. [Rule 1 - Bug] Grammar type_params regex: /[^]*)/ → /[^)]+/**
- **Found during:** Task 1 GREEN implementation
- **Issue:** Plan said `type_params: /[^)]*/` but Earley parser rejects zero-width regexps
- **Fix:** Changed to `type_params: /[^)]+/` (one or more chars)
- **Files modified:** `src/dmjedi/lang/grammar.lark`
- **Commit:** bb19860

## Known Stubs

None. All type mappings are fully wired.

## Threat Flags

None. No new network endpoints, auth paths, or trust boundary crossings introduced.

## Test Results

- Tests before: 75 (pre-milestone-2 baseline)
- Tests after: 99 (+24)
- All 99 pass

## Self-Check: PASSED

- src/dmjedi/model/types.py: FOUND
- src/dmjedi/lang/parser.py: FOUND
- tests/test_types.py: FOUND
- Commit 77bab1d: FOUND
- Commit bb19860: FOUND
- All 99 tests passing: CONFIRMED
