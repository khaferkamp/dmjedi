"""Tests for DVML file discovery."""

from pathlib import Path

import pytest

from dmjedi.lang.discovery import discover_dv_files


def test_discover_single_file(fixtures_dir: Path) -> None:
    """Pass a single .dv file path, get it back."""
    sales = fixtures_dir / "sales.dv"
    result = discover_dv_files([sales])
    assert result == [sales]


def test_discover_directory(fixtures_dir: Path) -> None:
    """Pass fixtures directory, get all .dv files recursively."""
    result = discover_dv_files([fixtures_dir])
    assert len(result) >= 1
    assert all(p.suffix == ".dv" for p in result)
    assert fixtures_dir / "sales.dv" in result


def test_discover_nonexistent() -> None:
    """Pass missing path, raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Path not found"):
        discover_dv_files([Path("/nonexistent/path.dv")])


def test_discover_mixed(fixtures_dir: Path) -> None:
    """Pass a file and a directory, get combined deduplicated results."""
    sales = fixtures_dir / "sales.dv"
    result = discover_dv_files([sales, fixtures_dir])
    # sales.dv appears in both the explicit file and the directory scan,
    # but should only appear once in the result
    assert result.count(sales) == 1
    assert sales in result


def test_discover_nested_dirs(tmp_path: Path) -> None:
    """Create nested dirs with .dv files, verify recursive find."""
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "b").mkdir()
    f1 = tmp_path / "top.dv"
    f2 = tmp_path / "a" / "mid.dv"
    f3 = tmp_path / "a" / "b" / "deep.dv"
    for f in (f1, f2, f3):
        f.write_text("# placeholder")

    result = discover_dv_files([tmp_path])
    assert len(result) == 3
    assert set(result) == {f1, f2, f3}
    # Verify sorted by string
    assert result == sorted(result, key=str)


def test_discover_empty_directory(tmp_path: Path) -> None:
    """Empty directory returns empty list."""
    result = discover_dv_files([tmp_path])
    assert result == []
