# -*- coding: utf-8 -*-
"""Module for defining database objects.

This module defines the different objects that are stored in a database.
It abstracts the conrecte phyisical logic and instead focusses on the logical description of the object
so that a generator has a chance to generate the best fit to the desired DBMS.

TODO:
 * Maybe define Schema and Database as real classes
"""


class Database:
    pass


class Table:
    """
    Represents a table in (a schema in) a database.
    """

    def __init__(
        self,
        name: str,
        display_name: str = None,
        schema: str = None,
        db: str = None,
        comment: str = None,
    ) -> None:
        self.name = name
        self.display_name = display_name
        self.schema = schema
        self.db = db
        self.comment = comment
        self.columns = []
        self.keys = []
        self.indexes = []
        self.partitions = []
        self.uuid = None
        self.rsrc = None

    def __str__(self) -> str:
        return self.name

    def describe(self) -> str:
        s = [
            f"Table [name '{self.name}'",
            f"display name '{self.display_name}'",
            f"schema: '{self.schema}'",
            f"database '{self.db}'",
            f"comment '{self.comment}']",
        ]

        for col in self.columns:
            s.append(f"\n{col.describe()}")

        return ", ".join(s)


class View:
    """
    Represents a view in a database.

    ToDo
     * How should a view be defined? Plain SQL?
    """

    pass
