from __future__ import annotations

from pathlib import Path

import pytest

from dmjedi.application.requests import CompileRequest
from dmjedi.application.results import GenerateResult, ValidateResult
from dmjedi.generators.base import GeneratorResult


def test_validate_result_json_schema() -> None:
    schema = ValidateResult.model_json_schema()

    assert schema["title"] == "ValidateResult"
    assert schema["properties"]["ok"]["type"] == "boolean"
    assert schema["properties"]["source_mode"]["type"] == "string"
    assert schema["properties"]["module_count"]["type"] == "integer"
    assert schema["properties"]["diagnostics"]["type"] == "array"


def test_generate_result_artifact_shape() -> None:
    payload = GenerateResult(
        ok=True,
        source_mode="paths",
        target="sql-jinja",
        dialect="postgres",
        module_count=1,
        diagnostics=[],
        artifacts=[
            {
                "path": "hubs/customer.sql",
                "content": "select 1",
            }
        ],
    ).model_dump(mode="json")

    assert payload["artifacts"] == [
        {
            "path": "hubs/customer.sql",
            "content": "select 1",
        }
    ]


def test_validate_request_parse_error_code() -> None:
    from dmjedi.application.services import validate_request

    result = validate_request(CompileRequest(source="this is not valid dvml !!!"))

    assert result.ok is False
    assert result.diagnostics[0].code == "parse-error"
    assert result.diagnostics[0].file == "<string>"


def test_validate_request_resolver_error_code() -> None:
    from dmjedi.application.services import validate_request

    result = validate_request(
        CompileRequest(
            source="namespace sales\nsatellite CustomerDetails of Missing {\n  email: string\n}\n"
        )
    )

    assert result.ok is False
    assert [diag.code for diag in result.diagnostics] == ["resolver-error"]


def test_generate_request_returns_artifacts_without_writing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dmjedi.application.services import generate_request

    def fail_write(self: GeneratorResult, output_dir: Path) -> list[Path]:
        msg = f"unexpected write to {output_dir}"
        raise AssertionError(msg)

    monkeypatch.setattr(GeneratorResult, "write", fail_write)

    result = generate_request(
        CompileRequest(paths=[Path("tests/fixtures/sales.dv")]),
        target="sql-jinja",
        dialect="postgres",
    )

    assert result.ok is True
    assert result.target == "sql-jinja"
    assert result.artifacts
    assert all(artifact.path for artifact in result.artifacts)
    assert all(artifact.content for artifact in result.artifacts)


def test_docs_request_returns_model_markdown_artifact() -> None:
    from dmjedi.application.services import docs_request

    result = docs_request(CompileRequest(paths=[Path("tests/fixtures/sales.dv")]))

    assert result.ok is True
    assert result.artifacts[0].path == "model.md"
    assert "# Data Vault Model Documentation" in result.artifacts[0].content
