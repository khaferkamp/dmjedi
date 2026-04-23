---
status: complete
phase: 04-lsp-server
source: [04-01-SUMMARY.md, 04-02-SUMMARY.md, 04-03-SUMMARY.md]
started: 2026-04-20T00:00:00+02:00
updated: 2026-04-21T00:05:00+02:00
updated: 2026-04-23T09:27:00+02:00
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
result: pass

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
passed: 8
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
