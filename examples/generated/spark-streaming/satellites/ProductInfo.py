import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *


@dlt.table(
    name="sat_ProductInfo",
    comment="Satellite: ProductInfo (parent: Product)"
)
def sat_ProductInfo():
    """Satellite entity attached to Product."""
    df = dlt.read_stream("src_ProductInfo")
    return df.select(
        F.col("Product_hk"),
        F.current_timestamp().alias("load_ts"),
        F.lit("dmjedi").alias("record_source"),
        F.sha2(F.concat_ws("||", F.col("product_name"), F.col("category"), F.col("price")), 256).alias("hash_diff"),
        F.col("product_name").cast(StringType()),
        F.col("category").cast(StringType()),
        F.col("price").cast(DecimalType(18, 2)),
    )
