"""Tests for the DVML parser."""

from pathlib import Path

from dmjedi.lang.parser import parse, parse_file


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
