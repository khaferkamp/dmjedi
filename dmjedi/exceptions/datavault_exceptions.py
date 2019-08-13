# -*- coding: utf-8 -*-
"""Module for data vault specific modeling exceptions.

This module defines several exception classes for exceptional behaviour in data vault modelling.
They are needed to reflect the precise error in the modelling process.
"""


class InvalidAttachedEntity(Exception):
    """
    This exception type indicates that a `SatelliteEntity` cannot be attached to this entity.
    """
    pass


class InvalidLinkedEntity(Exception):
    """
    This exception type indicates that one of the linked entities
    is not a `HubEntity`
    """
    pass
