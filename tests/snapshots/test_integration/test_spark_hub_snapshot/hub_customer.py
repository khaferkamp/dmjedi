import dlt
from pyspark.sql import functions as F


@dlt.table(
    name="hub_Customer",
    comment="Hub: Customer"
)
def hub_Customer():
    """Hub entity with business keys: customer_id."""
    df = dlt.read("src_Customer")
    return df.select(
        F.sha2(F.concat_ws("||", F.col("customer_id")), 256).alias("Customer_hk"),
        F.current_timestamp().alias("load_ts"),
        F.lit("dmjedi").alias("record_source"),
        F.col("customer_id"),
    ).distinct()
