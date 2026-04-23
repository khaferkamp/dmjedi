"""Shared application-layer request/result contracts for machine interfaces."""

from dmjedi.application.requests import CompileRequest
from dmjedi.application.results import (
    ArtifactResult,
    DiagnosticResult,
    DocsResult,
    ExplainEntityResult,
    ExplainResult,
    GenerateResult,
    ValidateResult,
)

__all__ = [
    "ArtifactResult",
    "CompileRequest",
    "DiagnosticResult",
    "DocsResult",
    "ExplainEntityResult",
    "ExplainResult",
    "GenerateResult",
    "ValidateResult",
]
