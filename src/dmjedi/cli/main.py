"""DMJEDI CLI entry point."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from dmjedi.cli.errors import format_parse_error, print_diagnostics
from dmjedi.lang.parser import DVMLParseError
from dmjedi.docs.markdown import generate_markdown
from dmjedi.generators import registry
from dmjedi.lang.ast import DVMLModule
from dmjedi.lang.discovery import discover_dv_files
from dmjedi.lang.imports import CircularImportError, resolve_imports
from dmjedi.lang.linter import LintDiagnostic, Severity, lint
from dmjedi.lang.parser import parse_file
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
        resolve(modules)
    except ResolverErrors as e:
        for err in e.errors:
            loc = f"{err.source_file}:{err.line} " if err.source_file else ""
            console.print(f"[red]E[/red] {loc}{err.message}")
        raise typer.Exit(code=1) from None

    if not all_diagnostics:
        console.print("[green]All files valid.[/green]")


@app.command()
def generate(
    paths: list[Path] = typer.Argument(..., help="DVML files or directories"),
    target: str = typer.Option("spark-declarative", "--target", "-t", help="Generator target"),
    output: Path = typer.Option("output", "--output", "-o", help="Output directory"),
) -> None:
    """Generate pipeline code from DVML models."""
    console = Console(stderr=True)
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

    # Generate
    try:
        gen = registry.get(target)
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

    markdown = generate_markdown(model)

    output.mkdir(parents=True, exist_ok=True)
    doc_path = output / "model.md"
    doc_path.write_text(markdown)
    console.print(f"[green]Documentation written to {doc_path}[/green]")


@app.command()
def lsp() -> None:
    """Start the DVML Language Server."""
    typer.echo("Starting DVML Language Server...")
    # TODO: launch pygls server


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
