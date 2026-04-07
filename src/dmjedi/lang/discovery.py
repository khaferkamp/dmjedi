"""DVML file discovery — finds .dv files in paths and directories."""

from pathlib import Path


def discover_dv_files(paths: list[Path]) -> list[Path]:
    """Discover all .dv files from a list of file and directory paths.

    - If a path is a file, include it directly (even if not .dv)
    - If a path is a directory, recursively find all .dv files within it
    - Returns paths sorted by string representation for deterministic ordering
    - Raises FileNotFoundError for paths that don't exist
    """
    result: list[Path] = []
    for path in paths:
        if not path.exists():
            msg = f"Path not found: {path}"
            raise FileNotFoundError(msg)
        if path.is_file():
            result.append(path)
        elif path.is_dir():
            result.extend(sorted(path.rglob("*.dv")))
    return sorted(set(result), key=str)
