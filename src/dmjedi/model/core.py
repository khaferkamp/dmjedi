"""Data Vault 2.1 domain model — resolved, validated model objects."""

from pydantic import BaseModel, model_validator


class Column(BaseModel):
    """A resolved column with physical type info."""

    name: str
    data_type: str
    is_business_key: bool = False
    nullable: bool = True


class Hub(BaseModel):
    """A resolved hub entity."""

    name: str
    namespace: str = ""
    business_keys: list[Column] = []
    columns: list[Column] = []

    @property
    def qualified_name(self) -> str:
        return f"{self.namespace}.{self.name}" if self.namespace else self.name


class Satellite(BaseModel):
    """A resolved satellite entity attached to a hub or link."""

    name: str
    namespace: str = ""
    parent_ref: str
    columns: list[Column] = []

    @property
    def qualified_name(self) -> str:
        return f"{self.namespace}.{self.name}" if self.namespace else self.name


class Link(BaseModel):
    """A resolved link entity referencing two or more hubs."""

    name: str
    namespace: str = ""
    hub_references: list[str] = []
    columns: list[Column] = []

    @model_validator(mode="after")
    def _check_min_refs(self) -> "Link":
        if len(self.hub_references) < 2:
            msg = f"Link '{self.name}' must reference at least 2 hubs"
            raise ValueError(msg)
        return self

    @property
    def qualified_name(self) -> str:
        return f"{self.namespace}.{self.name}" if self.namespace else self.name


class NhSat(BaseModel):
    """A resolved non-historized satellite (current-state-only)."""

    name: str
    namespace: str = ""
    parent_ref: str
    columns: list[Column] = []

    @property
    def qualified_name(self) -> str:
        return f"{self.namespace}.{self.name}" if self.namespace else self.name


class NhLink(BaseModel):
    """A resolved non-historized link (current-state-only)."""

    name: str
    namespace: str = ""
    hub_references: list[str] = []
    columns: list[Column] = []

    @model_validator(mode="after")
    def _check_min_refs(self) -> "NhLink":
        if len(self.hub_references) < 2:
            msg = f"NhLink '{self.name}' must reference at least 2 hubs"
            raise ValueError(msg)
        return self

    @property
    def qualified_name(self) -> str:
        return f"{self.namespace}.{self.name}" if self.namespace else self.name


class EffSat(BaseModel):
    """A resolved effectivity satellite (temporal link validity)."""

    name: str
    namespace: str = ""
    parent_ref: str
    columns: list[Column] = []

    @property
    def qualified_name(self) -> str:
        return f"{self.namespace}.{self.name}" if self.namespace else self.name


class SamLink(BaseModel):
    """A resolved same-as link (master/duplicate cross-source matching)."""

    name: str
    namespace: str = ""
    master_ref: str
    duplicate_ref: str
    columns: list[Column] = []

    @property
    def qualified_name(self) -> str:
        return f"{self.namespace}.{self.name}" if self.namespace else self.name


class DataVaultModel(BaseModel):
    """A complete, resolved Data Vault 2.1 model built from one or more DVML modules."""

    hubs: dict[str, Hub] = {}
    satellites: dict[str, Satellite] = {}
    links: dict[str, Link] = {}
    nhsats: dict[str, NhSat] = {}
    nhlinks: dict[str, NhLink] = {}
    effsats: dict[str, EffSat] = {}
    samlinks: dict[str, SamLink] = {}
