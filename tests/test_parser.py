"""Tests for the DVML parser."""

import pytest
from pathlib import Path

from dmjedi.lang.parser import parse, parse_file, _get_parser, DVMLParseError, ParseError


def test_parse_hub():
    source = """
    hub Customer {
        business_key customer_id : int
    }
    """
    module = parse(source)
    assert len(module.hubs) == 1
    hub = module.hubs[0]
    assert hub.name == "Customer"
    assert len(hub.business_keys) == 1
    assert hub.business_keys[0].name == "customer_id"
    assert hub.business_keys[0].data_type == "int"


def test_parse_satellite():
    source = """
    hub Customer {
        business_key customer_id : int
    }

    satellite CustomerDetails of Customer {
        first_name : string
        last_name  : string
    }
    """
    module = parse(source)
    assert len(module.satellites) == 1
    sat = module.satellites[0]
    assert sat.name == "CustomerDetails"
    assert sat.parent_ref == "Customer"
    assert len(sat.fields) == 2


def test_parse_link():
    source = """
    hub Customer {
        business_key customer_id : int
    }

    hub Product {
        business_key product_id : int
    }

    link CustomerProduct {
        references Customer, Product
    }
    """
    module = parse(source)
    assert len(module.links) == 1
    link = module.links[0]
    assert link.name == "CustomerProduct"
    assert link.references == ["Customer", "Product"]


def test_parse_namespace():
    source = """
    namespace sales

    hub Customer {
        business_key customer_id : int
    }
    """
    module = parse(source)
    assert module.namespace == "sales"


def test_parse_fixture_file(fixtures_dir: Path):
    module = parse_file(fixtures_dir / "sales.dv")
    assert module.namespace == "sales"
    assert len(module.hubs) == 2
    assert len(module.satellites) == 2
    assert len(module.links) == 1


# --- Task 1: Parser caching and new data types ---


def test_parser_caching():
    """PARSE-01: _get_parser() must return the same singleton object on repeated calls."""
    p1 = _get_parser()
    p2 = _get_parser()
    assert p1 is p2, "Parser should be a cached singleton"


def test_parse_bigint():
    """TYPE-01: bigint type parses without error."""
    source = "hub H { business_key k : bigint }"
    module = parse(source)
    assert module.hubs[0].business_keys[0].data_type == "bigint"


def test_parse_float():
    """TYPE-01: float type parses without error."""
    source = "hub H { business_key k : float }"
    module = parse(source)
    assert module.hubs[0].business_keys[0].data_type == "float"


def test_parse_varchar():
    """TYPE-01: varchar type parses without error."""
    source = "hub H { business_key k : varchar }"
    module = parse(source)
    assert module.hubs[0].business_keys[0].data_type == "varchar"


def test_parse_binary():
    """TYPE-01: binary type parses without error."""
    source = "hub H { business_key k : binary }"
    module = parse(source)
    assert module.hubs[0].business_keys[0].data_type == "binary"


def test_parse_parameterized_type():
    """D-01/D-02: varchar(100) parses as string pass-through."""
    source = "hub H { business_key k : varchar(100) }"
    module = parse(source)
    assert module.hubs[0].business_keys[0].data_type == "varchar(100)"


def test_parse_parameterized_decimal():
    """D-01/D-03: decimal(10,4) parses as string pass-through."""
    source = "hub H { business_key k : decimal(10,4) }"
    module = parse(source)
    assert module.hubs[0].business_keys[0].data_type == "decimal(10,4)"


def test_parse_unknown_type_rejected():
    """D-08: unknown types must be rejected at parse time."""
    source = "hub H { business_key k : unknowntype }"
    with pytest.raises(Exception):
        parse(source)


# --- Task 2: Structured parse errors ---


def test_parse_error_unterminated_block():
    """Parse error on unterminated block contains structured info."""
    with pytest.raises(DVMLParseError) as exc_info:
        parse("hub Foo {", source_file="test.dv")
    err = exc_info.value.error
    assert err.line >= 0
    assert err.hint


def test_parse_error_has_file_info():
    """ParseError carries the source_file name."""
    with pytest.raises(DVMLParseError) as exc_info:
        parse("hub Foo {", source_file="test.dv")
    err = exc_info.value.error
    assert err.file == "test.dv"


def test_parse_error_format():
    """str(DVMLParseError) matches file:line:col: hint format."""
    with pytest.raises(DVMLParseError) as exc_info:
        parse("hub Foo {", source_file="test.dv")
    msg = str(exc_info.value)
    assert "test.dv" in msg
    assert ":" in msg


def test_parse_error_dataclass_fields():
    """ParseError dataclass has all expected fields."""
    pe = ParseError(file="x.dv", line=1, column=5, hint="test hint")
    assert pe.file == "x.dv"
    assert pe.line == 1
    assert pe.column == 5
    assert pe.hint == "test hint"
    assert hasattr(pe, "source_line")


# --- Task 1: nhsat, nhlink, effsat ---


def test_parse_nhsat():
    """NhSatDecl: nhsat with of ref and fields parses into module.nhsats."""
    source = "nhsat CurrentState of Customer { active : boolean }"
    module = parse(source)
    assert len(module.nhsats) == 1
    nhsat = module.nhsats[0]
    assert nhsat.name == "CurrentState"
    assert nhsat.parent_ref == "Customer"
    assert len(nhsat.fields) == 1
    assert nhsat.fields[0].name == "active"
    assert nhsat.fields[0].data_type == "boolean"


def test_parse_nhsat_empty_body():
    """NhSatDecl: nhsat with empty body parses with 0 fields."""
    source = "nhsat Empty of Hub {}"
    module = parse(source)
    assert len(module.nhsats) == 1
    assert module.nhsats[0].name == "Empty"
    assert module.nhsats[0].parent_ref == "Hub"
    assert len(module.nhsats[0].fields) == 0


def test_parse_nhlink():
    """NhLinkDecl: nhlink with references parses into module.nhlinks."""
    source = "nhlink LatestOrder { references Customer, Product }"
    module = parse(source)
    assert len(module.nhlinks) == 1
    nhlink = module.nhlinks[0]
    assert nhlink.name == "LatestOrder"
    assert nhlink.references == ["Customer", "Product"]


def test_parse_nhlink_three_refs():
    """NhLinkDecl: nhlink with 3 references parses all 3."""
    source = "nhlink BigLink { references A, B, C }"
    module = parse(source)
    assert len(module.nhlinks) == 1
    assert module.nhlinks[0].references == ["A", "B", "C"]


def test_parse_effsat():
    """EffSatDecl: effsat with of ref and temporal fields parses correctly."""
    source = "effsat LinkValidity of CustomerProduct { valid_from : timestamp  valid_to : timestamp }"
    module = parse(source)
    assert len(module.effsats) == 1
    effsat = module.effsats[0]
    assert effsat.name == "LinkValidity"
    assert effsat.parent_ref == "CustomerProduct"
    assert len(effsat.fields) == 2
    assert effsat.fields[0].name == "valid_from"
    assert effsat.fields[1].name == "valid_to"
