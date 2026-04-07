"""Generator for SQL files via Jinja2 templates."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from dmjedi.generators.base import BaseGenerator, GeneratorResult
from dmjedi.generators.sql_jinja.types import map_type
from dmjedi.model.core import DataVaultModel

_TEMPLATES_DIR = Path(__file__).parent / "templates"


class SqlJinjaGenerator(BaseGenerator):
    def __init__(self, dialect: str = "default") -> None:
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

        return result
