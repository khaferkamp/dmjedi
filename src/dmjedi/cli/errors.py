"""Error and diagnostic formatting for Rich console output."""

from __future__ import annotations

from lark.exceptions import UnexpectedCharacters, UnexpectedInput, UnexpectedToken
from rich.console import Console

from dmjedi.lang.linter import LintDiagnostic, Severity

_SEVERITY_ICONS: dict[Severity, str] = {
    Severity.ERROR: "[red]E[/red]",
    Severity.WARNING: "[yellow]W[/yellow]",
    Severity.INFO: "[blue]I[/blue]",
}


def format_lint_diagnostic(diag: LintDiagnostic) -> str:
    """Format a single lint diagnostic for Rich markup output.

    Format: ``{severity_icon} {file}:{line}:{col} {message} [{rule}]``
    """
    icon = _SEVERITY_ICONS.get(diag.severity, "?")
    loc = diag.loc
    return f"{icon} {loc.file}:{loc.line}:{loc.column} {diag.message} [{diag.rule}]"


def format_parse_error(err: UnexpectedInput, source_file: str) -> str:
    """Format a Lark parse error for Rich markup output.

    Handles both :class:`UnexpectedToken` and :class:`UnexpectedCharacters`.
    """
    line: int = getattr(err, "line", 0)
    col: int = getattr(err, "column", 0)

    if isinstance(err, UnexpectedToken):
        expected = getattr(err, "expected", None)
        if expected:
            tokens = ", ".join(sorted(expected))
            msg = f"Syntax error: unexpected token. Expected one of: {tokens}"
        else:
            msg = f"Syntax error: unexpected token '{err.token}'"
    elif isinstance(err, UnexpectedCharacters):
        char = getattr(err, "char", "?")
        msg = f"Syntax error: unexpected character '{char}'"
    else:
        msg = f"Syntax error: {err}"

    return f"[red]E[/red] {source_file}:{line}:{col} {msg}"


def print_diagnostics(diagnostics: list[LintDiagnostic], console: Console) -> None:
    """Print all diagnostics to the console with a summary line."""
    for diag in diagnostics:
        console.print(format_lint_diagnostic(diag))

    errors = sum(1 for d in diagnostics if d.severity is Severity.ERROR)
    warnings = sum(1 for d in diagnostics if d.severity is Severity.WARNING)
    console.print(f"{errors} error(s), {warnings} warning(s)")
