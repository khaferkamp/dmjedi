"""Tests for DVML import resolution."""

from pathlib import Path

import pytest

from dmjedi.lang.ast import DVMLModule, ImportDecl, SourceLocation
from dmjedi.lang.imports import CircularImportError, resolve_imports
from dmjedi.lang.parser import parse_file


def test_resolve_no_imports(fixtures_dir: Path) -> None:
    """A module with no imports is returned unchanged."""
    module = parse_file(fixtures_dir / "imports" / "hub_defs.dv")
    result = resolve_imports([module])
    assert len(result) == 1
    assert result[0].source_file == module.source_file
    assert len(result[0].hubs) == 1
    assert result[0].hubs[0].name == "Customer"


def test_resolve_single_import(fixtures_dir: Path) -> None:
    """Resolving main.dv pulls in hub_defs.dv first (dependency order)."""
    module = parse_file(fixtures_dir / "imports" / "main.dv")
    result = resolve_imports([module])
    assert len(result) == 2
    # hub_defs.dv should come first (imported dependency)
    assert "hub_defs.dv" in result[0].source_file
    assert len(result[0].hubs) == 1
    # main.dv should come second
    assert "main.dv" in result[1].source_file
    assert len(result[1].satellites) == 1


def test_circular_import_detected(fixtures_dir: Path) -> None:
    """Circular imports between two files raise CircularImportError."""
    module = parse_file(fixtures_dir / "imports" / "circular_a.dv")
    with pytest.raises(CircularImportError) as exc_info:
        resolve_imports([module])
    assert len(exc_info.value.cycle) >= 2
    assert "circular_a.dv" in exc_info.value.cycle[0]


def test_import_file_not_found(tmp_path: Path) -> None:
    """Importing a non-existent file raises FileNotFoundError with a descriptive message."""
    module = DVMLModule(
        namespace="test",
        imports=[ImportDecl(path="nonexistent.dv", loc=SourceLocation(file="fake.dv", line=2))],
        source_file=str(tmp_path / "fake.dv"),
    )
    # Create the fake.dv so the parent dir resolves, but not the import target
    (tmp_path / "fake.dv").write_text("")
    with pytest.raises(FileNotFoundError, match=r"nonexistent\.dv"):
        resolve_imports([module])


def test_diamond_import(tmp_path: Path) -> None:
    """Diamond dependency (A->B,C; B->D; C->D) deduplicates D and orders correctly."""
    # Create D (leaf)
    (tmp_path / "d.dv").write_text('namespace test\n\nhub D {\n    business_key d_id : int\n}\n')
    # Create B (imports D)
    (tmp_path / "b.dv").write_text(
        'namespace test\n\nimport "d.dv"\n\nhub B {\n    business_key b_id : int\n}\n'
    )
    # Create C (imports D)
    (tmp_path / "c.dv").write_text(
        'namespace test\n\nimport "d.dv"\n\nhub C {\n    business_key c_id : int\n}\n'
    )
    # Create A (imports B and C)
    (tmp_path / "a.dv").write_text(
        'namespace test\n\nimport "b.dv"\nimport "c.dv"\n\n'
        "hub A {\n    business_key a_id : int\n}\n"
    )

    module_a = parse_file(tmp_path / "a.dv")
    result = resolve_imports([module_a])

    # Should have exactly 4 modules: D, B, C, A
    assert len(result) == 4
    names = [Path(m.source_file).name for m in result]
    assert names == ["d.dv", "b.dv", "c.dv", "a.dv"]


def test_resolve_string_source() -> None:
    """A module with source_file='<string>' passes through without import resolution."""
    module = DVMLModule(
        namespace="test",
        source_file="<string>",
        imports=[ImportDecl(path="something.dv")],
    )
    result = resolve_imports([module])
    assert len(result) == 1
    assert result[0].source_file == "<string>"
