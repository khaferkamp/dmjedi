---
phase: 9
slug: effectivity-satellites-and-same-as-links
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-08
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | ENTITY-01, ENTITY-02 | — | N/A | unit | `pytest tests/test_model.py -x -q` | ✅ | ⬜ pending |
| 09-01-02 | 01 | 1 | ENTITY-01, ENTITY-02 | — | N/A | unit | `pytest tests/test_model.py -x -q` | ✅ | ⬜ pending |
| 09-02-01 | 02 | 2 | LINT-01, LINT-02 | — | N/A | unit | `pytest tests/test_linter.py -x -q` | ✅ | ⬜ pending |
| 09-02-02 | 02 | 2 | LINT-03 | — | N/A | unit | `pytest tests/test_linter.py -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_model.py` — extend with effsat/samlink domain model and resolver tests
- [ ] `tests/test_linter.py` — extend with LINT-01, LINT-02, LINT-03 tests

*Existing infrastructure covers framework requirements.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
