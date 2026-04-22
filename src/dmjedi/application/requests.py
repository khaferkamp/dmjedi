"""Normalized compile requests shared by CLI JSON and MCP callers."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CompileRequest(BaseModel):
    """Accept either filesystem paths or inline source, but never both."""

    model_config = ConfigDict(str_strip_whitespace=True)

    paths: list[Path] = Field(default_factory=list)
    source: str | None = None
    source_name: str = "<string>"

    @model_validator(mode="after")
    def validate_input_mode(self) -> "CompileRequest":
        has_paths = bool(self.paths)
        has_source = self.source is not None and self.source != ""

        if has_paths == has_source:
            msg = "exactly one of paths or source must be provided"
            raise ValueError(msg)

        return self

    @property
    def source_mode(self) -> str:
        return "paths" if self.paths else "inline"

