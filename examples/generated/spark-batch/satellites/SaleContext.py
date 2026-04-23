import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *


@dlt.table(
    name="sat_SaleContext",
    comment="Satellite: SaleContext (parent: Sale)"
)
def sat_SaleContext():
    """Satellite entity attached to Sale."""
    df = dlt.read("src_SaleContext")
    return df.select(
        F.col("Sale_hk"),
        F.current_timestamp().alias("load_ts"),
        F.lit("dmjedi").alias("record_source"),
        F.sha2(F.concat_ws("||", F.col("channel"), F.col("discount"), F.col("payment")), 256).alias("hash_diff"),
        F.col("channel").cast(StringType()),
        F.col("discount").cast(DecimalType(18, 2)),
        F.col("payment").cast(StringType()),
    )
