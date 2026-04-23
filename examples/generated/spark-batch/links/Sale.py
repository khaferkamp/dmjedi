import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *


@dlt.table(
    name="link_Sale",
    comment="Link: Sale"
)
def link_Sale():
    """Link entity referencing: Customer, Product, Store."""
    df = dlt.read("src_Sale")
    return df.select(
        F.sha2(F.concat_ws("||", F.col("Customer_hk"), F.col("Product_hk"), F.col("Store_hk")), 256).alias("Sale_hk"),
        F.current_timestamp().alias("load_ts"),
        F.lit("dmjedi").alias("record_source"),
        F.col("Customer_hk"),
        F.col("Product_hk"),
        F.col("Store_hk"),
        F.col("sale_date").cast(TimestampType()),
        F.col("quantity").cast(IntegerType()),
        F.col("amount").cast(DecimalType(18, 2)),
    )
