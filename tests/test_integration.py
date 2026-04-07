"""End-to-end integration tests for the DMJEDI pipeline."""

from pathlib import Path

import pytest

from dmjedi.docs.markdown import generate_markdown
from dmjedi.generators import registry
from dmjedi.lang.imports import resolve_imports
from dmjedi.lang.linter import Severity, lint
from dmjedi.lang.parser import parse, parse_file
from dmjedi.model.core import Column, DataVaultModel, Hub, Link, Satellite
from dmjedi.model.resolver import ResolverErrors, resolve


def _sample_model() -> DataVaultModel:
    return DataVaultModel(
        hubs={
            "sales.Customer": Hub(
                name="Customer",
                namespace="sales",
                business_keys=[
                    Column(name="customer_id", data_type="int", is_business_key=True)
                ],
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
        links={
            "sales.CustomerProduct": Link(
                name="CustomerProduct",
                namespace="sales",
                hub_references=["Customer", "Product"],
            )
        },
    )


# ---------------------------------------------------------------------------
# E2E pipeline tests
# ---------------------------------------------------------------------------


def test_e2e_sql_pipeline():
    """Full pipeline: .dv file -> parse -> lint -> resolve -> SQL generation."""
    module = parse_file(Path("examples/sales-domain.dv"))

    diagnostics = lint(module)
    errors = [d for d in diagnostics if d.severity == Severity.ERROR]
    assert not errors, f"Unexpected lint errors: {errors}"

    model = resolve([module])

    gen = registry.get("sql-jinja")
    result = gen.generate(model)

    assert len(result.files) == 8, f"Expected 8 files, got {sorted(result.files.keys())}"

    for filename, sql in result.files.items():
        assert "CREATE TABLE" in sql, f"{filename} missing CREATE TABLE"
        stripped = sql.replace(" ", "").replace("\n", "")
        assert ",)" not in stripped, f"{filename} has trailing comma before )"


def test_e2e_spark_pipeline():
    """Full pipeline: .dv file -> parse -> resolve -> Spark DLT generation."""
    module = parse_file(Path("examples/sales-domain.dv"))
    model = resolve([module])

    gen = registry.get("spark-declarative")
    result = gen.generate(model)

    assert len(result.files) == 8, f"Expected 8 files, got {sorted(result.files.keys())}"

    for filename, code in result.files.items():
        assert "import dlt" in code, f"{filename} missing 'import dlt'"
        assert "@dlt.table" in code, f"{filename} missing '@dlt.table'"
        lines = [ln.strip() for ln in code.splitlines()]
        assert "pass" not in lines, f"{filename} contains 'pass' stub"
        assert not any("TODO" in ln for ln in lines), f"{filename} contains TODO"
        compile(code, filename, "exec")


def test_e2e_docs_pipeline():
    """Full pipeline: .dv file -> parse -> resolve -> markdown documentation."""
    module = parse_file(Path("examples/sales-domain.dv"))
    model = resolve([module])

    md = generate_markdown(model)

    assert "# Data Vault Model Documentation" in md
    for name in ("Customer", "Product", "Store", "Sale"):
        assert name in md, f"Entity '{name}' not found in docs output"


def test_e2e_multifile_resolve():
    """Multi-file pipeline: parse main.dv -> resolve imports -> resolve model."""
    module = parse_file(Path("tests/fixtures/imports/main.dv"))

    modules = resolve_imports([module])
    assert len(modules) >= 2, "Expected at least 2 modules after import resolution"

    model = resolve(modules)

    assert any("Customer" in k for k in model.hubs), "Hub from hub_defs.dv not resolved"
    assert any("CustomerDetails" in k for k in model.satellites), (
        "Satellite from main.dv not resolved"
    )


def test_e2e_validation_errors():
    """Error pipeline: parse bad DVML -> lint -> expect ERROR diagnostics."""
    module = parse("namespace t\nhub Bad {}")

    diagnostics = lint(module)

    error_diags = [d for d in diagnostics if d.severity == Severity.ERROR]
    assert error_diags, "Expected at least one ERROR diagnostic"
    assert any(d.rule == "hub-requires-business-key" for d in error_diags)


def test_e2e_resolver_errors():
    """Error pipeline: duplicate entities -> ResolverErrors raised."""
    mod1 = parse("namespace dup\nhub Same {\n  business_key id : int\n}", source_file="a.dv")
    mod2 = parse("namespace dup\nhub Same {\n  business_key id : int\n}", source_file="b.dv")

    with pytest.raises(ResolverErrors, match="Duplicate"):
        resolve([mod1, mod2])


def test_e2e_write_to_disk(tmp_path: Path):
    """Verify GeneratorResult.write() creates files on disk."""
    module = parse_file(Path("examples/sales-domain.dv"))
    model = resolve([module])

    gen = registry.get("sql-jinja")
    result = gen.generate(model)

    written = result.write(tmp_path)
    assert len(written) == len(result.files)

    for path in written:
        assert path.exists(), f"Written file does not exist: {path}"

    # Verify at least one file's content matches
    first_rel = next(iter(result.files))
    first_path = tmp_path / first_rel
    assert first_path.read_text() == result.files[first_rel]


# ---------------------------------------------------------------------------
# Snapshot tests
# ---------------------------------------------------------------------------


def test_sql_hub_snapshot(snapshot):
    """Snapshot test for hub SQL output."""
    model = _sample_model()
    gen = registry.get("sql-jinja")
    result = gen.generate(model)
    snapshot.assert_match(result.files["hubs/Customer.sql"], "hub_customer.sql")


def test_sql_link_snapshot(snapshot):
    """Snapshot test for link SQL output."""
    model = _sample_model()
    gen = registry.get("sql-jinja")
    result = gen.generate(model)
    snapshot.assert_match(result.files["links/CustomerProduct.sql"], "link_customerproduct.sql")


def test_spark_hub_snapshot(snapshot):
    """Snapshot test for hub Spark output."""
    model = _sample_model()
    gen = registry.get("spark-declarative")
    result = gen.generate(model)
    snapshot.assert_match(result.files["hubs/Customer.py"], "hub_customer.py")
