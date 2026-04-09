# Phase 9: Effectivity Satellites and Same-As Links - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Add resolver support, domain model types, and linter rules for effectivity satellites (effsat) and same-as links (samlink). Grammar and AST nodes already exist from Phase 7. Code generation for these types is deferred to Phase 11.

</domain>

<decisions>
## Implementation Decisions

### EffSat Temporal Field Handling
- **D-01:** Temporal fields (start_date, end_date, etc.) are regular `FieldDef` entries in the effsat body. No special AST tagging, no keyword prefix. Generators (Phase 11) will infer temporal semantics from field names or type.
- **D-02:** LINT-01 (effsat parent must be a link) is a linter rule (`LintDiagnostic` warning), not a resolver error. Fires post-parse, warns but doesn't block. Matches ROADMAP wording "Linter warns".

### SamLink Same-Hub Validation
- **D-03:** LINT-02 (master and duplicate must reference same hub) is a linter rule, not resolver validation. Consistent with LINT-01 approach.
- **D-04:** "Same hub" means exact string match of `master_ref == duplicate_ref` as declared in DVML. No resolver-level resolution needed. Simple, fast, catches the intent.

### Naming Convention Configuration
- **D-05:** LINT-03 naming rules are configured in a dedicated `.dvml-lint.toml` file in the project root. Linter reads it at startup if present; absent file means no naming enforcement.
- **D-06:** Naming patterns are prefix-per-entity-type only. Each entity type can have a required prefix (e.g., `hub_` for hubs, `sat_` for satellites). Missing prefix = lint warning. No suffix or regex support.

### Domain Model Design
- **D-07:** EffSat and SamLink get separate classes in `core.py`, with own dicts on `DataVaultModel` (`effsats: dict[str, EffSat]`, `samlinks: dict[str, SamLink]`). Follows Phase 8 NhSat/NhLink pattern exactly.
- **D-08:** SamLink domain model has `master_ref: str` and `duplicate_ref: str` as separate fields (not a hub_references list). Matches AST node and preserves semantic clarity for generators.

### Claude's Discretion
- EffSat resolver validation rules (parent ref checking — same as satellite or stricter)
- `.dvml-lint.toml` file format and parsing library (tomli/tomllib)
- Default naming convention prefixes (if any defaults are shipped)
- Test fixture `.dv` file design for effsat/samlink examples

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Parser and AST (Phase 7 output — already built)
- `src/dmjedi/lang/grammar.lark` — Grammar rules for `effsat_decl` and `samlink_decl` (lines 74-82)
- `src/dmjedi/lang/parser.py` — Transformer methods for effsat and samlink
- `src/dmjedi/lang/ast.py` — `EffSatDecl` and `SamLinkDecl` Pydantic models

### Domain Model (extend here)
- `src/dmjedi/model/core.py` — Hub, Satellite, Link, NhSat, NhLink, DataVaultModel
- `src/dmjedi/model/resolver.py` — Resolver with hub/sat/link/nhsat/nhlink loops

### Linter (extend here)
- `src/dmjedi/lang/linter.py` — 4 existing lint rules, LintDiagnostic pattern

### Requirements
- `.planning/REQUIREMENTS.md` — ENTITY-01, ENTITY-02, LINT-01, LINT-02, LINT-03

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `EffSatDecl` and `SamLinkDecl` AST nodes already defined with all needed fields
- `DVMLModule` already has `effsats` and `samlinks` lists populated by parser
- Phase 8 NhSat/NhLink pattern provides exact template for domain model + resolver extension
- `LintDiagnostic` dataclass and `lint()` function pattern for adding new rules
- Python 3.11+ has `tomllib` in stdlib — can read TOML config natively

### Established Patterns
- Domain model classes: Pydantic `BaseModel` with `qualified_name` property
- Resolver loops: iterate `module.{type}s`, build domain object, check duplicates, add to model dict
- Linter rules: each rule is a function called from `lint()`, returns list of `LintDiagnostic`
- Existing lint rules check: hub needs business keys, satellite needs parent, link needs 2+ refs, satellite parent exists

### Integration Points
- `DataVaultModel` in `core.py` — add `effsats` and `samlinks` dicts
- `resolve()` in `resolver.py` — add effsat/samlink resolution loops
- `lint()` in `linter.py` — add LINT-01, LINT-02, LINT-03 rules
- `.dvml-lint.toml` — new config file read by linter

</code_context>

<specifics>
## Specific Ideas

- LINT-01 needs resolved model context (must know if parent is a link vs hub) — linter may need to accept the resolved model as input, or this check moves to a post-resolution lint pass
- `.dvml-lint.toml` example format: `[naming]\nhub = "hub_"\nsat = "sat_"\nlink = "link_"`
- LINT-03 applies to ALL entity types (hub, satellite, link, nhsat, nhlink, effsat, samlink) — not just the new ones

</specifics>

<deferred>
## Deferred Ideas

- Code generation for effsat and samlink — Phase 11 (GEN-01, GEN-02)
- Documentation coverage for effsat and samlink — Phase 11 (DOC-01)

</deferred>

---

*Phase: 09-effectivity-satellites-and-same-as-links*
*Context gathered: 2026-04-08*
