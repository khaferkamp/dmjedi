---
status: diagnosed
phase: 04-lsp-server
source: [04-01-SUMMARY.md, 04-02-SUMMARY.md, 04-03-SUMMARY.md]
started: 2026-04-20T00:00:00+02:00
updated: 2026-04-21T00:05:00+02:00
updated: 2026-04-21T00:06:00+02:00
---

## Current Test

[testing complete]

## Tests

### 1. Start the LSP server
expected: Running `dmjedi lsp` should start a real stdio language server process instead of printing "not yet implemented" and exiting immediately with an error.
result: pass

### 2. Parse diagnostics appear for invalid DVML
expected: Opening or editing a malformed `.dv` document should surface a parse diagnostic at the current document position instead of failing silently.
result: pass

### 3. Lint diagnostics appear for valid-but-problematic DVML
expected: Opening or editing a `.dv` document with lint issues, such as a hub with no business key, should surface a warning or error diagnostic for that current document.
result: pass

### 4. Keyword completions are offered conservatively
expected: While typing DVML declaration keywords or field types, completion should offer relevant low-noise keyword suggestions rather than a broad unrelated symbol dump.
result: pass

### 5. Same-document entity references auto-complete
expected: In places like `of`, `references`, `master`, `duplicate`, `path`, or `tracks`, completion should suggest matching entities declared in the same document.
result: issue
reported: "At least in Vim I cannot verify that it works as expected. The completion shows entries, but I am not sure wether these are just Keywords in the buffer and that they are semantically correct. One example: When I define a satellite of satellite the LSP should yell an error, as satellites are just allowed on top of Links, Hubs and Reference Tables. What do you think?"
severity: major

### 6. Hover shows entity details
expected: Hovering a declaration or same-document reference should show useful entity details such as kind, keys or fields, relationships, and source location.
result: pass

### 7. Go-to-definition resolves same-document references
expected: Triggering go-to-definition on a same-document entity reference should jump to that entity's declaration in the current `.dv` file.
result: pass

### 8. Document symbols outline the current file
expected: The editor's document symbol view should list the entities in the open `.dv` file in a usable outline for navigation.
result: pass

## Summary

total: 8
passed: 6
passed: 7
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps
- truth: "In places like `of`, `references`, `master`, `duplicate`, `path`, or `tracks`, completion should suggest matching entities declared in the same document."
  status: failed
  reason: "User reported: At least in Vim I cannot verify that it works as expected. The completion shows entries, but I am not sure wether these are just Keywords in the buffer and that they are semantically correct. One example: When I define a satellite of satellite the LSP should yell an error, as satellites are just allowed on top of Links, Hubs and Reference Tables. What do you think?"
  severity: major
  test: 5
  root_cause: "The Phase 4 LSP only runs current-document parse and lint helpers from `src/dmjedi/lsp/analysis.py`; it does not run resolver-backed, model-aware validation in the editor, so invalid parent relationships like satellite-of-satellite are not surfaced as diagnostics. The current completion behavior is same-document AST-based, but it does not prove semantic validity of references."
  artifacts:
    - path: "src/dmjedi/lsp/analysis.py"
      issue: "Only parse/lint execution; no resolver/model-aware validation path"
    - path: "src/dmjedi/lang/linter.py"
      issue: "No regular satellite parent-kind rule analogous to effsat parent validation"
    - path: "src/dmjedi/model/resolver.py"
      issue: "Semantic parent validation exists for known entity kinds but is not integrated into LSP diagnostics"
  missing:
    - "Integrate safe current-document semantic validation into the LSP diagnostics path"
    - "Add a rule or resolver-backed diagnostic for invalid regular satellite parent relationships"
    - "Clarify or tighten completion/diagnostic expectations so semantic validity is visible in-editor"
  debug_session: "Phase 04 UAT analysis on 2026-04-21"
