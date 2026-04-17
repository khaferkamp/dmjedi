"""DMJEDI CLI entry point."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from dmjedi.cli.errors import format_parse_error, print_diagnostics
from dmjedi.docs.markdown import generate_markdown
from dmjedi.generators import registry
from dmjedi.lang.ast import DVMLModule
from dmjedi.lang.discovery import discover_dv_files
from dmjedi.lang.imports import CircularImportError, resolve_imports
from dmjedi.lang.linter import LintDiagnostic, Severity, lint
from dmjedi.lang.parser import DVMLParseError, parse_file
from dmjedi.lsp.server import start_server
from dmjedi.model.resolver import ResolverErrors, resolve

app = typer.Typer(
    name="dmjedi",
    help="Data Modeling Jedi — Data Vault 2.1 modeling and data warehouse automation.",
    no_args_is_help=True,
)


@app.command()
def validate(
    paths: list[Path] = typer.Argument(..., help="DVML files or directories to validate"),
) -> None:
    """Validate DVML model files."""
    console = Console(stderr=True)
    modules = _parse_all(paths, console)

    all_diagnostics: list[LintDiagnostic] = []
    for module in modules:
        all_diagnostics.extend(lint(module))

    if all_diagnostics:
        print_diagnostics(all_diagnostics, console)

    error_count = sum(1 for d in all_diagnostics if d.severity == Severity.ERROR)
    if error_count > 0:
        raise typer.Exit(code=1)

    # Also run resolver to catch cross-module errors
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

    if not all_diagnostics and not model_aware_diags:
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
) -> None:
    """Generate pipeline code from DVML models."""
    console = Console(stderr=True)

    # Validate dialect against supported dialects from type mapping (D-08)
    from dmjedi.model.types import SUPPORTED_DIALECTS

    if dialect not in SUPPORTED_DIALECTS:
        console.print(
            f"[red]Error:[/red] Invalid dialect '{dialect}'. "
            f"Choose from: {', '.join(SUPPORTED_DIALECTS)}"
        )
        raise typer.Exit(code=1)

    modules = _parse_all(paths, console)

    # Lint all modules
    all_diagnostics = []
    for module in modules:
        all_diagnostics.extend(lint(module))

    error_count = sum(1 for d in all_diagnostics if d.severity == Severity.ERROR)
    if all_diagnostics:
        print_diagnostics(all_diagnostics, console)
    if error_count > 0:
        raise typer.Exit(code=1)

    # Resolve
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

    # Warn if --dialect used with non-sql-jinja target (per D-15)
    if dialect != "default" and target != "sql-jinja":
        console.print(
            "[yellow]Warning:[/yellow] --dialect is only used with --target sql-jinja; ignoring."
        )

    # Generate via factory pattern (D-07)
    try:
        gen = registry.get(target, dialect=dialect)
    except KeyError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from None

    result = gen.generate(model)
    written = result.write(output)
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


def _parse_all(paths: list[Path], console: Console) -> list[DVMLModule]:
    """Discover, parse, and resolve imports for all .dv files."""
    # Step 1: Discover files
    try:
        dv_files = discover_dv_files(paths)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] File not found: {e}")
        raise typer.Exit(code=1) from None

    if not dv_files:
        console.print("[yellow]Warning:[/yellow] No .dv files found in the given paths.")
        raise typer.Exit(code=1)

    # Step 2: Parse all discovered files
    modules: list[DVMLModule] = []
    for path in dv_files:
        try:
            modules.append(parse_file(path))
        except DVMLParseError as e:
            console.print(format_parse_error(e))
            raise typer.Exit(code=1) from None

    # Step 3: Resolve imports
    try:
        modules = resolve_imports(modules)
    except CircularImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from None
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from None

    return modules


if __name__ == "__main__":
    app()
