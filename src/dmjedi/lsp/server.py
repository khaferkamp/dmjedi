"""DVML Language Server bootstrap and diagnostics handlers."""

from __future__ import annotations

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from dmjedi.lsp.analysis import (
    DocumentAnalysis,
    analyze_document,
    completion_context,
    completion_items_for_context,
    declaration_infos,
    lookup_symbol_at_position,
)
from dmjedi.lsp.protocol import build_definition_location, build_document_symbol, build_hover

SERVER = LanguageServer("dmjedi", "0.2.0")
_ANALYSES: dict[str, DocumentAnalysis] = {}


def refresh_document(uri: str, source: str, version: int | None) -> DocumentAnalysis:
    """Analyze and cache the current in-memory contents for a document URI."""
    analysis = analyze_document(uri=uri, source=source, version=version)
    _ANALYSES[uri] = analysis
    return analysis


def publish_document_diagnostics(
    server: LanguageServer,
    uri: str,
    source: str,
    version: int | None,
) -> DocumentAnalysis:
    """Publish current-document diagnostics for a single text document."""
    analysis = refresh_document(uri=uri, source=source, version=version)
    server.text_document_publish_diagnostics(
        types.PublishDiagnosticsParams(
            uri=uri,
            diagnostics=analysis.diagnostics,
            version=version,
        )
    )
    return analysis


def get_analysis(uri: str) -> DocumentAnalysis | None:
    """Return cached analysis for a document URI if available."""
    return _ANALYSES.get(uri)


def document_completions(
    analysis: DocumentAnalysis, position: types.Position
) -> list[types.CompletionItem]:
    """Return conservative completions for the current document and cursor position."""
    context = completion_context(analysis.source, position.line, position.character)
    return completion_items_for_context(analysis, context)


def document_hover(analysis: DocumentAnalysis, position: types.Position) -> types.Hover | None:
    """Build hover content for a declaration or same-document reference."""
    match = lookup_symbol_at_position(analysis, position)
    if match is None:
        return None

    declaration = match.declaration
    return build_hover(
        source=analysis.source,
        name=declaration.name,
        kind=declaration.kind,
        location=declaration.loc,
        business_keys=[field.name for field in declaration.business_keys],
        fields=[field.name for field in declaration.fields],
        references=declaration.references,
    )


def document_definition(
    analysis: DocumentAnalysis, position: types.Position
) -> types.Location | None:
    """Build a definition target for a same-document reference."""
    match = lookup_symbol_at_position(analysis, position)
    if match is None or not match.is_reference:
        return None
    return build_definition_location(
        uri=analysis.uri,
        source=analysis.source,
        name=match.declaration.name,
        location=match.declaration.loc,
    )


def document_symbols(analysis: DocumentAnalysis) -> list[types.DocumentSymbol]:
    """Build the document symbol outline for the active document."""
    return [
        build_document_symbol(
            source=analysis.source,
            name=declaration.name,
            kind=declaration.kind,
            location=declaration.loc,
            detail=declaration.kind,
        )
        for declaration in declaration_infos(analysis)
    ]


def _current_analysis(server: LanguageServer, uri: str) -> DocumentAnalysis:
    analysis = get_analysis(uri)
    if analysis is not None:
        return analysis

    document = server.workspace.get_text_document(uri)
    return refresh_document(document.uri, document.source, document.version)


@SERVER.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(server: LanguageServer, params: types.DidOpenTextDocumentParams) -> None:
    """Publish diagnostics for newly opened documents."""
    document = server.workspace.get_text_document(params.text_document.uri)
    publish_document_diagnostics(server, document.uri, document.source, document.version)


@SERVER.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(server: LanguageServer, params: types.DidChangeTextDocumentParams) -> None:
    """Re-analyze and publish diagnostics after document edits."""
    document = server.workspace.get_text_document(params.text_document.uri)
    publish_document_diagnostics(server, document.uri, document.source, document.version)


@SERVER.feature(types.TEXT_DOCUMENT_COMPLETION)
def completion(
    server: LanguageServer, params: types.CompletionParams
) -> list[types.CompletionItem]:
    """Return current-document completions for declarations, types, and references."""
    analysis = _current_analysis(server, params.text_document.uri)
    return document_completions(analysis, params.position)


@SERVER.feature(types.TEXT_DOCUMENT_HOVER)
def hover(server: LanguageServer, params: types.HoverParams) -> types.Hover | None:
    """Return same-document hover content for declarations and references."""
    analysis = _current_analysis(server, params.text_document.uri)
    return document_hover(analysis, params.position)


@SERVER.feature(types.TEXT_DOCUMENT_DEFINITION)
def definition(
    server: LanguageServer, params: types.DefinitionParams
) -> types.Location | None:
    """Resolve same-document definitions for references."""
    analysis = _current_analysis(server, params.text_document.uri)
    return document_definition(analysis, params.position)


@SERVER.feature(types.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
def document_symbol(
    server: LanguageServer, params: types.DocumentSymbolParams
) -> list[types.DocumentSymbol]:
    """Return the current document's DVML symbol outline."""
    analysis = _current_analysis(server, params.text_document.uri)
    return document_symbols(analysis)


def start_server() -> None:
    """Start the DMJEDI language server over stdio."""
    SERVER.start_io()
