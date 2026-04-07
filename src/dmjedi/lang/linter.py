"""DVML linter — validates AST nodes against Data Vault 2.1 modeling rules."""

from dataclasses import dataclass
from enum import Enum

from dmjedi.lang.ast import DVMLModule, SourceLocation


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class LintDiagnostic:
    message: str
    severity: Severity
    loc: SourceLocation
    rule: str


def lint(module: DVMLModule) -> list[LintDiagnostic]:
    """Run all lint rules against a parsed DVML module."""
    diagnostics: list[LintDiagnostic] = []
    diagnostics.extend(_check_namespace(module))
    diagnostics.extend(_check_hubs(module))
    diagnostics.extend(_check_satellites(module))
    diagnostics.extend(_check_links(module))
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
