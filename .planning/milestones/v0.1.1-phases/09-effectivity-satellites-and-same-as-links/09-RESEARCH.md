# Phase 9: Effectivity Satellites and Same-As Links - Research

**Researched:** 2026-04-08
**Domain:** Python domain model extension, linter rule design, TOML config parsing
**Confidence:** HIGH

## Summary

Phase 9 is a pure extension phase — grammar and AST nodes already exist and are fully wired. The work is three orthogonal tasks: (1) add `EffSat` and `SamLink` domain model classes and extend the resolver, (2) add three linter rules with a critical signature change for LINT-01, and (3) add a `.dvml-lint.toml` config loader for LINT-03.

All patterns are already established in the codebase. `EffSat`/`SamLink` domain model classes mirror `NhSat`/`NhLink` exactly. `EffSatDecl` and `SamLinkDecl` AST nodes are already fully populated by the parser and sit in `module.effsats`/`module.samlinks` lists ready for resolver loops. The main design question is the LINT-01 signature: the current `lint(module: DVMLModule)` has no access to the resolved model, but LINT-01 must check whether an effsat's `parent_ref` resolves to a link. The CONTEXT.md `<specifics>` section calls this out explicitly and the resolution is to add an optional `model` parameter to `lint()`.

**Primary recommendation:** Follow the NhSat/NhLink template for domain model and resolver; extend `lint()` with an optional `DataVaultModel` parameter to enable LINT-01; use Python 3.11+ stdlib `tomllib` to load `.dvml-lint.toml`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Temporal fields are regular `FieldDef` entries. No special AST tagging. Generators infer semantics from field names/type.
- **D-02:** LINT-01 is a linter rule (`LintDiagnostic` warning), not a resolver error. Fires post-parse, warns but doesn't block.
- **D-03:** LINT-02 is a linter rule, not resolver validation. Consistent with LINT-01 approach.
- **D-04:** "Same hub" means exact string match of `master_ref == duplicate_ref`. No resolver-level resolution needed.
- **D-05:** LINT-03 naming rules configured in `.dvml-lint.toml` in project root. Absent file = no naming enforcement.
- **D-06:** Naming patterns are prefix-per-entity-type only. Missing prefix = lint warning. No suffix or regex support.
- **D-07:** `EffSat` and `SamLink` get separate classes in `core.py`, with own dicts on `DataVaultModel` (`effsats: dict[str, EffSat]`, `samlinks: dict[str, SamLink]`). Follows Phase 8 NhSat/NhLink pattern exactly.
- **D-08:** `SamLink` domain model has `master_ref: str` and `duplicate_ref: str` as separate fields.

### Claude's Discretion
- EffSat resolver validation rules (parent ref checking)
- `.dvml-lint.toml` file format and parsing library (tomli/tomllib)
- Default naming convention prefixes (if any defaults are shipped)
- Test fixture `.dv` file design for effsat/samlink examples

### Deferred Ideas (OUT OF SCOPE)
- Code generation for effsat and samlink — Phase 11 (GEN-01, GEN-02)
- Documentation coverage for effsat and samlink — Phase 11 (DOC-01)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ENTITY-01 | User can declare `effsat` with `of` referencing a link, with user-declared temporal fields | Grammar exists; parser populates `module.effsats`; need `EffSat` domain class + resolver loop |
| ENTITY-02 | User can declare `samlink` with `master`/`duplicate` keywords referencing the same hub | Grammar exists; parser populates `module.samlinks`; need `SamLink` domain class + resolver loop |
| LINT-01 | Linter warns if `effsat` parent is not a link | Requires `lint()` to accept resolved model; check `parent_ref` against `model.links` |
| LINT-02 | Linter warns if `samlink` master/duplicate don't reference the same hub | AST-only check; `master_ref != duplicate_ref` string comparison |
| LINT-03 | Linter warns if entity names don't follow configurable naming convention (prefix/suffix) | Read `.dvml-lint.toml` via `tomllib`; check all entity types including new ones |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `tomllib` | stdlib (Python 3.11+) | Parse `.dvml-lint.toml` config | Already confirmed available: `uv run python -c "import tomllib"` passes [VERIFIED: runtime check] |
| `pydantic` | already in project | Domain model classes | All domain models use Pydantic v2 BaseModel [VERIFIED: core.py] |
| `pytest` | already in project | Testing | Project standard [VERIFIED: test suite runs 128 tests] |

### No New Dependencies Needed
This phase requires zero new package installs. `tomllib` is stdlib in Python 3.11+, and the project already runs on Python 3.12.12 (confirmed via `uv run python -c "import sys; print(sys.version)"`). [VERIFIED: runtime check]

**Installation:**
```bash
# No new installs required
```

## Architecture Patterns

### Recommended Project Structure Changes
```
src/dmjedi/model/core.py      # Add EffSat, SamLink classes + update DataVaultModel
src/dmjedi/model/resolver.py  # Add effsat/samlink resolution loops + parent ref validation
src/dmjedi/lang/linter.py     # Extend lint() signature; add _check_effsats, _check_samlinks, _check_naming
tests/test_model.py           # EffSat/SamLink domain model + resolver tests
tests/test_linter.py          # LINT-01, LINT-02, LINT-03 rule tests
tests/fixtures/               # effsat_samlink.dv fixture file
```

### Pattern 1: Domain Model Class (follows NhSat/NhLink template exactly)

**What:** Pydantic BaseModel with `name`, `namespace`, `parent_ref`/specialized fields, `columns`, and `qualified_name` property.

**When to use:** Every new resolved entity type.

**Example (from existing NhSat — exact template for EffSat):**
```python
# Source: src/dmjedi/model/core.py (verified lines 61-72)
class NhSat(BaseModel):
    """A resolved non-historized satellite (current-state-only)."""

    name: str
    namespace: str = ""
    parent_ref: str
    columns: list[Column] = []

    @property
    def qualified_name(self) -> str:
        return f"{self.namespace}.{self.name}" if self.namespace else self.name
```

**EffSat follows this pattern identically.** SamLink replaces `parent_ref` with `master_ref: str` and `duplicate_ref: str` per D-08.

### Pattern 2: Resolver Loop (follows nhsat/nhlink template exactly)

**What:** Iterate `module.{type}s`, construct domain object, check for duplicates, add to model dict. Raise `ResolverErrors` on duplicates.

**Example (from existing nhsat loop — exact template):**
```python
# Source: src/dmjedi/model/resolver.py (verified lines 110-132)
for nhsat_decl in module.nhsats:
    nhsat = NhSat(
        name=nhsat_decl.name,
        namespace=ns,
        parent_ref=nhsat_decl.parent_ref,
        columns=[
            Column(name=f.name, data_type=f.data_type) for f in nhsat_decl.fields
        ],
    )
    qname = nhsat.qualified_name
    if qname in model.nhsats:
        errors.append(
            ResolverError(
                message=(
                    f"Duplicate nhsat '{qname}' redefined"
                    f" in {module.source_file or '<string>'}:{nhsat_decl.loc.line}"
                ),
                source_file=module.source_file,
                line=nhsat_decl.loc.line,
            )
        )
    else:
        model.nhsats[qname] = nhsat
```

**EffSat loop:** identical substitution (`effsats`, `EffSat`, `effsat_decl`, `effsat`).

**SamLink loop:** same structure but construct `SamLink(name=..., namespace=ns, master_ref=..., duplicate_ref=..., columns=[...])`.

### Pattern 3: Post-Resolution Parent Ref Validation (Claude's discretion)

**Recommendation:** Add a post-resolution check for effsat `parent_ref` analogous to the existing satellite/nhsat parent ref checks. Check that `parent_ref` resolves to something in `model.links` (not hubs). This is a *resolver error* (unknown entity) distinct from the *linter warning* LINT-01 (known entity but wrong type). [ASSUMED — the existing sat/nhsat checks provide the pattern; applying it to effsats is natural.]

```python
# Source: src/dmjedi/model/resolver.py (verified lines 158-175 — existing satellite pattern)
for effsat in model.effsats.values():
    ref = effsat.parent_ref
    ns_ref = f"{effsat.namespace}.{ref}" if effsat.namespace else ref
    # Check entity exists at all (resolver error, not lint warning)
    all_known = {**model.hubs, **model.links, **model.nhlinks}
    if ref not in all_known and ns_ref not in all_known:
        errors.append(ResolverError(
            message=f"EffSat '{effsat.qualified_name}' references unknown parent '{ref}'"
        ))
```

LINT-01 is the additional *type check* (parent must specifically be a link, not a hub).

### Pattern 4: Lint Rule Function

**What:** Private function `_check_X(module) -> list[LintDiagnostic]`, called from `lint()`.

**Example (from existing _check_links):**
```python
# Source: src/dmjedi/lang/linter.py (verified lines 77-88)
def _check_links(module: DVMLModule) -> list[LintDiagnostic]:
    diags: list[LintDiagnostic] = []
    for link in module.links:
        if len(link.references) < 2:
            diags.append(
                LintDiagnostic(
                    message=f"Link '{link.name}' must reference at least 2 hubs",
                    severity=Severity.ERROR,
                    loc=link.loc,
                    rule="link-requires-two-refs",
                )
            )
    return diags
```

### Pattern 5: LINT-01 — Resolved Model Lint (critical design)

**What:** LINT-01 needs the resolved `DataVaultModel` to know whether a `parent_ref` resolves to a link. The current `lint()` signature only takes `DVMLModule`.

**Solution:** Add an optional `model: DataVaultModel | None = None` parameter to `lint()`. Rules that need the resolved model check `if model is not None` before running. Rules that work on AST only are unaffected.

**Signature change:**
```python
# New signature — backward compatible
def lint(module: DVMLModule, model: DataVaultModel | None = None) -> list[LintDiagnostic]:
    diagnostics: list[LintDiagnostic] = []
    diagnostics.extend(_check_namespace(module))
    diagnostics.extend(_check_hubs(module))
    diagnostics.extend(_check_satellites(module))
    diagnostics.extend(_check_links(module))
    diagnostics.extend(_check_effsats(module, model))   # LINT-01: needs model
    diagnostics.extend(_check_samlinks(module))          # LINT-02: AST-only
    diagnostics.extend(_check_naming(module, config))    # LINT-03: config-driven
    return diagnostics
```

**CLI integration:** In `cli/main.py`, `lint()` is called before `resolve()` (lines 36-37, 71-72, 114-115). The caller must resolve first, then call `lint(module, model=model)` — or lint is called twice (once pre-resolve for AST rules, once post-resolve for model-aware rules). [ASSUMED — need to decide call ordering in CLI.]

**Recommended approach:** Keep lint call-site pre-resolve for AST-only rules; pass resolved model only when available. In validate/generate/docs, call `lint(module, model=resolved_model)` after the `resolve()` call. The `model=None` default means existing call sites without model continue to work — LINT-01 simply skips when model is not provided. [ASSUMED]

### Pattern 6: LINT-03 TOML Config Loading

**What:** Read `.dvml-lint.toml` from the project root (cwd). Parse with `tomllib`. Return a typed config object.

**tomllib usage:**
```python
# Source: Python 3.11+ stdlib docs [CITED: docs.python.org/3/library/tomllib.html]
import tomllib
from pathlib import Path

def _load_lint_config() -> dict[str, str]:
    """Load naming prefixes from .dvml-lint.toml if present."""
    config_path = Path(".dvml-lint.toml")
    if not config_path.exists():
        return {}
    with config_path.open("rb") as f:
        data = tomllib.load(f)
    return data.get("naming", {})
```

**Example `.dvml-lint.toml`:**
```toml
[naming]
hub = "hub_"
sat = "sat_"
link = "link_"
nhsat = "nhsat_"
nhlink = "nhlink_"
effsat = "effsat_"
samlink = "samlink_"
```

**LINT-03 applies to all 7 entity types** per CONTEXT.md `<specifics>`: hub, satellite, link, nhsat, nhlink, effsat, samlink.

**Config loading:** Load once at `lint()` call, not per rule invocation. Pass config dict to `_check_naming()`. [ASSUMED — module-level caching vs per-call load is an implementation detail.]

### Anti-Patterns to Avoid
- **Don't add EffSat/SamLink to the resolver's pre-existing parent-ref validation block without also doing the new resolver loops** — if the resolver runs post-resolution checks before the effsats dict is populated, checks will always fail.
- **Don't make lint() reject when model is None for LINT-01** — warning must silently skip if model unavailable; this preserves backward compatibility and the existing test suite.
- **Don't hard-code default prefixes** — D-05 says absent `.dvml-lint.toml` = no naming enforcement. Ship zero defaults.
- **Don't use `tomli` (backport)** — project is Python 3.12, stdlib `tomllib` is available and already verified. [VERIFIED: runtime check]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TOML parsing | Custom parser | `tomllib` (stdlib) | Handle quoting, escaping, nested tables correctly |
| Duplicate qualified name detection | Custom set tracking | Follow existing resolver pattern | Already handles source_file and line attribution correctly |
| Pydantic model field validation | Custom `__init__` checks | `model_validator(mode="after")` | Consistent with Link/NhLink pattern (though EffSat/SamLink don't need min-refs validators) |

**Key insight:** Every problem in this phase already has a solved pattern within the codebase. There is nothing novel to design — only apply the established template.

## Common Pitfalls

### Pitfall 1: LINT-01 Called Before Model is Available
**What goes wrong:** If `lint()` is called before `resolve()` (as in the current CLI), LINT-01 has no model context and silently skips. The warning never fires.
**Why it happens:** Current CLI call order: parse → lint → resolve. LINT-01 needs resolved model.
**How to avoid:** In CLI commands (`validate`, `generate`, `docs`), move the lint call (or add a second lint call) after `resolve()`, passing the resolved model. Or restructure to resolve first, then lint.
**Warning signs:** Tests pass but LINT-01 never produces diagnostics even with bad effsat declarations.

### Pitfall 2: LINT-03 Config Path Resolution
**What goes wrong:** `.dvml-lint.toml` is read from cwd at runtime, but tests don't have this file. Tests that expect LINT-03 to fire may fail if config is unexpectedly found on a developer's machine.
**Why it happens:** `Path(".dvml-lint.toml")` resolves to the test runner's cwd.
**How to avoid:** Make config path injectable (pass as parameter or monkeypatch in tests). Test both "config present" and "config absent" branches explicitly.
**Warning signs:** Tests pass locally but fail in CI (or vice versa).

### Pitfall 3: EffSat Parent Ref Resolution Scope
**What goes wrong:** effsat `parent_ref` is stored without namespace qualification in the AST (e.g., `"CustomerOrder"` not `"sales.CustomerOrder"`). The post-resolution check must match both bare name and namespace-qualified name, exactly as the existing satellite/nhsat checks do.
**Why it happens:** User writes `effsat Validity of CustomerOrder { ... }` — the parser stores `"CustomerOrder"` as a bare string. The resolved link key is `"sales.CustomerOrder"`.
**How to avoid:** Copy the exact lookup pattern from the existing nhsat parent ref check (resolver.py lines 178-194): check `ref not in model.X and ns_ref not in model.X`.

### Pitfall 4: SamLink Resolver Loop — Missing master_ref / duplicate_ref
**What goes wrong:** Parser sets `master_ref = ""` and `duplicate_ref = ""` as defaults (parser.py lines 292-293). A samlink declaration that omits `master` or `duplicate` produces empty strings silently.
**Why it happens:** The parser uses empty string defaults, no validation at parse time.
**How to avoid:** In the resolver loop for samlinks, check that `master_ref` and `duplicate_ref` are non-empty and emit a `ResolverError` if missing. Or add a linter rule. Either way, document the choice.

### Pitfall 5: LINT-03 Applies to All 7 Entity Types
**What goes wrong:** Implementing LINT-03 only for the new entity types (effsat, samlink), missing hubs, satellites, links, nhsats, nhlinks.
**Why it happens:** Phase 9 adds effsat/samlink — easy to scope the naming check to just the new types.
**How to avoid:** Per CONTEXT.md `<specifics>`: LINT-03 applies to ALL entity types. The `_check_naming()` function must iterate all 7 entity collections in the module.

## Code Examples

### EffSat Domain Class
```python
# Pattern: mirrors NhSat exactly (src/dmjedi/model/core.py lines 61-71)
class EffSat(BaseModel):
    """A resolved effectivity satellite (temporal link validity)."""

    name: str
    namespace: str = ""
    parent_ref: str
    columns: list[Column] = []

    @property
    def qualified_name(self) -> str:
        return f"{self.namespace}.{self.name}" if self.namespace else self.name
```

### SamLink Domain Class
```python
# Pattern: mirrors NhSat but with master_ref/duplicate_ref per D-08
class SamLink(BaseModel):
    """A resolved same-as link (master/duplicate cross-source matching)."""

    name: str
    namespace: str = ""
    master_ref: str
    duplicate_ref: str
    columns: list[Column] = []

    @property
    def qualified_name(self) -> str:
        return f"{self.namespace}.{self.name}" if self.namespace else self.name
```

### DataVaultModel Extension
```python
# Add to existing DataVaultModel in core.py
class DataVaultModel(BaseModel):
    hubs: dict[str, Hub] = {}
    satellites: dict[str, Satellite] = {}
    links: dict[str, Link] = {}
    nhsats: dict[str, NhSat] = {}
    nhlinks: dict[str, NhLink] = {}
    effsats: dict[str, EffSat] = {}    # NEW
    samlinks: dict[str, SamLink] = {}  # NEW
```

### LINT-01 Implementation
```python
def _check_effsats(
    module: DVMLModule, model: "DataVaultModel | None"
) -> list[LintDiagnostic]:
    diags: list[LintDiagnostic] = []
    for effsat in module.effsats:
        if model is not None:
            ref = effsat.parent_ref
            # Check if ref resolves to a hub rather than a link
            ns = module.namespace
            ns_ref = f"{ns}.{ref}" if ns else ref
            in_links = ref in model.links or ns_ref in model.links
            in_hubs = ref in model.hubs or ns_ref in model.hubs
            if in_hubs and not in_links:
                diags.append(LintDiagnostic(
                    message=f"EffSat '{effsat.name}' parent '{ref}' is a hub, not a link",
                    severity=Severity.WARNING,
                    loc=effsat.loc,
                    rule="effsat-parent-must-be-link",
                ))
    return diags
```

### LINT-02 Implementation
```python
def _check_samlinks(module: DVMLModule) -> list[LintDiagnostic]:
    diags: list[LintDiagnostic] = []
    for samlink in module.samlinks:
        if samlink.master_ref != samlink.duplicate_ref:
            diags.append(LintDiagnostic(
                message=(
                    f"SamLink '{samlink.name}' master '{samlink.master_ref}' and "
                    f"duplicate '{samlink.duplicate_ref}' reference different hubs"
                ),
                severity=Severity.WARNING,
                loc=samlink.loc,
                rule="samlink-same-hub",
            ))
    return diags
```

### LINT-03 Implementation Sketch
```python
def _check_naming(
    module: DVMLModule, config: dict[str, str]
) -> list[LintDiagnostic]:
    """Check entity names against configured prefixes."""
    if not config:
        return []
    diags: list[LintDiagnostic] = []
    checks = [
        ("hub", module.hubs),
        ("sat", module.satellites),
        ("link", module.links),
        ("nhsat", module.nhsats),
        ("nhlink", module.nhlinks),
        ("effsat", module.effsats),
        ("samlink", module.samlinks),
    ]
    for entity_type, entities in checks:
        prefix = config.get(entity_type)
        if not prefix:
            continue
        for entity in entities:
            if not entity.name.startswith(prefix):
                diags.append(LintDiagnostic(
                    message=(
                        f"{entity_type.capitalize()} '{entity.name}' does not start "
                        f"with required prefix '{prefix}'"
                    ),
                    severity=Severity.WARNING,
                    loc=entity.loc,
                    rule="naming-convention",
                ))
    return diags
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `tomli` backport for Python 3.9 | `tomllib` stdlib (Python 3.11+) | Python 3.11 release | No extra dependency needed [VERIFIED: Python 3.12 in project] |
| Per-parse Lark instance | Module-level singleton (`_parser`) | Phase 7 (PARSE-01) | Already implemented; no action needed here |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Recommended approach: call `lint(module, model=resolved_model)` after resolve in CLI; current pre-resolve call handles AST-only rules | Architecture Patterns (Pattern 5) | CLI integration may need different structure; planner must decide |
| A2 | Module-level config loading (load once per `lint()` call, not cached at import) | Architecture Patterns (Pattern 6) | Could cause repeated file reads if lint is called many times; minor perf concern |
| A3 | EffSat resolver should validate parent ref exists (ResolverError for unknown ref), separate from LINT-01 (warning for known-but-wrong type ref) | Architecture Patterns (Pattern 3) | If not done, users get confusing no-output rather than a clear error for `effsat Foo of NonExistent {}` |
| A4 | SamLink resolver should validate non-empty `master_ref`/`duplicate_ref` | Common Pitfalls (Pitfall 4) | Silent empty string silently produces broken domain objects |

**Three of these (A1, A3, A4) are within Claude's Discretion per CONTEXT.md — planner can decide implementation details.**

## Open Questions

1. **CLI call ordering for LINT-01**
   - What we know: Current CLI calls `lint(module)` before `resolve()`. LINT-01 needs the resolved model. The `model=None` default means it silently skips without the model.
   - What's unclear: Should the CLI call lint twice (once pre-resolve, once post-resolve with model), or restructure to resolve first?
   - Recommendation: Add a second lint call after resolve in each CLI command, passing the resolved model. This keeps the existing "lint before resolve" check for AST-level errors intact and adds model-aware checks after.

2. **Config path resolution in tests**
   - What we know: `Path(".dvml-lint.toml")` is cwd-relative. Tests run from project root.
   - What's unclear: Best practice for making this testable without coupling tests to filesystem state.
   - Recommendation: Accept config path as parameter to `lint()` (or to `_load_lint_config()`), defaulting to `Path(".dvml-lint.toml")`. Tests pass a tmp_path fixture file. This is 3 lines of change.

## Environment Availability

Step 2.6: SKIPPED (no external dependencies beyond stdlib tomllib, which is verified available).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (confirmed via test suite: 128 tests passing) |
| Config file | `pytest.ini` or `pyproject.toml` (project standard) |
| Quick run command | `uv run pytest tests/test_model.py tests/test_linter.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ENTITY-01 | EffSat resolves with correct parent_ref and columns | unit | `uv run pytest tests/test_model.py -k "effsat" -x` | ❌ Wave 0 |
| ENTITY-01 | Duplicate EffSat raises ResolverErrors | unit | `uv run pytest tests/test_model.py -k "duplicate_effsat" -x` | ❌ Wave 0 |
| ENTITY-01 | EffSat with unknown parent_ref raises ResolverErrors | unit | `uv run pytest tests/test_model.py -k "effsat_invalid_parent" -x` | ❌ Wave 0 |
| ENTITY-02 | SamLink resolves with correct master_ref/duplicate_ref | unit | `uv run pytest tests/test_model.py -k "samlink" -x` | ❌ Wave 0 |
| ENTITY-02 | Duplicate SamLink raises ResolverErrors | unit | `uv run pytest tests/test_model.py -k "duplicate_samlink" -x` | ❌ Wave 0 |
| LINT-01 | Linter warns when effsat parent is a hub (not link) | unit | `uv run pytest tests/test_linter.py -k "effsat_parent" -x` | ❌ Wave 0 |
| LINT-01 | LINT-01 skips silently when model=None | unit | `uv run pytest tests/test_linter.py -k "effsat_no_model" -x` | ❌ Wave 0 |
| LINT-02 | Linter warns when samlink master != duplicate ref | unit | `uv run pytest tests/test_linter.py -k "samlink_different_hub" -x` | ❌ Wave 0 |
| LINT-02 | No warning when master == duplicate ref | unit | `uv run pytest tests/test_linter.py -k "samlink_same_hub" -x` | ❌ Wave 0 |
| LINT-03 | Linter warns when entity name missing prefix | unit | `uv run pytest tests/test_linter.py -k "naming" -x` | ❌ Wave 0 |
| LINT-03 | No warning when prefix present or config absent | unit | `uv run pytest tests/test_linter.py -k "naming_valid" -x` | ❌ Wave 0 |
| LINT-03 | Applies to all 7 entity types | unit | `uv run pytest tests/test_linter.py -k "naming_all_types" -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_model.py tests/test_linter.py -x`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green (currently 128 tests) before completion

### Wave 0 Gaps
All test cases above are new — add to existing `tests/test_model.py` and `tests/test_linter.py`. No new test files needed.
- [ ] `tests/fixtures/effsat_samlink.dv` — integration fixture for parse+resolve round-trip tests

## Security Domain

No security-relevant changes in this phase. This phase adds domain model classes, a linter rule, and reads a local config file. No user input is executed, no network calls, no authentication, no cryptography. ASVS categories V2/V3/V4/V6 are not applicable. V5 (Input Validation) is trivially satisfied: TOML parsing via stdlib `tomllib` handles all input validation internally.

## Sources

### Primary (HIGH confidence)
- `src/dmjedi/model/core.py` — NhSat/NhLink patterns for EffSat/SamLink [VERIFIED: read directly]
- `src/dmjedi/model/resolver.py` — resolver loop and post-resolution validation patterns [VERIFIED: read directly]
- `src/dmjedi/lang/linter.py` — LintDiagnostic pattern and existing rules [VERIFIED: read directly]
- `src/dmjedi/lang/ast.py` — EffSatDecl and SamLinkDecl already defined and complete [VERIFIED: read directly]
- `src/dmjedi/lang/parser.py` — effsat_decl and samlink_decl transformer methods fully implemented [VERIFIED: read directly]
- `src/dmjedi/lang/grammar.lark` — grammar rules lines 73-82 confirmed [VERIFIED: read directly]
- Runtime: `uv run python -c "import tomllib"` confirms stdlib availability on Python 3.12 [VERIFIED: runtime check]

### Secondary (MEDIUM confidence)
- Python 3.11+ tomllib stdlib documentation [CITED: docs.python.org/3/library/tomllib.html]

### Tertiary (LOW confidence)
None — all claims are verified from codebase or stdlib.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified from running codebase
- Architecture: HIGH — patterns read directly from source; extension is mechanical
- Pitfalls: HIGH for codebase-derived pitfalls; MEDIUM for CLI call ordering (A1 — design choice)

**Research date:** 2026-04-08
**Valid until:** 2026-05-08 (stable codebase, no external dependencies)
