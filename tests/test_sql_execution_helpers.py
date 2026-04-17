"""Tests for shared SQL execution helpers and canonical fixture data."""

EXPECTED_SOURCE_TABLES = {
    "src_Customer",
    "src_Product",
    "src_CustomerDetails",
    "src_CustomerProduct",
    "src_CurrentStatus",
    "src_ActiveRelation",
    "src_RelationValidity",
    "src_CustomerMatch",
}


def test_canonical_source_rows_cover_expected_tables(
    all_entity_source_rows: dict[str, list[dict[str, object]]],
) -> None:
    """Canonical source data should cover every generated staging input table."""
    assert set(all_entity_source_rows) == EXPECTED_SOURCE_TABLES
