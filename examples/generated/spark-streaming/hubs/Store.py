import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *


@dlt.table(
    name="hub_Store",
    comment="Hub: Store"
)
def hub_Store():
    """Hub entity with business keys: store_id."""
    df = dlt.read_stream("src_Store")
    return df.select(
        F.sha2(F.concat_ws("||", F.col("store_id")), 256).alias("Store_hk"),
        F.current_timestamp().alias("load_ts"),
        F.lit("dmjedi").alias("record_source"),
        F.col("store_id"),
    ).distinct()
