import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *


@dlt.table(
    name="hub_Product",
    comment="Hub: Product"
)
def hub_Product():
    """Hub entity with business keys: product_id, sku."""
    df = dlt.read_stream("src_Product")
    return df.select(
        F.sha2(F.concat_ws("||", F.col("product_id"), F.col("sku")), 256).alias("Product_hk"),
        F.current_timestamp().alias("load_ts"),
        F.lit("dmjedi").alias("record_source"),
        F.col("product_id"),
        F.col("sku"),
    ).distinct()
