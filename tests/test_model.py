"""Tests for the Data Vault domain model and resolver."""

import pytest
from pydantic import ValidationError

from dmjedi.lang.parser import parse
from dmjedi.model.core import Link
from dmjedi.model.resolver import ResolverErrors, resolve


def test_link_requires_two_refs():
    with pytest.raises(ValidationError, match="at least 2 hubs"):
        Link(name="bad_link", hub_references=["OnlyOne"])


def test_resolve_single_module():
    source = """
    namespace sales

    hub Customer {
        business_key customer_id : int
    }

    hub Product {
        business_key product_id : int
    }

    satellite CustomerDetails of Customer {
        first_name : string
    }

    link CustomerProduct {
        references Customer, Product
    }
    """
    module = parse(source)
    model = resolve([module])

    assert "sales.Customer" in model.hubs
    assert "sales.Product" in model.hubs
    assert "sales.CustomerDetails" in model.satellites
    assert "sales.CustomerProduct" in model.links

    hub = model.hubs["sales.Customer"]
    assert hub.business_keys[0].name == "customer_id"
    assert hub.business_keys[0].is_business_key is True


def test_resolve_multiple_modules():
    mod1 = parse("namespace crm\nhub Customer { business_key cid : int }")
    mod2 = parse("namespace sales\nhub Product { business_key pid : int }")
    model = resolve([mod1, mod2])

    assert "crm.Customer" in model.hubs
    assert "sales.Product" in model.hubs


def test_duplicate_hub_raises():
    """Duplicate hub qualified name raises ResolverErrors."""
    mod1 = parse("namespace sales\nhub Customer { business_key cid : int }")
    mod2 = parse("namespace sales\nhub Customer { business_key cid : int }")
    with pytest.raises(ResolverErrors, match="Duplicate hub"):
        resolve([mod1, mod2])


def test_duplicate_satellite_raises():
    """Duplicate satellite qualified name raises ResolverErrors."""
    src = "namespace s\nhub H { business_key id : int }\nsatellite S of H { x : string }"
    mod1 = parse(src)
    mod2 = parse(src)
    with pytest.raises(ResolverErrors, match="Duplicate"):
        resolve([mod1, mod2])


def test_invalid_parent_ref_raises():
    """Satellite referencing non-existent parent raises ResolverErrors."""
    mod = parse("namespace test\nsatellite Bad of NonExistent { x : string }")
    with pytest.raises(ResolverErrors, match="unknown parent"):
        resolve([mod])


def test_valid_parent_ref_passes():
    """Satellite referencing existing hub resolves without error."""
    mod = parse(
        "namespace test\nhub Customer { business_key id : int }"
        "\nsatellite Details of Customer { name : string }"
    )
    model = resolve([mod])
    assert "test.Details" in model.satellites
