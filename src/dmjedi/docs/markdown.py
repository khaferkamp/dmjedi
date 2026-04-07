"""Markdown documentation generator for Data Vault models."""

from dmjedi.model.core import DataVaultModel, Hub, Link, Satellite


def generate_markdown(model: DataVaultModel) -> str:
    """Generate a markdown document describing the full Data Vault model."""
    sections: list[str] = ["# Data Vault Model Documentation\n"]

    if model.hubs:
        sections.append("## Hubs\n")
        for hub in model.hubs.values():
            sections.append(_hub_section(hub))

    if model.links:
        sections.append("## Links\n")
        for link in model.links.values():
            sections.append(_link_section(link))

    if model.satellites:
        sections.append("## Satellites\n")
        for sat in model.satellites.values():
            sections.append(_satellite_section(sat))

    return "\n".join(sections)


def _hub_section(hub: Hub) -> str:
    lines = [f"### {hub.qualified_name}\n"]
    if hub.business_keys:
        lines.append("**Business Keys:**\n")
        lines.append("| Name | Type |")
        lines.append("|------|------|")
        for bk in hub.business_keys:
            lines.append(f"| `{bk.name}` | `{bk.data_type}` |")
        lines.append("")
    return "\n".join(lines)


def _satellite_section(sat: Satellite) -> str:
    lines = [f"### {sat.qualified_name}\n", f"**Parent:** `{sat.parent_ref}`\n"]
    if sat.columns:
        lines.append("**Columns:**\n")
        lines.append("| Name | Type |")
        lines.append("|------|------|")
        for col in sat.columns:
            lines.append(f"| `{col.name}` | `{col.data_type}` |")
        lines.append("")
    return "\n".join(lines)


def _link_section(link: Link) -> str:
    refs = ", ".join(f"`{r}`" for r in link.hub_references)
    lines = [f"### {link.qualified_name}\n", f"**References:** {refs}\n"]
    if link.columns:
        lines.append("**Columns:**\n")
        lines.append("| Name | Type |")
        lines.append("|------|------|")
        for col in link.columns:
            lines.append(f"| `{col.name}` | `{col.data_type}` |")
        lines.append("")
    return "\n".join(lines)
