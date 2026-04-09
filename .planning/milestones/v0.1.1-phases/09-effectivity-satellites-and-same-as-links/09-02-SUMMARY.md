---
phase: 09-effectivity-satellites-and-same-as-links
plan: "02"
subsystem: linter
tags: [linter, lint-rules, effsat, samlink, naming-convention, cli]
dependency_graph:
  requires: [09-01]
  provides: [LINT-01 effsat parent check, LINT-02 samlink same-hub check, LINT-03 naming convention]
  affects: [src/dmjedi/lang/linter.py, src/dmjedi/cli/main.py, tests/test_linter.py]
tech_stack:
  added: [tomllib (stdlib Python 3.11+)]
  patterns: [TDD red-green, TYPE_CHECKING for circular import avoidance, StrEnum]
key_files:
  created: []
  modified:
    - src/dmjedi/lang/linter.py
    - src/dmjedi/cli/main.py
    - tests/test_linter.py
decisions:
  - lint() uses optional model param with TYPE_CHECKING import to avoid circular dependency with model.core
  - CLI adds second lint pass post-resolve filtering to model-aware rules only (no duplicate diagnostics)
  - _load_lint_config returns empty dict when .dvml-lint.toml absent (silent enforcement)
  - Severity refactored from str+Enum to StrEnum to satisfy ruff UP042
metrics:
  duration: "~10 minutes"
  completed: "2026-04-08"
  tasks_completed: 2
  files_changed: 3
requirements_satisfied:
  - LINT-01
  - LINT-02
  - LINT-03
---

# Phase 09 Plan 02: EffSat/SamLink Linter Rules and Naming Convention Summary

**One-liner:** Three new linter rules (LINT-01 effsat parent check, LINT-02 samlink same-hub, LINT-03 configurable naming prefixes from .dvml-lint.toml) added to linter.py with extended lint() signature and CLI post-resolve lint pass.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Failing tests for LINT-01/02/03 | 084cf2d | tests/test_linter.py |
| 1 (GREEN) | Extend lint() with LINT-01/02/03 | 0a9fa85 | src/dmjedi/lang/linter.py |
| 2 | CLI post-resolve lint pass + fixes | 603fff3 | src/dmjedi/cli/main.py, src/dmjedi/lang/linter.py |

## Decisions Made

1. **TYPE_CHECKING import for DataVaultModel** — `from dmjedi.model.core import DataVaultModel` placed under `if TYPE_CHECKING:` to avoid circular import. Runtime type annotation uses string forward reference via `from __future__ import annotations`.

2. **CLI adds second lint pass post-resolve** — Rather than moving resolve() before the first lint pass (which would change error ordering), a second lint call is made after resolve() that filters to model-aware rules only (`effsat-parent-must-be-link`). This avoids duplicating AST-level diagnostics.

3. **_load_lint_config returns empty dict when absent** — Zero enforcement when .dvml-lint.toml is not present. Teams opt in to naming conventions explicitly.

4. **Severity refactored to StrEnum** — Pre-existing ruff UP042 violation (inheriting from both `str` and `Enum`) fixed since the file was touched. Changed to `class Severity(StrEnum)`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Pre-existing ruff UP042: Severity(str, Enum) -> StrEnum**
- **Found during:** Task 2 verification (ruff check)
- **Issue:** `class Severity(str, Enum)` violated ruff UP042 rule (pre-existing in base linter.py)
- **Fix:** Changed to `class Severity(StrEnum)` using `from enum import StrEnum`
- **Files modified:** src/dmjedi/lang/linter.py
- **Commit:** 603fff3

**2. [Rule 1 - Bug] mypy: untyped return and list[Any] annotation needed**
- **Found during:** Task 2 mypy verification
- **Issue:** `data.get("naming", {})` returned `Any` without intermediate typed variable; `list[tuple[str, list]]` needed type param
- **Fix:** Added `naming: dict[str, str] = data.get(...)` variable; changed to `list[tuple[str, list[Any]]]`; added `Any` to typing imports
- **Files modified:** src/dmjedi/lang/linter.py
- **Commit:** 603fff3

## Verification Results

- `uv run pytest tests/test_linter.py -x -q`: 16 passed
- `uv run pytest -x -q`: 149 passed (no regressions from 133 pre-plan baseline + 10 new tests)
- `uv run mypy src/dmjedi/lang/linter.py src/dmjedi/cli/main.py`: no issues
- `uv run ruff check src/dmjedi/lang/ src/dmjedi/cli/`: all checks passed

## Known Stubs

None — all three lint rules are fully implemented and tested. Naming convention enforcement is explicitly opt-in (absent config = no warnings) per design.

## Threat Flags

No new trust boundaries introduced beyond T-09-03/04/05 already in plan's threat model. The `_load_lint_config` function reads user-owned .dvml-lint.toml via stdlib tomllib (no code execution from config). Diagnostic messages contain only entity names from user's own .dv files.

## Self-Check: PASSED
