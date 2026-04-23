import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *


@dlt.table(
    name="sat_StoreInfo",
    comment="Satellite: StoreInfo (parent: Store)"
)
def sat_StoreInfo():
    """Satellite entity attached to Store."""
    df = dlt.read_stream("src_StoreInfo")
    return df.select(
        F.col("Store_hk"),
        F.current_timestamp().alias("load_ts"),
        F.lit("dmjedi").alias("record_source"),
        F.sha2(F.concat_ws("||", F.col("store_name"), F.col("city"), F.col("country")), 256).alias("hash_diff"),
        F.col("store_name").cast(StringType()),
        F.col("city").cast(StringType()),
        F.col("country").cast(StringType()),
    )
