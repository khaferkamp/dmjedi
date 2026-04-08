"""Tests for the Data Vault domain model and resolver."""

import pytest
from pydantic import ValidationError

from dmjedi.lang.parser import parse
from dmjedi.model.core import EffSat, Link, NhLink, NhSat, SamLink
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


# --- NhSat / NhLink domain model tests ---


def test_nhlink_requires_two_refs():
    """NhLink with fewer than 2 hub_references raises ValidationError."""
    with pytest.raises(ValidationError, match="at least 2 hubs"):
        NhLink(name="bad_nhlink", hub_references=["OnlyOne"])


def test_nhsat_qualified_name():
    """NhSat qualified_name returns 'ns.Name' when namespace is set."""
    nhsat = NhSat(name="Status", namespace="sales", parent_ref="Customer")
    assert nhsat.qualified_name == "sales.Status"


def test_nhlink_qualified_name():
    """NhLink qualified_name returns 'ns.Name' when namespace is set."""
    nhlink = NhLink(name="AB", namespace="ns", hub_references=["A", "B"])
    assert nhlink.qualified_name == "ns.AB"


def test_data_vault_model_has_nhsats_nhlinks():
    """DataVaultModel can be constructed with nhsats and nhlinks dicts."""
    from dmjedi.model.core import DataVaultModel

    nhsat = NhSat(name="S", namespace="n", parent_ref="H")
    nhlink = NhLink(name="L", namespace="n", hub_references=["A", "B"])
    model = DataVaultModel(
        nhsats={"n.S": nhsat},
        nhlinks={"n.L": nhlink},
    )
    assert "n.S" in model.nhsats
    assert "n.L" in model.nhlinks


# --- Resolver tests for nhsat / nhlink ---


def test_resolve_nhsat():
    """Parsed nhsat declaration appears in model.nhsats with correct fields."""
    src = (
        "namespace test\n"
        "hub Customer { business_key id : int }\n"
        "nhsat CurrentStatus of Customer { status : string }"
    )
    module = parse(src)
    model = resolve([module])
    assert "test.CurrentStatus" in model.nhsats
    nhsat = model.nhsats["test.CurrentStatus"]
    assert nhsat.parent_ref == "Customer"
    assert nhsat.columns[0].name == "status"


def test_resolve_nhlink():
    """Parsed nhlink declaration appears in model.nhlinks with correct fields."""
    src = (
        "namespace test\n"
        "hub A { business_key id : int }\n"
        "hub B { business_key id : int }\n"
        "nhlink AB { references A, B }"
    )
    module = parse(src)
    model = resolve([module])
    assert "test.AB" in model.nhlinks
    assert len(model.nhlinks["test.AB"].hub_references) == 2


def test_nhsat_invalid_parent_raises():
    """NhSat with parent_ref pointing to non-existent entity raises ResolverErrors."""
    src = "namespace test\nnhsat Bad of NonExistent { x : string }"
    module = parse(src)
    with pytest.raises(ResolverErrors, match="unknown parent"):
        resolve([module])


def test_nhsat_parent_ref_to_link_valid():
    """NhSat with parent_ref pointing to a link resolves without error."""
    src = (
        "namespace test\n"
        "hub A { business_key id : int }\n"
        "hub B { business_key id : int }\n"
        "link AB { references A, B }\n"
        "nhsat LinkStatus of AB { active : boolean }"
    )
    module = parse(src)
    model = resolve([module])
    assert "test.LinkStatus" in model.nhsats


def test_duplicate_nhsat_raises():
    """Duplicate nhsat qualified name raises ResolverErrors."""
    src = (
        "namespace test\n"
        "hub Customer { business_key id : int }\n"
        "nhsat CurrentStatus of Customer { status : string }"
    )
    mod1 = parse(src)
    mod2 = parse(src)
    with pytest.raises(ResolverErrors, match="Duplicate nhsat"):
        resolve([mod1, mod2])


def test_duplicate_nhlink_raises():
    """Duplicate nhlink qualified name raises ResolverErrors."""
    src = (
        "namespace test\n"
        "hub A { business_key id : int }\n"
        "hub B { business_key id : int }\n"
        "nhlink AB { references A, B }"
    )
    mod1 = parse(src)
    mod2 = parse(src)
    with pytest.raises(ResolverErrors, match="Duplicate nhlink"):
        resolve([mod1, mod2])


# --- EffSat / SamLink domain model tests ---


def test_effsat_qualified_name():
    """EffSat qualified_name returns 'ns.Name' when namespace is set."""
    effsat = EffSat(name="Validity", namespace="sales", parent_ref="CO")
    assert effsat.qualified_name == "sales.Validity"


def test_samlink_qualified_name():
    """SamLink qualified_name returns 'ns.Name' when namespace is set."""
    samlink = SamLink(name="CustMatch", namespace="crm", master_ref="Customer", duplicate_ref="Customer")
    assert samlink.qualified_name == "crm.CustMatch"


def test_samlink_has_separate_refs():
    """SamLink stores master_ref and duplicate_ref as separate fields."""
    samlink = SamLink(name="M", namespace="ns", master_ref="A", duplicate_ref="B")
    assert samlink.master_ref == "A"
    assert samlink.duplicate_ref == "B"


def test_data_vault_model_has_effsats_samlinks():
    """DataVaultModel can be constructed with effsats and samlinks dicts."""
    from dmjedi.model.core import DataVaultModel

    effsat = EffSat(name="E", namespace="n", parent_ref="L")
    samlink = SamLink(name="S", namespace="n", master_ref="H", duplicate_ref="H")
    model = DataVaultModel(
        effsats={"n.E": effsat},
        samlinks={"n.S": samlink},
    )
    assert "n.E" in model.effsats
    assert "n.S" in model.samlinks


# --- Resolver tests for effsat / samlink ---


def test_resolve_effsat():
    """Parsed effsat declaration resolves into model.effsats with correct fields."""
    src = (
        "namespace test\n"
        "hub Customer { business_key id : int }\n"
        "hub Product { business_key id : int }\n"
        "link CustomerOrder { references Customer, Product }\n"
        "effsat OrderValidity of CustomerOrder {\n"
        "    start_date : timestamp\n"
        "    end_date : timestamp\n"
        "}"
    )
    module = parse(src)
    model = resolve([module])
    assert "test.OrderValidity" in model.effsats
    effsat = model.effsats["test.OrderValidity"]
    assert effsat.parent_ref == "CustomerOrder"
    assert len(effsat.columns) == 2
    assert effsat.columns[0].name == "start_date"
    assert effsat.columns[1].name == "end_date"


def test_resolve_samlink():
    """Parsed samlink declaration resolves into model.samlinks with correct fields."""
    src = (
        "namespace test\n"
        "hub Customer { business_key id : int }\n"
        "samlink CustomerMatch {\n"
        "    master Customer\n"
        "    duplicate Customer\n"
        "    confidence_score : decimal\n"
        "}"
    )
    module = parse(src)
    model = resolve([module])
    assert "test.CustomerMatch" in model.samlinks
    samlink = model.samlinks["test.CustomerMatch"]
    assert samlink.master_ref == "Customer"
    assert samlink.duplicate_ref == "Customer"


def test_duplicate_effsat_raises():
    """Duplicate effsat qualified name raises ResolverErrors."""
    src = (
        "namespace test\n"
        "hub Customer { business_key id : int }\n"
        "hub Product { business_key id : int }\n"
        "link CustomerOrder { references Customer, Product }\n"
        "effsat OrderValidity of CustomerOrder { start_date : timestamp }"
    )
    mod1 = parse(src)
    mod2 = parse(src)
    with pytest.raises(ResolverErrors, match="Duplicate effsat"):
        resolve([mod1, mod2])


def test_duplicate_samlink_raises():
    """Duplicate samlink qualified name raises ResolverErrors."""
    src = (
        "namespace test\n"
        "hub Customer { business_key id : int }\n"
        "samlink CustomerMatch {\n"
        "    master Customer\n"
        "    duplicate Customer\n"
        "}"
    )
    mod1 = parse(src)
    mod2 = parse(src)
    with pytest.raises(ResolverErrors, match="Duplicate samlink"):
        resolve([mod1, mod2])


def test_effsat_invalid_parent_raises():
    """EffSat referencing unknown parent raises ResolverErrors."""
    src = (
        "namespace test\n"
        "effsat BadValidity of NonExistent { start_date : timestamp }"
    )
    module = parse(src)
    with pytest.raises(ResolverErrors, match="unknown parent"):
        resolve([module])


def test_effsat_parent_ref_to_hub_resolves():
    """EffSat of a hub (not link) resolves without error — type check is linter's job."""
    src = (
        "namespace test\n"
        "hub Customer { business_key id : int }\n"
        "effsat CustomerValidity of Customer { active : boolean }"
    )
    module = parse(src)
    model = resolve([module])
    assert "test.CustomerValidity" in model.effsats


def test_samlink_empty_ref_raises():
    """SamLink with empty master_ref raises ResolverErrors."""
    from dmjedi.lang.ast import SamLinkDecl, DVMLModule

    decl = SamLinkDecl(name="BadSamLink", master_ref="", duplicate_ref="Customer")
    module = DVMLModule(namespace="test", samlinks=[decl])
    with pytest.raises(ResolverErrors, match="missing master"):
        resolve([module])
