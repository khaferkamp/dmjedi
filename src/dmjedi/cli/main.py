"""DMJEDI CLI entry point."""

from __future__ import annotations

from pathlib import Path

import typer
from lark.exceptions import UnexpectedInput
from rich.console import Console

from dmjedi.cli.errors import format_parse_error, print_diagnostics
from dmjedi.docs.markdown import generate_markdown
from dmjedi.generators import registry
from dmjedi.lang.ast import DVMLModule
from dmjedi.lang.linter import LintDiagnostic, Severity, lint
from dmjedi.lang.parser import parse_file
from dmjedi.model.resolver import resolve

app = typer.Typer(
    name="dmjedi",
    help="Data Modeling Jedi — Data Vault 2.1 modeling and data warehouse automation.",
    no_args_is_help=True,
)


@app.command()
def validate(
    paths: list[Path] = typer.Argument(..., help="DVML files to validate"),
) -> None:
    """Validate DVML model files."""
    console = Console(stderr=True)
    all_diagnostics: list[LintDiagnostic] = []
    has_parse_error = False

    for path in paths:
        if not path.exists():
            console.print(f"[red]Error:[/red] File not found: {path}")
            raise typer.Exit(code=1)
        try:
            module = parse_file(path)
        except UnexpectedInput as e:
            console.print(format_parse_error(e, str(path)))
            has_parse_error = True
            continue
        diags = lint(module)
        all_diagnostics.extend(diags)

    if all_diagnostics:
        print_diagnostics(all_diagnostics, console)

    error_count = sum(1 for d in all_diagnostics if d.severity == Severity.ERROR)
    if has_parse_error or error_count > 0:
        raise typer.Exit(code=1)

    if not has_parse_error and not all_diagnostics:
        console.print("[green]All files valid.[/green]")


@app.command()
def generate(
    paths: list[Path] = typer.Argument(..., help="DVML files"),
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
    model = resolve(modules)

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
    paths: list[Path] = typer.Argument(..., help="DVML files"),
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

    model = resolve(modules)
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
    """Parse all .dv files, printing errors and exiting on failure."""
    modules: list[DVMLModule] = []
    for path in paths:
        if not path.exists():
            console.print(f"[red]Error:[/red] File not found: {path}")
            raise typer.Exit(code=1)
        try:
            modules.append(parse_file(path))
        except UnexpectedInput as e:
            console.print(format_parse_error(e, str(path)))
            raise typer.Exit(code=1) from None
    return modules


if __name__ == "__main__":
    app()
