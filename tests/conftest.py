"""Shared test fixtures."""

from pathlib import Path

import pytest

from dmjedi.generators import registry
from dmjedi.lang.parser import parse_file
from dmjedi.model.resolver import resolve
from tests.fixtures.all_entity_rows import ALL_ENTITY_SOURCE_ROWS

FIXTURES_DIR = Path(__file__).parent / "fixtures"
ALL_ENTITY_FIXTURE = FIXTURES_DIR / "all_entity_types.dv"
PHASE_03_DIALECTS = ("duckdb", "databricks")


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture(scope="module")
def all_entity_fixture_path() -> Path:
    return ALL_ENTITY_FIXTURE


@pytest.fixture(scope="module")
def all_entity_model(all_entity_fixture_path: Path):
    module = parse_file(all_entity_fixture_path)
    return resolve([module])


@pytest.fixture(scope="module")
def generated_results(all_entity_model):
    results = {}
    for dialect in PHASE_03_DIALECTS:
        generator = registry.get("sql-jinja", dialect=dialect)
        results[dialect] = generator.generate(all_entity_model)
    return results


@pytest.fixture(scope="module")
def duckdb_generated_result(generated_results):
    return generated_results["duckdb"]


@pytest.fixture(scope="module")
def databricks_generated_result(generated_results):
    return generated_results["databricks"]


@pytest.fixture(scope="module")
def all_entity_source_rows() -> dict[str, list[dict[str, object]]]:
    return ALL_ENTITY_SOURCE_ROWS
