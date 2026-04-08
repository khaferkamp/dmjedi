---
phase: 8
slug: non-historized-entities
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-08
validated: 2026-04-08
---

# Phase 8 — Validation Strategy

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
| 08-01-01 | 01 | 1 | ENTITY-03, ENTITY-04 | T-08-01, T-08-02 | model_validator enforces 2-hub min; resolver validates parent_ref | unit | `pytest tests/test_model.py -x -q` | ✅ | ✅ green |
| 08-01-02 | 01 | 1 | ENTITY-03, ENTITY-04 | T-08-03 | Resolver detects duplicate nhsat/nhlink names | unit | `pytest tests/test_model.py -x -q` | ✅ | ✅ green |
| 08-02-01 | 02 | 2 | GEN-03 | T-08-05 | SQL uses MERGE INTO (Jinja2 variable substitution, grammar-constrained names) | unit | `pytest tests/test_generators.py -x -q` | ✅ | ✅ green |
| 08-02-02 | 02 | 2 | GEN-03 | T-08-06 | Spark uses apply_changes (grammar-constrained names in f-strings) | unit | `pytest tests/test_generators.py -x -q` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Requirement Coverage Detail

| Requirement | Tests | Count | Status |
|-------------|-------|-------|--------|
| ENTITY-03 | test_parse_nhsat, test_parse_nhsat_empty_body, test_resolve_nhsat, test_nhsat_invalid_parent_raises, test_nhsat_parent_ref_to_link_valid, test_nhsat_qualified_name, test_duplicate_nhsat_raises | 7 | ✅ COVERED |
| ENTITY-04 | test_parse_nhlink, test_parse_nhlink_three_refs, test_resolve_nhlink, test_nhlink_requires_two_refs, test_nhlink_qualified_name, test_duplicate_nhlink_raises | 6 | ✅ COVERED |
| GEN-03 | test_sql_nhsat_output_valid, test_sql_nhlink_output_valid, test_sql_nhsat_no_columns_valid, test_sql_nhlink_no_columns_valid, test_spark_nhsat_output_functional, test_spark_nhlink_output_functional, test_spark_nhsat_no_columns | 7 | ✅ COVERED |

**Total: 20 tests covering 3 requirements. 0 gaps.**

---

## Wave 0 Requirements

- [x] `tests/test_model.py` — extended with nhsat/nhlink domain model and resolver tests (10 new tests)

*Existing infrastructure covers framework requirements.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-04-08

---

## Validation Audit 2026-04-08

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
