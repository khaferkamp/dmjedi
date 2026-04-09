# Phase 11: Output Completeness - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-08
**Phase:** 11-output-completeness
**Areas discussed:** EffSat/SamLink generation, Docs generator expansion, Mermaid ER diagrams, --dialect CLI flag

---

## EffSat/SamLink Code Generation

### EffSat SQL Pattern

| Option | Description | Selected |
|--------|-------------|----------|
| INSERT historized | Standard satellite INSERT pattern | |
| MERGE INTO | MERGE pattern for temporal validity updates | ✓ |
| You decide | Let Claude pick | |

**User's choice:** MERGE INTO (user corrected initial INSERT selection to MERGE)
**Notes:** Temporal validity records need update semantics.

### SamLink SQL Pattern

| Option | Description | Selected |
|--------|-------------|----------|
| Standard link INSERT | Same INSERT as regular links | |
| MERGE for deduplication | MERGE pattern for updateable dedup relationships | ✓ |
| You decide | Let Claude pick | |

**User's choice:** MERGE for deduplication
**Notes:** None

### Spark DLT Patterns

| Option | Description | Selected |
|--------|-------------|----------|
| Match SQL patterns | EffSat and SamLink both use apply_changes(scd_type=1) | ✓ |
| You decide | Let Claude pick | |

**User's choice:** Match SQL patterns
**Notes:** Both use MERGE semantics via apply_changes.

### Output Directories

| Option | Description | Selected |
|--------|-------------|----------|
| Entity-type dirs | effsat→satellites/, samlink→links/ | ✓ |
| Separate dirs | effsat/, samlink/ | |

**User's choice:** Entity-type dirs
**Notes:** Consistent with Phase 8 nhsat/nhlink convention.

---

## Docs Generator Expansion

| Option | Description | Selected |
|--------|-------------|----------|
| Grouped by category | Raw Vault + Query Assist sections | ✓ |
| Flat list | All types as top-level sections | |
| You decide | Let Claude pick | |

**User's choice:** Grouped by category
**Notes:** Raw Vault (hubs, links, satellites, nhsat, nhlink, effsat, samlink) and Query Assist (bridge, pit).

---

## Mermaid ER Diagrams

### Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Single diagram per model | One erDiagram covering all entities | ✓ |
| Split by category | Separate diagrams per category | |
| You decide | Let Claude pick | |

**User's choice:** Single diagram per model
**Notes:** None

### Placement

| Option | Description | Selected |
|--------|-------------|----------|
| At the top | Diagram first, then details | ✓ |
| At the bottom | Details first, diagram summary | |
| Separate file | Alongside main docs | |

**User's choice:** At the top
**Notes:** Overview-first layout.

---

## --dialect CLI Flag

| Option | Description | Selected |
|--------|-------------|----------|
| Only for sql-jinja target | --dialect ignored with warning for other targets | ✓ |
| Universal flag | Affects all generators | |
| You decide | Let Claude pick | |

**User's choice:** Only for sql-jinja target
**Notes:** Choices: default, postgres, spark. Default value: default.

---

## Claude's Discretion

- MERGE match key details for effsat and samlink across dialects
- Mermaid relationship cardinality annotations
- Docs markdown formatting for new entity sections
- apply_changes() parameter tuning
- Test fixture design

## Deferred Ideas

None — discussion stayed within phase scope.
