"""AST node definitions for DVML, backed by Pydantic models."""

from pydantic import BaseModel


class SourceLocation(BaseModel):
    """Location in a DVML source file."""

    file: str = ""
    line: int = 0
    column: int = 0


class FieldDef(BaseModel):
    """A typed field (column) in an entity."""

    name: str
    data_type: str
    loc: SourceLocation = SourceLocation()


class BusinessKeyDef(BaseModel):
    """A business key declaration inside a hub."""

    name: str
    data_type: str
    loc: SourceLocation = SourceLocation()


class HubDecl(BaseModel):
    """A hub entity declaration."""

    name: str
    business_keys: list[BusinessKeyDef] = []
    fields: list[FieldDef] = []
    loc: SourceLocation = SourceLocation()


class SatelliteDecl(BaseModel):
    """A satellite entity declaration, attached to a hub or link."""

    name: str
    parent_ref: str
    fields: list[FieldDef] = []
    loc: SourceLocation = SourceLocation()


class LinkDecl(BaseModel):
    """A link entity declaration referencing two or more hubs."""

    name: str
    references: list[str] = []
    fields: list[FieldDef] = []
    loc: SourceLocation = SourceLocation()


class ImportDecl(BaseModel):
    """An import statement to include another DVML file."""

    path: str
    loc: SourceLocation = SourceLocation()


class DVMLModule(BaseModel):
    """A parsed DVML file containing all declarations."""

    namespace: str = ""
    imports: list[ImportDecl] = []
    hubs: list[HubDecl] = []
    satellites: list[SatelliteDecl] = []
    links: list[LinkDecl] = []
    source_file: str = ""
