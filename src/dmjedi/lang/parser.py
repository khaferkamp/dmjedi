"""DVML parser — transforms .dv source files into AST nodes using Lark."""

from dataclasses import dataclass, field
from pathlib import Path

from lark import Lark, Transformer, v_args
from lark.exceptions import UnexpectedCharacters, UnexpectedEOF, UnexpectedInput, UnexpectedToken

from dmjedi.lang.ast import (
    BridgeDecl,
    BusinessKeyDef,
    DVMLModule,
    EffSatDecl,
    FieldDef,
    HubDecl,
    ImportDecl,
    LinkDecl,
    NhLinkDecl,
    NhSatDecl,
    PitDecl,
    SamLinkDecl,
    SatelliteDecl,
    SourceLocation,
)

_GRAMMAR_PATH = Path(__file__).parent / "grammar.lark"

# PARSE-01: Module-level singleton — only one Lark instance is created per process.
_parser: Lark | None = None


def _get_parser() -> Lark:
    """Return the module-level cached Lark parser singleton."""
    global _parser
    if _parser is None:
        _parser = Lark(
            _GRAMMAR_PATH.read_text(),
            parser="earley",
            propagate_positions=True,
        )
    return _parser


@dataclass
class ParseError:
    """Structured parse error data. Renderer-agnostic per D-05."""

    file: str
    line: int
    column: int
    hint: str
    source_line: str = field(default="")  # reserved for TUI milestone


class DVMLParseError(Exception):
    """A user-facing parse error with structured location and hint data."""

    def __init__(self, error: ParseError) -> None:
        self.error = error
        super().__init__(f"{error.file}:{error.line}:{error.column}: {error.hint}")


# D-06: Curated hint catalog mapping expected token sets to friendly messages.
_HINTS: dict[frozenset[str], str] = {
    frozenset({"RBRACE", "IDENTIFIER"}): 'expected field declaration or "}" to close block',
    frozenset({"RBRACE"}): 'expected "}" to close block',
    frozenset({"COLON"}): 'expected ":" after field name',
    frozenset({"LBRACE"}): 'expected "{" to open entity body',
}


def _get_hint(err: object) -> str:
    """Derive a human-readable hint from a Lark exception."""
    if isinstance(err, UnexpectedToken):
        expected = frozenset(getattr(err, "expected", set()))
        if expected in _HINTS:
            return _HINTS[expected]
        # Check subset matches for partial catalog hits
        for catalog_key, hint in _HINTS.items():
            if catalog_key.issubset(expected):
                return hint
        tokens = ", ".join(sorted(expected))
        return f"expected one of: {tokens}"
    if isinstance(err, UnexpectedCharacters):
        char = getattr(err, "char", "?")
        return f"unexpected character '{char}'"
    if isinstance(err, UnexpectedEOF):
        expected = getattr(err, "expected", [])
        tokens = ", ".join(sorted(expected))
        return f"unexpected end of file, expected one of: {tokens}"
    return str(err)


@v_args(tree=True)
class DVMLTransformer(Transformer):  # type: ignore[type-arg]
    """Transforms Lark parse tree into DVML AST nodes."""

    def __init__(self, source_file: str = "") -> None:
        super().__init__()
        self._source_file = source_file

    def _loc(self, tree: object) -> SourceLocation:
        meta = getattr(tree, "meta", None)
        if meta and hasattr(meta, "line"):
            return SourceLocation(
                file=self._source_file, line=meta.line, column=meta.column
            )
        return SourceLocation(file=self._source_file)

    def IDENTIFIER(self, token: object) -> str:
        return str(token)

    def STRING(self, token: object) -> str:
        return str(token).strip('"')

    def qualified_ref(self, tree: object) -> str:
        return ".".join(tree.children)  # type: ignore[union-attr]

    def data_type(self, tree: object) -> str:
        children = tree.children  # type: ignore[union-attr]
        type_name = children[0]  # str from type_name alias method
        if len(children) > 1:
            params = str(children[1])  # type_params token
            return f"{type_name}({params})"
        return str(type_name)

    def type_params(self, tree: object) -> str:
        children = tree.children  # type: ignore[union-attr]
        return str(children[0]) if children else ""

    def type_int(self, tree: object) -> str:
        return "int"

    def type_string(self, tree: object) -> str:
        return "string"

    def type_decimal(self, tree: object) -> str:
        return "decimal"

    def type_date(self, tree: object) -> str:
        return "date"

    def type_timestamp(self, tree: object) -> str:
        return "timestamp"

    def type_boolean(self, tree: object) -> str:
        return "boolean"

    def type_json(self, tree: object) -> str:
        return "json"

    def type_bigint(self, tree: object) -> str:
        return "bigint"

    def type_float(self, tree: object) -> str:
        return "float"

    def type_varchar(self, tree: object) -> str:
        return "varchar"

    def type_binary(self, tree: object) -> str:
        return "binary"

    def type_name(self, tree: object) -> str:
        # type_name is an alias rule — its child is already a string from the alias method
        children = tree.children  # type: ignore[union-attr]
        return str(children[0])

    def field_decl(self, tree: object) -> FieldDef:
        children = tree.children  # type: ignore[union-attr]
        return FieldDef(name=children[0], data_type=children[1], loc=self._loc(tree))

    def business_key_decl(self, tree: object) -> BusinessKeyDef:
        children = tree.children  # type: ignore[union-attr]
        return BusinessKeyDef(
            name=children[0], data_type=children[1], loc=self._loc(tree)
        )

    def hub_member(self, tree: object) -> BusinessKeyDef | FieldDef:
        return tree.children[0]  # type: ignore[union-attr]

    def hub_body(self, tree: object) -> list[BusinessKeyDef | FieldDef]:
        return list(tree.children)  # type: ignore[union-attr]

    def hub_decl(self, tree: object) -> HubDecl:
        children = tree.children  # type: ignore[union-attr]
        name = children[0]
        members = children[1]
        bks = [m for m in members if isinstance(m, BusinessKeyDef)]
        fields = [m for m in members if isinstance(m, FieldDef)]
        return HubDecl(
            name=name, business_keys=bks, fields=fields, loc=self._loc(tree)
        )

    def sat_body(self, tree: object) -> list[FieldDef]:
        return list(tree.children)  # type: ignore[union-attr]

    def satellite_decl(self, tree: object) -> SatelliteDecl:
        children = tree.children  # type: ignore[union-attr]
        return SatelliteDecl(
            name=children[0],
            parent_ref=children[1],
            fields=children[2],
            loc=self._loc(tree),
        )

    def references_decl(self, tree: object) -> list[str]:
        return list(tree.children)  # type: ignore[union-attr]

    def link_member(self, tree: object) -> list[str] | FieldDef:
        return tree.children[0]  # type: ignore[union-attr]

    def link_body(self, tree: object) -> list[list[str] | FieldDef]:
        return list(tree.children)  # type: ignore[union-attr]

    def link_decl(self, tree: object) -> LinkDecl:
        children = tree.children  # type: ignore[union-attr]
        name = children[0]
        members = children[1]
        refs: list[str] = []
        fields: list[FieldDef] = []
        for m in members:
            if isinstance(m, list):
                refs.extend(m)
            elif isinstance(m, FieldDef):
                fields.append(m)
        return LinkDecl(
            name=name, references=refs, fields=fields, loc=self._loc(tree)
        )

    def nhsat_body(self, tree: object) -> list[FieldDef]:
        return list(tree.children)  # type: ignore[union-attr]

    def nhsat_decl(self, tree: object) -> NhSatDecl:
        children = tree.children  # type: ignore[union-attr]
        return NhSatDecl(
            name=children[0],
            parent_ref=children[1],
            fields=children[2],
            loc=self._loc(tree),
        )

    def nhlink_member(self, tree: object) -> list[str] | FieldDef:
        return tree.children[0]  # type: ignore[union-attr]

    def nhlink_body(self, tree: object) -> list[list[str] | FieldDef]:
        return list(tree.children)  # type: ignore[union-attr]

    def nhlink_decl(self, tree: object) -> NhLinkDecl:
        children = tree.children  # type: ignore[union-attr]
        name = children[0]
        members = children[1]
        refs: list[str] = []
        fields: list[FieldDef] = []
        for m in members:
            if isinstance(m, list):
                refs.extend(m)
            elif isinstance(m, FieldDef):
                fields.append(m)
        return NhLinkDecl(
            name=name, references=refs, fields=fields, loc=self._loc(tree)
        )

    def effsat_body(self, tree: object) -> list[FieldDef]:
        return list(tree.children)  # type: ignore[union-attr]

    def effsat_decl(self, tree: object) -> EffSatDecl:
        children = tree.children  # type: ignore[union-attr]
        return EffSatDecl(
            name=children[0],
            parent_ref=children[1],
            fields=children[2],
            loc=self._loc(tree),
        )

    def master_ref(self, tree: object) -> tuple[str, str]:
        return ("master", tree.children[0])  # type: ignore[union-attr]

    def duplicate_ref(self, tree: object) -> tuple[str, str]:
        return ("duplicate", tree.children[0])  # type: ignore[union-attr]

    def samlink_member(self, tree: object) -> tuple[str, str] | FieldDef:
        return tree.children[0]  # type: ignore[union-attr]

    def samlink_body(self, tree: object) -> list[tuple[str, str] | FieldDef]:
        return list(tree.children)  # type: ignore[union-attr]

    def samlink_decl(self, tree: object) -> SamLinkDecl:
        children = tree.children  # type: ignore[union-attr]
        name = children[0]
        members = children[1]
        master = ""
        duplicate = ""
        fields: list[FieldDef] = []
        for m in members:
            if isinstance(m, tuple) and m[0] == "master":
                master = m[1]
            elif isinstance(m, tuple) and m[0] == "duplicate":
                duplicate = m[1]
            elif isinstance(m, FieldDef):
                fields.append(m)
        return SamLinkDecl(
            name=name, master_ref=master, duplicate_ref=duplicate,
            fields=fields, loc=self._loc(tree),
        )

    def path_chain(self, tree: object) -> list[str]:
        return list(tree.children)  # type: ignore[union-attr]

    def path_decl(self, tree: object) -> list[str]:
        return tree.children[0]  # type: ignore[union-attr]

    def bridge_member(self, tree: object) -> list[str] | FieldDef:
        return tree.children[0]  # type: ignore[union-attr]

    def bridge_body(self, tree: object) -> list[list[str] | FieldDef]:
        return list(tree.children)  # type: ignore[union-attr]

    def bridge_decl(self, tree: object) -> BridgeDecl:
        children = tree.children  # type: ignore[union-attr]
        name = children[0]
        members = children[1]
        path: list[str] = []
        fields: list[FieldDef] = []
        for m in members:
            if isinstance(m, list):
                path = m
            elif isinstance(m, FieldDef):
                fields.append(m)
        return BridgeDecl(
            name=name, path=path, fields=fields, loc=self._loc(tree),
        )

    def pit_of(self, tree: object) -> tuple[str, str]:
        return ("of", tree.children[0])  # type: ignore[union-attr]

    def pit_tracks(self, tree: object) -> tuple[str, list[str]]:
        return ("tracks", list(tree.children))  # type: ignore[union-attr]

    def pit_member(self, tree: object) -> tuple | FieldDef:
        return tree.children[0]  # type: ignore[union-attr]

    def pit_body(self, tree: object) -> list:
        return list(tree.children)  # type: ignore[union-attr]

    def pit_decl(self, tree: object) -> PitDecl:
        children = tree.children  # type: ignore[union-attr]
        name = children[0]
        members = children[1]
        anchor = ""
        tracked: list[str] = []
        fields: list[FieldDef] = []
        for m in members:
            if isinstance(m, tuple) and m[0] == "of":
                anchor = m[1]
            elif isinstance(m, tuple) and m[0] == "tracks":
                tracked = m[1]
            elif isinstance(m, FieldDef):
                fields.append(m)
        return PitDecl(
            name=name, anchor_ref=anchor, tracked_satellites=tracked,
            fields=fields, loc=self._loc(tree),
        )

    def import_decl(self, tree: object) -> ImportDecl:
        return ImportDecl(path=tree.children[0], loc=self._loc(tree))  # type: ignore[union-attr]

    def namespace_decl(self, tree: object) -> str:
        return tree.children[0]  # type: ignore[union-attr]

    def statement(self, tree: object) -> object:
        return tree.children[0]  # type: ignore[union-attr]

    def start(self, tree: object) -> DVMLModule:
        module = DVMLModule(source_file=self._source_file)
        for item in tree.children:  # type: ignore[union-attr]
            if isinstance(item, str):
                module.namespace = item
            elif isinstance(item, ImportDecl):
                module.imports.append(item)
            elif isinstance(item, HubDecl):
                module.hubs.append(item)
            elif isinstance(item, SatelliteDecl):
                module.satellites.append(item)
            elif isinstance(item, LinkDecl):
                module.links.append(item)
            elif isinstance(item, NhSatDecl):
                module.nhsats.append(item)
            elif isinstance(item, NhLinkDecl):
                module.nhlinks.append(item)
            elif isinstance(item, EffSatDecl):
                module.effsats.append(item)
            elif isinstance(item, SamLinkDecl):
                module.samlinks.append(item)
            elif isinstance(item, BridgeDecl):
                module.bridges.append(item)
            elif isinstance(item, PitDecl):
                module.pits.append(item)
        return module


def parse(source: str, source_file: str = "<string>") -> DVMLModule:
    """Parse DVML source text and return an AST module."""
    parser = _get_parser()
    try:
        tree = parser.parse(source)
    except UnexpectedInput as err:
        line = max(0, getattr(err, "line", 0))
        col = max(0, getattr(err, "column", 0))
        hint = _get_hint(err)
        raise DVMLParseError(ParseError(
            file=source_file, line=line, column=col, hint=hint
        )) from err
    transformer = DVMLTransformer(source_file=source_file)
    return transformer.transform(tree)


def parse_file(path: Path) -> DVMLModule:
    """Parse a .dv file and return an AST module."""
    return parse(path.read_text(), source_file=str(path))
