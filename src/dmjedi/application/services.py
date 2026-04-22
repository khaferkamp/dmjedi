"""Shared compile/use-case services for CLI JSON and MCP adapters."""

from __future__ import annotations

from pathlib import Path

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
from dmjedi.docs.markdown import generate_markdown
from dmjedi.generators import registry
from dmjedi.lang.ast import DVMLModule
from dmjedi.lang.discovery import discover_dv_files
from dmjedi.lang.imports import CircularImportError, resolve_imports
from dmjedi.lang.linter import LintDiagnostic, Severity, lint
from dmjedi.lang.parser import DVMLParseError, parse, parse_file
from dmjedi.model.core import DataVaultModel
from dmjedi.model.resolver import ResolverErrors, resolve

_MODEL_AWARE_RULES = {"effsat-parent-must-be-link"}


def validate_request(request: CompileRequest) -> ValidateResult:
    """Validate a compile request and return a stable machine-readable result."""
    loaded = _load_modules(request)
    if loaded.diagnostics:
        return ValidateResult(
            ok=False,
            source_mode=request.source_mode,
            module_count=len(loaded.modules),
            diagnostics=loaded.diagnostics,
        )

    compiled = _compile_modules(loaded.modules)
    return ValidateResult(
        ok=compiled.ok,
        source_mode=request.source_mode,
        module_count=len(loaded.modules),
        diagnostics=compiled.diagnostics,
    )


def generate_request(request: CompileRequest, target: str, dialect: str) -> GenerateResult:
    """Generate artifacts in-memory without writing to disk."""
    loaded = _load_modules(request)
    if loaded.diagnostics:
        return GenerateResult(
            ok=False,
            source_mode=request.source_mode,
            target=target,
            dialect=dialect,
            module_count=len(loaded.modules),
            diagnostics=loaded.diagnostics,
            artifacts=[],
        )

    compiled = _compile_modules(loaded.modules)
    if not compiled.ok or compiled.model is None:
        return GenerateResult(
            ok=False,
            source_mode=request.source_mode,
            target=target,
            dialect=dialect,
            module_count=len(loaded.modules),
            diagnostics=compiled.diagnostics,
            artifacts=[],
        )

    try:
        generator = registry.get(target, dialect=dialect)
    except KeyError as err:
        return GenerateResult(
            ok=False,
            source_mode=request.source_mode,
            target=target,
            dialect=dialect,
            module_count=len(loaded.modules),
            diagnostics=[
                DiagnosticResult(
                    severity=Severity.ERROR.value,
                    code="generator-error",
                    message=str(err),
                )
            ],
            artifacts=[],
        )

    result = generator.generate(compiled.model)
    artifacts = [
        ArtifactResult(path=path, content=content)
        for path, content in sorted(result.files.items())
    ]
    return GenerateResult(
        ok=True,
        source_mode=request.source_mode,
        target=target,
        dialect=dialect,
        module_count=len(loaded.modules),
        diagnostics=compiled.diagnostics,
        artifacts=artifacts,
    )


def docs_request(request: CompileRequest) -> DocsResult:
    """Render markdown docs in-memory without writing to disk."""
    loaded = _load_modules(request)
    if loaded.diagnostics:
        return DocsResult(
            ok=False,
            source_mode=request.source_mode,
            module_count=len(loaded.modules),
            diagnostics=loaded.diagnostics,
            artifacts=[],
        )

    compiled = _compile_modules(loaded.modules)
    if not compiled.ok or compiled.model is None:
        return DocsResult(
            ok=False,
            source_mode=request.source_mode,
            module_count=len(loaded.modules),
            diagnostics=compiled.diagnostics,
            artifacts=[],
        )

    return DocsResult(
        ok=True,
        source_mode=request.source_mode,
        module_count=len(loaded.modules),
        diagnostics=compiled.diagnostics,
        artifacts=[ArtifactResult(path="model.md", content=generate_markdown(compiled.model))],
    )


def explain_request(request: CompileRequest) -> ExplainResult:
    """Return a deterministic summary of the resolved model."""
    loaded = _load_modules(request)
    if loaded.diagnostics:
        return ExplainResult(
            ok=False,
            source_mode=request.source_mode,
            module_count=len(loaded.modules),
            diagnostics=loaded.diagnostics,
            summary="",
            entity_counts=_entity_counts(None),
            entities=[],
        )

    compiled = _compile_modules(loaded.modules)
    if not compiled.ok or compiled.model is None:
        return ExplainResult(
            ok=False,
            source_mode=request.source_mode,
            module_count=len(loaded.modules),
            diagnostics=compiled.diagnostics,
            summary="",
            entity_counts=_entity_counts(None),
            entities=[],
        )

    entity_counts = _entity_counts(compiled.model)
    return ExplainResult(
        ok=True,
        source_mode=request.source_mode,
        module_count=len(loaded.modules),
        diagnostics=compiled.diagnostics,
        summary=_build_summary(entity_counts),
        entity_counts=entity_counts,
        entities=_build_entities(compiled.model),
    )


class _LoadedModules:
    def __init__(self, modules: list[DVMLModule], diagnostics: list[DiagnosticResult]) -> None:
        self.modules = modules
        self.diagnostics = diagnostics


class _CompiledModules:
    def __init__(
        self,
        model: DataVaultModel | None,
        diagnostics: list[DiagnosticResult],
    ) -> None:
        self.model = model
        self.diagnostics = diagnostics

    @property
    def ok(self) -> bool:
        return not any(diag.severity == Severity.ERROR.value for diag in self.diagnostics)


def _load_modules(request: CompileRequest) -> _LoadedModules:
    if request.paths:
        return _load_path_modules(request.paths)
    return _load_inline_module(request)


def _load_path_modules(paths: list[Path]) -> _LoadedModules:
    try:
        dv_files = discover_dv_files(paths)
    except FileNotFoundError as err:
        return _LoadedModules(
            [],
            [DiagnosticResult(severity=Severity.ERROR.value, code="path-error", message=str(err))],
        )

    if not dv_files:
        return _LoadedModules(
            [],
            [
                DiagnosticResult(
                    severity=Severity.ERROR.value,
                    code="path-error",
                    message="No .dv files found in the given paths.",
                )
            ],
        )

    modules: list[DVMLModule] = []
    for path in dv_files:
        try:
            modules.append(parse_file(path))
        except DVMLParseError as err:
            return _LoadedModules([], [_parse_error_to_diagnostic(err)])

    try:
        return _LoadedModules(resolve_imports(modules), [])
    except CircularImportError as err:
        return _LoadedModules(
            [],
            [
                DiagnosticResult(
                    severity=Severity.ERROR.value,
                    code="import-error",
                    message=str(err),
                )
            ],
        )
    except FileNotFoundError as err:
        return _LoadedModules(
            [],
            [
                DiagnosticResult(
                    severity=Severity.ERROR.value,
                    code="import-error",
                    message=str(err),
                )
            ],
        )


def _load_inline_module(request: CompileRequest) -> _LoadedModules:
    try:
        module = parse(request.source or "", source_file=request.source_name)
    except DVMLParseError as err:
        return _LoadedModules([], [_parse_error_to_diagnostic(err)])

    if module.imports:
        return _LoadedModules(
            [module],
            [
                DiagnosticResult(
                    severity=Severity.ERROR.value,
                    code="inline-source-imports-unsupported",
                    message=(
                        "Inline source cannot use import declarations; "
                        "use path mode for imported models."
                    ),
                    file=module.source_file or request.source_name,
                    line=module.imports[0].loc.line,
                    column=module.imports[0].loc.column,
                )
            ],
        )

    return _LoadedModules([module], [])


def _compile_modules(modules: list[DVMLModule]) -> _CompiledModules:
    diagnostics = [_lint_to_diagnostic(diag) for diag in _lint_modules(modules)]
    if any(diag.severity == Severity.ERROR.value for diag in diagnostics):
        return _CompiledModules(None, diagnostics)

    try:
        model = resolve(modules)
    except ResolverErrors as err:
        resolver_diags = [
            DiagnosticResult(
                severity=Severity.ERROR.value,
                code="resolver-error",
                message=item.message,
                file=item.source_file or None,
                line=item.line or None,
                column=None,
            )
            for item in err.errors
        ]
        return _CompiledModules(None, resolver_diags)

    model_diags = [
        _lint_to_diagnostic(diag)
        for diag in _lint_modules(modules, model=model)
        if diag.rule in _MODEL_AWARE_RULES
    ]
    all_diags = [*diagnostics, *model_diags]
    if any(diag.severity == Severity.ERROR.value for diag in all_diags):
        return _CompiledModules(None, all_diags)

    return _CompiledModules(model, all_diags)


def _lint_modules(
    modules: list[DVMLModule],
    model: DataVaultModel | None = None,
) -> list[LintDiagnostic]:
    diagnostics: list[LintDiagnostic] = []
    for module in modules:
        diagnostics.extend(lint(module, model=model))
    return diagnostics


def _parse_error_to_diagnostic(err: DVMLParseError) -> DiagnosticResult:
    return DiagnosticResult(
        severity=Severity.ERROR.value,
        code="parse-error",
        message=err.error.hint,
        file=err.error.file,
        line=err.error.line,
        column=err.error.column,
    )


def _lint_to_diagnostic(diag: LintDiagnostic) -> DiagnosticResult:
    return DiagnosticResult(
        severity=diag.severity.value,
        code=diag.rule,
        message=diag.message,
        file=diag.loc.file or None,
        line=diag.loc.line or None,
        column=diag.loc.column or None,
    )


def _entity_counts(model: DataVaultModel | None) -> dict[str, int]:
    if model is None:
        return {
            "hubs": 0,
            "links": 0,
            "satellites": 0,
            "nhsats": 0,
            "nhlinks": 0,
            "effsats": 0,
            "samlinks": 0,
            "bridges": 0,
            "pits": 0,
        }

    return {
        "hubs": len(model.hubs),
        "links": len(model.links),
        "satellites": len(model.satellites),
        "nhsats": len(model.nhsats),
        "nhlinks": len(model.nhlinks),
        "effsats": len(model.effsats),
        "samlinks": len(model.samlinks),
        "bridges": len(model.bridges),
        "pits": len(model.pits),
    }


def _build_summary(entity_counts: dict[str, int]) -> str:
    parts = [f"{count} {name}" for name, count in entity_counts.items()]
    return "Resolved model contains " + ", ".join(parts) + "."


def _build_entities(model: DataVaultModel) -> list[ExplainEntityResult]:
    entities: list[ExplainEntityResult] = []
    entities.extend(_build_hub_entities(model.hubs.values()))
    entities.extend(_build_satellite_entities(model.satellites.values()))
    entities.extend(_build_link_entities(model.links.values()))
    entities.extend(_build_satellite_entities(model.nhsats.values(), kind="nhsat"))
    entities.extend(_build_link_entities(model.nhlinks.values(), kind="nhlink"))
    entities.extend(_build_satellite_entities(model.effsats.values(), kind="effsat"))
    entities.extend(_build_samlink_entities(model.samlinks.values()))
    entities.extend(_build_bridge_entities(model.bridges.values()))
    entities.extend(_build_pit_entities(model.pits.values()))
    return sorted(entities, key=lambda entity: entity.qualified_name)


def _build_hub_entities(hubs: object) -> list[ExplainEntityResult]:
    return [
        ExplainEntityResult(
            qualified_name=hub.qualified_name,
            kind="hub",
            columns=[column.name for column in [*hub.business_keys, *hub.columns]],
            references=[],
        )
        for hub in sorted(hubs, key=lambda item: item.qualified_name)
    ]


def _build_satellite_entities(
    satellites: object,
    kind: str = "satellite",
) -> list[ExplainEntityResult]:
    return [
        ExplainEntityResult(
            qualified_name=satellite.qualified_name,
            kind=kind,
            columns=[column.name for column in satellite.columns],
            references=[_qualify_reference(satellite.parent_ref, satellite.namespace)],
        )
        for satellite in sorted(satellites, key=lambda item: item.qualified_name)
    ]


def _build_link_entities(links: object, kind: str = "link") -> list[ExplainEntityResult]:
    return [
        ExplainEntityResult(
            qualified_name=link.qualified_name,
            kind=kind,
            columns=[column.name for column in link.columns],
            references=[_qualify_reference(reference, link.namespace) for reference in link.hub_references],
        )
        for link in sorted(links, key=lambda item: item.qualified_name)
    ]


def _build_samlink_entities(samlinks: object) -> list[ExplainEntityResult]:
    return [
        ExplainEntityResult(
            qualified_name=samlink.qualified_name,
            kind="samlink",
            columns=[column.name for column in samlink.columns],
            references=[
                _qualify_reference(samlink.master_ref, samlink.namespace),
                _qualify_reference(samlink.duplicate_ref, samlink.namespace),
            ],
        )
        for samlink in sorted(samlinks, key=lambda item: item.qualified_name)
    ]


def _build_bridge_entities(bridges: object) -> list[ExplainEntityResult]:
    return [
        ExplainEntityResult(
            qualified_name=bridge.qualified_name,
            kind="bridge",
            columns=[],
            references=[_qualify_reference(reference, bridge.namespace) for reference in bridge.path],
        )
        for bridge in sorted(bridges, key=lambda item: item.qualified_name)
    ]


def _build_pit_entities(pits: object) -> list[ExplainEntityResult]:
    return [
        ExplainEntityResult(
            qualified_name=pit.qualified_name,
            kind="pit",
            columns=[],
            references=[
                _qualify_reference(pit.anchor_ref, pit.namespace),
                *[_qualify_reference(reference, pit.namespace) for reference in pit.tracked_satellites],
            ],
        )
        for pit in sorted(pits, key=lambda item: item.qualified_name)
    ]


def _qualify_reference(reference: str, namespace: str) -> str:
    if "." in reference or not namespace:
        return reference
    return f"{namespace}.{reference}"
