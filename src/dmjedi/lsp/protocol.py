"""Typed mapping helpers between DMJEDI diagnostics and LSP diagnostics."""

from __future__ import annotations

from lsprotocol import types

from dmjedi.lang.ast import SourceLocation
from dmjedi.lang.linter import LintDiagnostic, Severity
from dmjedi.lang.parser import DVMLParseError

_WORD_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-")
_SEVERITY_MAP = {
    Severity.ERROR: types.DiagnosticSeverity.Error,
    Severity.WARNING: types.DiagnosticSeverity.Warning,
    Severity.INFO: types.DiagnosticSeverity.Information,
}


def range_from_location(
    source: str,
    location: SourceLocation,
    fallback_length: int = 1,
) -> types.Range:
    """Build an LSP range from a start-only source location and current document text."""
    lines = source.splitlines(keepends=True)
    line_index = max(location.line - 1, 0)
    character = max(location.column - 1, 0)

    if line_index >= len(lines):
        end_character = character + max(fallback_length, 1)
        return types.Range(
            start=types.Position(line=line_index, character=character),
            end=types.Position(line=line_index, character=end_character),
        )

    line_text = lines[line_index].rstrip("\r\n")
    token_length = _token_length_at_column(line_text, character, fallback_length)

    return types.Range(
        start=types.Position(line=line_index, character=character),
        end=types.Position(line=line_index, character=character + token_length),
    )


def parse_error_to_lsp(error: DVMLParseError, source: str) -> types.Diagnostic:
    """Convert a structured parse error into an LSP diagnostic."""
    return types.Diagnostic(
        range=range_from_location(source, _parse_error_location(error), fallback_length=1),
        message=error.error.hint,
        severity=types.DiagnosticSeverity.Error,
        source="dmjedi",
    )


def lint_diagnostic_to_lsp(diagnostic: LintDiagnostic, source: str) -> types.Diagnostic:
    """Convert a lint diagnostic into an LSP diagnostic."""
    return types.Diagnostic(
        range=range_from_location(source, diagnostic.loc, fallback_length=1),
        message=diagnostic.message,
        severity=_SEVERITY_MAP[diagnostic.severity],
        code=diagnostic.rule,
        source="dmjedi",
    )


def _parse_error_location(error: DVMLParseError) -> SourceLocation:
    return SourceLocation(
        file=error.error.file,
        line=error.error.line,
        column=error.error.column,
    )


def name_range_from_location(source: str, location: SourceLocation, name: str) -> types.Range:
    """Build a range for an entity name that appears after a declaration keyword."""
    line_index = max(location.line - 1, 0)
    character = max(location.column - 1, 0)
    line_text = source.splitlines()[line_index] if line_index < len(source.splitlines()) else ""
    name_start = line_text.find(name, character)
    if name_start < 0:
        name_start = character
    return types.Range(
        start=types.Position(line=line_index, character=name_start),
        end=types.Position(line=line_index, character=name_start + max(len(name), 1)),
    )


def block_range_from_location(source: str, location: SourceLocation) -> types.Range:
    """Build a coarse declaration block range from its opening line to closing brace."""
    lines = source.splitlines()
    line_index = max(location.line - 1, 0)
    if line_index >= len(lines):
        return range_from_location(source, location, fallback_length=1)

    end_line = line_index
    for candidate in range(line_index, len(lines)):
        end_line = candidate
        if "}" in lines[candidate]:
            break
    return types.Range(
        start=types.Position(line=line_index, character=0),
        end=types.Position(line=end_line, character=len(lines[end_line])),
    )


def build_hover(
    source: str,
    name: str,
    kind: str,
    location: SourceLocation,
    business_keys: list[str],
    fields: list[str],
    references: list[str],
) -> types.Hover:
    """Build markdown hover content for a declaration or reference."""
    lines = [f"```dvml\n{kind} {name}\n```"]
    if business_keys:
        lines.append(f"Business keys: {', '.join(business_keys)}")
    if fields:
        lines.append(f"Fields: {', '.join(fields)}")
    if references:
        lines.append(f"Relationships: {', '.join(references)}")
    lines.append(f"Defined at {location.file or '<memory>'}:{location.line}:{location.column}")
    return types.Hover(
        contents=types.MarkupContent(
            kind=types.MarkupKind.Markdown,
            value="\n\n".join(lines),
        ),
        range=name_range_from_location(source, location, name),
    )


def build_definition_location(
    uri: str,
    source: str,
    name: str,
    location: SourceLocation,
) -> types.Location:
    """Build a definition location for a current-document declaration."""
    return types.Location(
        uri=uri,
        range=name_range_from_location(source, location, name),
    )


def build_document_symbol(
    source: str,
    name: str,
    kind: str,
    location: SourceLocation,
    detail: str,
) -> types.DocumentSymbol:
    """Build a document symbol entry for a DVML declaration."""
    return types.DocumentSymbol(
        name=name,
        detail=detail,
        kind=_symbol_kind(kind),
        range=block_range_from_location(source, location),
        selection_range=name_range_from_location(source, location, name),
    )


def _symbol_kind(kind: str) -> types.SymbolKind:
    return {
        "hub": types.SymbolKind.Class,
        "satellite": types.SymbolKind.Struct,
        "link": types.SymbolKind.Interface,
        "nhsat": types.SymbolKind.Struct,
        "nhlink": types.SymbolKind.Interface,
        "effsat": types.SymbolKind.Struct,
        "samlink": types.SymbolKind.Interface,
        "bridge": types.SymbolKind.Function,
        "pit": types.SymbolKind.Object,
    }.get(kind, types.SymbolKind.Class)


def _token_length_at_column(line_text: str, character: int, fallback_length: int) -> int:
    if character >= len(line_text):
        return max(fallback_length, 1)

    end = character
    while end < len(line_text) and line_text[end] in _WORD_CHARS:
        end += 1

    if end > character:
        return end - character
    return max(fallback_length, 1)
