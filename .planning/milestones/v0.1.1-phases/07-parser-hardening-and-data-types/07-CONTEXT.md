# Phase 7: Parser Hardening and Data Types - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Harden the parser foundation (caching, error messages) and extend the type system with `bigint`, `float`, `varchar`, `binary` before adding new entities. Add full grammar rules and stub AST nodes for all 6 new entity types (nhsat, nhlink, effsat, samlink, bridge, pit) so Phases 8-10 can focus on resolver/generator work.

</domain>

<decisions>
## Implementation Decisions

### Data Type Parameters
- **D-01:** DVML supports optional type parameters on any type: `varchar(100)`, `decimal(10,4)`, `float(32)`. Parameters are not required — bare `varchar` is valid.
- **D-02:** Type parameters are stored as string pass-through in the AST (e.g., `data_type = "varchar(100)"`). No structured representation — generators parse the string when needed.
- **D-03:** Grammar allows parameters on any type (not restricted to specific types). Forward-compatible; generators ignore irrelevant params.

### Error Message Format
- **D-04:** Parse errors render as colored one-liner: `sales.dv:12:5: error: expected "}" after field declaration`. Compact, grep-friendly, CI-compatible.
- **D-05:** Structured error object captures all data: file, line, column, hint, and source line text. One-liner renderer for now; TUI milestone adds multi-line renderer using the same data.
- **D-06:** Contextual hints use curated error messages for common mistakes with expected-token fallback for everything else. Curated message catalog is fixed in the parser layer (not extensible by generators).
- **D-07:** Color output auto-detects TTY (disabled when piped). `--no-color` flag for explicit override. Rich handles this natively.

### Unknown Type Handling
- **D-08:** Grammar only accepts known DVML types. Unrecognized types are a parse error with a hint listing valid types. Strict approach catches typos at parse time.

### New Entity Keywords
- **D-09:** Phase 7 adds full grammar rules for all 6 new entity types (nhsat, nhlink, effsat, samlink, bridge, pit) with their body syntax (of, master/duplicate, path, tracks).
- **D-10:** Full vertical slice: grammar rules + AST node definitions (Pydantic models) + transformer methods + DVMLModule fields. A `.dv` file with `nhsat` parses into a real AST node. Resolver/generators skip unknown node types until their respective phases.
- **D-11:** Each entity gets explicit, self-contained grammar rules and transformer methods. No shared body patterns — some duplication is acceptable for testability and clarity.

### Spark Type Mapping Strategy
- **D-12:** Create a shared type mapping module (e.g., `model/types.py`) used by both SQL Jinja and Spark generators. Single source of truth for DVML type to target type mappings.
- **D-13:** The shared module is parameter-aware: it parses type strings like `varchar(100)` and returns the correct target representation with parameters applied. Generators call one function.

### Parser Caching
- **D-14:** Module-level singleton for Lark parser instance. Simple `_parser = None`, created on first call, reused forever. Matches existing module-level pattern (`_GRAMMAR_PATH`).

### Default Type Parameter Values
- **D-15:** Default type parameters are defined in the shared type module, not per generator or in the grammar. Single source of truth for defaults.
- **D-16:** Bare `varchar` defaults to `VARCHAR(255)` in SQL (matching existing `string` mapping). Other defaults follow industry standard conventions.

### Claude's Discretion
- Exact structure of the curated error message catalog
- PySpark type representations for new types (StringType, LongType, etc.)
- Exact default values for `bigint`, `float`, `binary` across dialects
- Internal naming of the shared type module

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Parser and Grammar
- `src/dmjedi/lang/grammar.lark` -- Current Lark grammar with 7 data types and 3 entity types
- `src/dmjedi/lang/parser.py` -- Parser with `_get_parser()` (caching target) and `DVMLTransformer`
- `src/dmjedi/lang/ast.py` -- AST node definitions (Pydantic models) to extend with 6 new entity types

### Type System
- `src/dmjedi/generators/sql_jinja/types.py` -- Current `_TYPE_MAP` with 3-dialect SQL mappings (to be migrated to shared module)
- `src/dmjedi/generators/spark_declarative/generator.py` -- Spark generator with NO type mapping (needs PySpark types)

### Model Layer
- `src/dmjedi/model/core.py` -- Domain model classes (Hub, Satellite, Link, Column, DataVaultModel) to extend
- `src/dmjedi/model/resolver.py` -- Resolver that merges AST modules into DataVaultModel

### Requirements
- `.planning/REQUIREMENTS.md` -- PARSE-01, PARSE-02, PARSE-03, TYPE-01, TYPE-02, TYPE-03

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_TYPE_MAP` in `sql_jinja/types.py`: 7-type mapping dict with 3 dialects — good template for the shared module
- `SourceLocation` in `ast.py`: Already captures file/line/column — extend for error reporting
- `LintDiagnostic` pattern: Structured diagnostic with severity/rule/location — error object can follow similar design
- Rich library: Already a declared dependency, unused — available for colored output

### Established Patterns
- Lark `@v_args(tree=True)` transformer with `type_*` methods per data type
- Pydantic `BaseModel` for all AST nodes with `SourceLocation` field
- Module-level private state (`_REGISTRY`, `_GRAMMAR_PATH`) — same pattern for parser cache
- `*Decl` suffix for AST nodes, bare names for domain model

### Integration Points
- `DVMLModule` fields: currently `hubs`, `satellites`, `links` — add 6 new entity lists
- `parse()` / `parse_file()` public API: error wrapping goes here
- `_get_parser()`: caching target
- Generator `generate()` methods: will need to handle new entity types (Phases 8-10)
- `statement` grammar rule: add new entity types to the alternatives list

</code_context>

<specifics>
## Specific Ideas

- Error messages should prepare for a future TUI milestone — store all data in structured object, render minimally now
- Multi-line error display (source line + caret) deferred to TUI milestone to stay focused
- Shared type module eliminates the current `_TYPE_MAP` in sql_jinja/types.py — SQL Jinja generator should be migrated to use the shared module

</specifics>

<deferred>
## Deferred Ideas

- Multi-line error display with source context and caret — TUI milestone
- Thread-local parser caching for LSP server parallel parsing — LSP milestone
- Extensible error catalog for generator-specific errors — future milestone
- Flexible/pass-through type handling (accept any identifier as type) — not planned, but could revisit if user demand arises

None -- discussion stayed within phase scope

</deferred>

---

*Phase: 07-parser-hardening-and-data-types*
*Context gathered: 2026-04-08*
