# Phase 8: Non-Historized Entities - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-08
**Phase:** 08-non-historized-entities
**Areas discussed:** Domain model design, MERGE/overwrite SQL pattern, Resolver validation rules, Generator output layout

---

## Domain Model Design

| Option | Description | Selected |
|--------|-------------|----------|
| Separate classes | New NhSat and NhLink classes alongside existing Satellite and Link | ✓ |
| Subclass existing types | NhSat(Satellite) and NhLink(Link) inheriting from existing classes | |
| You decide | Claude picks the best approach | |

**User's choice:** Separate classes (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Own dicts | DataVaultModel gets nhsats and nhlinks as new dict fields | ✓ |
| Shared dicts with flag | Satellite/Link get is_historized bool field | |
| You decide | Claude picks | |

**User's choice:** Own dicts (Recommended)

---

## MERGE/Overwrite SQL Pattern

| Option | Description | Selected |
|--------|-------------|----------|
| MERGE INTO | Standard SQL MERGE — UPDATE existing, INSERT new | ✓ |
| DELETE + INSERT | Delete matching rows first, then INSERT all | |
| INSERT OVERWRITE | Spark-native full partition overwrite | |

**User's choice:** MERGE INTO (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| apply_changes() | DLT's built-in SCD Type 1 API | ✓ |
| foreachBatch with MERGE | Lower-level custom merge | |
| You decide | Claude picks | |

**User's choice:** apply_changes() (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Parent hash key | nhsat matches on parent_hk, nhlink on link_hk | ✓ |
| Business keys directly | Match on parent's business keys | |
| You decide | Claude picks | |

**User's choice:** Parent hash key (Recommended)

---

## Resolver Validation Rules

| Option | Description | Selected |
|--------|-------------|----------|
| Same rules | nhsat parent_ref must reference existing hub or link, same as satellite | ✓ |
| Hub-only parents | nhsat can only attach to hubs, not links | |
| You decide | Claude picks | |

**User's choice:** Same rules (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, same rule | NhLink must reference ≥2 hubs, same as Link | ✓ |
| Relaxed (1+ hubs) | Allow nhlink with 1 hub reference | |
| You decide | Claude picks | |

**User's choice:** Yes, same rule (Recommended)

---

## Generator Output Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Same dirs as sat/link | nhsat in satellites/, nhlink in links/, prefix distinguishes | ✓ |
| Separate directories | nhsatellites/ and nhlinks/ as new top-level dirs | |
| You decide | Claude picks | |

**User's choice:** Same dirs as sat/link (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Separate templates | nhsat.sql.j2 and nhlink.sql.j2 as new files | ✓ |
| Parameterized shared | sat.sql.j2 with {% if historized %} branch | |

**User's choice:** Separate templates (Recommended)

---

## Claude's Discretion

- apply_changes() parameter configuration
- SQL MERGE dialect variations
- Test fixture design
- NhSat/NhLink base mixin decision

## Deferred Ideas

None
