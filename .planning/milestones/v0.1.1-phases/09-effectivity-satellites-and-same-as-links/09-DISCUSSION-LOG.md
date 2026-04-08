# Phase 9: Effectivity Satellites and Same-As Links - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-08
**Phase:** 09-effectivity-satellites-and-same-as-links
**Areas discussed:** EffSat temporal field handling, SamLink same-hub validation, Naming convention config, Domain model design

---

## EffSat Temporal Field Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Regular fields, no special tagging | Temporal fields are just regular FieldDef entries | ✓ |
| Keyword-tagged fields | Grammar adds 'temporal' keyword before field declarations | |
| You decide | Claude picks | |

**User's choice:** Regular fields, no special tagging (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Linter rule | LintDiagnostic warning, post-parse | ✓ |
| Resolver validation | Hard error in resolver | |
| You decide | Claude picks | |

**User's choice:** Linter rule (Recommended)

---

## SamLink Same-Hub Validation

| Option | Description | Selected |
|--------|-------------|----------|
| Linter rule | LINT-02 as LintDiagnostic warning | ✓ |
| Resolver validation | Hard error in resolver | |
| Both | Linter warns, resolver errors | |

**User's choice:** Linter rule (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| String match | master_ref == duplicate_ref as declared | ✓ |
| Resolved entity match | Resolve both to hub entities, compare qualified names | |
| You decide | Claude picks | |

**User's choice:** String match (Recommended)

---

## Naming Convention Config

| Option | Description | Selected |
|--------|-------------|----------|
| pyproject.toml section | [tool.dmjedi.lint] in pyproject.toml | |
| Dedicated .dvml-lint.toml file | Separate lint config file | ✓ |
| CLI flags only | --naming-prefix and --naming-suffix | |
| You decide | Claude picks | |

**User's choice:** Dedicated .dvml-lint.toml file

| Option | Description | Selected |
|--------|-------------|----------|
| Prefix per entity type | Required prefix per entity type | ✓ |
| Prefix + suffix per entity type | Both prefix and suffix configurable | |
| Regex per entity type | Full regex pattern per entity type | |
| You decide | Claude picks | |

**User's choice:** Prefix per entity type (Recommended)

---

## Domain Model Design

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, same pattern | Separate classes, own dicts, follows Phase 8 | ✓ |
| Different approach | Describe alternative | |

**User's choice:** Yes, same pattern (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Separate fields | master_ref and duplicate_ref as separate str fields | ✓ |
| hub_references list | Reuse list[str] like Link | |

**User's choice:** Separate fields (Recommended)

---

## Claude's Discretion

- EffSat resolver validation rules
- .dvml-lint.toml format and parsing
- Default naming prefixes
- Test fixture design

## Deferred Ideas

- Code generation for effsat/samlink — Phase 11
- Documentation for effsat/samlink — Phase 11
