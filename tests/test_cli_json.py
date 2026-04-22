from __future__ import annotations

from dmjedi.application.results import GenerateResult, ValidateResult


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

