---
phase: 7
slug: parser-hardening-and-data-types
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-08
---

# Phase 7 — Validation Strategy

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
| 07-01-01 | 01 | 1 | PARSE-01 | — | N/A | unit | `pytest tests/test_parser.py -x -q` | ✅ | ⬜ pending |
| 07-01-02 | 01 | 1 | PARSE-02 | — | N/A | unit | `pytest tests/test_parser.py -x -q` | ❌ W0 | ⬜ pending |
| 07-01-03 | 01 | 1 | PARSE-03 | — | N/A | unit | `pytest tests/test_parser.py -x -q` | ❌ W0 | ⬜ pending |
| 07-02-01 | 02 | 1 | TYPE-01 | — | N/A | unit | `pytest tests/test_parser.py -x -q` | ❌ W0 | ⬜ pending |
| 07-02-02 | 02 | 1 | TYPE-02 | — | N/A | unit | `pytest tests/test_types.py -x -q` | ❌ W0 | ⬜ pending |
| 07-02-03 | 02 | 1 | TYPE-03 | — | N/A | unit | `pytest tests/test_types.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_parser.py` — extend with error format and new type parsing tests
- [ ] `tests/test_types.py` — new file for shared type mapping module tests
- [ ] `tests/conftest.py` — shared fixtures (already exists)

*Existing infrastructure covers framework requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Color output auto-detects TTY | PARSE-02 | TTY detection requires real terminal | Run `dmjedi validate bad.dv` in terminal, verify colored output; pipe to file, verify no ANSI codes |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
