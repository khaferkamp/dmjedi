"""Test module for a real world example

This module tests a real world but simple data vault model. It is very basic but describes
a model containing the following entities:

* two hubs (shop and visitor)
* one link in between these hubs
* referenced opening hours of the shop (excel file)

The resulting model should look like:
     +-------------------+
     |                   |
     |  satellite shop   |
     |                   |
     +---------|---------+
               |
               |
         +-----v-----+         +-------------------------------------+        +---------------+
         |           |         |                                     |        |               |
         |  hub shop ---------->  non-historized link visitor count  <---------  hub visitor  |
         |           |         |                                     |        |               |
         +-----^-----+         +-------------------------------------+        +---------------+
               |
               |
+----------------------------+
|                            |
|   reference opening hours  |
|                            |
+----------------------------+

TODO: Reference data
"""

# import pytest

from dmjedi.model.datavault import HubEntity, SatelliteEntity, LinkEntity

from dmjedi.model.columns import IntColumn, TextColumn, NumericColumn, TimestampColumn


def _createModel() -> None:
    """
    Creates the simple data vault model.
    """
    shop_h = HubEntity(name="shop_h", display_name="Hub for shops")
    shop_h.add_field(
        IntColumn(
            name="shop_no", display_name="Shop No.", primary_key=True, nullable=False
        )
    )  # Primary key should auotmatically be assigned for business keys

    visitor_h = HubEntity(
        name="visitor_h", display_name="Hub for visitors"
    )  # artificial hub with just ghost records to validly define a link. That's the real world...
    visitor_h.add_field(IntColumn(name="visitor_no", display_name="Vistitor No."))

    shop_s = SatelliteEntity(
        name="shop_s", display_name="Satellite for shops", entity=shop_h
    )
    shop_s.add_field(TextColumn(name="abbr", display_name="Abbreviation"))
    shop_s.add_field(TextColumn(name="lname", display_name="Long name"))
    shop_s.add_field(TextColumn(name="sname", display_name="Short name"))
    shop_s.add_field(
        NumericColumn(name="total_area_sqm", display_name="Total area in sqm")
    )
    shop_s.add_field(
        NumericColumn(name="net_area_sqm", display_name="Net shop area in sqm")
    )
    shop_s.add_field(TextColumn(name="street", display_name="Street"))
    shop_s.add_field(TextColumn(name="street_no", display_name="Street number"))
    shop_s.add_field(TextColumn(name="plc", display_name="Postal code"))
    shop_s.add_field(
        TextColumn(name="addr_add", display_name="Additional address information")
    )
    shop_s.add_field(TextColumn(name="city", display_name="City"))
    shop_s.add_field(TextColumn(name="state", display_name="State"))
    shop_s.add_field(TextColumn(name="country", display_name="Country"))
    shop_s.add_field(TextColumn(name="int_info", display_name="Information internal"))
    shop_s.add_field(TextColumn(name="ext_info", display_name="Information external"))
    shop_s.add_field(TimestampColumn(name="valid_from", display_name="Valid from"))
    shop_s.add_field(TimestampColumn(name="valid_to", display_name="Valid to"))
    shop_s.add_field(TimestampColumn(name="changed_at", display_name="Changed at"))
    shop_s.add_field(TextColumn(name="changed_by", display_name="Changed by"))

    visitcount_nhl = LinkEntity(
        name="visitcount_nhl",
        display_name="Count of visitors in shops per time interval",
    )
    visitcount_nhl.add_hub(visitor_h)
    visitcount_nhl.add_hub(shop_h)
    visitcount_nhl.add_field(TimestampColumn(name="day", display_name="Day"))
    visitcount_nhl.add_field(TimestampColumn(name="time", display_name="Time"))
    visitcount_nhl.add_field(NumericColumn(name="count_in", display_name="Count in"))
    visitcount_nhl.add_field(NumericColumn(name="count_out", display_name="Count out"))
    visitcount_nhl.add_field(NumericColumn(name="occupancy", display_name="Occupancy"))
    visitcount_nhl.add_field(
        NumericColumn(name="period_min", display_name="Period in min")
    )
    visitcount_nhl.add_field(
        NumericColumn(name="interpolated", display_name="Interpolated")
    )


def test_model() -> None:
    """
    Tests the validity of the basic data vault model.
    """

    _createModel()
    assert True
