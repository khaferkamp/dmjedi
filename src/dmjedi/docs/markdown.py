"""Markdown documentation generator for Data Vault models."""

from dmjedi.model.core import (
    Bridge,
    DataVaultModel,
    EffSat,
    Hub,
    Link,
    NhLink,
    NhSat,
    Pit,
    SamLink,
    Satellite,
)


def generate_markdown(model: DataVaultModel) -> str:
    """Generate a markdown document describing the full Data Vault model."""
    sections: list[str] = ["# Data Vault Model Documentation\n"]

    # Mermaid ER diagram at top (per D-12)
    diagram = _mermaid_diagram(model)
    if diagram:
        sections.append(diagram)

    # Raw Vault group (per D-07)
    raw_vault_sections: list[str] = []
    if model.hubs:
        raw_vault_sections.append("### Hubs\n")
        for hub in model.hubs.values():
            raw_vault_sections.append(_hub_section(hub))
    if model.links:
        raw_vault_sections.append("### Links\n")
        for link in model.links.values():
            raw_vault_sections.append(_link_section(link))
    if model.satellites:
        raw_vault_sections.append("### Satellites\n")
        for sat in model.satellites.values():
            raw_vault_sections.append(_satellite_section(sat))
    if model.nhsats:
        raw_vault_sections.append("### Non-Historized Satellites\n")
        for nhsat in model.nhsats.values():
            raw_vault_sections.append(_nhsat_section(nhsat))
    if model.nhlinks:
        raw_vault_sections.append("### Non-Historized Links\n")
        for nhlink in model.nhlinks.values():
            raw_vault_sections.append(_nhlink_section(nhlink))
    if model.effsats:
        raw_vault_sections.append("### Effectivity Satellites\n")
        for effsat in model.effsats.values():
            raw_vault_sections.append(_effsat_section(effsat))
    if model.samlinks:
        raw_vault_sections.append("### Same-As Links\n")
        for samlink in model.samlinks.values():
            raw_vault_sections.append(_samlink_section(samlink))

    if raw_vault_sections:
        sections.append("## Raw Vault\n")
        sections.extend(raw_vault_sections)

    # Query Assist group (per D-07)
    query_assist_sections: list[str] = []
    if model.bridges:
        query_assist_sections.append("### Bridges\n")
        for bridge in model.bridges.values():
            query_assist_sections.append(_bridge_section(bridge))
    if model.pits:
        query_assist_sections.append("### Point-in-Time Tables\n")
        for pit in model.pits.values():
            query_assist_sections.append(_pit_section(pit))

    if query_assist_sections:
        sections.append("## Query Assist\n")
        sections.extend(query_assist_sections)

    return "\n".join(sections)


def _hub_section(hub: Hub) -> str:
    lines = [f"#### {hub.qualified_name}\n"]
    if hub.business_keys:
        lines.append("**Business Keys:**\n")
        lines.append("| Name | Type |")
        lines.append("|------|------|")
        for bk in hub.business_keys:
            lines.append(f"| `{bk.name}` | `{bk.data_type}` |")
        lines.append("")
    return "\n".join(lines)


def _satellite_section(sat: Satellite) -> str:
    lines = [f"#### {sat.qualified_name}\n", f"**Parent:** `{sat.parent_ref}`\n"]
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
    lines = [f"#### {link.qualified_name}\n", f"**References:** {refs}\n"]
    if link.columns:
        lines.append("**Columns:**\n")
        lines.append("| Name | Type |")
        lines.append("|------|------|")
        for col in link.columns:
            lines.append(f"| `{col.name}` | `{col.data_type}` |")
        lines.append("")
    return "\n".join(lines)


def _nhsat_section(nhsat: NhSat) -> str:
    lines = [f"#### {nhsat.qualified_name}\n", f"**Parent:** `{nhsat.parent_ref}`\n"]
    if nhsat.columns:
        lines.append("**Columns:**\n")
        lines.append("| Name | Type |")
        lines.append("|------|------|")
        for col in nhsat.columns:
            lines.append(f"| `{col.name}` | `{col.data_type}` |")
        lines.append("")
    return "\n".join(lines)


def _nhlink_section(nhlink: NhLink) -> str:
    refs = ", ".join(f"`{r}`" for r in nhlink.hub_references)
    lines = [f"#### {nhlink.qualified_name}\n", f"**References:** {refs}\n"]
    if nhlink.columns:
        lines.append("**Columns:**\n")
        lines.append("| Name | Type |")
        lines.append("|------|------|")
        for col in nhlink.columns:
            lines.append(f"| `{col.name}` | `{col.data_type}` |")
        lines.append("")
    return "\n".join(lines)


def _effsat_section(effsat: EffSat) -> str:
    lines = [f"#### {effsat.qualified_name}\n", f"**Parent (Link):** `{effsat.parent_ref}`\n"]
    if effsat.columns:
        lines.append("**Columns:**\n")
        lines.append("| Name | Type |")
        lines.append("|------|------|")
        for col in effsat.columns:
            lines.append(f"| `{col.name}` | `{col.data_type}` |")
        lines.append("")
    return "\n".join(lines)


def _samlink_section(samlink: SamLink) -> str:
    lines = [
        f"#### {samlink.qualified_name}\n",
        f"**Master:** `{samlink.master_ref}`\n",
        f"**Duplicate:** `{samlink.duplicate_ref}`\n",
    ]
    if samlink.columns:
        lines.append("**Columns:**\n")
        lines.append("| Name | Type |")
        lines.append("|------|------|")
        for col in samlink.columns:
            lines.append(f"| `{col.name}` | `{col.data_type}` |")
        lines.append("")
    return "\n".join(lines)


def _bridge_section(bridge: Bridge) -> str:
    path_chain = " -> ".join(bridge.path)
    lines = [f"#### {bridge.qualified_name}\n", f"**Path:** {path_chain}\n"]
    return "\n".join(lines)


def _pit_section(pit: Pit) -> str:
    lines = [f"#### {pit.qualified_name}\n", f"**Anchor:** `{pit.anchor_ref}`\n"]
    if pit.tracked_satellites:
        lines.append("**Tracked Satellites:**\n")
        for sat_ref in pit.tracked_satellites:
            lines.append(f"- `{sat_ref}`")
        lines.append("")
    return "\n".join(lines)


def _mermaid_diagram(model: DataVaultModel) -> str:
    """Generate a Mermaid erDiagram block showing entity relationships."""
    lines: list[str] = []

    # Hub -> Satellite relationships (||--o{)
    for sat in model.satellites.values():
        lines.append(f"    {sat.parent_ref} ||--o{{ {sat.name} : \"sat\"")

    # Hub -> NhSat
    for nhsat in model.nhsats.values():
        lines.append(f"    {nhsat.parent_ref} ||--o{{ {nhsat.name} : \"nhsat\"")

    # Hub -> Link (each hub ref)
    for link in model.links.values():
        for ref in link.hub_references:
            lines.append(f"    {ref} ||--o{{ {link.name} : \"link\"")

    # Hub -> NhLink (each hub ref)
    for nhlink in model.nhlinks.values():
        for ref in nhlink.hub_references:
            lines.append(f"    {ref} ||--o{{ {nhlink.name} : \"nhlink\"")

    # Link -> EffSat
    for effsat in model.effsats.values():
        lines.append(f"    {effsat.parent_ref} ||--o{{ {effsat.name} : \"effsat\"")

    # SamLink master/duplicate
    for samlink in model.samlinks.values():
        lines.append(f"    {samlink.master_ref} ||--o{{ {samlink.name} : \"master\"")
        lines.append(f"    {samlink.duplicate_ref} ||--o{{ {samlink.name} : \"duplicate\"")

    # Bridge (dotted lines per D-13)
    for bridge in model.bridges.values():
        if bridge.path:
            lines.append(f"    {bridge.path[0]} ||..o{{ {bridge.name} : \"bridge\"")

    # PIT (dotted lines per D-13)
    for pit in model.pits.values():
        lines.append(f"    {pit.anchor_ref} ||..o{{ {pit.name} : \"pit\"")

    if not lines:
        return ""

    return "```mermaid\nerDiagram\n" + "\n".join(lines) + "\n```\n"
