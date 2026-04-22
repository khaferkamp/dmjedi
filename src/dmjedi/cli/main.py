"""DMJEDI CLI entry point."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from dmjedi.application.requests import CompileRequest
from dmjedi.application.results import ArtifactResult, DiagnosticResult, DocsResult, GenerateResult
from dmjedi.application.results import ValidateResult
from dmjedi.application.services import docs_request, generate_request, validate_request
from dmjedi.cli.errors import format_lint_diagnostic, print_diagnostics
from dmjedi.generators.base import GeneratorResult
from dmjedi.lang.ast import SourceLocation
from dmjedi.lang.linter import LintDiagnostic, Severity
from dmjedi.lsp.server import start_server

app = typer.Typer(
    name="dmjedi",
    help="Data Modeling Jedi — Data Vault 2.1 modeling and data warehouse automation.",
    no_args_is_help=True,
)

_OUTPUT_FORMATS = {"text", "json"}
_STRUCTURED_ERROR_CODES = {
    "generator-error",
    "import-error",
    "parse-error",
    "path-error",
    "resolver-error",
}


@app.command()
def validate(
    paths: list[Path] = typer.Argument(..., help="DVML files or directories to validate"),
    format: str = typer.Option("text", "--format", help="Output format: text or json."),
) -> None:
    """Validate DVML model files."""
    console = Console(stderr=True)
    output_format = _parse_output_format(format, console)
    result = validate_request(CompileRequest(paths=paths))

    if output_format == "json":
        typer.echo(result.model_dump_json(indent=2))
        if not result.ok:
            raise typer.Exit(code=1)
        return

    _print_result_diagnostics(result.diagnostics, console)
    if not result.ok:
        raise typer.Exit(code=1)
    if not result.diagnostics:
        console.print("[green]All files valid.[/green]")


@app.command()
def generate(
    paths: list[Path] = typer.Argument(..., help="DVML files or directories"),
    target: str = typer.Option("spark-declarative", "--target", "-t", help="Generator target"),
    output: Path = typer.Option("output", "--output", "-o", help="Output directory"),
    dialect: str = typer.Option(
        "default",
        "--dialect",
        help="SQL dialect for type mapping. Only applies to --target sql-jinja.",
    ),
    format: str = typer.Option("text", "--format", help="Output format: text or json."),
) -> None:
    """Generate pipeline code from DVML models."""
    console = Console(stderr=True)
    output_format = _parse_output_format(format, console)

    # Validate dialect against supported dialects from type mapping (D-08)
    from dmjedi.model.types import SUPPORTED_DIALECTS

    if dialect not in SUPPORTED_DIALECTS:
        result = GenerateResult(
            ok=False,
            source_mode="paths",
            target=target,
            dialect=dialect,
            diagnostics=[
                DiagnosticResult(
                    severity=Severity.ERROR.value,
                    code="generator-error",
                    message=(
                        f"Invalid dialect '{dialect}'. "
                        f"Choose from: {', '.join(SUPPORTED_DIALECTS)}"
                    ),
                )
            ],
        )
    else:
        result = generate_request(CompileRequest(paths=paths), target=target, dialect=dialect)

    if output_format == "json":
        typer.echo(result.model_dump_json(indent=2))
        if not result.ok:
            raise typer.Exit(code=1)
        return

    _print_result_diagnostics(result.diagnostics, console)
    if not result.ok:
        raise typer.Exit(code=1)

    if dialect != "default" and target != "sql-jinja":
        console.print(
            "[yellow]Warning:[/yellow] --dialect is only used with --target sql-jinja; ignoring."
        )

    written = _write_artifacts(result.artifacts, output)
    console.print(f"[green]Generated {len(written)} file(s) into {output}/[/green]")
    for p in written:
        console.print(f"  {p}")


@app.command()
def docs(
    paths: list[Path] = typer.Argument(..., help="DVML files or directories"),
    output: Path = typer.Option("output/docs", "--output", "-o", help="Output directory"),
) -> None:
    """Generate markdown documentation from DVML models."""
    console = Console(stderr=True)
    modules = _parse_all(paths, console)

    # Lint
    all_diagnostics = []
    for module in modules:
        all_diagnostics.extend(lint(module))
    error_count = sum(1 for d in all_diagnostics if d.severity == Severity.ERROR)
    if all_diagnostics:
        print_diagnostics(all_diagnostics, console)
    if error_count > 0:
        raise typer.Exit(code=1)

    try:
        model = resolve(modules)
    except ResolverErrors as e:
        for err in e.errors:
            loc = f"{err.source_file}:{err.line} " if err.source_file else ""
            console.print(f"[red]E[/red] {loc}{err.message}")
        raise typer.Exit(code=1) from None

    # Post-resolve lint for model-aware rules (LINT-01 effsat parent check)
    post_resolve_diags: list[LintDiagnostic] = []
    for module in modules:
        post_resolve_diags.extend(lint(module, model=model))
    model_aware_diags = [
        d for d in post_resolve_diags if d.rule in ("effsat-parent-must-be-link",)
    ]
    if model_aware_diags:
        print_diagnostics(model_aware_diags, console)
    model_aware_error_count = sum(1 for d in model_aware_diags if d.severity == Severity.ERROR)
    if model_aware_error_count > 0:
        raise typer.Exit(code=1)

    markdown = generate_markdown(model)

    output.mkdir(parents=True, exist_ok=True)
    doc_path = output / "model.md"
    doc_path.write_text(markdown)
    console.print(f"[green]Documentation written to {doc_path}[/green]")


@app.command()
def lsp() -> None:
    """Start the DVML Language Server."""
    start_server()


def _parse_output_format(value: str, console: Console) -> str:
    if value in _OUTPUT_FORMATS:
        return value

    console.print("[red]Error:[/red] Invalid format. Choose from: text, json")
    raise typer.Exit(code=1)


def _print_result_diagnostics(diagnostics: list[DiagnosticResult], console: Console) -> None:
    lint_diagnostics: list[LintDiagnostic] = []

    for diagnostic in diagnostics:
        if diagnostic.code in _STRUCTURED_ERROR_CODES:
            _print_structured_diagnostic(diagnostic, console)
            continue

        lint_diagnostics.append(
            LintDiagnostic(
                message=diagnostic.message,
                severity=Severity(diagnostic.severity),
                loc=SourceLocation(
                    file=diagnostic.file or "<unknown>",
                    line=diagnostic.line or 0,
                    column=diagnostic.column or 0,
                ),
                rule=diagnostic.code,
            )
        )

    if lint_diagnostics:
        print_diagnostics(lint_diagnostics, console)


def _print_structured_diagnostic(diagnostic: DiagnosticResult, console: Console) -> None:
    if diagnostic.code == "parse-error":
        loc = (
            f"{diagnostic.file}:{diagnostic.line}:{diagnostic.column}"
            if diagnostic.line and diagnostic.column
            else (diagnostic.file or "<unknown>")
        )
        console.print(f"[red]{loc}: error:[/red] {diagnostic.message}")
        return

    if diagnostic.code == "resolver-error" and diagnostic.file and diagnostic.line:
        console.print(f"[red]E[/red] {diagnostic.file}:{diagnostic.line} {diagnostic.message}")
        return

    label = "[red]Error:[/red]" if diagnostic.severity == Severity.ERROR.value else "[yellow]Warning:[/yellow]"
    console.print(f"{label} {diagnostic.message}")


def _write_artifacts(artifacts: list[ArtifactResult], output_dir: Path) -> list[Path]:
    result = GeneratorResult()
    for artifact in artifacts:
        result.add_file(artifact.path, artifact.content)
    return result.write(output_dir)


if __name__ == "__main__":
    app()
