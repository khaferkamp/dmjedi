"""Tests for the DVML linter."""

from pathlib import Path

import pytest

from dmjedi.lang.ast import (
    BusinessKeyDef,
    DVMLModule,
    EffSatDecl,
    FieldDef,
    HubDecl,
    LinkDecl,
    NhLinkDecl,
    NhSatDecl,
    SamLinkDecl,
    SatelliteDecl,
)
from dmjedi.lang.linter import Severity, lint
from dmjedi.model.core import Column, DataVaultModel, Hub, Link


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
    module = DVMLModule(
        namespace="test",
        hubs=[HubDecl(name="Test", business_keys=[BusinessKeyDef(name="id", data_type="int")])],
    )
    diags = lint(module)
    ns_diags = [d for d in diags if d.rule == "missing-namespace"]
    assert len(ns_diags) == 0


# ---------------------------------------------------------------------------
# LINT-01: effsat parent must be link
# ---------------------------------------------------------------------------


def test_effsat_parent_not_link():
    """EffSat with a hub parent should produce a warning (LINT-01)."""
    module = DVMLModule(
        namespace="test",
        effsats=[EffSatDecl(name="V", parent_ref="Customer")],
    )
    model = DataVaultModel(
        hubs={
            "test.Customer": Hub(
                name="Customer",
                namespace="test",
                business_keys=[Column(name="id", data_type="int", is_business_key=True)],
            )
        }
    )
    diags = [d for d in lint(module, model=model) if d.rule == "effsat-parent-must-be-link"]
    assert len(diags) == 1
    assert diags[0].severity == Severity.WARNING


def test_effsat_parent_is_link_no_warning():
    """EffSat with a link parent should produce no LINT-01 warning."""
    module = DVMLModule(
        namespace="test",
        effsats=[EffSatDecl(name="V", parent_ref="CO")],
    )
    model = DataVaultModel(
        links={
            "test.CO": Link(name="CO", namespace="test", hub_references=["A", "B"])
        }
    )
    diags = [d for d in lint(module, model=model) if d.rule == "effsat-parent-must-be-link"]
    assert len(diags) == 0


def test_effsat_no_model_skips():
    """lint() called without model silently skips LINT-01 (backward compat)."""
    module = DVMLModule(
        namespace="test",
        effsats=[EffSatDecl(name="V", parent_ref="Customer")],
    )
    diags = [d for d in lint(module) if d.rule == "effsat-parent-must-be-link"]
    assert len(diags) == 0


# ---------------------------------------------------------------------------
# LINT-02: samlink same-hub check
# ---------------------------------------------------------------------------


def test_samlink_different_hubs():
    """SamLink with different master/duplicate refs should warn (LINT-02)."""
    module = DVMLModule(
        namespace="test",
        samlinks=[SamLinkDecl(name="M", master_ref="A", duplicate_ref="B")],
    )
    diags = [d for d in lint(module) if d.rule == "samlink-same-hub"]
    assert len(diags) == 1
    assert diags[0].severity == Severity.WARNING


def test_samlink_same_hub_no_warning():
    """SamLink with identical master/duplicate refs produces no LINT-02 warning."""
    module = DVMLModule(
        namespace="test",
        samlinks=[SamLinkDecl(name="M", master_ref="Customer", duplicate_ref="Customer")],
    )
    diags = [d for d in lint(module) if d.rule == "samlink-same-hub"]
    assert len(diags) == 0


def test_existing_rules_still_work():
    """Existing lint rules work unchanged when called without model param."""
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


# ---------------------------------------------------------------------------
# LINT-03: naming convention
# ---------------------------------------------------------------------------


def test_naming_missing_prefix(tmp_path: Path) -> None:
    """Hub without required prefix should produce a naming-convention warning."""
    toml_file = tmp_path / ".dvml-lint.toml"
    toml_file.write_text('[naming]\nhub = "hub_"\n')
    module = DVMLModule(
        namespace="test",
        hubs=[HubDecl(name="Customer", business_keys=[BusinessKeyDef(name="id", data_type="int")])],
    )
    diags = [d for d in lint(module, config_path=toml_file) if d.rule == "naming-convention"]
    assert len(diags) == 1
    assert "does not start with required prefix 'hub_'" in diags[0].message


def test_naming_correct_prefix(tmp_path: Path) -> None:
    """Hub with correct prefix should produce no naming-convention warning."""
    toml_file = tmp_path / ".dvml-lint.toml"
    toml_file.write_text('[naming]\nhub = "hub_"\n')
    module = DVMLModule(
        namespace="test",
        hubs=[HubDecl(name="hub_Customer", business_keys=[BusinessKeyDef(name="id", data_type="int")])],
    )
    diags = [d for d in lint(module, config_path=toml_file) if d.rule == "naming-convention"]
    assert len(diags) == 0


def test_naming_no_config_file() -> None:
    """Absent config file produces no naming-convention warnings."""
    module = DVMLModule(
        namespace="test",
        hubs=[HubDecl(name="Customer", business_keys=[BusinessKeyDef(name="id", data_type="int")])],
    )
    diags = [
        d
        for d in lint(module, config_path=Path("/nonexistent/.dvml-lint.toml"))
        if d.rule == "naming-convention"
    ]
    assert len(diags) == 0


def test_naming_all_seven_types(tmp_path: Path) -> None:
    """Naming check applies to all 7 entity types, producing one warning each."""
    toml_file = tmp_path / ".dvml-lint.toml"
    toml_file.write_text(
        "[naming]\n"
        'hub = "h_"\n'
        'sat = "s_"\n'
        'link = "l_"\n'
        'nhsat = "ns_"\n'
        'nhlink = "nl_"\n'
        'effsat = "es_"\n'
        'samlink = "sl_"\n'
    )
    bk = BusinessKeyDef(name="id", data_type="int")
    fd = FieldDef(name="x", data_type="string")
    module = DVMLModule(
        namespace="test",
        hubs=[HubDecl(name="X", business_keys=[bk])],
        satellites=[SatelliteDecl(name="X", parent_ref="H", fields=[fd])],
        links=[LinkDecl(name="X", references=["A", "B"])],
        nhsats=[NhSatDecl(name="X", parent_ref="H")],
        nhlinks=[NhLinkDecl(name="X", references=["A", "B"])],
        effsats=[EffSatDecl(name="X", parent_ref="L")],
        samlinks=[SamLinkDecl(name="X", master_ref="H", duplicate_ref="H")],
    )
    diags = [d for d in lint(module, config_path=toml_file) if d.rule == "naming-convention"]
    assert len(diags) == 7
