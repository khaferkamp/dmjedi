"""DVML import resolution -- resolves import declarations across modules."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from dmjedi.lang.ast import DVMLModule
from dmjedi.lang.parser import parse_file


class CircularImportError(Exception):
    """Raised when a circular import is detected."""

    def __init__(self, cycle: list[str]) -> None:
        self.cycle = cycle
        cycle_str = " -> ".join(cycle)
        super().__init__(f"Circular import detected: {cycle_str}")


def resolve_imports(
    modules: list[DVMLModule],
    parse_fn: Callable[[Path], DVMLModule] = parse_file,
) -> list[DVMLModule]:
    """Resolve imports across all modules, returning the complete module list.

    - Recursively follows import declarations
    - Import paths are resolved relative to the importing file's directory
    - Deduplicates by resolved absolute path
    - Detects circular imports and raises CircularImportError
    - Returns modules in dependency order (imported modules first)
    """
    visited: set[str] = set()
    result: list[DVMLModule] = []

    for module in modules:
        _resolve_module(module, visited, result, [], parse_fn)

    return result


def _resolve_module(
    module: DVMLModule,
    visited: set[str],
    result: list[DVMLModule],
    stack: list[str],
    parse_fn: Callable[[Path], DVMLModule],
) -> None:
    """Recursively resolve a module's imports via DFS."""
    resolved_path = (
        str(Path(module.source_file).resolve())
        if module.source_file and module.source_file != "<string>"
        else module.source_file or "<string>"
    )

    if resolved_path in visited:
        return

    stack_set = set(stack)
    if resolved_path in stack_set:
        cycle = [*stack[stack.index(resolved_path) :], resolved_path]
        raise CircularImportError(cycle)

    current_stack = [*stack, resolved_path]

    # Resolve imports depth-first (before marking visited, so cycles are detected)
    if module.source_file and module.source_file != "<string>":
        base_dir = Path(module.source_file).resolve().parent
        for imp in module.imports:
            import_path = (base_dir / imp.path).resolve()
            if not import_path.exists():
                loc = f"{module.source_file}:{imp.loc.line}"
                msg = f"Import not found: '{imp.path}' (referenced from {loc})"
                raise FileNotFoundError(msg)
            import_key = str(import_path)
            if import_key not in visited:
                imported = parse_fn(import_path)
                _resolve_module(imported, visited, result, current_stack, parse_fn)

    visited.add(resolved_path)
    result.append(module)
