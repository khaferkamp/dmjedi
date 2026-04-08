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
    assert "not found" in result.output.lower()


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
    assert "error:" in result.output


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
    assert "not found" in result.output.lower()


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
    from dmjedi.lang.parser import DVMLParseError, parse

    try:
        parse("this is not valid dvml !!!", source_file="bad.dv")
    except DVMLParseError as err:
        formatted = format_parse_error(err)
        assert "bad.dv:" in formatted
        assert "error:" in formatted


# --- directory and import integration ---


def test_validate_directory() -> None:
    """Validate accepts a directory and discovers .dv files."""
    result = runner.invoke(app, ["validate", "examples/"])
    assert result.exit_code == 0
    assert "valid" in result.output.lower()


def test_validate_empty_directory(tmp_path: Path) -> None:
    """Validate on empty directory shows warning."""
    result = runner.invoke(app, ["validate", str(tmp_path)])
    assert result.exit_code == 1
    assert "No .dv files found" in result.output


def test_generate_directory() -> None:
    """Generate accepts a directory argument."""
    import tempfile

    with tempfile.TemporaryDirectory() as out:
        result = runner.invoke(app, ["generate", "examples/", "-t", "sql-jinja", "-o", out])
        assert result.exit_code == 0
        assert "Generated" in result.output


def test_validate_duplicate_entity(tmp_path: Path) -> None:
    """Validate catches duplicate entities across files."""
    f1 = tmp_path / "a.dv"
    f2 = tmp_path / "b.dv"
    f1.write_text("namespace test\nhub Customer { business_key id : int }")
    f2.write_text("namespace test\nhub Customer { business_key id : int }")
    result = runner.invoke(app, ["validate", str(f1), str(f2)])
    assert result.exit_code == 1
    assert "Duplicate" in result.output or "duplicate" in result.output.lower()


def test_validate_bad_parent_ref(tmp_path: Path) -> None:
    """Validate catches satellites with non-existent parents."""
    f = tmp_path / "bad.dv"
    f.write_text("namespace test\nsatellite Bad of Ghost { x : string }")
    result = runner.invoke(app, ["validate", str(f)])
    assert result.exit_code == 1
    assert "unknown parent" in result.output.lower() or "Unknown parent" in result.output


def test_validate_with_imports(fixtures_dir: Path) -> None:
    """Validate works with files that have imports."""
    main_dv = fixtures_dir / "imports" / "main.dv"
    if main_dv.exists():
        result = runner.invoke(app, ["validate", str(main_dv)])
        assert result.exit_code == 0


# --- --dialect flag tests ---


FIXTURE_DV = str(Path(__file__).parent / "fixtures" / "sales.dv")


def test_cli_dialect_in_help() -> None:
    """generate --help shows --dialect option with default 'default'."""
    result = runner.invoke(app, ["generate", "--help"])
    assert result.exit_code == 0
    assert "--dialect" in result.output
    assert "default" in result.output


def test_cli_dialect_sql_jinja_postgres(tmp_path: Path) -> None:
    """--dialect postgres produces postgres-specific type mappings in SQL output."""
    result = runner.invoke(
        app,
        [
            "generate",
            FIXTURE_DV,
            "--target",
            "sql-jinja",
            "--dialect",
            "postgres",
            "--output",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0
    # Check that at least one hub SQL file was generated
    hub_files = list((tmp_path / "hubs").glob("*.sql"))
    assert len(hub_files) > 0
    content = hub_files[0].read_text()
    # Postgres dialect maps 'int' to 'INTEGER' (not BIGINT or NUMBER)
    assert "INTEGER" in content or "TEXT" in content


def test_cli_dialect_non_sql_jinja_warns(tmp_path: Path) -> None:
    """--dialect with spark-declarative target emits a warning and exits 0."""
    result = runner.invoke(
        app,
        [
            "generate",
            FIXTURE_DV,
            "--target",
            "spark-declarative",
            "--dialect",
            "postgres",
            "--output",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0
    # Warning must be present in combined output
    combined = result.output + (result.stderr if hasattr(result, "stderr") and result.stderr else "")
    assert "Warning" in combined or "warning" in combined.lower()
    assert "dialect" in combined.lower()


def test_cli_dialect_invalid_value(tmp_path: Path) -> None:
    """--dialect with an invalid value is rejected with exit code 1."""
    result = runner.invoke(
        app,
        [
            "generate",
            FIXTURE_DV,
            "--target",
            "sql-jinja",
            "--dialect",
            "invalid_dialect",
            "--output",
            str(tmp_path),
        ],
    )
    assert result.exit_code != 0
