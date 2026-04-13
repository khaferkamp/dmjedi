"""Generator for SQL files via Jinja2 templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from dmjedi.generators.base import BaseGenerator, GeneratorResult
from dmjedi.generators.sql_jinja.types import map_type
from dmjedi.model.core import DataVaultModel

_TEMPLATES_DIR = Path(__file__).parent / "templates"


class SqlJinjaGenerator(BaseGenerator):
    def __init__(self, dialect: str = "default", **kwargs: Any) -> None:
        self._dialect = dialect

    @property
    def name(self) -> str:
        return "sql-jinja"

    def generate(self, model: DataVaultModel) -> GeneratorResult:
        env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            keep_trailing_newline=True,
            autoescape=False,
        )
        env.globals["map_type"] = lambda t: map_type(t, self._dialect)
        result = GeneratorResult()

        hub_tpl = env.get_template("hub.sql.j2")
        for hub in model.hubs.values():
            result.add_file(f"hubs/{hub.name}.sql", hub_tpl.render(hub=hub))

        sat_tpl = env.get_template("satellite.sql.j2")
        for sat in model.satellites.values():
            result.add_file(f"satellites/{sat.name}.sql", sat_tpl.render(sat=sat))

        link_tpl = env.get_template("link.sql.j2")
        for link in model.links.values():
            result.add_file(f"links/{link.name}.sql", link_tpl.render(link=link))

        nhsat_tpl = env.get_template("nhsat.sql.j2")
        for nhsat in model.nhsats.values():
            result.add_file(
                f"satellites/nhsat_{nhsat.name}.sql", nhsat_tpl.render(nhsat=nhsat)
            )

        nhlink_tpl = env.get_template("nhlink.sql.j2")
        for nhlink in model.nhlinks.values():
            result.add_file(
                f"links/nhlink_{nhlink.name}.sql", nhlink_tpl.render(nhlink=nhlink)
            )

        bridge_tpl = env.get_template("bridge.sql.j2")
        for bridge in model.bridges.values():
            result.add_file(
                f"views/bridge_{bridge.name}.sql", bridge_tpl.render(bridge=bridge)
            )

        pit_tpl = env.get_template("pit.sql.j2")
        for pit in model.pits.values():
            result.add_file(
                f"views/pit_{pit.name}.sql", pit_tpl.render(pit=pit)
            )

        effsat_tpl = env.get_template("effsat.sql.j2")
        for effsat in model.effsats.values():
            result.add_file(
                f"satellites/effsat_{effsat.name}.sql", effsat_tpl.render(effsat=effsat)
            )

        samlink_tpl = env.get_template("samlink.sql.j2")
        for samlink in model.samlinks.values():
            result.add_file(
                f"links/samlink_{samlink.name}.sql", samlink_tpl.render(samlink=samlink)
            )

        return result
