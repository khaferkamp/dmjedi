"""Tests for the DVML linter."""

from dmjedi.lang.ast import DVMLModule, HubDecl, LinkDecl, SatelliteDecl
from dmjedi.lang.linter import Severity, lint


def test_hub_without_business_key():
    module = DVMLModule(hubs=[HubDecl(name="BadHub")])
    diags = [d for d in lint(module) if d.rule == "hub-requires-business-key"]
    assert len(diags) == 1
    assert diags[0].severity == Severity.ERROR
    assert "no business keys" in diags[0].message


def test_link_with_one_ref():
    module = DVMLModule(links=[LinkDecl(name="BadLink", references=["OnlyOne"])])
    diags = [d for d in lint(module) if d.rule == "link-requires-two-refs"]
    assert len(diags) == 1
    assert diags[0].rule == "link-requires-two-refs"


def test_satellite_without_fields():
    module = DVMLModule(
        satellites=[SatelliteDecl(name="EmptySat", parent_ref="SomeHub")]
    )
    diags = [d for d in lint(module) if d.rule == "satellite-requires-fields"]
    assert len(diags) == 1
    assert diags[0].severity == Severity.WARNING


def test_valid_module_no_diagnostics():
    from dmjedi.lang.ast import BusinessKeyDef, FieldDef

    module = DVMLModule(
        namespace="test",
        hubs=[HubDecl(name="Good", business_keys=[BusinessKeyDef(name="id", data_type="int")])],
        satellites=[
            SatelliteDecl(
                name="GoodSat",
                parent_ref="Good",
                fields=[FieldDef(name="x", data_type="string")],
            )
        ],
        links=[LinkDecl(name="GoodLink", references=["A", "B"])],
    )
    assert lint(module) == []


def test_missing_namespace_warning():
    """Module with no namespace produces a warning."""
    from dmjedi.lang.ast import BusinessKeyDef

    module = DVMLModule(
        hubs=[HubDecl(name="Test", business_keys=[BusinessKeyDef(name="id", data_type="int")])]
    )
    diags = lint(module)
    ns_diags = [d for d in diags if d.rule == "missing-namespace"]
    assert len(ns_diags) == 1
    assert ns_diags[0].severity == Severity.WARNING
    assert "No namespace" in ns_diags[0].message


def test_namespace_present_no_warning():
    """Module with namespace produces no namespace warning."""
    from dmjedi.lang.ast import BusinessKeyDef

    module = DVMLModule(
        namespace="test",
        hubs=[HubDecl(name="Test", business_keys=[BusinessKeyDef(name="id", data_type="int")])],
    )
    diags = lint(module)
    ns_diags = [d for d in diags if d.rule == "missing-namespace"]
    assert len(ns_diags) == 0
