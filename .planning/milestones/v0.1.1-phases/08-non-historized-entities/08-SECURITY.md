# Security Audit — Phase 08: Non-Historized Entities

**Audit Date:** 2026-04-08
**ASVS Level:** 1
**Phase Plans Audited:** 08-01, 08-02
**Auditor:** GSD Security Phase (claude-sonnet-4-6)

---

## Threat Verification

| Threat ID | Category | Disposition | Status | Evidence |
|-----------|----------|-------------|--------|----------|
| T-08-01 | Tampering | mitigate | CLOSED | `src/dmjedi/model/core.py:82-87` — `NhLink._check_min_refs` model_validator raises `ValueError("NhLink '{self.name}' must reference at least 2 hubs")` when `len(self.hub_references) < 2` |
| T-08-02 | Tampering | mitigate | CLOSED | `src/dmjedi/model/resolver.py:178-194` — post-resolution loop checks each `nhsat.parent_ref` against `model.hubs` and `model.links` (both plain and namespace-qualified forms); raises `ResolverErrors` with message `"references unknown parent"` if not found |
| T-08-03 | Denial of Service | mitigate | CLOSED | `src/dmjedi/model/resolver.py:120-132` (nhsat) and `144-156` (nhlink) — duplicate qualified-name check inside each resolution loop; `errors.append(ResolverError(...))` with `"Duplicate nhsat"` / `"Duplicate nhlink"` message; `ResolverErrors` raised at line 197 if any errors accumulated |
| T-08-04 | Information Disclosure | accept | CLOSED | Accepted: generated SQL/Spark files are inert text written to the user-specified output directory. No credentials, secrets, or PII involved. No transfer documentation required. |
| T-08-05 | Injection | accept | CLOSED | Accepted: entity names are constrained by Lark grammar to alphanumeric + underscore identifiers before reaching templates. Jinja2 performs variable substitution, not free-text interpolation. SQL templates in `nhsat.sql.j2` and `nhlink.sql.j2` use only `nhsat.*` / `nhlink.*` grammar-validated properties. |
| T-08-06 | Injection | accept | CLOSED | Accepted: same rationale as T-08-05. Spark generator uses f-string interpolation of `nhsat.name`, `nhsat.parent_ref`, `nhlink.name` — all grammar-constrained identifiers from the resolver. See `src/dmjedi/generators/spark_declarative/generator.py:125-171`. |
| T-08-07 | Information Disclosure | accept | CLOSED | Accepted: generated `.py` and `.sql` files contain only inert code patterns. No secrets, PII, or runtime credentials appear in generated output. |

---

## Accepted Risks Log

| Threat ID | Accepted By | Rationale |
|-----------|-------------|-----------|
| T-08-04 | Plan 08-01 threat model | Generated files are local inert text; no sensitive data in scope |
| T-08-05 | Plan 08-02 threat model | Grammar enforces identifier constraints upstream of template rendering |
| T-08-06 | Plan 08-02 threat model | Grammar enforces identifier constraints upstream of f-string generation |
| T-08-07 | Plan 08-02 threat model | Generated files are local inert text; no sensitive data in scope |

---

## Unregistered Threat Flags

None. The `## Threat Flags` section of 08-02-SUMMARY.md explicitly states: "None. No new network endpoints, auth paths, or trust-boundary changes introduced."

---

## Verification Detail

### T-08-01 (NhLink 2-hub minimum)

`src/dmjedi/model/core.py` lines 82-87:

```python
@model_validator(mode="after")
def _check_min_refs(self) -> "NhLink":
    if len(self.hub_references) < 2:
        msg = f"NhLink '{self.name}' must reference at least 2 hubs"
        raise ValueError(msg)
    return self
```

Validator fires at Pydantic construction time. Any attempt to create an `NhLink` with fewer than 2 `hub_references` raises `ValidationError` before the object exists.

### T-08-02 (NhSat parent_ref cross-reference)

`src/dmjedi/model/resolver.py` lines 178-194:

```python
for nhsat in model.nhsats.values():
    ref = nhsat.parent_ref
    ns_ref = f"{nhsat.namespace}.{ref}" if nhsat.namespace else ref
    if (
        ref not in model.hubs
        and ref not in model.links
        and ns_ref not in model.hubs
        and ns_ref not in model.links
    ):
        errors.append(ResolverError(
            message=f"NhSat '{nhsat.qualified_name}' references unknown parent '{ref}'",
        ))
```

Runs after all modules are resolved, checks both bare and namespace-qualified parent names against hubs and links. Errors accumulate and are raised together at line 197.

### T-08-03 (Duplicate entity name detection)

Both nhsat (lines 120-132) and nhlink (lines 144-156) loops in resolver check `if qname in model.nhsats` / `if qname in model.nhlinks` before insertion. Duplicates produce `ResolverError` entries and never enter the model.

---

## Summary

**Threats Closed:** 7/7
**Open Threats:** 0
**Unregistered Flags:** 0
**Block Condition (block_on: high):** Not triggered — no open high-severity threats.
