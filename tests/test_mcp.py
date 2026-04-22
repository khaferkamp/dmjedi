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
            source='namespace sales\nimport "./shared.dv"\nhub Customer {\n  business_key id: int\n}\n',
        )
    )

    assert result.ok is False
    assert [diag.code for diag in result.diagnostics] == ["inline-source-imports-unsupported"]
