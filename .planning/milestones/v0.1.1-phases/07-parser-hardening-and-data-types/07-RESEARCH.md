# Phase 7: Parser Hardening and Data Types - Research

**Researched:** 2026-04-08
**Domain:** Lark grammar extension, Python module-level caching, Rich error formatting, PySpark/SQL type mapping
**Confidence:** HIGH

## Summary

Phase 7 has three tightly-related workstreams that build on an already well-structured codebase: (1) convert the parser singleton from re-creation on every call to a module-level cached instance, (2) improve parse error messages with file/line/column and contextual hints rendered by Rich, and (3) extend the grammar and type system with four new DVML data types and six new entity types.

All three workstreams are low-risk because the existing code provides exact extension points. The parser caching change is a two-line edit to `_get_parser()`. The error formatting infrastructure already exists in `cli/errors.py` — it needs a structured `ParseError` dataclass and contextual hints. The type system already has a three-dialect `_TYPE_MAP` in `sql_jinja/types.py` that needs four new entries and migration to a shared `model/types.py` module that both generators consume.

The grammar extension is the largest piece but was verified to work: Lark Earley handles optional type parameters `(VARCHAR(100))`, rejects unknown types at parse time (D-08), and supports all six new entity grammars (nhsat, nhlink, effsat, samlink, bridge, pit) without ambiguity. The DVMLTransformer and DVMLModule need corresponding new methods and list fields.

**Primary recommendation:** Work in four sequential waves — (1) parser cache, (2) error reporting, (3) data types and shared type module, (4) new entity grammar + AST stubs. Each wave is independently testable.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** DVML supports optional type parameters on any type: `varchar(100)`, `decimal(10,4)`, `float(32)`. Parameters are not required — bare `varchar` is valid.
- **D-02:** Type parameters are stored as string pass-through in the AST (e.g., `data_type = "varchar(100)"`). No structured representation — generators parse the string when needed.
- **D-03:** Grammar allows parameters on any type (not restricted to specific types). Forward-compatible; generators ignore irrelevant params.
- **D-04:** Parse errors render as colored one-liner: `sales.dv:12:5: error: expected "}" after field declaration`. Compact, grep-friendly, CI-compatible.
- **D-05:** Structured error object captures all data: file, line, column, hint, and source line text. One-liner renderer for now; TUI milestone adds multi-line renderer using the same data.
- **D-06:** Contextual hints use curated error messages for common mistakes with expected-token fallback for everything else. Curated message catalog is fixed in the parser layer (not extensible by generators).
- **D-07:** Color output auto-detects TTY (disabled when piped). `--no-color` flag for explicit override. Rich handles this natively.
- **D-08:** Grammar only accepts known DVML types. Unrecognized types are a parse error with a hint listing valid types. Strict approach catches typos at parse time.
- **D-09:** Phase 7 adds full grammar rules for all 6 new entity types (nhsat, nhlink, effsat, samlink, bridge, pit) with their body syntax (of, master/duplicate, path, tracks).
- **D-10:** Full vertical slice: grammar rules + AST node definitions (Pydantic models) + transformer methods + DVMLModule fields. A `.dv` file with `nhsat` parses into a real AST node. Resolver/generators skip unknown node types until their respective phases.
- **D-11:** Each entity gets explicit, self-contained grammar rules and transformer methods. No shared body patterns — some duplication is acceptable for testability and clarity.
- **D-12:** Create a shared type mapping module (e.g., `model/types.py`) used by both SQL Jinja and Spark generators. Single source of truth for DVML type to target type mappings.
- **D-13:** The shared module is parameter-aware: it parses type strings like `varchar(100)` and returns the correct target representation with parameters applied. Generators call one function.
- **D-14:** Module-level singleton for Lark parser instance. Simple `_parser = None`, created on first call, reused forever. Matches existing module-level pattern (`_GRAMMAR_PATH`).
- **D-15:** Default type parameters are defined in the shared type module, not per generator or in the grammar. Single source of truth for defaults.
- **D-16:** Bare `varchar` defaults to `VARCHAR(255)` in SQL (matching existing `string` mapping). Other defaults follow industry standard conventions.

### Claude's Discretion

- Exact structure of the curated error message catalog
- PySpark type representations for new types (StringType, LongType, etc.)
- Exact default values for `bigint`, `float`, `binary` across dialects
- Internal naming of the shared type module

### Deferred Ideas (OUT OF SCOPE)

- Multi-line error display with source context and caret — TUI milestone
- Thread-local parser caching for LSP server parallel parsing — LSP milestone
- Extensible error catalog for generator-specific errors — future milestone
- Flexible/pass-through type handling (accept any identifier as type) — not planned
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PARSE-01 | Parser caches Lark instance as singleton instead of creating per call | D-14 confirmed; two-line edit to `_get_parser()` using module-level `_parser = None` pattern already used for `_GRAMMAR_PATH` |
| PARSE-02 | Parse errors include source file, line, column, and contextual hint | `cli/errors.py` already has `format_parse_error()`; needs structured `ParseError` dataclass + hint catalog; Rich `Console(no_color=True)` handles D-07 |
| PARSE-03 | Parser handles all new entity keywords without grammar ambiguity | Verified: all 6 entity grammars parse without ambiguity in Lark Earley; requires updating `statement` alternatives and adding 6 grammar rules |
| TYPE-01 | User can use `bigint`, `float`, `varchar`, `binary` data types in field declarations | Requires grammar extension with 4 new type keywords + optional params; Earley handles optional `(params)` suffix; unknown types rejected (D-08) |
| TYPE-02 | SQL Jinja generator maps new data types correctly per dialect (default, postgres, spark) | `_TYPE_MAP` in `sql_jinja/types.py` migrates to `model/types.py`; 4 new type entries added; parameter-aware `map_type()` needed (D-13) |
| TYPE-03 | Spark Declarative generator maps new data types to PySpark types | Spark generator currently has NO type mapping; new shared module adds PySpark column in type map or separate mapping function |
</phase_requirements>

---

## Standard Stack

### Core (already declared in pyproject.toml)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| lark | 1.3.1 [VERIFIED: uv run] | Grammar definition, Earley parser | Project's established parser; Earley handles ambiguous/context-sensitive grammars well |
| pydantic | ≥2.0 [VERIFIED: pyproject.toml] | AST and domain model nodes | Project standard for all models |
| rich | 14.3.3 [VERIFIED: uv run] | Colored terminal output, TTY detection | Already a dependency; `Console(no_color=True)` and `color_system="auto"` (TTY-aware by default) |

### No New Dependencies

This phase requires zero new package installations. All required libraries are already declared in `pyproject.toml`. [VERIFIED: pyproject.toml]

## Architecture Patterns

### Recommended File Changes

```
src/dmjedi/
├── lang/
│   ├── grammar.lark          # Add 4 type keywords + params, 6 entity rules
│   ├── parser.py             # Module-level cache; ParseError dataclass; hint catalog
│   └── ast.py                # 6 new *Decl Pydantic models; extend DVMLModule
├── model/
│   ├── types.py              # NEW: shared type mapping (migrated from sql_jinja/types.py)
│   └── core.py               # 6 new domain model stubs (optional — see note)
└── generators/
    ├── sql_jinja/
    │   └── types.py          # Replaced by import from model/types.py
    └── spark_declarative/
        └── generator.py      # Import map_type from model/types.py
```

**Note on `model/core.py`:** D-10 says "Resolver/generators skip unknown node types until their respective phases." Phase 7 only needs AST nodes (in `lang/ast.py`), not domain model nodes (in `model/core.py`). Domain model nodes are added in Phases 8-10 when the resolver is extended for each entity type.

### Pattern 1: Module-Level Parser Cache (PARSE-01)

**What:** Replace per-call `Lark(...)` construction with a module-level `_parser` sentinel that is initialized once.

**Current code (parser.py lines 21-26):**
```python
# BEFORE — creates new Lark instance on every call
def _get_parser() -> Lark:
    return Lark(
        _GRAMMAR_PATH.read_text(),
        parser="earley",
        propagate_positions=True,
    )
```

**After:**
```python
# Source: D-14, verified against module-level _GRAMMAR_PATH pattern in parser.py
_parser: Lark | None = None

def _get_parser() -> Lark:
    global _parser
    if _parser is None:
        _parser = Lark(
            _GRAMMAR_PATH.read_text(),
            parser="earley",
            propagate_positions=True,
        )
    return _parser
```

**Verified:** Module-level singleton pattern with `global` works correctly in Python — two calls to `_get_parser()` return `is`-equal objects. [VERIFIED: uv run python -c "..."]

### Pattern 2: Structured Parse Error (PARSE-02)

**What:** A `ParseError` dataclass in `lang/parser.py` (or `cli/errors.py`) captures all structured data. The one-liner renderer in `cli/errors.py` consumes it.

**Existing infrastructure:**
- `SourceLocation` in `ast.py` already captures `file`, `line`, `column`
- `LintDiagnostic` in `linter.py` is the design template (`@dataclass` with message/severity/loc/rule)
- `format_parse_error()` in `cli/errors.py` already handles `UnexpectedToken` / `UnexpectedCharacters`

**Proposed `ParseError` dataclass (lang/parser.py):**
```python
# Source: inspired by LintDiagnostic pattern in lang/linter.py
from dataclasses import dataclass

@dataclass
class ParseError:
    file: str
    line: int
    column: int
    hint: str
    source_line: str = ""  # reserved for TUI milestone, not used in renderer yet
```

**Lark exception attribute map (VERIFIED: uv run):**

| Exception class | `.line` | `.column` | `.char` | `.token` | `.expected` | `.accepts` |
|-----------------|---------|-----------|---------|----------|-------------|------------|
| `UnexpectedCharacters` | int | int | str | — | — | — |
| `UnexpectedToken` | int | int | — | Token | set[str] | — |
| `UnexpectedEOF` | -1 | -1 | — | Token | list[str] | — |

**Note:** `UnexpectedEOF.line` returns -1. The renderer must guard against this (display "end of file" or line 0). [VERIFIED: uv run]

### Pattern 3: Contextual Hint Catalog (D-06)

**What:** A dict mapping `frozenset[str]` of expected tokens to human-readable hint strings. Falls back to generic "expected: {tokens}" for unmatched cases.

**Curated hints (Claude's discretion — recommended catalog):**
```python
# Source: [ASSUMED] — common Lark error patterns for DVML grammar
_HINTS: dict[frozenset[str], str] = {
    frozenset({"RBRACE", "IDENTIFIER"}): 'expected field declaration or "}" to close block',
    frozenset({"RBRACE"}): 'expected "}" to close block',
    frozenset({"COLON"}): 'expected ":" after field name',
    frozenset({"LBRACE"}): 'expected "{" to open entity body',
}
```

**Fallback:** `f'expected one of: {", ".join(sorted(tokens))}'`

**How to derive hint:** In `format_parse_error()`, check `UnexpectedToken.expected` or `UnexpectedCharacters.allowed` against the catalog. Use `match_examples()` only if the catalog approach is insufficient (adds complexity, not needed here).

### Pattern 4: Grammar Extension for Type Parameters (TYPE-01)

**What:** Extend `data_type` rule in grammar to accept optional `(params)` suffix. List all known types as keyword alternatives.

**Verified grammar pattern (Lark Earley):**
```lark
// Source: verified with uv run python grammar test
data_type: type_name ("(" type_params ")")?

type_name: "int"       -> type_int
         | "string"    -> type_string
         | "decimal"   -> type_decimal
         | "date"      -> type_date
         | "timestamp" -> type_timestamp
         | "boolean"   -> type_boolean
         | "json"      -> type_json
         | "bigint"    -> type_bigint
         | "float"     -> type_float
         | "varchar"   -> type_varchar
         | "binary"    -> type_binary

type_params: /[^)]+/
```

**Key constraint:** Earley dynamic mode prohibits zero-width regexps — use `/[^)]+/` (one or more), not `/[^)]*/` (zero or more). [VERIFIED: uv run]

**Transformer changes:** Add `type_bigint`, `type_float`, `type_varchar`, `type_binary` methods. Update `data_type()` to build the full string `"varchar(100)"` when params are present. [ASSUMED: parameter concatenation approach]

**String assembly in transformer:**
```python
# Source: [ASSUMED] — consistent with D-02 (string pass-through)
def data_type(self, tree: object) -> str:
    children = tree.children  # type: ignore[union-attr]
    type_name = children[0]   # str from type_name alias
    if len(children) > 1:
        params = str(children[1])  # type_params token
        return f"{type_name}({params})"
    return type_name
```

### Pattern 5: Shared Type Module (TYPE-02, TYPE-03, D-12/D-13)

**What:** `model/types.py` becomes the single source of truth. It contains the full type map and a parameter-aware `map_type()` function. Both generators import from it.

**Current `sql_jinja/types.py` structure to migrate and extend:**
```python
# VERIFIED: src/dmjedi/generators/sql_jinja/types.py
_TYPE_MAP: dict[str, dict[str, str]] = {
    "int":       {"default": "INT",          "postgres": "INTEGER",     "spark": "INT"},
    "string":    {"default": "VARCHAR(255)",  "postgres": "TEXT",        "spark": "STRING"},
    "decimal":   {"default": "DECIMAL(18,2)", "postgres": "NUMERIC(18,2)","spark": "DECIMAL(18,2)"},
    "date":      {"default": "DATE",          "postgres": "DATE",        "spark": "DATE"},
    "timestamp": {"default": "TIMESTAMP",     "postgres": "TIMESTAMP",   "spark": "TIMESTAMP"},
    "boolean":   {"default": "BOOLEAN",       "postgres": "BOOLEAN",     "spark": "BOOLEAN"},
    "json":      {"default": "JSON",          "postgres": "JSONB",       "spark": "STRING"},
}
```

**New entries to add (D-15/D-16, Claude's discretion for exact values):**

| DVML type | default | postgres | spark | PySpark | Rationale |
|-----------|---------|----------|-------|---------|-----------|
| `bigint` | `BIGINT` | `BIGINT` | `BIGINT` | `LongType()` | Standard SQL across all dialects [ASSUMED] |
| `float` | `FLOAT` | `DOUBLE PRECISION` | `FLOAT` | `FloatType()` | Postgres uses `DOUBLE PRECISION` for float8 [ASSUMED] |
| `varchar` | `VARCHAR(255)` | `VARCHAR(255)` | `STRING` | `StringType()` | D-16: bare varchar defaults to VARCHAR(255); Spark has no varchar, maps to STRING [ASSUMED] |
| `binary` | `BINARY` | `BYTEA` | `BINARY` | `BinaryType()` | Postgres uses BYTEA for binary data [ASSUMED] |

**Parameter-aware map_type() (D-13):**
```python
# Source: [ASSUMED] — consistent with D-02 and D-13
import re

_PARAM_RE = re.compile(r'^(\w+)\(([^)]*)\)$')

def map_type(dvml_type: str, dialect: str = "default") -> str:
    """Map a DVML type string (possibly with params) to a SQL type."""
    m = _PARAM_RE.match(dvml_type)
    if m:
        base, params = m.group(1).lower(), m.group(2)
        entry = _TYPE_MAP.get(base)
        if entry:
            base_sql = entry.get(dialect, entry["default"])
            # Strip default params from base_sql, apply user params
            base_sql_no_params = re.sub(r'\([^)]*\)', '', base_sql)
            return f"{base_sql_no_params}({params})"
        return f"{base.upper()}({params})"
    type_entry = _TYPE_MAP.get(dvml_type.lower())
    if type_entry is None:
        return dvml_type.upper()
    return type_entry.get(dialect, type_entry["default"])
```

**PySpark mapping:** The Spark generator currently does NOT use `map_type()` for column types. It only calls `F.col()` on column names — it doesn't emit `StructType` schemas. The "PySpark type" requirement (TYPE-03) means the shared module needs a `pyspark` key in the type map so that if/when schemas are generated, the mapping exists. For Phase 7 the simplest approach: add `pyspark` as a fourth dialect in `_TYPE_MAP` without wiring it into the generator yet — or alternatively, add a separate `_PYSPARK_MAP` dict in `model/types.py`. [ASSUMED: pyspark as fourth dialect is simpler — one map_type() call covers all four targets]

### Pattern 6: New Entity Grammar Rules (PARSE-03, D-09/D-10/D-11)

**All six verified in isolation (VERIFIED: uv run):**

```lark
// nhsat — non-historized satellite (like satellite but no timeline)
nhsat_decl: "nhsat" IDENTIFIER "of" qualified_ref "{" sat_body "}"

// nhlink — non-historized link
nhlink_decl: "nhlink" IDENTIFIER "{" link_body "}"

// effsat — effectivity satellite (attached to a link)
effsat_decl: "effsat" IDENTIFIER "of" qualified_ref "{" sat_body "}"

// samlink — same-as link (master/duplicate pattern)
samlink_decl: "samlink" IDENTIFIER "{" samlink_body "}"
samlink_body: samlink_member*
samlink_member: "master" qualified_ref | "duplicate" qualified_ref | field_decl

// bridge — cross-hub query assist
bridge_decl: "bridge" IDENTIFIER "{" bridge_body "}"
bridge_body: bridge_member*
bridge_member: "path" path_chain | field_decl
path_chain: qualified_ref ("->" qualified_ref)+

// pit — point-in-time query assist
pit_decl: "pit" IDENTIFIER "{" pit_body "}"
pit_body: pit_member*
pit_member: "of" qualified_ref | "tracks" qualified_ref ("," qualified_ref)* | field_decl
```

**Add all six to `statement` rule alternatives.**

**AST nodes to add (D-10, following `*Decl` pattern):**

```python
# Source: consistent with existing pattern in lang/ast.py

class NhSatDecl(BaseModel):
    name: str
    parent_ref: str
    fields: list[FieldDef] = []
    loc: SourceLocation = SourceLocation()

class NhLinkDecl(BaseModel):
    name: str
    references: list[str] = []
    fields: list[FieldDef] = []
    loc: SourceLocation = SourceLocation()

class EffSatDecl(BaseModel):
    name: str
    parent_ref: str      # must be a link — enforced by linter in Phase 9
    fields: list[FieldDef] = []
    loc: SourceLocation = SourceLocation()

class SamLinkDecl(BaseModel):
    name: str
    master_ref: str
    duplicate_ref: str
    fields: list[FieldDef] = []
    loc: SourceLocation = SourceLocation()

class BridgeDecl(BaseModel):
    name: str
    path: list[str] = []  # ordered list of entity refs
    fields: list[FieldDef] = []
    loc: SourceLocation = SourceLocation()

class PitDecl(BaseModel):
    name: str
    anchor_ref: str           # the hub this PIT is anchored to
    tracked_satellites: list[str] = []
    fields: list[FieldDef] = []
    loc: SourceLocation = SourceLocation()
```

**DVMLModule additions:**
```python
# Add to DVMLModule in lang/ast.py
nhsats: list[NhSatDecl] = []
nhlinks: list[NhLinkDecl] = []
effsats: list[EffSatDecl] = []
samlinks: list[SamLinkDecl] = []
bridges: list[BridgeDecl] = []
pits: list[PitDecl] = []
```

**Transformer `start()` additions:**
```python
# Add to DVMLTransformer.start() dispatch in parser.py
elif isinstance(item, NhSatDecl):
    module.nhsats.append(item)
# ... etc for all 6 types
```

### Anti-Patterns to Avoid

- **Shared body rules between entity types:** D-11 explicitly forbids it. Write self-contained `nhsat_decl`, `effsat_decl`, etc. even if bodies look similar.
- **Zero-width regexp in Earley grammar:** Use `/[^)]+/` not `/[^)]*/` for `type_params`. [VERIFIED]
- **Mutating grammar at runtime:** Cache is built from the grammar string at first call. Grammar changes must be in the `.lark` file — never patch Lark after creation.
- **Rendering errors without structuring first:** Always populate `ParseError` dataclass before rendering. The renderer is a thin one-liner over the dataclass.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TTY detection for color | Custom `sys.stdout.isatty()` check | `rich.Console(color_system="auto")` | Rich handles Windows/pipe/CI/NO_COLOR env correctly [VERIFIED: rich 14.3.3] |
| Parser construction | New `Lark(...)` each call | Module-level `_parser` singleton | Lark Earley construction is expensive; singleton pattern established in codebase |
| Type parameter parsing | Custom regex per generator | Single `_PARAM_RE` in `model/types.py` | One regex, one place; generators just call `map_type()` |
| Grammar ambiguity resolution | Custom disambiguation code | Lark Earley (already chosen) | Earley handles context-sensitive grammars; the grammar was verified ambiguity-free |

**Key insight:** The existing codebase already made the right tool choices. This phase is extension, not invention.

## Common Pitfalls

### Pitfall 1: `UnexpectedEOF.line` Returns -1
**What goes wrong:** EOF errors report `line=-1`, `column=-1`. Rendering `file:-1:-1: error:` looks broken.
**Why it happens:** Lark has no line info when input ends unexpectedly — there is no character at which to point.
**How to avoid:** In `format_parse_error()`, guard with `if line < 0: line_str = "end of file"` or similar.
**Warning signs:** Test with an unterminated block `hub Foo {` — check the rendered error string.

### Pitfall 2: Grammar Cache Must Not Be Invalidated Between Tests
**What goes wrong:** If tests mutate the module-level `_parser`, other tests get stale or inconsistent instances.
**Why it happens:** Module-level state persists across tests unless reset.
**How to avoid:** The parser is read-only after creation — never reassign `_parser` after initialization. Tests that need a fresh parser can call `_parser = None` in a fixture teardown, but this should be rare.
**Warning signs:** Tests that pass individually but fail when run together.

### Pitfall 3: Existing `map_type()` Has `binary` as Unknown Passthrough
**What goes wrong:** `test_sql_type_mapping_unknown_passthrough` asserts `map_type("binary") == "BINARY"` (passthrough behavior). After adding `binary` to `_TYPE_MAP`, this test will fail.
**Why it happens:** Test was written when `binary` was not a DVML type.
**How to avoid:** Update the test to `assert map_type("binary") == "BINARY"` (same result, but now from the map, not passthrough). Also move the test to the new type module tests.
**Warning signs:** `test_sql_type_mapping_unknown_passthrough` failure after type map migration.

### Pitfall 4: SQL Jinja Templates May Hardcode Type Strings
**What goes wrong:** If SQL Jinja Jinja2 templates call `map_type()` or format types inline, migrating to `model/types.py` might break import paths.
**Why it happens:** There are two layers — the Python generator calls `map_type()`, which feeds types into Jinja2 templates.
**How to avoid:** Verify that all type mapping calls flow through `map_type()` (not template literals). Check `sql_jinja/generator.py` and all `.sql.j2` templates.
**Warning signs:** Tests that test SQL output pass but wrong dialect types appear.

### Pitfall 5: `pit_body` `tracks` Rule With Trailing Comma
**What goes wrong:** If `tracks` grammar allows trailing comma, parser may fail on `tracks Sat1, Sat2` without trailing comma, or vice versa.
**Why it happens:** Comma-separated lists in Lark need explicit grammar — no trailing comma by default.
**How to avoid:** Use `qualified_ref ("," qualified_ref)*` (no trailing comma). Add a regression test for `tracks Sat1, Sat2` and `tracks Sat1` (single item).

## Code Examples

### Parser Singleton (PARSE-01)
```python
# Source: module-level pattern from parser.py _GRAMMAR_PATH
_GRAMMAR_PATH = Path(__file__).parent / "grammar.lark"
_parser: Lark | None = None

def _get_parser() -> Lark:
    global _parser
    if _parser is None:
        _parser = Lark(
            _GRAMMAR_PATH.read_text(),
            parser="earley",
            propagate_positions=True,
        )
    return _parser
```

### ParseError Dataclass and Renderer (PARSE-02)
```python
# Source: LintDiagnostic pattern from lang/linter.py
from dataclasses import dataclass

@dataclass
class ParseError:
    file: str
    line: int
    column: int
    hint: str
    source_line: str = ""  # populated for future TUI renderer


def _make_parse_error(err: UnexpectedInput, source_file: str) -> ParseError:
    line: int = max(0, getattr(err, "line", 0))  # guard UnexpectedEOF -1
    col: int = max(0, getattr(err, "column", 0))
    hint = _get_hint(err)
    return ParseError(file=source_file, line=line, column=col, hint=hint)


def format_parse_error(err: UnexpectedInput, source_file: str) -> str:
    """One-liner renderer. Returns Rich markup string."""
    pe = _make_parse_error(err, source_file)
    loc = f"{pe.file}:{pe.line}:{pe.column}" if pe.line > 0 else f"{pe.file}:end-of-file"
    return f"[red]{loc}: error:[/red] {pe.hint}"
```

### Shared Type Module Skeleton (TYPE-02, TYPE-03)
```python
# Source: migrated from generators/sql_jinja/types.py, extended per D-12/D-15/D-16
# model/types.py

import re
from __future__ import annotations

_TYPE_MAP: dict[str, dict[str, str]] = {
    # existing 7 types ...
    "bigint":    {"default": "BIGINT",        "postgres": "BIGINT",           "spark": "BIGINT",   "pyspark": "LongType()"},
    "float":     {"default": "FLOAT",         "postgres": "DOUBLE PRECISION", "spark": "FLOAT",    "pyspark": "FloatType()"},
    "varchar":   {"default": "VARCHAR(255)",  "postgres": "VARCHAR(255)",     "spark": "STRING",   "pyspark": "StringType()"},
    "binary":    {"default": "BINARY",        "postgres": "BYTEA",            "spark": "BINARY",   "pyspark": "BinaryType()"},
}

SUPPORTED_DIALECTS = ["default", "postgres", "spark", "pyspark"]

_PARAM_RE = re.compile(r'^(\w+)\(([^)]*)\)$')


def map_type(dvml_type: str, dialect: str = "default") -> str:
    """Map a DVML type string (with optional params) to a target type."""
    m = _PARAM_RE.match(dvml_type)
    if m:
        base, params = m.group(1).lower(), m.group(2)
        entry = _TYPE_MAP.get(base)
        if entry:
            base_sql = entry.get(dialect, entry["default"])
            base_sql_no_params = re.sub(r'\([^)]*\)', '', base_sql)
            return f"{base_sql_no_params}({params})"
        return f"{base.upper()}({params})"
    entry = _TYPE_MAP.get(dvml_type.lower())
    if entry is None:
        return dvml_type.upper()
    return entry.get(dialect, entry["default"])
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| New Lark instance per `parse()` call | Module-level singleton | This phase | No external API change; `parse()` and `parse_file()` signatures unchanged |
| Raw `UnexpectedInput` string in `format_parse_error()` | Structured `ParseError` dataclass + hint catalog | This phase | CLI output format changes to `file:line:col: error: hint` |
| `_TYPE_MAP` only in `sql_jinja/types.py` | Shared `model/types.py` consumed by both generators | This phase | `sql_jinja/types.py` becomes a thin re-export or deleted; Spark gains type mapping |
| 7 DVML types | 11 DVML types (+ bigint, float, varchar, binary) | This phase | `.dv` files using new types become valid; old files unchanged |
| 3 entity types in grammar | 9 entity types (+ 6 new) | This phase | New entities parse to AST stubs; resolver/generators silently ignore in Phase 7 |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `bigint` maps to `BIGINT` across default/postgres/spark SQL dialects | Standard Stack / Code Examples | Low — BIGINT is universal SQL; would only affect test assertions |
| A2 | `float` maps to `DOUBLE PRECISION` in postgres dialect | Standard Stack / Code Examples | Medium — postgres has `REAL` (4-byte) and `DOUBLE PRECISION` (8-byte); if user means 4-byte float, wrong mapping |
| A3 | `binary` maps to `BYTEA` in postgres dialect | Standard Stack / Code Examples | Low — BYTEA is the only postgres binary type |
| A4 | `varchar` maps to `STRING` in Spark SQL dialect | Standard Stack / Code Examples | Low — Spark SQL does not support VARCHAR, STRING is the correct mapping |
| A5 | PySpark types: `LongType()`, `FloatType()`, `StringType()`, `BinaryType()` for the four new types | Code Examples | Low — these are standard PySpark DataTypes; risk is import path if generator uses `pyspark.sql.types` |
| A6 | Parameter-aware `map_type()` strips existing default params and replaces with user params | Code Examples | Medium — edge case: `decimal(10,4)` with postgres dialect gives `NUMERIC(10,4)` — this is the desired behavior, but the regex sub approach needs testing |
| A7 | `type_params` transformer returns the token string directly without further transformation | Architecture Patterns | Low — Lark token strings are just Python strings; D-02 confirms string pass-through |
| A8 | The curated hint catalog keys on `frozenset` of expected token names | Architecture Patterns | Low — Lark's `UnexpectedToken.expected` is a set of terminal names; this approach is standard |

## Open Questions

1. **Should `sql_jinja/types.py` be deleted or become a thin re-export?**
   - What we know: `test_generators.py` imports `from dmjedi.generators.sql_jinja.types import map_type` directly
   - What's unclear: Whether to keep the old import path for backwards compatibility or update all tests
   - Recommendation: Keep `sql_jinja/types.py` as a thin re-export (`from dmjedi.model.types import map_type, SUPPORTED_DIALECTS`) to avoid touching test_generators.py imports

2. **Does the Spark generator need to emit `StructType` schemas in Phase 7 for TYPE-03?**
   - What we know: Current spark generator uses `F.col(name)` — no type info in generated code; `pyspark` dialect in the type map would exist but not be called by any generator
   - What's unclear: Whether TYPE-03 success criterion requires the type map to be *used* or just *defined*
   - Recommendation: Add `pyspark` as a fourth dialect key to `_TYPE_MAP` in `model/types.py` so the mapping is defined. The success criterion says "maps new data types to PySpark types" — interpret this as the map existing and being tested, not necessarily called by the generator in Phase 7.

## Environment Availability

Step 2.6: SKIPPED — no external dependencies identified. All required tools (lark, rich, pydantic, pytest) are already installed in the project virtualenv. [VERIFIED: uv run]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/test_parser.py tests/test_generators.py -x -q` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PARSE-01 | `_get_parser()` called twice returns same `Lark` instance | unit | `uv run pytest tests/test_parser.py::test_parser_singleton -x` | ❌ Wave 0 |
| PARSE-02 | Parse error on `hub Foo { bad_field : unknowntype }` includes filename, line, col, hint | unit | `uv run pytest tests/test_parser.py::test_parse_error_format -x` | ❌ Wave 0 |
| PARSE-02 | `UnexpectedEOF` (missing `}`) renders with "end of file" location, not -1 | unit | `uv run pytest tests/test_parser.py::test_parse_error_eof -x` | ❌ Wave 0 |
| PARSE-03 | `.dv` file with `nhsat Foo of Customer { name: string }` parses to `NhSatDecl` | unit | `uv run pytest tests/test_parser.py::test_parse_nhsat -x` | ❌ Wave 0 |
| PARSE-03 | All 6 new entity types parse without error | unit | `uv run pytest tests/test_parser.py -k "nhsat or nhlink or effsat or samlink or bridge or pit" -x` | ❌ Wave 0 |
| TYPE-01 | Fields with `bigint`, `float`, `varchar`, `binary` parse to correct `data_type` strings | unit | `uv run pytest tests/test_parser.py::test_parse_new_data_types -x` | ❌ Wave 0 |
| TYPE-01 | `varchar(100)` parses to `data_type="varchar(100)"` | unit | `uv run pytest tests/test_parser.py::test_parse_type_with_params -x` | ❌ Wave 0 |
| TYPE-01 | Unknown type `badtype` raises parse error | unit | `uv run pytest tests/test_parser.py::test_parse_unknown_type_error -x` | ❌ Wave 0 |
| TYPE-02 | `map_type("bigint")` returns `"BIGINT"`, postgres `"BIGINT"`, spark `"BIGINT"` | unit | `uv run pytest tests/test_generators.py::test_sql_type_mapping_new_types -x` | ❌ Wave 0 |
| TYPE-02 | `map_type("varchar(50)")` returns `"VARCHAR(50)"` (user params respected) | unit | `uv run pytest tests/test_generators.py::test_sql_type_mapping_with_params -x` | ❌ Wave 0 |
| TYPE-03 | `model/types.py` defines `pyspark` dialect for all 11 DVML types | unit | `uv run pytest tests/test_generators.py::test_pyspark_type_mapping -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_parser.py tests/test_generators.py -x -q`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_parser.py` — add: `test_parser_singleton`, `test_parse_error_format`, `test_parse_error_eof`, `test_parse_nhsat`, `test_parse_nhlink`, `test_parse_effsat`, `test_parse_samlink`, `test_parse_bridge`, `test_parse_pit`, `test_parse_new_data_types`, `test_parse_type_with_params`, `test_parse_unknown_type_error`
- [ ] `tests/test_generators.py` — add: `test_sql_type_mapping_new_types`, `test_sql_type_mapping_with_params`, `test_pyspark_type_mapping`; update `test_sql_type_mapping_unknown_passthrough` (binary is now a known type)
- [ ] `tests/test_types.py` — optional: dedicated test module for `model/types.py` if `test_generators.py` grows too large

## Security Domain

No security-relevant changes in this phase. The parser processes trusted local `.dv` files with no network exposure, user authentication, session state, cryptography, or input that flows to external systems. Input validation in scope (grammar rejects unknown types) is covered by the functional tests above.

## Sources

### Primary (HIGH confidence)
- Lark 1.3.1 source code and exception attributes — verified via `uv run python` REPL
- `src/dmjedi/lang/grammar.lark` — current grammar, read directly
- `src/dmjedi/lang/parser.py` — current parser structure, read directly
- `src/dmjedi/lang/ast.py` — current AST nodes, read directly
- `src/dmjedi/generators/sql_jinja/types.py` — current type map, read directly
- `src/dmjedi/generators/spark_declarative/generator.py` — current spark generator, read directly
- `src/dmjedi/cli/errors.py` — existing error formatting, read directly
- `src/dmjedi/cli/main.py` — CLI wiring, read directly
- `pyproject.toml` — declared dependencies, read directly
- Grammar and exception behavior — verified with live `uv run python` calls in project venv

### Secondary (MEDIUM confidence)
- Rich 14.3.3 `Console.__init__` signature — verified via `inspect.signature` in project venv; `no_color` and `color_system="auto"` confirmed

### Tertiary (LOW confidence — see Assumptions Log)
- SQL type mappings for new types (bigint, float, binary, varchar per dialect) — [ASSUMED] based on standard SQL conventions
- PySpark DataType names — [ASSUMED] based on training knowledge; should be verified against pyspark.sql.types docs if Spark schema generation is exercised

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified in live venv, no new dependencies
- Architecture: HIGH — all patterns verified against actual source code; grammar patterns confirmed with live Lark tests
- Pitfalls: MEDIUM — structural pitfalls verified (EOF line=-1, zero-width regexp); type mapping defaults are ASSUMED
- Type defaults: LOW — exact SQL type defaults for new types not verified against official SQL standards

**Research date:** 2026-04-08
**Valid until:** 2026-05-08 (stable stack, 30-day window)
