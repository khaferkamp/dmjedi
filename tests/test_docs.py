"""Tests for the markdown documentation generator covering all entity types and Mermaid ER."""

from dmjedi.docs.markdown import generate_markdown
from dmjedi.model.core import (
    Bridge,
    Column,
    DataVaultModel,
    EffSat,
    Hub,
    Link,
    NhLink,
    NhSat,
    Pit,
    SamLink,
    Satellite,
)


def _full_model() -> DataVaultModel:
    """Return a DataVaultModel with at least one of every entity type."""
    return DataVaultModel(
        hubs={
            "sales.Customer": Hub(
                name="Customer",
                namespace="sales",
                business_keys=[Column(name="customer_id", data_type="int", is_business_key=True)],
            )
        },
        links={
            "sales.CustomerProduct": Link(
                name="CustomerProduct",
                namespace="sales",
                hub_references=["Customer", "Product"],
            )
        },
        satellites={
            "sales.CustomerDetails": Satellite(
                name="CustomerDetails",
                namespace="sales",
                parent_ref="Customer",
                columns=[Column(name="first_name", data_type="string")],
            )
        },
        nhsats={
            "sales.CurrentStatus": NhSat(
                name="CurrentStatus",
                namespace="sales",
                parent_ref="Customer",
                columns=[Column(name="status", data_type="string")],
            )
        },
        nhlinks={
            "sales.AB": NhLink(
                name="AB",
                namespace="sales",
                hub_references=["A", "B"],
                columns=[],
            )
        },
        effsats={
            "sales.CustProdValidity": EffSat(
                name="CustProdValidity",
                namespace="sales",
                parent_ref="CustomerProduct",
                columns=[Column(name="valid_from", data_type="timestamp")],
            )
        },
        samlinks={
            "sales.CustomerMatch": SamLink(
                name="CustomerMatch",
                namespace="sales",
                master_ref="Customer",
                duplicate_ref="Customer",
                columns=[Column(name="confidence", data_type="decimal")],
            )
        },
        bridges={
            "sales.CustProd": Bridge(
                name="CustProd",
                namespace="sales",
                path=["Customer", "CustomerProduct", "Product"],
            )
        },
        pits={
            "sales.CustPit": Pit(
                name="CustPit",
                namespace="sales",
                anchor_ref="Customer",
                tracked_satellites=["CustomerDetails"],
            )
        },
    )


def test_docs_raw_vault_grouping() -> None:
    """Output contains ## Raw Vault section header."""
    md = generate_markdown(_full_model())
    assert "## Raw Vault" in md


def test_docs_query_assist_grouping() -> None:
    """Output contains ## Query Assist section header."""
    md = generate_markdown(_full_model())
    assert "## Query Assist" in md


def test_docs_nhsat_section() -> None:
    """Output contains nhsat qualified name, parent ref, and columns."""
    md = generate_markdown(_full_model())
    assert "sales.CurrentStatus" in md
    assert "Customer" in md  # parent_ref
    assert "status" in md  # column name


def test_docs_nhlink_section() -> None:
    """Output contains nhlink qualified name and hub references."""
    md = generate_markdown(_full_model())
    assert "sales.AB" in md
    assert "`A`" in md
    assert "`B`" in md


def test_docs_effsat_section() -> None:
    """Output contains effsat qualified name, parent ref (link), and columns."""
    md = generate_markdown(_full_model())
    assert "sales.CustProdValidity" in md
    assert "CustomerProduct" in md  # parent_ref (link)
    assert "valid_from" in md  # column name


def test_docs_samlink_section() -> None:
    """Output contains samlink qualified name, master ref, and duplicate ref."""
    md = generate_markdown(_full_model())
    assert "sales.CustomerMatch" in md
    assert "Master" in md or "master" in md
    assert "Duplicate" in md or "duplicate" in md


def test_docs_bridge_section() -> None:
    """Output contains bridge qualified name and path chain."""
    md = generate_markdown(_full_model())
    assert "sales.CustProd" in md
    assert "Customer" in md
    assert "CustomerProduct" in md
    assert "Product" in md  # path chain per D-08


def test_docs_pit_section() -> None:
    """Output contains pit qualified name, anchor ref, and tracked satellites."""
    md = generate_markdown(_full_model())
    assert "sales.CustPit" in md
    assert "Customer" in md  # anchor_ref per D-08
    assert "CustomerDetails" in md  # tracked satellite


def test_docs_mermaid_diagram() -> None:
    """Output contains mermaid erDiagram before ## Raw Vault."""
    md = generate_markdown(_full_model())
    assert "```mermaid" in md
    assert "erDiagram" in md
    mermaid_pos = md.index("erDiagram")
    raw_vault_pos = md.index("## Raw Vault")
    assert mermaid_pos < raw_vault_pos  # diagram before sections per D-12


def test_docs_mermaid_hub_sat_relationship() -> None:
    """erDiagram contains hub-satellite relationship with ||--o{ notation."""
    md = generate_markdown(_full_model())
    assert "||--o{" in md  # per D-13: satellites use ||--o{


def test_docs_mermaid_bridge_dotted() -> None:
    """erDiagram contains bridge relationship with ||..o{ dotted notation."""
    md = generate_markdown(_full_model())
    assert "||..o{" in md  # per D-13: bridge/pit use dotted lines


def test_docs_empty_model() -> None:
    """Empty model produces no empty section headers."""
    md = generate_markdown(DataVaultModel())
    assert "## Raw Vault" not in md
    assert "## Query Assist" not in md
