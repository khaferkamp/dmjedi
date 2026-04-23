import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *


@dlt.table(
    name="sat_CustomerDetails",
    comment="Satellite: CustomerDetails (parent: Customer)"
)
def sat_CustomerDetails():
    """Satellite entity attached to Customer."""
    df = dlt.read("src_CustomerDetails")
    return df.select(
        F.col("Customer_hk"),
        F.current_timestamp().alias("load_ts"),
        F.lit("dmjedi").alias("record_source"),
        F.sha2(F.concat_ws("||", F.col("first_name"), F.col("last_name"), F.col("email"), F.col("registered")), 256).alias("hash_diff"),
        F.col("first_name").cast(StringType()),
        F.col("last_name").cast(StringType()),
        F.col("email").cast(StringType()),
        F.col("registered").cast(TimestampType()),
    )
