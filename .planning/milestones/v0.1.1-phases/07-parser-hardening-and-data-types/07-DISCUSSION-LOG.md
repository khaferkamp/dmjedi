# Phase 7: Parser Hardening and Data Types - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md -- this log preserves the alternatives considered.

**Date:** 2026-04-08
**Phase:** 07-parser-hardening-and-data-types
**Areas discussed:** Data type parameters, Error message format, Unknown type handling, New entity keywords, Spark type mapping strategy, Parser caching scope, Grammar extensibility pattern, Default type parameter values

---

## Data Type Parameters

| Option | Description | Selected |
|--------|-------------|----------|
| Parameterless only | Keep types as bare keywords. Generators pick defaults. | |
| Optional parameters | Allow varchar(100) or decimal(10,4) but don't require them. | ✓ |
| Required parameters for some | varchar always requires length, decimal requires precision/scale. | |

**User's choice:** Optional parameters
**Notes:** None

### Follow-up: Parameter scope

| Option | Description | Selected |
|--------|-------------|----------|
| Any type | Grammar allows parameters on any type. Forward-compatible. | ✓ |
| Restricted types only | Only varchar, decimal, float accept parameters. | |

**User's choice:** Any type

### Follow-up: Parameter representation

| Option | Description | Selected |
|--------|-------------|----------|
| String pass-through | Store data_type as string like "varchar(100)". Minimal changes. | ✓ |
| Structured representation | AST stores type name + optional params list. More typed. | |

**User's choice:** String pass-through

---

## Error Message Format

| Option | Description | Selected |
|--------|-------------|----------|
| Compact one-liner | Format: 'file:line:col: error: message'. grep-friendly. | |
| Multi-line with context | Show offending line with caret. More helpful for humans. | |
| Rich terminal output | Colored panels with syntax highlighting via Rich. | |

**User's choice:** User clarified: wants colored output AND programmatic parsability. Multi-line deferred to TUI milestone.

### Follow-up: Colored one-liner vs multi-line now

| Option | Description | Selected |
|--------|-------------|----------|
| Colored one-liner now | Structured error object, renders as colored compact line. TUI adds multi-line later. | ✓ |
| Multi-line with color now | Full multi-line output with source context and caret now. | |

**User's choice:** Colored one-liner now

### Follow-up: Source line capture

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, capture source line | Error object stores offending source line text for future use. | ✓ |
| No, just coordinates | Error object has file/line/col/hint only. TUI re-reads file. | |

**User's choice:** Yes, capture source line

### Follow-up: Contextual hints

| Option | Description | Selected |
|--------|-------------|----------|
| Expected-token hints | Derive hints from Lark parser state. Automatic, low maintenance. | |
| Curated error messages | Hand-written messages for common mistakes. Better UX. | |
| Both -- curated with fallback | Curated for known patterns, expected-token for everything else. | ✓ |

**User's choice:** Both -- curated with fallback

### Follow-up: Color control

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-detect + flag | Disable color when not TTY. --no-color flag. Rich handles natively. | ✓ |
| Always colored | Always output color. Users pipe through tools to strip ANSI. | |
| You decide | Claude picks. | |

**User's choice:** Auto-detect + flag

### Follow-up: Error catalog scope

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed in parser | Curated messages live in lang/ layer only. | ✓ |
| Extensible catalog | Generators can register additional error patterns. | |
| You decide | Claude picks. | |

**User's choice:** Fixed in parser

---

## Unknown Type Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Strict -- parse error | Grammar only accepts known types. Catches typos early. | ✓ |
| Flexible -- pass-through | Grammar accepts any identifier as type. Extensible. | |
| Flexible with lint warning | Accept any identifier, linter warns on unknown. | |

**User's choice:** Strict -- parse error

---

## New Entity Keywords

| Option | Description | Selected |
|--------|-------------|----------|
| Full grammar rules | Complete grammar rules with body syntax for all 6 entities. | ✓ |
| Reserved keywords only | Add keywords but no body rules. Phases 8-10 add rules. | |
| Grammar + AST nodes | Full grammar AND complete AST node definitions. | |

**User's choice:** Full grammar rules

### Follow-up: Vertical slice depth

| Option | Description | Selected |
|--------|-------------|----------|
| Full vertical slice | Grammar + AST nodes + transformer + DVMLModule fields. | ✓ |
| Grammar only, no AST | Grammar parses but transformer raises NotImplementedError. | |

**User's choice:** Full vertical slice

---

## Spark Type Mapping Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Shared type module | Top-level type mapping module used by both generators. Single source of truth. | ✓ |
| Generator-specific mapping | Each generator manages own mappings independently. | |
| You decide | Claude picks. | |

**User's choice:** Shared type module

### Follow-up: Parameter awareness

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, parameter-aware | Shared module parses type strings and returns correct target with params. | ✓ |
| Generators handle params | Shared module maps base types only. Generators parse params themselves. | |

**User's choice:** Yes, parameter-aware

---

## Parser Caching Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Module-level singleton | Simple _parser = None, created on first call, reused forever. | ✓ |
| Thread-local singleton | One Lark instance per thread via threading.local(). | |
| You decide | Claude picks. | |

**User's choice:** Module-level singleton

---

## Grammar Extensibility Pattern

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit per entity | Each entity gets own grammar rule, transformer method, AST node. | ✓ |
| Shared body patterns | Factor common patterns into shared rules. Less grammar duplication. | |
| You decide | Claude picks. | |

**User's choice:** Explicit per entity

---

## Default Type Parameter Values

| Option | Description | Selected |
|--------|-------------|----------|
| In the shared type module | Defaults defined in shared module. Single source of truth. | ✓ |
| Per generator | Each generator defines own defaults. More flexible. | |
| In the grammar/AST | Grammar desugars bare types to defaults at parse time. | |

**User's choice:** In the shared type module

### Follow-up: varchar default

| Option | Description | Selected |
|--------|-------------|----------|
| VARCHAR(255) | Industry standard. Matches existing string mapping. | ✓ |
| VARCHAR(MAX) / TEXT | Unbounded by default. | |
| You decide | Claude picks. | |

**User's choice:** VARCHAR(255)

---

## Claude's Discretion

- Exact structure of the curated error message catalog
- PySpark type representations for new types
- Exact default values for bigint, float, binary across dialects
- Internal naming of the shared type module

## Deferred Ideas

- Multi-line error display with source context and caret -- TUI milestone
- Thread-local parser caching for LSP parallel parsing -- LSP milestone
- Extensible error catalog for generator-specific errors -- future milestone
- Flexible/pass-through type handling -- not planned
