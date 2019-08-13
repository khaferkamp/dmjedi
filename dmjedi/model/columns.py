# -*- coding: utf-8 -*-
"""Module for table column definitions.

This module describes the different table columns.
"""
from abc import ABC


class AbstractColumn(ABC):
    """
    Represents a the abstract construct of a column for use in a `Table`.
    """

    def __init__(
        self,
        name: str,
        data_type: str,
        display_name: str = None,
        default_value: str = "",
        primary_key: bool = False,
        unique: bool = False,
        indexed: bool = False,
        nullable: bool = True,
        comment: str = None,
    ) -> None:
        self.name = name
        self.data_type = data_type
        self.display_name = display_name
        self.default_value = default_value
        self.primary_key = primary_key
        self.unique = unique
        self.indexed = indexed
        self.nullable = nullable
        self.comment = comment
        self._alias = None

    def __str__(self) -> str:
        return self.name

    def describe(self) -> str:
        s = [
            f"Column [name '{self.name}'",
            f"display name '{self.display_name}'",
            f"data type: '{self.data_type}'",
            f"default value '{self.default_value}'",
            f"primary key '{self.primary_key}'",
            f"unique '{self.unique}'",
            f"indexed '{self.indexed}'",
            f"nullable '{self.nullable}']",
        ]

        return ", ".join(s)


class IntColumn(AbstractColumn):
    """
    Column for Integer values. Extends `AbstractColumn`.
    """

    def __init__(
        self,
        name: str,
        display_name: str = None,
        default_value: str = "",
        primary_key: bool = False,
        unique: bool = False,
        indexed: bool = False,
        nullable: bool = True,
        comment: str = None,
    ) -> None:
        super().__init__(
            name,
            "integer",
            display_name,
            default_value,
            primary_key,
            unique,
            indexed,
            nullable,
            comment,
        )


class TextColumn(AbstractColumn):
    """
    Column for Text values. Extends `AbstractColumn`.

    ToDo
        * Maybe separate into varchar/char/text
        * Also to consider: binary variants...
    """

    def __init__(
        self,
        name: str,
        display_name: str = None,
        default_value: str = "",
        primary_key: bool = False,
        unique: bool = False,
        indexed: bool = False,
        nullable: bool = True,
        comment: str = None,
    ) -> None:
        super().__init__(
            name,
            "text",
            display_name,
            default_value,
            primary_key,
            unique,
            indexed,
            nullable,
            comment,
        )


class DateColumn(AbstractColumn):
    """
    Column for Date values. Extends `AbstractColumn`.
    """

    def __init__(
        self,
        name: str,
        display_name: str = None,
        default_value: str = "",
        primary_key: bool = False,
        unique: bool = False,
        indexed: bool = False,
        nullable: bool = True,
        comment: str = None,
    ) -> None:
        super().__init__(
            name,
            "date",
            display_name,
            default_value,
            primary_key,
            unique,
            indexed,
            nullable,
            comment,
        )


class TimestampColumn(AbstractColumn):
    """
    Column for Timestamp values. Extends `AbstractColumn`.
    """

    def __init__(
        self,
        name: str,
        display_name: str = None,
        default_value: str = "",
        primary_key: bool = False,
        unique: bool = False,
        indexed: bool = False,
        nullable: bool = True,
        comment: str = None,
    ) -> None:
        super().__init__(
            name,
            "timestamp",
            display_name,
            default_value,
            primary_key,
            unique,
            indexed,
            nullable,
            comment,
        )


class NumericColumn(AbstractColumn):
    """
    Column for Date values. Extends `AbstractColumn`.
    """

    def __init__(
        self,
        name: str,
        display_name: str = None,
        default_value: str = "",
        primary_key: bool = False,
        unique: bool = False,
        indexed: bool = False,
        nullable: bool = True,
        comment: str = None,
    ) -> None:
        super().__init__(
            name,
            "numeric",
            display_name,
            default_value,
            primary_key,
            unique,
            indexed,
            nullable,
            comment,
        )


class BoolColumn(AbstractColumn):
    """
    Column for Boolean values. Extends `AbstractColumn`.

    Since `bool` is not available on all DBMS there will be logic for translating it into something usable.
    """

    def __init__(
        self,
        name: str,
        display_name: str = None,
        default_value: str = "",
        primary_key: bool = False,
        unique: bool = False,
        indexed: bool = False,
        nullable: bool = True,
        comment: str = None,
    ) -> None:
        super().__init__(
            name,
            "numeric",
            display_name,
            default_value,
            primary_key,
            unique,
            indexed,
            nullable,
            comment,
        )


class JsonColumn(AbstractColumn):
    """
    Column for JSON values. Extends `AbstractColumn`.
    """

    def __init__(
        self,
        name: str,
        display_name: str = None,
        default_value: str = "",
        primary_key: bool = False,
        unique: bool = False,
        indexed: bool = False,
        nullable: bool = True,
        comment: str = None,
    ) -> None:
        super().__init__(
            name,
            "jsonb",
            display_name,
            default_value,
            primary_key,
            unique,
            indexed,
            nullable,
            comment,
        )