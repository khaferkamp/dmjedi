from __future__ import annotations

from lsprotocol import types
from pygls.workspace import TextDocument

from dmjedi.lang.ast import SourceLocation
from dmjedi.lang.linter import LintDiagnostic, Severity
from dmjedi.lang.parser import DVMLParseError, parse
from dmjedi.lsp.analysis import analyze_document, completion_context
from dmjedi.lsp.protocol import (
    build_document_symbol,
    build_hover,
    lint_diagnostic_to_lsp,
    name_range_from_location,
    parse_error_to_lsp,
    range_from_location,
)
from dmjedi.lsp.server import (
    document_completions,
    document_definition,
    document_hover,
    document_symbols,
    get_analysis,
    publish_document_diagnostics,
    refresh_document,
)


class RecordingServer:
    def __init__(self) -> None:
        self.published: list[types.PublishDiagnosticsParams] = []

    def text_document_publish_diagnostics(self, params: types.PublishDiagnosticsParams) -> None:
        self.published.append(params)


def test_range_from_location_uses_source_text_for_end_column() -> None:
    source = "namespace sales\nhub Customer {\n}\n"

    result = range_from_location(
        source,
        SourceLocation(file="model.dv", line=2, column=5),
        fallback_length=len("Customer"),
    )

    assert result == types.Range(
        start=types.Position(line=1, character=4),
        end=types.Position(line=1, character=12),
    )


def test_parse_error_to_lsp_maps_current_line_position() -> None:
    source = "namespace sales\nhub Customer {\n  business_key id int\n}\n"

    try:
        parse(source, source_file="broken.dv")
    except DVMLParseError as err:
        diagnostic = parse_error_to_lsp(err, source)
    else:
        msg = "expected parse failure"
        raise AssertionError(msg)

    assert diagnostic.message == "unexpected character 'i'"
    assert diagnostic.severity == types.DiagnosticSeverity.Error
    assert diagnostic.source == "dmjedi"
    assert diagnostic.range == types.Range(
        start=types.Position(line=2, character=18),
        end=types.Position(line=2, character=21),
    )


def test_lint_diagnostic_to_lsp_maps_severity_and_range() -> None:
    source = "namespace sales\nhub Customer {\n}\n"
    lint_diag = LintDiagnostic(
        message="Hub 'Customer' has no business keys defined",
        severity=Severity.ERROR,
        loc=SourceLocation(file="lint.dv", line=2, column=1),
        rule="hub-requires-business-key",
    )

    diagnostic = lint_diagnostic_to_lsp(lint_diag, source)

    assert diagnostic.message == "Hub 'Customer' has no business keys defined"
    assert diagnostic.severity == types.DiagnosticSeverity.Error
    assert diagnostic.code == "hub-requires-business-key"
    assert diagnostic.range == types.Range(
        start=types.Position(line=1, character=0),
        end=types.Position(line=1, character=3),
    )


def test_analyze_document_returns_parse_diagnostics_without_module() -> None:
    source = "namespace sales\nhub Customer {\n  business_key id int\n}\n"

    analysis = analyze_document(
        uri="file:///tmp/broken.dv",
        source=source,
        version=7,
    )

    assert analysis.uri == "file:///tmp/broken.dv"
    assert analysis.version == 7
    assert analysis.module is None
    assert len(analysis.diagnostics) == 1
    assert analysis.diagnostics[0].severity == types.DiagnosticSeverity.Error


def test_analyze_document_returns_lint_diagnostics_for_current_document() -> None:
    source = "namespace sales\nhub Customer {\n}\n"

    analysis = analyze_document(
        uri="file:///tmp/lint.dv",
        source=source,
        version=3,
    )

    assert analysis.uri == "file:///tmp/lint.dv"
    assert analysis.version == 3
    assert analysis.module is not None
    assert [diag.code for diag in analysis.diagnostics] == ["hub-requires-business-key"]


def test_analyze_document_returns_semantic_diagnostic_for_invalid_satellite_parent() -> None:
    source = (
        "namespace sales\n"
        "hub Customer {\n  business_key customer_id: int\n}\n"
        "satellite ParentDetails of Customer {\n  email: string\n}\n"
        "satellite ChildDetails of ParentDetails {\n  status: string\n}\n"
    )

    analysis = analyze_document("file:///tmp/semantic.dv", source, version=2)

    invalid_parent = [diag for diag in analysis.diagnostics if diag.code == "invalid-parent-kind"]

    assert len(invalid_parent) == 1
    assert "Invalid parent 'ParentDetails'" in invalid_parent[0].message
    assert invalid_parent[0].range == types.Range(
        start=types.Position(line=7, character=26),
        end=types.Position(line=7, character=39),
    )


def test_refresh_document_caches_current_document_analysis() -> None:
    source = "namespace sales\nhub Customer {\n}\n"

    analysis = refresh_document("file:///tmp/cache.dv", source, version=4)

    assert get_analysis("file:///tmp/cache.dv") == analysis
    assert [diag.code for diag in analysis.diagnostics] == ["hub-requires-business-key"]


def test_publish_document_diagnostics_emits_publish_params() -> None:
    server = RecordingServer()
    source = "namespace sales\nhub Customer {\n}\n"

    analysis = publish_document_diagnostics(
        server,  # type: ignore[arg-type]
        "file:///tmp/publish.dv",
        source,
        version=9,
    )

    assert analysis.version == 9
    assert len(server.published) == 1
    assert server.published[0].uri == "file:///tmp/publish.dv"
    assert server.published[0].version == 9
    assert [diag.code for diag in server.published[0].diagnostics] == [
        "hub-requires-business-key"
    ]


def test_text_document_shape_matches_server_helpers() -> None:
    document = TextDocument(
        uri="file:///tmp/document.dv",
        source="namespace sales\nhub Customer {\n}\n",
        version=12,
    )

    analysis = refresh_document(document.uri, document.source, document.version)

    assert analysis.uri == document.uri
    assert analysis.version == document.version


def test_completion_context_detects_keyword_positions() -> None:
    context = completion_context("namespace sales\nhu", line=1, character=2)

    assert context is not None
    assert context.kind == "keyword"
    assert context.prefix == "hu"


def test_completion_context_detects_reference_positions() -> None:
    source = "namespace sales\nsatellite CustomerDetails of Cust"

    context = completion_context(source, line=1, character=len("satellite CustomerDetails of Cust"))

    assert context is not None
    assert context.kind == "entity_reference_parent"
    assert context.prefix == "Cust"


def test_document_completions_return_keywords_for_declaration_prefix() -> None:
    analysis = analyze_document("file:///tmp/keywords.dv", "namespace sales\nhu", version=1)

    items = document_completions(analysis, types.Position(line=1, character=2))

    assert [item.label for item in items] == ["hub"]


def test_document_completions_return_same_document_references() -> None:
    source = (
        "namespace sales\n"
        "hub Customer {\n  business_key customer_id: int\n}\n"
        "hub Product {\n  business_key product_id: int\n}\n"
        "satellite CustomerDetails of Customer {\n  email: string\n}\n"
    )
    analysis = analyze_document("file:///tmp/completion.dv", source, version=1)
    line = "satellite CustomerDetails of Customer {"
    character = line.index("Customer {") + len("Cust")

    items = document_completions(
        analysis,
        types.Position(line=7, character=character),
    )

    assert [item.label for item in items] == ["Customer"]


def test_document_completions_exclude_satellites_for_satellite_parent_context() -> None:
    source = (
        "namespace sales\n"
        "hub Customer {\n  business_key customer_id: int\n}\n"
        "satellite CustomerDetails of Customer {\n  email: string\n}\n"
        "satellite ChildDetails of Customer {\n  status: string\n}\n"
    )
    analysis = analyze_document("file:///tmp/semantic-completion.dv", source, version=1)
    line = "satellite ChildDetails of Customer {"

    items = document_completions(
        analysis,
        types.Position(line=7, character=line.index("Customer {") + len("Cust")),
    )

    assert [item.label for item in items] == ["Customer"]


def test_document_completions_stay_conservative_in_unrelated_positions() -> None:
    source = "namespace sales\nhub Customer {\n  business_key customer_id: int\n}\n"
    analysis = analyze_document("file:///tmp/noisy.dv", source, version=1)

    items = document_completions(
        analysis,
        types.Position(line=2, character=len("  business_key customer_id")),
    )

    assert items == []


def test_name_range_from_location_finds_entity_name_after_keyword() -> None:
    source = "namespace sales\nhub Customer {\n}\n"

    result = name_range_from_location(
        source,
        SourceLocation(file="model.dv", line=2, column=1),
        "Customer",
    )

    assert result == types.Range(
        start=types.Position(line=1, character=4),
        end=types.Position(line=1, character=12),
    )


def test_protocol_builders_render_hover_and_document_symbol() -> None:
    source = "namespace sales\nhub Customer {\n  business_key customer_id: int\n}\n"

    hover = build_hover(
        source=source,
        name="Customer",
        kind="hub",
        location=SourceLocation(file="model.dv", line=2, column=1),
        business_keys=["customer_id"],
        fields=[],
        references=[],
    )
    symbol = build_document_symbol(
        source=source,
        name="Customer",
        kind="hub",
        location=SourceLocation(file="model.dv", line=2, column=1),
        detail="hub",
    )

    assert "customer_id" in hover.contents.value
    assert symbol.name == "Customer"
    assert symbol.selection_range.start == types.Position(line=1, character=4)


def test_document_hover_returns_entity_details_for_reference() -> None:
    source = (
        "namespace sales\n"
        "hub Customer {\n  business_key customer_id: int\n}\n"
        "satellite CustomerDetails of Customer {\n  email: string\n}\n"
    )
    analysis = analyze_document("file:///tmp/hover.dv", source, version=1)
    line = "satellite CustomerDetails of Customer {"
    position = types.Position(line=4, character=line.index("Customer {") + 2)

    hover = document_hover(analysis, position)

    assert hover is not None
    assert "hub Customer" in hover.contents.value
    assert "customer_id" in hover.contents.value
    assert "Defined at" in hover.contents.value


def test_document_definition_returns_same_document_target() -> None:
    source = (
        "namespace sales\n"
        "hub Customer {\n  business_key customer_id: int\n}\n"
        "satellite CustomerDetails of Customer {\n  email: string\n}\n"
    )
    analysis = analyze_document("file:///tmp/definition.dv", source, version=1)
    line = "satellite CustomerDetails of Customer {"
    position = types.Position(line=4, character=line.index("Customer {") + 2)

    location = document_definition(analysis, position)

    assert location is not None
    assert location.uri == "file:///tmp/definition.dv"
    assert location.range == types.Range(
        start=types.Position(line=1, character=4),
        end=types.Position(line=1, character=12),
    )


def test_document_symbols_outline_entities_in_source_order() -> None:
    source = (
        "namespace sales\n"
        "hub Customer {\n  business_key customer_id: int\n}\n"
        "link CustomerProduct {\n  references Customer, Product\n}\n"
        "hub Product {\n  business_key product_id: int\n}\n"
    )
    analysis = analyze_document("file:///tmp/symbols.dv", source, version=1)

    symbols = document_symbols(analysis)

    assert [symbol.name for symbol in symbols] == ["Customer", "CustomerProduct", "Product"]
    assert [symbol.detail for symbol in symbols] == ["hub", "link", "hub"]
