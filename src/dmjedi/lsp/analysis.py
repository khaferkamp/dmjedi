"""Current-document parse and lint analysis for the DVML LSP server."""

from __future__ import annotations

import re
from dataclasses import dataclass

from lsprotocol import types

from dmjedi.lang.ast import (
    BridgeDecl,
    BusinessKeyDef,
    DVMLModule,
    EffSatDecl,
    FieldDef,
    LinkDecl,
    NhLinkDecl,
    NhSatDecl,
    PitDecl,
    SamLinkDecl,
    SatelliteDecl,
    SourceLocation,
)
from dmjedi.lang.linter import lint
from dmjedi.lang.parser import DVMLParseError, parse
from dmjedi.lsp.protocol import lint_diagnostic_to_lsp, parse_error_to_lsp

_DECLARATION_KEYWORDS = (
    "namespace",
    "import",
    "hub",
    "satellite",
    "link",
    "nhsat",
    "nhlink",
    "effsat",
    "samlink",
    "bridge",
    "pit",
    "business_key",
)
_TYPE_KEYWORDS = (
    "int",
    "string",
    "decimal",
    "date",
    "timestamp",
    "boolean",
    "json",
    "bigint",
    "float",
    "varchar",
    "binary",
)
_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*")
_FIELD_TYPE_RE = re.compile(r"(?:business_key\s+\w+\s*:\s*|[\w]+\s*:\s*)([\w()]*)$")
_REFERENCE_LIST_RE = re.compile(
    r"^(?:references|tracks)\s+"
    r"[A-Za-z_][A-Za-z0-9_.]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_.]*)*"
    r"\s*,?\s*[A-Za-z_][A-Za-z0-9_.]*?$"
)
_PATH_RE = re.compile(
    r"^path\s+"
    r"[A-Za-z_][A-Za-z0-9_.]*(?:\s*->\s*[A-Za-z_][A-Za-z0-9_.]*)*"
    r"\s*(?:->\s*)?[A-Za-z_][A-Za-z0-9_.]*?$"
)
_PATH_ARROW_RE = re.compile(
    r"^path\s+[A-Za-z_][A-Za-z0-9_.]*(?:\s*->\s*[A-Za-z_][A-Za-z0-9_.]*)*\s*->\s*$"
)
_REFERENCE_LIST_TRAILING_COMMA_RE = re.compile(
    r"^(?:references|tracks)\s+[A-Za-z_][A-Za-z0-9_.]*"
    r"(?:\s*,\s*[A-Za-z_][A-Za-z0-9_.]*)*\s*,\s*$"
)


@dataclass(slots=True)
class DeclarationInfo:
    """Same-document entity metadata used by semantic LSP features."""

    name: str
    kind: str
    loc: SourceLocation
    business_keys: list[BusinessKeyDef]
    fields: list[FieldDef]
    references: list[str]


@dataclass(slots=True)
class CompletionContext:
    """Conservative completion classification for the active cursor position."""

    kind: str
    prefix: str


@dataclass(slots=True)
class SymbolLookup:
    """A declaration or reference resolved from a cursor position."""

    name: str
    declaration: DeclarationInfo
    range: types.Range
    is_reference: bool


@dataclass(slots=True)
class DocumentAnalysis:
    """Analysis result for a single in-memory DVML document."""

    uri: str
    version: int | None
    source: str
    module: DVMLModule | None
    diagnostics: list[types.Diagnostic]
    declarations: dict[str, DeclarationInfo]


def analyze_document(uri: str, source: str, version: int | None) -> DocumentAnalysis:
    """Parse and lint the current document without consulting workspace state."""
    try:
        module = parse(source, source_file=uri)
    except DVMLParseError as error:
        return DocumentAnalysis(
            uri=uri,
            version=version,
            source=source,
            module=None,
            diagnostics=[parse_error_to_lsp(error, source)],
            declarations={},
        )

    declarations = build_declaration_index(module)
    diagnostics = [lint_diagnostic_to_lsp(diagnostic, source) for diagnostic in lint(module)]
    return DocumentAnalysis(
        uri=uri,
        version=version,
        source=source,
        module=module,
        diagnostics=diagnostics,
        declarations=declarations,
    )


def build_declaration_index(module: DVMLModule) -> dict[str, DeclarationInfo]:
    """Collect same-document declarations keyed by entity name."""
    declarations: dict[str, DeclarationInfo] = {}
    for declaration in module.hubs:
        declarations[declaration.name] = DeclarationInfo(
            name=declaration.name,
            kind="hub",
            loc=declaration.loc,
            business_keys=declaration.business_keys,
            fields=declaration.fields,
            references=[],
        )
    for declaration in module.satellites:
        declarations[declaration.name] = _entity_info(
            declaration, "satellite", declaration.fields, [declaration.parent_ref]
        )
    for declaration in module.links:
        declarations[declaration.name] = _entity_info(
            declaration, "link", declaration.fields, declaration.references
        )
    for declaration in module.nhsats:
        declarations[declaration.name] = _entity_info(
            declaration, "nhsat", declaration.fields, [declaration.parent_ref]
        )
    for declaration in module.nhlinks:
        declarations[declaration.name] = _entity_info(
            declaration, "nhlink", declaration.fields, declaration.references
        )
    for declaration in module.effsats:
        declarations[declaration.name] = _entity_info(
            declaration, "effsat", declaration.fields, [declaration.parent_ref]
        )
    for declaration in module.samlinks:
        declarations[declaration.name] = _entity_info(
            declaration,
            "samlink",
            declaration.fields,
            [declaration.master_ref, declaration.duplicate_ref],
        )
    for declaration in module.bridges:
        declarations[declaration.name] = _entity_info(
            declaration, "bridge", declaration.fields, declaration.path
        )
    for declaration in module.pits:
        declarations[declaration.name] = _entity_info(
            declaration,
            "pit",
            declaration.fields,
            [declaration.anchor_ref, *declaration.tracked_satellites],
        )
    return declarations


def completion_context(source: str, line: int, character: int) -> CompletionContext | None:
    """Classify the active cursor position for conservative completion behavior."""
    line_text = _line_at(source, line)
    prefix = line_text[:character]
    stripped = prefix.lstrip()
    current_prefix = _identifier_prefix(prefix)

    if not stripped or (" " not in stripped and ":" not in stripped and "{" not in stripped):
        return CompletionContext(kind="keyword", prefix=current_prefix)

    field_match = _FIELD_TYPE_RE.search(stripped)
    if field_match is not None:
        return CompletionContext(kind="data_type", prefix=field_match.group(1))

    reference_kind = _reference_context_kind(stripped)
    if reference_kind is not None:
        return CompletionContext(kind=reference_kind, prefix=current_prefix)

    return None


def completion_items_for_context(
    analysis: DocumentAnalysis, context: CompletionContext | None
) -> list[types.CompletionItem]:
    """Return typed completion items for a conservative completion context."""
    if context is None:
        return []
    if context.kind == "keyword":
        return [
            types.CompletionItem(
                label=keyword,
                kind=types.CompletionItemKind.Keyword,
            )
            for keyword in _filtered(_DECLARATION_KEYWORDS, context.prefix)
        ]
    if context.kind == "data_type":
        return [
            types.CompletionItem(
                label=data_type,
                kind=types.CompletionItemKind.Keyword,
            )
            for data_type in _filtered(_TYPE_KEYWORDS, context.prefix)
        ]
    if context.kind.startswith("entity_reference"):
        items: list[types.CompletionItem] = []
        for declaration in _sorted_declarations(analysis):
            if not _kind_allowed_in_context(declaration.kind, context.kind):
                continue
            if context.prefix and not declaration.name.startswith(context.prefix):
                continue
            items.append(
                types.CompletionItem(
                    label=declaration.name,
                    kind=types.CompletionItemKind.Class,
                    detail=declaration.kind,
                )
            )
        return items
    return []


def lookup_symbol_at_position(
    analysis: DocumentAnalysis, position: types.Position
) -> SymbolLookup | None:
    """Resolve a declaration or same-document reference under the cursor."""
    declaration_match = _lookup_declaration_at_position(analysis, position)
    if declaration_match is not None:
        return declaration_match
    return _lookup_reference_at_position(analysis, position)


def declaration_infos(analysis: DocumentAnalysis) -> list[DeclarationInfo]:
    """Return declarations in stable source order for symbols and completions."""
    return _sorted_declarations(analysis)


def _entity_info(
    declaration: SatelliteDecl
    | LinkDecl
    | NhSatDecl
    | NhLinkDecl
    | EffSatDecl
    | SamLinkDecl
    | BridgeDecl
    | PitDecl,
    kind: str,
    fields: list[FieldDef],
    references: list[str],
) -> DeclarationInfo:
    return DeclarationInfo(
        name=declaration.name,
        kind=kind,
        loc=declaration.loc,
        business_keys=[],
        fields=fields,
        references=references,
    )


def _sorted_declarations(analysis: DocumentAnalysis) -> list[DeclarationInfo]:
    return sorted(
        analysis.declarations.values(),
        key=lambda declaration: (declaration.loc.line, declaration.loc.column, declaration.name),
    )


def _lookup_declaration_at_position(
    analysis: DocumentAnalysis, position: types.Position
) -> SymbolLookup | None:
    for declaration in analysis.declarations.values():
        match_range = _entity_name_range(analysis.source, declaration)
        if match_range is not None and _position_in_range(position, match_range):
            return SymbolLookup(
                name=declaration.name,
                declaration=declaration,
                range=match_range,
                is_reference=False,
            )
    return None


def _lookup_reference_at_position(
    analysis: DocumentAnalysis, position: types.Position
) -> SymbolLookup | None:
    word = _word_at_position(analysis.source, position.line, position.character)
    if word is None:
        return None
    name, start, end = word
    declaration = analysis.declarations.get(name)
    if declaration is None:
        return None

    prefix = _line_at(analysis.source, position.line)[:start].lstrip()
    if not _is_reference_context(prefix):
        return None

    return SymbolLookup(
        name=name,
        declaration=declaration,
        range=types.Range(
            start=types.Position(line=position.line, character=start),
            end=types.Position(line=position.line, character=end),
        ),
        is_reference=True,
    )


def _entity_name_range(source: str, declaration: DeclarationInfo) -> types.Range | None:
    line_index = max(declaration.loc.line - 1, 0)
    line_text = _line_at(source, line_index)
    keyword_start = max(declaration.loc.column - 1, 0)
    name_start = line_text.find(declaration.name, keyword_start)
    if name_start < 0:
        return None
    return types.Range(
        start=types.Position(line=line_index, character=name_start),
        end=types.Position(line=line_index, character=name_start + len(declaration.name)),
    )


def _position_in_range(position: types.Position, target: types.Range) -> bool:
    if position.line != target.start.line:
        return False
    return target.start.character <= position.character <= target.end.character


def _word_at_position(source: str, line: int, character: int) -> tuple[str, int, int] | None:
    line_text = _line_at(source, line)
    for match in _IDENTIFIER_RE.finditer(line_text):
        if match.start() <= character <= match.end():
            return (match.group(0), match.start(), match.end())
    return None


def _line_at(source: str, line: int) -> str:
    lines = source.splitlines()
    if 0 <= line < len(lines):
        return lines[line]
    return ""


def _identifier_prefix(prefix: str) -> str:
    match = re.search(r"[A-Za-z_][A-Za-z0-9_.]*$", prefix)
    return match.group(0) if match is not None else ""


def _is_reference_context(prefix: str) -> bool:
    return _reference_context_kind(prefix) is not None


def _reference_context_kind(prefix: str) -> str | None:
    if re.search(r"^(?:satellite|nhsat)\s+\w+\s+of\s+[A-Za-z_][A-Za-z0-9_.]*?$", prefix):
        return "entity_reference_parent"
    if re.search(r"^(?:effsat)\s+\w+\s+of\s+[A-Za-z_][A-Za-z0-9_.]*?$", prefix):
        return "entity_reference_link"
    if re.search(r"^(?:of)\s+[A-Za-z_][A-Za-z0-9_.]*?$", prefix):
        return "entity_reference_parent"
    if re.search(r"^(?:master|duplicate)\s+[A-Za-z_][A-Za-z0-9_.]*?$", prefix):
        return "entity_reference_hub"
    if re.search(r"(?:^|\s)(?:of|master|duplicate)\s+[A-Za-z_][A-Za-z0-9_.]*?$", prefix):
        return "entity_reference_parent"
    if re.search(r"(?:^|\s)of\s*$", prefix):
        return "entity_reference_parent"
    if re.search(r"(?:^|\s)(?:master|duplicate)\s*$", prefix):
        return "entity_reference_hub"
    if _REFERENCE_LIST_RE.search(prefix):
        return "entity_reference_any"
    if _PATH_RE.search(prefix):
        return "entity_reference_any"
    if bool(
        re.search(r"^(?:references|tracks)\s*$", prefix)
        or re.search(r"^path\s*$", prefix)
        or re.search(r"^(?:of|master|duplicate)\s*$", prefix)
        or _PATH_ARROW_RE.search(prefix)
        or _REFERENCE_LIST_TRAILING_COMMA_RE.search(prefix)
    ):
        if re.search(r"^(?:master|duplicate)\s*$", prefix):
            return "entity_reference_hub"
        if re.search(r"^(?:of)\s*$", prefix):
            return "entity_reference_parent"
        return "entity_reference_any"
    return None


def _kind_allowed_in_context(kind: str, context_kind: str) -> bool:
    if context_kind == "entity_reference_any":
        return True
    if context_kind == "entity_reference_hub":
        return kind == "hub"
    if context_kind == "entity_reference_link":
        return kind in {"link", "nhlink"}
    if context_kind == "entity_reference_parent":
        return kind in {"hub", "link", "nhlink"}
    return True


def _filtered(values: tuple[str, ...], prefix: str) -> list[str]:
    if not prefix:
        return list(values)
    return [value for value in values if value.startswith(prefix)]
