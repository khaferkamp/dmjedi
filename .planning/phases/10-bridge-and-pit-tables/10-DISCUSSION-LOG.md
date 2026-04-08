# Phase 10: Bridge and PIT Tables - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-08
**Phase:** 10-bridge-and-pit-tables
**Areas discussed:** Bridge domain model, Path validation, PIT satellite ownership, View generation

---

## Bridge Domain Model

| Option | Description | Selected |
|--------|-------------|----------|
| Flat list of refs | path: list[str] — mirrors AST exactly. Validation logic interprets alternating Hub/Link pattern. | ✓ |
| Typed pairs list | path: list[PathStep] where PathStep has (ref, entity_type). Richer model. | |
| Hub/link split lists | hub_refs: list[str] + link_refs: list[str]. Loses ordering. | |

**User's choice:** Flat list of refs
**Notes:** Consistent with how Link stores hub_references. Simple, mirrors AST.

### PIT Domain Model (follow-up)

| Option | Description | Selected |
|--------|-------------|----------|
| Mirror AST | anchor_ref: str + tracked_satellites: list[str], same as PitDecl | ✓ |
| Resolved satellite refs | tracked_satellites stores qualified names | |

**User's choice:** Mirror AST
**Notes:** Consistent with Bridge decision.

---

## Path Validation

| Option | Description | Selected |
|--------|-------------|----------|
| Alternating Hub→Link→Hub | Odd positions = hubs, even = links. Start/end with hub. Min 3 elements. | ✓ |
| All refs exist, no type check | Only validate names resolve. No alternating pattern enforcement. | |
| Strict: alternating + link connects hubs | Alternating AND each link references adjacent hubs. Full graph check. | |

**User's choice:** Alternating Hub→Link→Hub
**Notes:** None

### LINT-04 Error Type (follow-up)

| Option | Description | Selected |
|--------|-------------|----------|
| Resolver error | Hard error — bridge meaningless without valid chain. Matches roadmap wording. | ✓ |
| Linter warning | Warn but don't block. | |

**User's choice:** Resolver error
**Notes:** Roadmap says "Resolver validates" — resolver error is consistent.

---

## PIT Satellite Ownership

| Option | Description | Selected |
|--------|-------------|----------|
| Direct parent match | Satellite's parent_ref must equal PIT's anchor_ref. Clean, simple. | ✓ |
| Include NhSat too | Also accept NhSat entities with matching parent_ref. | |
| Transitive via links | Also accept satellites of links referencing the anchor hub. | |

**User's choice:** Direct parent match
**Notes:** Matches DV 2.1 PIT semantics.

### LINT-05 Error Type (follow-up)

| Option | Description | Selected |
|--------|-------------|----------|
| Resolver error | Consistent with LINT-04. PIT tracking wrong satellites is fundamentally broken. | ✓ |
| Linter warning | Warn but allow. | |

**User's choice:** Resolver error
**Notes:** Consistent with LINT-04 decision.

---

## View Generation

### SQL Generation

| Option | Description | Selected |
|--------|-------------|----------|
| CREATE VIEW + SELECT | `CREATE OR REPLACE VIEW` wrapping SELECT with JOINs. Standard SQL, portable. | ✓ |
| SELECT only (no DDL) | Just the SELECT statement. User wraps however they want. | |
| Configurable | Default to CREATE VIEW, flag for bare SELECT or CREATE TABLE. | |

**User's choice:** CREATE VIEW + SELECT
**Notes:** None

### Spark DLT Generation

| Option | Description | Selected |
|--------|-------------|----------|
| DLT view function | @dlt.view decorator. Views are recomputed, not stored. | ✓ |
| DLT table (materialized) | @dlt.table — materializes for performance. Contradicts GEN-04. | |
| You decide | Let Claude pick. | |

**User's choice:** DLT view function
**Notes:** Fits DLT semantics — views recomputed, not stored.

### Output Directory

| Option | Description | Selected |
|--------|-------------|----------|
| Separate views/ directory | bridge and pit files in views/. Distinguishes from physical tables. | ✓ |
| Mixed in entity dirs | bridge in bridges/, pit in pits/. Each type gets own dir. | |
| You decide | Let Claude pick. | |

**User's choice:** Separate views/ directory
**Notes:** For now store in views/. Future phases will introduce raw vault / business vault structures using namespaces. Start simple first.

---

## Claude's Discretion

- SQL JOIN condition details (hash key matching across dialects)
- PIT snapshot logic (latest record per satellite, temporal join)
- Spark DataFrame join implementation
- SQL Jinja template file names and structure
- Test fixture `.dv` file design

## Deferred Ideas

- Raw vault / business vault directory organization using namespaces — future phase
- Materialized bridge/PIT (CREATE TABLE) — future enhancement
- NhSat/EffSat as valid PIT tracking targets — extend LINT-05 later
- Strict bridge connectivity (links reference adjacent hubs) — strengthen LINT-04 later
