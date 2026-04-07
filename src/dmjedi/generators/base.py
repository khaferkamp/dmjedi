"""Abstract base for pluggable code generators."""

from abc import ABC, abstractmethod
from pathlib import Path

from dmjedi.model.core import DataVaultModel


class GeneratorResult:
    """Container for generated output files."""

    def __init__(self) -> None:
        self.files: dict[str, str] = {}  # relative path -> content

    def add_file(self, path: str, content: str) -> None:
        self.files[path] = content

    def write(self, output_dir: Path) -> list[Path]:
        """Write all generated files to disk. Returns list of written paths."""
        written: list[Path] = []
        for rel_path, content in self.files.items():
            full_path = output_dir / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            written.append(full_path)
        return written


class BaseGenerator(ABC):
    """Abstract base class for pipeline code generators.

    Implement this interface to add a new generation target (e.g., dbt, SQL, Spark).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this generator (used with --target flag)."""

    @abstractmethod
    def generate(self, model: DataVaultModel) -> GeneratorResult:
        """Generate pipeline code from a resolved Data Vault model."""
