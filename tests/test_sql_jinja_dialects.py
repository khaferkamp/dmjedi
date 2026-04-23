"""Dialect snapshot tests for SQL Jinja generator.

Validates DDL and staging view output for DuckDB, Databricks SQL, and PostgreSQL
across all 9 DV2.1 entity types. Per D-11 and D-12.
"""

from pathlib import Path

import pytest
from sqlglot import parse
from sqlglot.errors import ParseError

from dmjedi.generators import registry
from dmjedi.lang.parser import parse_file
from dmjedi.model.resolver import resolve

DIALECTS = ["duckdb", "databricks", "postgres"]

# Entity type -> DDL output file key
DDL_ENTITY_FILES = {
    "hub_Customer": "hubs/Customer.sql",
    "hub_Product": "hubs/Product.sql",
    "satellite_CustomerDetails": "satellites/CustomerDetails.sql",
    "link_CustomerProduct": "links/CustomerProduct.sql",
    "nhsat_CurrentStatus": "satellites/nhsat_CurrentStatus.sql",
    "nhlink_ActiveRelation": "links/nhlink_ActiveRelation.sql",
    "effsat_RelationValidity": "satellites/effsat_RelationValidity.sql",
    "samlink_CustomerMatch": "links/samlink_CustomerMatch.sql",
    "bridge_CustomerProductBridge": "views/bridge_CustomerProductBridge.sql",
    "pit_CustomerPit": "views/pit_CustomerPit.sql",
}

# Staging view output file keys (8 entities -- no bridge/PIT)
STAGING_ENTITY_FILES = {
    "staging_hub_Customer": "staging/hubs/Customer.sql",
    "staging_hub_Product": "staging/hubs/Product.sql",
    "staging_satellite_CustomerDetails": "staging/satellites/CustomerDetails.sql",
    "staging_link_CustomerProduct": "staging/links/CustomerProduct.sql",
    "staging_nhsat_CurrentStatus": "staging/satellites/nhsat_CurrentStatus.sql",
    "staging_nhlink_ActiveRelation": "staging/links/nhlink_ActiveRelation.sql",
    "staging_effsat_RelationValidity": "staging/satellites/effsat_RelationValidity.sql",
    "staging_samlink_CustomerMatch": "staging/links/samlink_CustomerMatch.sql",
}


def _assert_databricks_files_parse(files: dict[str, str]) -> None:
    for file_key, sql in sorted(files.items()):
        try:
            expressions = parse(sql, dialect="databricks")
        except ParseError as exc:
            pytest.fail(f"databricks parse failed for {file_key}: {exc}")

        assert expressions, f"databricks parse returned no expressions for {file_key}"


@pytest.fixture(scope="module")
def all_entity_model():
    """Parse and resolve the comprehensive all-entity-types fixture."""
    module = parse_file(Path("tests/fixtures/all_entity_types.dv"))
    return resolve([module])


@pytest.fixture(scope="module")
def generated_results(all_entity_model):
    """Generate SQL for all 3 dialects. Returns dict[dialect, GeneratorResult]."""
    results = {}
    for dialect in DIALECTS:
        gen = registry.get("sql-jinja", dialect=dialect)
        results[dialect] = gen.generate(all_entity_model)
    return results


# --- DDL snapshot tests: 10 entities x 3 dialects = 30 snapshot tests ---


@pytest.mark.parametrize("dialect", DIALECTS)
@pytest.mark.parametrize("entity,file_key", list(DDL_ENTITY_FILES.items()))
def test_ddl_dialect_snapshot(dialect, entity, file_key, generated_results, snapshot):
    """Snapshot test for DDL output per entity per dialect."""
    result = generated_results[dialect]
    assert file_key in result.files, f"Missing DDL file: {file_key} for {dialect}"
    snapshot.assert_match(
        result.files[file_key],
        f"ddl_{entity}_{dialect}.sql",
    )


# --- Staging view snapshot tests: 8 entities x 3 dialects = 24 snapshot tests ---


@pytest.mark.parametrize("dialect", DIALECTS)
@pytest.mark.parametrize("entity,file_key", list(STAGING_ENTITY_FILES.items()))
def test_staging_dialect_snapshot(dialect, entity, file_key, generated_results, snapshot):
    """Snapshot test for staging view output per entity per dialect."""
    result = generated_results[dialect]
    assert file_key in result.files, f"Missing staging file: {file_key} for {dialect}"
    snapshot.assert_match(
        result.files[file_key],
        f"{entity}_{dialect}.sql",
    )


# --- Structural validation tests ---


@pytest.mark.parametrize("dialect", DIALECTS)
def test_all_ddl_files_present(dialect, generated_results):
    """Every expected DDL file is present in generator output."""
    result = generated_results[dialect]
    for _entity, file_key in DDL_ENTITY_FILES.items():
        assert file_key in result.files, f"{dialect}: missing DDL {file_key}"


@pytest.mark.parametrize("dialect", DIALECTS)
def test_all_staging_files_present(dialect, generated_results):
    """Every expected staging file is present (no bridge/PIT staging)."""
    result = generated_results[dialect]
    for _entity, file_key in STAGING_ENTITY_FILES.items():
        assert file_key in result.files, f"{dialect}: missing staging {file_key}"
    # Verify NO bridge or PIT staging files exist
    staging_files = [k for k in result.files if k.startswith("staging/")]
    for sf in staging_files:
        assert "bridge" not in sf.lower(), f"{dialect}: unexpected bridge staging: {sf}"
        assert "pit" not in sf.lower(), f"{dialect}: unexpected PIT staging: {sf}"


@pytest.mark.parametrize("dialect", DIALECTS)
def test_ddl_identifiers_quoted(dialect, generated_results):
    """All DDL output uses double-quoted identifiers per D-09/D-10."""
    result = generated_results[dialect]
    hub_sql = result.files["hubs/Customer.sql"]
    assert '"Customer"' in hub_sql, f"{dialect}: table name not quoted"
    assert '"Customer_hk"' in hub_sql, f"{dialect}: hash key column not quoted"
    assert '"load_ts"' in hub_sql, f"{dialect}: load_ts not quoted"
    assert '"record_source"' in hub_sql, f"{dialect}: record_source not quoted"
    assert '"customer_id"' in hub_sql, f"{dialect}: business key not quoted"


@pytest.mark.parametrize("dialect", DIALECTS)
def test_ddl_uses_char64_for_hash_keys(dialect, generated_results):
    """All DDL output uses CHAR(64) for hash key columns per D-03."""
    result = generated_results[dialect]
    hub_sql = result.files["hubs/Customer.sql"]
    assert "CHAR(64)" in hub_sql, f"{dialect}: hash key not CHAR(64)"
    sat_sql = result.files["satellites/CustomerDetails.sql"]
    assert "CHAR(64)" in sat_sql, f"{dialect}: sat hash key not CHAR(64)"
    link_sql = result.files["links/CustomerProduct.sql"]
    assert "CHAR(64)" in link_sql, f"{dialect}: link hash key not CHAR(64)"


def test_databricks_ansi_header(generated_results):
    """Databricks dialect output includes ANSI mode requirement comment."""
    result = generated_results["databricks"]
    for file_key in DDL_ENTITY_FILES.values():
        sql = result.files[file_key]
        assert "ANSI_MODE=true" in sql, f"databricks {file_key}: missing ANSI note"


def test_non_databricks_no_ansi_header(generated_results):
    """Non-Databricks dialects do NOT include ANSI mode comment."""
    for dialect in ["duckdb", "postgres"]:
        result = generated_results[dialect]
        for file_key in DDL_ENTITY_FILES.values():
            sql = result.files[file_key]
            assert "ANSI_MODE" not in sql, f"{dialect} {file_key}: unexpected ANSI note"


# --- Hash function dialect verification ---


HASH_MARKERS = {
    "duckdb": "sha256(",
    "databricks": "sha2(",
    "postgres": "encode(sha256(",
}


@pytest.mark.parametrize("dialect", DIALECTS)
def test_staging_hub_uses_correct_hash_function(dialect, generated_results):
    """Staging hub view uses the dialect-specific hash function."""
    result = generated_results[dialect]
    stg_sql = result.files["staging/hubs/Customer.sql"]
    marker = HASH_MARKERS[dialect]
    assert marker in stg_sql, f"{dialect}: staging hub missing {marker}"


@pytest.mark.parametrize("dialect", DIALECTS)
def test_staging_uses_coalesce_and_delimiter(dialect, generated_results):
    """Staging views use COALESCE for NULL handling and || delimiter per D-04/D-07."""
    result = generated_results[dialect]
    # Product hub has 2 business keys -> should have delimiter
    stg_sql = result.files["staging/hubs/Product.sql"]
    assert "COALESCE(" in stg_sql, f"{dialect}: missing COALESCE"
    assert "|| '||' ||" in stg_sql, f"{dialect}: missing double-pipe delimiter"


def test_databricks_sqlglot_parses_every_generated_file(generated_results):
    """Every generated Databricks SQL file should parse under SQLGlot."""
    _assert_databricks_files_parse(generated_results["databricks"].files)
