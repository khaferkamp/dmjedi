"""DVML linter — validates AST nodes against Data Vault 2.1 modeling rules."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dmjedi.lang.ast import DVMLModule, SourceLocation

if TYPE_CHECKING:
    from dmjedi.model.core import DataVaultModel


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class LintDiagnostic:
    message: str
    severity: Severity
    loc: SourceLocation
    rule: str


def lint(
    module: DVMLModule,
    model: DataVaultModel | None = None,
    config_path: Path | None = None,
) -> list[LintDiagnostic]:
    """Run all lint rules against a parsed DVML module."""
    diagnostics: list[LintDiagnostic] = []
    diagnostics.extend(_check_namespace(module))
    diagnostics.extend(_check_hubs(module))
    diagnostics.extend(_check_satellites(module))
    diagnostics.extend(_check_links(module))
    diagnostics.extend(_check_effsats(module, model))
    diagnostics.extend(_check_samlinks(module))
    naming_config = _load_lint_config(config_path or Path(".dvml-lint.toml"))
    diagnostics.extend(_check_naming(module, naming_config))
    return diagnostics


def _check_namespace(module: DVMLModule) -> list[LintDiagnostic]:
    diags: list[LintDiagnostic] = []
    if not module.namespace:
        diags.append(
            LintDiagnostic(
                message=f"No namespace declared in '{module.source_file or '<string>'}'",
                severity=Severity.WARNING,
                loc=SourceLocation(file=module.source_file),
                rule="missing-namespace",
            )
        )
    return diags


def _check_hubs(module: DVMLModule) -> list[LintDiagnostic]:
    diags: list[LintDiagnostic] = []
    for hub in module.hubs:
        if not hub.business_keys:
            diags.append(
                LintDiagnostic(
                    message=f"Hub '{hub.name}' has no business keys defined",
                    severity=Severity.ERROR,
                    loc=hub.loc,
                    rule="hub-requires-business-key",
                )
            )
    return diags


def _check_satellites(module: DVMLModule) -> list[LintDiagnostic]:
    diags: list[LintDiagnostic] = []
    for sat in module.satellites:
        if not sat.fields:
            diags.append(
                LintDiagnostic(
                    message=f"Satellite '{sat.name}' has no fields defined",
                    severity=Severity.WARNING,
                    loc=sat.loc,
                    rule="satellite-requires-fields",
                )
            )
    return diags


def _check_links(module: DVMLModule) -> list[LintDiagnostic]:
    diags: list[LintDiagnostic] = []
    for link in module.links:
        if len(link.references) < 2:
            diags.append(
                LintDiagnostic(
                    message=f"Link '{link.name}' must reference at least 2 hubs",
                    severity=Severity.ERROR,
                    loc=link.loc,
                    rule="link-requires-two-refs",
                )
            )
    return diags


def _check_effsats(
    module: DVMLModule, model: DataVaultModel | None
) -> list[LintDiagnostic]:
    """LINT-01: EffSat parent must be a link, not a hub."""
    diags: list[LintDiagnostic] = []
    if model is None:
        return diags
    for effsat in module.effsats:
        ref = effsat.parent_ref
        ns = module.namespace
        ns_ref = f"{ns}.{ref}" if ns else ref
        in_links = ref in model.links or ns_ref in model.links
        in_hubs = ref in model.hubs or ns_ref in model.hubs
        if not in_links and in_hubs:
            diags.append(
                LintDiagnostic(
                    message=f"EffSat '{effsat.name}' parent '{ref}' is a hub, not a link",
                    severity=Severity.WARNING,
                    loc=effsat.loc,
                    rule="effsat-parent-must-be-link",
                )
            )
    return diags


def _check_samlinks(module: DVMLModule) -> list[LintDiagnostic]:
    """LINT-02: SamLink master and duplicate should reference the same hub."""
    diags: list[LintDiagnostic] = []
    for samlink in module.samlinks:
        if samlink.master_ref != samlink.duplicate_ref:
            diags.append(
                LintDiagnostic(
                    message=(
                        f"SamLink '{samlink.name}' master '{samlink.master_ref}' and "
                        f"duplicate '{samlink.duplicate_ref}' reference different hubs"
                    ),
                    severity=Severity.WARNING,
                    loc=samlink.loc,
                    rule="samlink-same-hub",
                )
            )
    return diags


def _load_lint_config(config_path: Path) -> dict[str, str]:
    """Load naming prefixes from .dvml-lint.toml if present."""
    if not config_path.exists():
        return {}
    with config_path.open("rb") as f:
        data = tomllib.load(f)
    naming: dict[str, str] = data.get("naming", {})
    return naming


def _check_naming(
    module: DVMLModule, config: dict[str, str]
) -> list[LintDiagnostic]:
    """LINT-03: Entity names must match configured prefix conventions."""
    if not config:
        return []
    diags: list[LintDiagnostic] = []
    checks: list[tuple[str, list[Any]]] = [
        ("hub", module.hubs),
        ("sat", module.satellites),
        ("link", module.links),
        ("nhsat", module.nhsats),
        ("nhlink", module.nhlinks),
        ("effsat", module.effsats),
        ("samlink", module.samlinks),
    ]
    for entity_type, entities in checks:
        prefix = config.get(entity_type)
        if not prefix:
            continue
        for entity in entities:
            if not entity.name.startswith(prefix):
                diags.append(
                    LintDiagnostic(
                        message=(
                            f"{entity_type.capitalize()} '{entity.name}' does not start "
                            f"with required prefix '{prefix}'"
                        ),
                        severity=Severity.WARNING,
                        loc=entity.loc,
                        rule="naming-convention",
                    )
                )
    return diags
