"""Stable Pydantic result envelopes for machine-readable DMJedi operations."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DiagnosticResult(BaseModel):
    severity: str
    code: str
    message: str
    file: str | None = None
    line: int | None = None
    column: int | None = None


class ArtifactResult(BaseModel):
    path: str
    content: str


class ValidateResult(BaseModel):
    ok: bool
    source_mode: str
    module_count: int = 0
    diagnostics: list[DiagnosticResult] = Field(default_factory=list)


class GenerateResult(BaseModel):
    ok: bool
    source_mode: str
    target: str
    dialect: str
    module_count: int = 0
    diagnostics: list[DiagnosticResult] = Field(default_factory=list)
    artifacts: list[ArtifactResult] = Field(default_factory=list)


class DocsResult(BaseModel):
    ok: bool
    source_mode: str
    module_count: int = 0
    diagnostics: list[DiagnosticResult] = Field(default_factory=list)
    artifacts: list[ArtifactResult] = Field(default_factory=list)


class ExplainEntityResult(BaseModel):
    qualified_name: str
    kind: str
    columns: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)


class ExplainResult(BaseModel):
    ok: bool
    source_mode: str
    module_count: int = 0
    diagnostics: list[DiagnosticResult] = Field(default_factory=list)
    summary: str = ""
    entity_counts: dict[str, int] = Field(default_factory=dict)
    entities: list[ExplainEntityResult] = Field(default_factory=list)
