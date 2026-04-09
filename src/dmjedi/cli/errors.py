"""Error and diagnostic formatting for Rich console output."""

from __future__ import annotations

from lark.exceptions import UnexpectedCharacters, UnexpectedInput, UnexpectedToken
from rich.console import Console

from dmjedi.lang.linter import LintDiagnostic, Severity
from dmjedi.lang.parser import DVMLParseError
from dmjedi.lang.parser import ParseError as ParseErrorData

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


def format_parse_error(err: UnexpectedInput | DVMLParseError, source_file: str = "") -> str:
    """Format a parse error for Rich markup output.

    Accepts either a :class:`DVMLParseError` (structured, preferred) or a raw
    :class:`~lark.exceptions.UnexpectedInput` (legacy path).

    Format: ``{file}:{line}:{col}: error: {hint}``
    """
    if isinstance(err, DVMLParseError):
        pe = err.error
    else:
        # Legacy path — build ParseError from raw Lark exception
        line: int = max(0, getattr(err, "line", 0))
        col: int = max(0, getattr(err, "column", 0))
        if isinstance(err, UnexpectedToken):
            expected = getattr(err, "expected", None)
            if expected:
                tokens = ", ".join(sorted(expected))
                hint = f"Syntax error: unexpected token. Expected one of: {tokens}"
            else:
                hint = f"Syntax error: unexpected token '{err.token}'"
        elif isinstance(err, UnexpectedCharacters):
            char = getattr(err, "char", "?")
            hint = f"Syntax error: unexpected character '{char}'"
        else:
            hint = f"Syntax error: {err}"
        pe = ParseErrorData(file=source_file, line=line, column=col, hint=hint)

    loc = f"{pe.file}:{pe.line}:{pe.column}" if pe.line > 0 else f"{pe.file}:end-of-file"
    return f"[red]{loc}: error:[/red] {pe.hint}"


def print_diagnostics(diagnostics: list[LintDiagnostic], console: Console) -> None:
    """Print all diagnostics to the console with a summary line."""
    for diag in diagnostics:
        console.print(format_lint_diagnostic(diag))

    errors = sum(1 for d in diagnostics if d.severity is Severity.ERROR)
    warnings = sum(1 for d in diagnostics if d.severity is Severity.WARNING)
    console.print(f"{errors} error(s), {warnings} warning(s)")
