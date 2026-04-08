"""Generator for Databricks Spark Declarative Pipelines (DLT)."""

from dmjedi.generators.base import BaseGenerator, GeneratorResult
from dmjedi.model.core import DataVaultModel, Hub, Link, NhLink, NhSat, Satellite
from dmjedi.model.types import map_pyspark_type

_IMPORTS = 'import dlt\nfrom pyspark.sql import functions as F\nfrom pyspark.sql.types import *\n'


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
        for nhsat in model.nhsats.values():
            result.add_file(
                f"satellites/nhsat_{nhsat.name}.py", self._generate_nhsat(nhsat)
            )
        for nhlink in model.nhlinks.values():
            result.add_file(
                f"links/nhlink_{nhlink.name}.py", self._generate_nhlink(nhlink)
            )
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
        col_selects = "".join(
            f'        F.col("{c.name}").cast({map_pyspark_type(c.data_type)}),\n'
            for c in sat.columns
        )

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
        col_selects = "".join(
            f'        F.col("{c.name}").cast({map_pyspark_type(c.data_type)}),\n'
            for c in link.columns
        )
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

    def _generate_nhsat(self, nhsat: NhSat) -> str:
        table_name = f"nhsat_{nhsat.name}"
        # NOTE: No column selection in generated code. dlt.apply_changes() infers
        # the full schema from the source dataset at runtime. User-defined columns
        # are validated at the model layer but do not appear in DLT output.

        return (
            f"{_IMPORTS}\n\n"
            f"@dlt.table(\n"
            f'    name="{table_name}",\n'
            f'    comment="NhSat: {nhsat.name} (parent: {nhsat.parent_ref}) — current-state"\n'
            f")\n"
            f"def {table_name}_target():\n"
            f'    """Schema definition for non-historized satellite {nhsat.name}."""\n'
            f"    pass\n\n"
            f"dlt.apply_changes(\n"
            f'    target="{table_name}",\n'
            f'    source="src_{nhsat.name}",\n'
            f'    keys=["{nhsat.parent_ref}_hk"],\n'
            f'    sequence_by=F.col("load_ts"),\n'
            f"    stored_as_scd_type=1,\n"
            f")\n"
        )

    def _generate_nhlink(self, nhlink: NhLink) -> str:
        table_name = f"nhlink_{nhlink.name}"
        # NOTE: No column selection or hub-ref column lists in generated code.
        # dlt.apply_changes() infers the full schema from the source dataset at
        # runtime. The only explicit key is the link hash key used for MERGE matching.

        return (
            f"{_IMPORTS}\n\n"
            f"@dlt.table(\n"
            f'    name="{table_name}",\n'
            f'    comment="NhLink: {nhlink.name} — current-state"\n'
            f")\n"
            f"def {table_name}_target():\n"
            f'    """Schema definition for non-historized link {nhlink.name}."""\n'
            f"    pass\n\n"
            f"dlt.apply_changes(\n"
            f'    target="{table_name}",\n'
            f'    source="src_{nhlink.name}",\n'
            f'    keys=["{nhlink.name}_hk"],\n'
            f'    sequence_by=F.col("load_ts"),\n'
            f"    stored_as_scd_type=1,\n"
            f")\n"
        )
