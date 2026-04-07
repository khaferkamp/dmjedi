"""DVML Language Server — provides diagnostics, completion, and hover for .dv files."""

# Placeholder — will be implemented with pygls.
# Architecture:
#   - On open/change: parse with dmjedi.lang.parser, run dmjedi.lang.linter
#   - Publish diagnostics from lint results
#   - Provide completion for keywords, entity references
#   - Provide hover info for entity definitions
