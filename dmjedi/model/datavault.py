# -*- coding: utf-8 -*-

"""
Module for raw data vault data object definitions.

This module contains the necessary entities for defining a
valid (raw) data vault model.

TODO
 * Metaclasses??
"""
from dmjedi.model.database import Table
from dmjedi.model.columns import AbstractColumn
from dmjedi.exceptions import InvalidAttachedEntity, InvalidLinkedEntity
from copy import copy
import uuid


class AbstractBaseEntity(Table):
    """
    Represents the basic entity as an abstract class.

    ToDo
     * Immutable or mutable add field?
     * Add DV fields like record_source etc.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self._uuid = str(uuid.uuid4())

    # def __str__(self) -> str:
    #     return f"{type(self)}, {self.name} ({self.display_name}), UUID: {self._uuid}"

    # def __set_uuid__(self, uuid: str): {}
    def add_field(self, field: AbstractColumn) -> None:
        """
        Adds a field to the list of columns.
        :param field: A field of type `AbstractColumn`.
        :return: None
        """
        self.columns.append(field)

    def is_valid(self) -> bool:
        """
        Calculates the validity of the entity definition.
        :return: True for valid model and False for invalid model.
        """
        return False

    def describe(self) -> str:
        """
        Returns a human readable description of the entity.
        :return: Description as `str`
        """
        return super().describe()


class AbstractSatAttachable(AbstractBaseEntity):
    """
    Indicates if a satellite entity can be attached to this (derived) entity.
    """

    pass


class HubEntity(AbstractSatAttachable):
    """
    Represents the hub entity in data vault.
    """

    # def __repr__(self):

    def describe(self) -> str:
        """
        Returns a human readable description of the entity.
        :return: Description as `str`
        """
        s = [
            f"Hub entity '{self.name}' (with name '{self.display_name}') "
            + "has the following definition:",
            f"{super().describe()}",
        ]

        return "\n".join(s)

    def is_valid(self) -> bool:
        """
        Calculates the validity of the entity definition.
        A hub is valid when there is at least one business key defined.
        :return: True for valid model and False for invalid model.
        """
        return len(self.columns) > 0


class SatelliteEntity(AbstractBaseEntity):
    """
    Represents the standard satellite entity.
    """

    def __init__(
        self,
        entity: AbstractSatAttachable,
        name: str,
        display_name: str = None,
        schema: str = None,
        db: str = None,
        comment: str = None,
    ) -> None:
        super().__init__(name, display_name, schema, db, comment)
        if isinstance(entity, AbstractSatAttachable):
            self.entity = entity
        else:
            raise InvalidAttachedEntity(
                "A satellite cannot be attached to this entity!\n"
                + f"Referenced object {entity}."
            )

    # def __repr__(self) -> str:

    def describe(self) -> str:
        """
        Returns a human readable description of the entity.
        :return: Description as `str`
        """
        s = [
            f"Satellite entity '{self.name}' (with name '{self.display_name}')"
            + " has the following definition:",
            f"{super().describe()}",
            f"Attached entity {self.entity.describe()}",
        ]

        return "\n".join(s)

    def is_valid(self) -> bool:
        """
        Calculates the validity of the entity definition.
        A satellite is valid when there is at least one field defined and it
        is attached to an entity.
        :return: True for valid model and False for invalid model.
        """
        return len(self.columns) > 0 and self.entity is not None


class LinkEntity(AbstractSatAttachable):
    """
    Represents the standard link entity.
    """

    def __init__(
        self,
        name: str,
        display_name: str = None,
        schema: str = None,
        db: str = None,
        comment: str = None,
    ) -> None:
        super().__init__(name, display_name, schema, db, comment)
        self.hubs = []  # List[HubEntity]

    # def __repr__(self) -> str:

    def add_hub(self, hub: HubEntity) -> None:
        """
        Adds a `HubEntity` to the list of hubs. To add the same hub more than
        once use `add_hub_clone()` instead.
        :param hub: Hub entity of type `HubEntity` which will be added
                    to the list.
        :return: None
        """
        if isinstance(hub, HubEntity):
            self.hubs.append(hub)
        else:
            raise InvalidLinkedEntity("Only hubs can be linked together! No hub defined." if(hub is None) else f"Only hubs can be linked together! Linked entity '{hub.name}'.")

    def add_hub_clone(
        self, hub: HubEntity, new_name: str, new_display_name: str = None
    ) -> None:
        """
        Adds a `HubEntity` to the list of hubs. Use this function to add an
        alias to an already added hub to the list.
        :param hub: Hub entity
        :param new_name:
        :param new_display_name:
        :return:
        """
        if isinstance(hub, HubEntity):
            h = copy(hub)
            h.name = new_name
            h.display_name = new_display_name
            h._alias = hub
            self.hubs.append(h)
        else:
            raise InvalidLinkedEntity(
                f"Only hubs can be linked together! Linked entity "
                + f"'{hub.name} ({new_display_name})'."
            )

    def describe(self) -> str:
        """
        Returns a human readable description of the entity.
        :return: Description as `str`
        """
        s = [
            f"Link entity '{self.name}' (with name '{self.display_name}') has "
            + f"the following definition:",
            f"{super().describe()}",
        ]

        for h in self.hubs:
            s.append(f"Linked entity {h.describe()}")

        return "\n".join(s)

    def is_valid(self) -> bool:
        """
        Calculates the validity of the entity definition.
        A link is valid when there is at least two objects of type `HubEntity`.
        :return: True for valid model and False for invalid model.
        """
        return len(self.hubs) > 1


class DataVaultModel:
    """
    A data vault model and its entities.
    Contains some helper functions for ensuring validity.
    """

    pass


class Ensemble:
    pass


class PointInTime:
    pass


class Bridge:
    pass
