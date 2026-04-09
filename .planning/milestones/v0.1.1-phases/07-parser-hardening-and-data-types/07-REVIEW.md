---
phase: 07-parser-hardening-and-data-types
reviewed: 2026-04-08T14:10:00Z
depth: standard
files_reviewed: 13
files_reviewed_list:
  - src/dmjedi/cli/errors.py
  - src/dmjedi/cli/main.py
  - src/dmjedi/generators/spark_declarative/generator.py
  - src/dmjedi/generators/sql_jinja/types.py
  - src/dmjedi/lang/ast.py
  - src/dmjedi/lang/grammar.lark
  - src/dmjedi/lang/parser.py
  - src/dmjedi/model/types.py
  - tests/snapshots/test_integration/test_spark_hub_snapshot/hub_customer.py
  - tests/test_cli.py
  - tests/test_generators.py
  - tests/test_parser.py
  - tests/test_types.py
findings:
  critical: 0
  warning: 4
  info: 5
  total: 9
status: issues_found
---

# Phase 07: Code Review Report

**Reviewed:** 2026-04-08T14:10:00Z
**Depth:** standard
**Files Reviewed:** 13
**Status:** issues_found

## Summary

This phase delivers parser hardening (singleton caching, structured parse errors) and adds four new DVML data types (`bigint`, `float`, `varchar`, `binary`) plus extended parameterized type support. The core architecture is sound and the data-flow model is clean. Tests are thorough and cover all new grammar rules.

Four warnings were found, all of which are correctness or reliability risks rather than style preferences: a silent data loss in `samlink_decl` when `master`/`duplicate` are both absent, a misleading `varchar(100)` → `STRING(100)` output for the Spark SQL dialect, a mutable thread-safety concern on the parser singleton, and a test that will silently pass even when it should fail. Five informational items are also noted.

## Warnings

### WR-01: `samlink_decl` silently produces empty `master_ref`/`duplicate_ref` on missing keys

**File:** `src/dmjedi/lang/parser.py:288-305`

**Issue:** `samlink_decl` initializes `master = ""` and `duplicate = ""` and only populates them if the corresponding `("master", ...)` / `("duplicate", ...)` tuple is found in `members`. If DVML source is parsed that omits either clause, or if future grammar changes alter how the tuples are keyed, `SamLinkDecl` is constructed with empty strings for both refs — no error is raised, no warning is emitted. A downstream consumer reading `samlink.master_ref == ""` has no way to distinguish "not yet resolved" from "missing in source".

**Fix:** Add an explicit guard after the loop before constructing `SamLinkDecl`:
```python
if not master or not duplicate:
    # surface a parse error — both refs are required for a samlink
    raise DVMLParseError(ParseError(
        file=self._source_file,
        line=self._loc(tree).line,
        column=self._loc(tree).column,
        hint="samlink requires both 'master' and 'duplicate' references",
    ))
return SamLinkDecl(
    name=name, master_ref=master, duplicate_ref=duplicate,
    fields=fields, loc=self._loc(tree),
)
```
Alternatively, add a Pydantic validator on `SamLinkDecl` that rejects empty strings.

---

### WR-02: `map_type("varchar(100)", "spark")` produces `STRING(100)` — invalid Spark SQL

**File:** `src/dmjedi/model/types.py:62-64`

**Issue:** For the `spark` dialect, `varchar` maps to `STRING`. When `map_type` handles a parameterized type like `varchar(100)`, it strips the default params from the base SQL (`STRING`) and then re-appends the user params, producing `STRING(100)`. `STRING(100)` is not valid Spark SQL — `STRING` does not accept a length parameter. The test at `tests/test_types.py:29` asserts `map_type("varchar(100)", "spark") == "STRING(100)"` which confirms this incorrect value is locked in by the test suite.

**Fix:** In `map_type`, when appending user params to a dialect's base SQL, skip the re-append if the type has no parameter slot (i.e., the base SQL after stripping has no natural parameter concept). A targeted fix for the `spark` dialect:
```python
# In map_type, after computing base_sql_no_params:
# For Spark, varchar/string never accept params.
if dialect == "spark" and base in ("varchar", "string"):
    return base_sql_no_params  # just "STRING"
return f"{base_sql_no_params}({params})"
```
The corresponding assertion in `test_types.py:29` should also be corrected to `"STRING"`.

---

### WR-03: Parser singleton `_parser` is not thread-safe

**File:** `src/dmjedi/lang/parser.py:29-41`

**Issue:** `_get_parser()` uses a module-level `_parser: Lark | None = None` variable with a bare `global _parser` write, protected by only a `None` check. In a multi-threaded environment (e.g., a future LSP server or parallel test runner), two threads can both observe `_parser is None` simultaneously, both construct a `Lark` instance, and one write will silently replace the other. The Lark `Earley` parser is not documented as thread-safe for construction. At minimum this is a TOCTOU window; in practice the LSP stub (`lsp/server.py`) makes this a forward-looking risk.

**Fix:** Use `threading.Lock` to guard the lazy-init:
```python
import threading
_parser: Lark | None = None
_parser_lock = threading.Lock()

def _get_parser() -> Lark:
    global _parser
    if _parser is None:
        with _parser_lock:
            if _parser is None:
                _parser = Lark(
                    _GRAMMAR_PATH.read_text(),
                    parser="earley",
                    propagate_positions=True,
                )
    return _parser
```

---

### WR-04: `test_parse_unknown_type_rejected` uses bare `Exception` — test may pass vacuously

**File:** `tests/test_parser.py:136-141`

**Issue:** The test asserts `pytest.raises(Exception)` for an unknown type. `Exception` is the base of nearly every exception class in Python. If any unrelated error fires (import error, attribute error, etc.), the test passes. More importantly, the intent is to verify that the grammar rejects the input via a `DVMLParseError`, but this is not asserted. If the grammar were changed to silently ignore unknown types and no other error was thrown, this test would still pass because no exception at all would be raised and `pytest.raises(Exception)` would then fail — but the failure message would be confusing and not point to the real regression.

**Fix:** Assert the specific exception type, and optionally check the error message:
```python
def test_parse_unknown_type_rejected():
    """D-08: unknown types must be rejected at parse time."""
    source = "hub H { business_key k : unknowntype }"
    with pytest.raises(DVMLParseError):
        parse(source)
```

---

## Info

### IN-01: `_parse_all` halts on first file parse error, dropping subsequent errors

**File:** `src/dmjedi/cli/main.py:160-165`

**Issue:** The `_parse_all` loop calls `raise typer.Exit(code=1) from None` immediately on the first `DVMLParseError`, meaning subsequent files in the batch are never parsed. A developer editing multiple files will see only the first error, fix it, re-run, and see the next. This is a UX degradation for large projects; it is not a crash but it is a reliability concern for error-reporting completeness.

**Suggestion:** Collect all parse errors in a list and print them all before exiting, similar to how lint diagnostics are handled:
```python
parse_errors = []
for path in dv_files:
    try:
        modules.append(parse_file(path))
    except DVMLParseError as e:
        parse_errors.append(e)
if parse_errors:
    for e in parse_errors:
        console.print(format_parse_error(e))
    raise typer.Exit(code=1)
```

---

### IN-02: `lsp` command is a stub with a TODO comment

**File:** `src/dmjedi/cli/main.py:138-142`

**Issue:** The `lsp` command body is `typer.echo("Starting DVML Language Server...")` followed by a `# TODO: launch pygls server` comment. This is intentional scaffolding but the TODO signals unfinished work and the function silently succeeds (`exit_code == 0`) while doing nothing.

**Suggestion:** Either raise `typer.Exit(code=1)` with a "not yet implemented" message, or remove the command until the LSP is ready. The current behavior misleads users who invoke `dmjedi lsp`.

---

### IN-03: `bridge_decl` silently drops second and subsequent `path` declarations

**File:** `src/dmjedi/lang/parser.py:319-332`

**Issue:** In `bridge_decl`, the loop processes members and assigns `path = m` for any `list` member. If two `path` declarations appeared in the same bridge body, the second would silently overwrite the first — no error, no warning. The grammar (`bridge_body: bridge_member*`, `bridge_member: path_decl | field_decl`) permits this syntactically. This is a minor latent correctness risk, analogous to the `samlink` issue in WR-01.

**Suggestion:** Raise a parse error if `path` is already non-empty when a second `path` member is encountered, or enforce uniqueness with a grammar-level rule.

---

### IN-04: Snapshot file uses a `*` wildcard import

**File:** `tests/snapshots/test_integration/test_spark_hub_snapshot/hub_customer.py:3`

**Issue:** The snapshot contains `from pyspark.sql.types import *`. This is generated output (so the generator produces the wildcard), not test code itself. Wildcard imports are generally discouraged; if any PySpark type name clashes with a local variable in user pipeline code, debugging is difficult. The snapshot only reflects what `_IMPORTS` in the generator emits.

**Suggestion:** In `generators/spark_declarative/generator.py:7`, consider enumerating the specific types needed (e.g., `from pyspark.sql.types import IntegerType, StringType, ...`) or accept the wildcard as a deliberate DLT convention and document it.

---

### IN-05: `type_name` transformer method is unreachable dead code

**File:** `src/dmjedi/lang/parser.py:164-167`

**Issue:** The grammar defines `type_name` with alias rules (`-> type_int`, `-> type_string`, etc.). When Lark processes an alias rule, it calls the method corresponding to the alias (e.g., `type_int`), not the parent rule method (`type_name`). The `type_name` method at line 164 (`return str(children[0])`) can never be called via the normal Lark alias dispatch path. It exists as a fallback but its presence may mislead future maintainers into thinking it is the primary dispatch point.

**Suggestion:** Add a comment explaining this method is a safety fallback that Lark's alias dispatch will never invoke in normal operation, or remove it if confidence in the alias-only path is high.

---

_Reviewed: 2026-04-08T14:10:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
