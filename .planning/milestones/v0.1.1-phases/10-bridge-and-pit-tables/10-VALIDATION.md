---
phase: 10
slug: bridge-and-pit-tables
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-08
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pyproject.toml` |
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
| 10-01-01 | 01 | 1 | QUERY-01 | — | N/A | unit | `pytest tests/test_model.py -k bridge -x` | ❌ W0 | ⬜ pending |
| 10-01-02 | 01 | 1 | QUERY-02 | — | N/A | unit | `pytest tests/test_model.py -k pit -x` | ❌ W0 | ⬜ pending |
| 10-01-03 | 01 | 1 | LINT-04 | — | N/A | unit | `pytest tests/test_resolver.py -k bridge -x` | ❌ W0 | ⬜ pending |
| 10-01-04 | 01 | 1 | LINT-05 | — | N/A | unit | `pytest tests/test_resolver.py -k pit -x` | ❌ W0 | ⬜ pending |
| 10-02-01 | 02 | 2 | GEN-04 | — | N/A | unit | `pytest tests/test_generators.py -k bridge -x` | ❌ W0 | ⬜ pending |
| 10-02-02 | 02 | 2 | GEN-04 | — | N/A | unit | `pytest tests/test_generators.py -k pit -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_model.py` — add Bridge and Pit model construction tests
- [ ] `tests/test_resolver.py` — add bridge path validation and PIT satellite ownership tests
- [ ] `tests/test_generators.py` — add bridge and PIT view generation tests

*Existing infrastructure covers test framework and fixtures.*

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
