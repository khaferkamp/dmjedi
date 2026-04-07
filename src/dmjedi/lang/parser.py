"""DVML parser — transforms .dv source files into AST nodes using Lark."""

from pathlib import Path

from lark import Lark, Transformer, v_args

from dmjedi.lang.ast import (
    BusinessKeyDef,
    DVMLModule,
    FieldDef,
    HubDecl,
    ImportDecl,
    LinkDecl,
    SatelliteDecl,
    SourceLocation,
)

_GRAMMAR_PATH = Path(__file__).parent / "grammar.lark"


def _get_parser() -> Lark:
    return Lark(
        _GRAMMAR_PATH.read_text(),
        parser="earley",
        propagate_positions=True,
    )


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

    def IDENTIFIER(self, token: object) -> str:  # noqa: N802
        return str(token)

    def STRING(self, token: object) -> str:  # noqa: N802
        return str(token).strip('"')

    def qualified_ref(self, tree: object) -> str:
        return ".".join(tree.children)  # type: ignore[union-attr]

    def data_type(self, tree: object) -> str:
        child = tree.children[0]  # type: ignore[union-attr]
        return child.data if hasattr(child, "data") else str(child)

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
        return module


def parse(source: str, source_file: str = "<string>") -> DVMLModule:
    """Parse DVML source text and return an AST module."""
    parser = _get_parser()
    tree = parser.parse(source)
    transformer = DVMLTransformer(source_file=source_file)
    return transformer.transform(tree)


def parse_file(path: Path) -> DVMLModule:
    """Parse a .dv file and return an AST module."""
    return parse(path.read_text(), source_file=str(path))
