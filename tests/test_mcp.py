from __future__ import annotations

import pytest
from pydantic import ValidationError

from dmjedi.application.requests import CompileRequest


def test_compile_request_rejects_path_and_source_together() -> None:
    with pytest.raises(ValidationError):
        CompileRequest(paths=["examples/sales-domain.dv"], source="namespace sales")


def test_inline_source_with_imports_is_rejected() -> None:
    from dmjedi.application.services import validate_request

    result = validate_request(
        CompileRequest(
            source=(
                'namespace sales\nimport "./shared.dv"\n'
                "hub Customer {\n  business_key id: int\n}\n"
            ),
        )
    )

    assert result.ok is False
    assert [diag.code for diag in result.diagnostics] == ["inline-source-imports-unsupported"]


def test_validate_request_preserves_lint_location_fields() -> None:
    from dmjedi.application.services import validate_request

    result = validate_request(
        CompileRequest(source="namespace sales\nhub Customer {\n}\n", source_name="inline.dv")
    )

    assert result.ok is False
    diagnostic = result.diagnostics[0]
    assert diagnostic.code == "hub-requires-business-key"
    assert diagnostic.file == "inline.dv"
    assert diagnostic.line == 2
    assert diagnostic.column == 1


def test_explain_request_returns_summary_and_all_entity_count_keys() -> None:
    from dmjedi.application.services import explain_request

    result = explain_request(
        CompileRequest(
            source=(
                "namespace sales\n"
                "hub Customer {\n  business_key customer_id: int\n}\n"
                "satellite CustomerDetails of Customer {\n  email: string\n}\n"
            )
        )
    )

    assert result.ok is True
    assert result.summary
    assert result.entity_counts == {
        "hubs": 1,
        "links": 0,
        "satellites": 1,
        "nhsats": 0,
        "nhlinks": 0,
        "effsats": 0,
        "samlinks": 0,
        "bridges": 0,
        "pits": 0,
    }
    assert result.entities[0].qualified_name == "sales.Customer"
