from __future__ import annotations

from pathlib import Path

import pytest

from dmjedi.generators.base import GeneratorResult


def test_mcp_tool_list_is_validate_generate_explain_only() -> None:
    from dmjedi.mcp.server import SERVER

    tool_names = sorted(tool.name for tool in SERVER._tool_manager.list_tools())

    assert tool_names == ["explain", "generate", "validate"]


def test_mcp_validate_accepts_source_and_path_inputs(tmp_path: Path) -> None:
    from dmjedi.mcp.tools import validate

    path = tmp_path / "sales.dv"
    path.write_text("namespace sales\nhub Customer {\n  business_key customer_id: int\n}\n")

    source_result = validate(
        source="namespace sales\nhub Product {\n  business_key product_id: int\n}\n",
        source_name="inline.dv",
    )
    path_result = validate(path=str(path))

    assert source_result["ok"] is True
    assert source_result["source_mode"] == "inline"
    assert source_result["module_count"] == 1
    assert path_result["ok"] is True
    assert path_result["source_mode"] == "paths"
    assert path_result["module_count"] == 1


def test_mcp_generate_returns_artifacts_without_disk_writes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from dmjedi.mcp.tools import generate

    def fail_write(self: GeneratorResult, output_dir: Path) -> list[Path]:
        msg = f"unexpected write to {output_dir}"
        raise AssertionError(msg)

    monkeypatch.setattr(GeneratorResult, "write", fail_write)

    model_path = tmp_path / "sales.dv"
    model_path.write_text(
        "namespace sales\n"
        "hub Customer {\n  business_key customer_id: int\n}\n"
        "satellite CustomerDetails of Customer {\n  email: string\n}\n"
    )

    result = generate(path=str(model_path), target="sql-jinja", dialect="postgres")

    assert result["ok"] is True
    assert result["source_mode"] == "paths"
    assert result["target"] == "sql-jinja"
    assert result["dialect"] == "postgres"
    assert result["artifacts"]
    assert all("path" in artifact and "content" in artifact for artifact in result["artifacts"])
    assert not (tmp_path / "output").exists()


def test_mcp_explain_returns_summary_and_entity_counts() -> None:
    from dmjedi.mcp.tools import explain

    result = explain(
        source=(
            "namespace sales\n"
            "hub Customer {\n  business_key customer_id: int\n}\n"
            "hub Product {\n  business_key product_id: int\n}\n"
            "link CustomerProduct {\n"
            "  refs Customer, Product\n"
            "}\n"
            "satellite CustomerDetails of Customer {\n  email: string\n}\n"
        ),
        source_name="inline.dv",
    )

    assert result["ok"] is True
    assert result["summary"]
    assert result["entity_counts"] == {
        "hubs": 2,
        "links": 1,
        "satellites": 1,
        "nhsats": 0,
        "nhlinks": 0,
        "effsats": 0,
        "samlinks": 0,
        "bridges": 0,
        "pits": 0,
    }
    assert result["entities"] == [
        {
            "qualified_name": "sales.Customer",
            "kind": "hub",
            "columns": ["customer_id"],
            "references": [],
        },
        {
            "qualified_name": "sales.Product",
            "kind": "hub",
            "columns": ["product_id"],
            "references": [],
        },
        {
            "qualified_name": "sales.CustomerDetails",
            "kind": "satellite",
            "columns": ["email"],
            "references": ["sales.Customer"],
        },
        {
            "qualified_name": "sales.CustomerProduct",
            "kind": "link",
            "columns": [],
            "references": ["sales.Customer", "sales.Product"],
        },
    ]
