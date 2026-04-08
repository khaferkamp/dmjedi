---
phase: 11
slug: output-completeness
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-08
---

# Phase 11 — Validation Strategy

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
| 11-01-01 | 01 | 1 | GEN-01 | — | N/A | unit | `pytest tests/test_generators.py -k "effsat or samlink" -x` | ❌ W0 | ⬜ pending |
| 11-01-02 | 01 | 1 | GEN-02 | — | N/A | unit | `pytest tests/test_generators.py -k "effsat or samlink" -x` | ❌ W0 | ⬜ pending |
| 11-02-01 | 02 | 2 | DOC-01 | — | N/A | unit | `pytest tests/test_docs.py -x` | ❌ W0 | ⬜ pending |
| 11-02-02 | 02 | 2 | DOC-02 | — | N/A | unit | `pytest tests/test_docs.py -k mermaid -x` | ❌ W0 | ⬜ pending |
| 11-02-03 | 02 | 2 | CLI-01 | — | N/A | unit | `pytest tests/test_cli.py -k dialect -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_generators.py` — add effsat/samlink generation tests
- [ ] `tests/test_docs.py` — create new test file for docs generator (currently untested)
- [ ] `tests/test_cli.py` — verify existence, add --dialect flag tests

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
