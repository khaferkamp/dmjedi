"""Generator for Databricks Spark Declarative Pipelines (DLT)."""

from dmjedi.generators.base import BaseGenerator, GeneratorResult
from dmjedi.model.core import DataVaultModel, Hub, Link, Satellite

_IMPORTS = 'import dlt\nfrom pyspark.sql import functions as F\n'


class SparkDeclarativeGenerator(BaseGenerator):
    @property
    def name(self) -> str:
        return "spark-declarative"

    def generate(self, model: DataVaultModel) -> GeneratorResult:
        result = GeneratorResult()
        for hub in model.hubs.values():
            result.add_file(f"hubs/{hub.name}.py", self._generate_hub(hub))
        for sat in model.satellites.values():
            result.add_file(f"satellites/{sat.name}.py", self._generate_satellite(sat))
        for link in model.links.values():
            result.add_file(f"links/{link.name}.py", self._generate_link(link))
        return result

    def _generate_hub(self, hub: Hub) -> str:
        table_name = f"hub_{hub.name}"
        bk_names = [bk.name for bk in hub.business_keys]
        bk_concat = ", ".join(f'F.col("{bk}")' for bk in bk_names)
        bk_selects = "".join(f'        F.col("{bk}"),\n' for bk in bk_names)
        bk_doc = ", ".join(bk_names)

        return (
            f"{_IMPORTS}\n\n"
            f"@dlt.table(\n"
            f'    name="{table_name}",\n'
            f'    comment="Hub: {hub.name}"\n'
            f")\n"
            f"def {table_name}():\n"
            f'    """Hub entity with business keys: {bk_doc}."""\n'
            f'    df = dlt.read("src_{hub.name}")\n'
            f"    return df.select(\n"
            f'        F.sha2(F.concat_ws("||", {bk_concat}), 256).alias("{hub.name}_hk"),\n'
            f'        F.current_timestamp().alias("load_ts"),\n'
            f'        F.lit("dmjedi").alias("record_source"),\n'
            f"{bk_selects}"
            f"    ).distinct()\n"
        )

    def _generate_satellite(self, sat: Satellite) -> str:
        table_name = f"sat_{sat.name}"
        col_names = [c.name for c in sat.columns]
        col_concat = ", ".join(f'F.col("{c}")' for c in col_names)
        col_selects = "".join(f'        F.col("{c}"),\n' for c in col_names)

        # hash_diff line: hash all user columns together
        if col_names:
            hash_diff_line = (
                f'        F.sha2(F.concat_ws("||", {col_concat}), 256)'
                f'.alias("hash_diff"),\n'
            )
        else:
            hash_diff_line = (
                '        F.sha2(F.lit(""), 256).alias("hash_diff"),\n'
            )

        return (
            f"{_IMPORTS}\n\n"
            f"@dlt.table(\n"
            f'    name="{table_name}",\n'
            f'    comment="Satellite: {sat.name} (parent: {sat.parent_ref})"\n'
            f")\n"
            f"def {table_name}():\n"
            f'    """Satellite entity attached to {sat.parent_ref}."""\n'
            f'    df = dlt.read("src_{sat.name}")\n'
            f"    return df.select(\n"
            f'        F.col("{sat.parent_ref}_hk"),\n'
            f'        F.current_timestamp().alias("load_ts"),\n'
            f'        F.lit("dmjedi").alias("record_source"),\n'
            f"{hash_diff_line}"
            f"{col_selects}"
            f"    )\n"
        )

    def _generate_link(self, link: Link) -> str:
        table_name = f"link_{link.name}"
        ref_hk_names = [f"{ref}_hk" for ref in link.hub_references]
        ref_concat = ", ".join(f'F.col("{hk}")' for hk in ref_hk_names)
        ref_selects = "".join(f'        F.col("{hk}"),\n' for hk in ref_hk_names)
        col_selects = "".join(f'        F.col("{c.name}"),\n' for c in link.columns)
        refs_doc = ", ".join(link.hub_references)

        return (
            f"{_IMPORTS}\n\n"
            f"@dlt.table(\n"
            f'    name="{table_name}",\n'
            f'    comment="Link: {link.name}"\n'
            f")\n"
            f"def {table_name}():\n"
            f'    """Link entity referencing: {refs_doc}."""\n'
            f'    df = dlt.read("src_{link.name}")\n'
            f"    return df.select(\n"
            f'        F.sha2(F.concat_ws("||", {ref_concat}), 256)'
            f'.alias("{link.name}_hk"),\n'
            f'        F.current_timestamp().alias("load_ts"),\n'
            f'        F.lit("dmjedi").alias("record_source"),\n'
            f"{ref_selects}"
            f"{col_selects}"
            f"    )\n"
        )
