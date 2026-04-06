"""Tests for CLI commands and error formatting."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from dmjedi.cli.errors import format_lint_diagnostic, format_parse_error
from dmjedi.cli.main import app
from dmjedi.lang.ast import SourceLocation
from dmjedi.lang.linter import LintDiagnostic, Severity

runner = CliRunner()


# --- validate command ---


def test_validate_valid_file() -> None:
    result = runner.invoke(app, ["validate", "examples/sales-domain.dv"])
    assert result.exit_code == 0


def test_validate_nonexistent_file() -> None:
    result = runner.invoke(app, ["validate", "nonexistent.dv"])
    assert result.exit_code == 1
    assert "File not found" in result.output


def test_validate_lint_error(tmp_path: Path) -> None:
    bad_dv = tmp_path / "bad.dv"
    bad_dv.write_text("namespace test\nhub Empty {\n}\n")
    result = runner.invoke(app, ["validate", str(bad_dv)])
    assert result.exit_code == 1
    # Rich may wrap long lines, so normalize whitespace before checking
    normalized = " ".join(result.output.split())
    assert "has no business keys" in normalized


def test_validate_syntax_error(tmp_path: Path) -> None:
    bad_dv = tmp_path / "syntax.dv"
    bad_dv.write_text("this is not valid dvml !!!")
    result = runner.invoke(app, ["validate", str(bad_dv)])
    assert result.exit_code == 1
    assert "Syntax error" in result.output


# --- generate command ---


def test_generate_valid(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "generate",
            "examples/sales-domain.dv",
            "--target",
            "sql-jinja",
            "--output",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0
    assert "Generated" in result.output
    generated_files = list(tmp_path.rglob("*"))
    assert len([f for f in generated_files if f.is_file()]) > 0


def test_generate_unknown_target() -> None:
    result = runner.invoke(app, ["generate", "examples/sales-domain.dv", "--target", "nonexistent"])
    assert result.exit_code == 1
    assert "Unknown generator" in result.output


def test_generate_nonexistent_file() -> None:
    result = runner.invoke(app, ["generate", "nonexistent.dv"])
    assert result.exit_code == 1
    assert "File not found" in result.output


# --- docs command ---


def test_docs_valid(tmp_path: Path) -> None:
    result = runner.invoke(app, ["docs", "examples/sales-domain.dv", "--output", str(tmp_path)])
    assert result.exit_code == 0
    assert "Documentation written" in result.output
    assert (tmp_path / "model.md").exists()
    content = (tmp_path / "model.md").read_text()
    assert "Customer" in content


# --- error formatting ---


def test_format_lint_diagnostic() -> None:
    diag = LintDiagnostic(
        message="Hub 'Foo' has no business keys",
        severity=Severity.ERROR,
        loc=SourceLocation(file="test.dv", line=5, column=1),
        rule="hub-requires-business-key",
    )
    formatted = format_lint_diagnostic(diag)
    assert "test.dv:5:1" in formatted
    assert "hub-requires-business-key" in formatted
    assert "[red]E[/red]" in formatted


def test_format_lint_diagnostic_warning() -> None:
    diag = LintDiagnostic(
        message="Satellite 'Foo' has no fields",
        severity=Severity.WARNING,
        loc=SourceLocation(file="test.dv", line=10, column=1),
        rule="satellite-requires-fields",
    )
    formatted = format_lint_diagnostic(diag)
    assert "[yellow]W[/yellow]" in formatted


def test_format_parse_error() -> None:
    from dmjedi.lang.parser import parse

    try:
        parse("this is not valid dvml !!!")
    except Exception as err:
        from lark.exceptions import UnexpectedInput

        assert isinstance(err, UnexpectedInput)
        formatted = format_parse_error(err, "bad.dv")
        assert "bad.dv:" in formatted
        assert "Syntax error" in formatted
