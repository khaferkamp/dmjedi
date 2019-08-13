"""Simple test class for testing data vault modelling.

This test suite checks the basic data vault modelling features of correctness.
It targets the most basic modelling rules so it is guaranteed that the model is valid.
"""
import pytest
from dmjedi.model.datavault import (
    HubEntity,
    SatelliteEntity,
    LinkEntity,
    AbstractSatAttachable,
)
from dmjedi.exceptions import InvalidAttachedEntity, InvalidLinkedEntity
from dmjedi.model.columns import IntColumn, TextColumn


def _prepare_inavlid_hub() -> HubEntity:
    """
    Returns an invalid instance of`HubEntity`.
    The instance is lacking a business key and is therefore not valid.
    """
    return HubEntity(name="invalidhub1_h", display_name="Invalid Hub1 hub")


def _prepare_valid_hub() -> HubEntity:
    """
    Returns a valid instance of `HubEntity` with two business keys.
    """
    h = HubEntity(name="hub2_h", display_name="Hub2 hub")
    h.add_field(IntColumn(name="bk1", display_name="Business Key 1"))
    h.add_field(IntColumn(name="bk2", display_name="Business Key 2"))
    return h


def _prepare_invalid_satellite(
    sat_entity: AbstractSatAttachable = None
) -> SatelliteEntity:
    """
    Returns an invalid instance of `SatelliteEntity`.
    The instance does not contain any fields and thefefore is not valid.
    """
    return SatelliteEntity(
        name="invalidsat1_s", display_name="Invalid Satellite", entity=sat_entity
    )


def _prepare_valid_satellite(
    sat_entity: AbstractSatAttachable = None
) -> SatelliteEntity:
    """
    Return a valid instance of `SatelliteEntity` which contains one text attribute.
    """
    s = SatelliteEntity(
        name="sat2_s", display_name="Valid Satellite", entity=sat_entity
    )
    s.add_field(TextColumn(name="text1", display_name="Text 1", default_value="N/A"))
    return s


def _prepare_link(hub1: HubEntity = None, hub2: HubEntity = None) -> LinkEntity:
    """
    Returns an invalid instance of `LinkEntity`.
    The instance has no references to any hubs defined, therefore it is not valid until it receives at least two instances of `HubEntity`.

    TODO:
      * maybe refactor into two methods for clearer responsibilities
    """

    if hub1 is not None and hub2 is not None:
        """ Valid case (!) """
        lnk = LinkEntity(name="link1_l", display_name="Link 1")
        lnk.add_hub(hub1)

        if hub1.name == hub2.name:
            lnk.add_hub_clone(hub2)
        else:
            lnk.add_hub(hub2)
        return lnk
    elif hub1 is None and hub2 is None:
        return LinkEntity(name="invalidlink1_l", display_name="Link 1")
    else:
        lnk = LinkEntity(name="invalidlink2_l", display_name="Link 1")
        lnk.add_hub(hub1)
        lnk.add_hub(hub2)


def test_invalid_hub() -> None:
    assert not _prepare_inavlid_hub().is_valid()


def test_valid_hub() -> None:
    assert _prepare_valid_hub().is_valid()


def test_invaid_satellite_with_exception() -> None:
    with pytest.raises(InvalidAttachedEntity):
        SatelliteEntity(name="sat1_s", display_name="Invalid Satellite", entity=None)


def test_invalid_satellite() -> None:
    s = _prepare_invalid_satellite(_prepare_valid_hub())
    assert not s.is_valid()


def test_valid_satellite() -> None:
    s = _prepare_valid_satellite(_prepare_valid_hub())
    assert s.is_valid()


def test_invalid_link() -> None:
    assert not _prepare_link().is_valid()


def test_invalid_link_entities() -> None:
    with pytest.raises(InvalidLinkedEntity):
        _prepare_link(_prepare_valid_hub(), None)
        _prepare_link(None, _prepare_valid_hub())
