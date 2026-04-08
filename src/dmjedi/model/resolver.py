"""Resolves parsed DVML AST modules into a unified DataVaultModel."""

from dataclasses import dataclass

from dmjedi.lang.ast import DVMLModule
from dmjedi.model.core import (
    Column,
    DataVaultModel,
    EffSat,
    Hub,
    Link,
    NhLink,
    NhSat,
    SamLink,
    Satellite,
)


@dataclass
class ResolverError:
    """A single resolver validation error."""

    message: str
    source_file: str = ""
    line: int = 0


class ResolverErrors(Exception):
    """Raised when resolver detects validation errors."""

    def __init__(self, errors: list[ResolverError]) -> None:
        self.errors = errors
        messages = [e.message for e in errors]
        super().__init__(f"Resolver found {len(errors)} error(s):\n" + "\n".join(messages))


def resolve(modules: list[DVMLModule]) -> DataVaultModel:
    """Merge and resolve multiple DVML modules into a single DataVaultModel."""
    model = DataVaultModel()
    errors: list[ResolverError] = []

    for module in modules:
        ns = module.namespace

        for hub_decl in module.hubs:
            hub = Hub(
                name=hub_decl.name,
                namespace=ns,
                business_keys=[
                    Column(name=bk.name, data_type=bk.data_type, is_business_key=True)
                    for bk in hub_decl.business_keys
                ],
                columns=[
                    Column(name=f.name, data_type=f.data_type) for f in hub_decl.fields
                ],
            )
            qname = hub.qualified_name
            if qname in model.hubs:
                errors.append(
                    ResolverError(
                        message=(
                            f"Duplicate hub '{qname}' redefined"
                            f" in {module.source_file or '<string>'}:{hub_decl.loc.line}"
                        ),
                        source_file=module.source_file,
                        line=hub_decl.loc.line,
                    )
                )
            else:
                model.hubs[qname] = hub

        for sat_decl in module.satellites:
            sat = Satellite(
                name=sat_decl.name,
                namespace=ns,
                parent_ref=sat_decl.parent_ref,
                columns=[
                    Column(name=f.name, data_type=f.data_type) for f in sat_decl.fields
                ],
            )
            qname = sat.qualified_name
            if qname in model.satellites:
                errors.append(
                    ResolverError(
                        message=(
                            f"Duplicate satellite '{qname}' redefined"
                            f" in {module.source_file or '<string>'}:{sat_decl.loc.line}"
                        ),
                        source_file=module.source_file,
                        line=sat_decl.loc.line,
                    )
                )
            else:
                model.satellites[qname] = sat

        for link_decl in module.links:
            link = Link(
                name=link_decl.name,
                namespace=ns,
                hub_references=link_decl.references,
                columns=[
                    Column(name=f.name, data_type=f.data_type) for f in link_decl.fields
                ],
            )
            qname = link.qualified_name
            if qname in model.links:
                errors.append(
                    ResolverError(
                        message=(
                            f"Duplicate link '{qname}' redefined"
                            f" in {module.source_file or '<string>'}:{link_decl.loc.line}"
                        ),
                        source_file=module.source_file,
                        line=link_decl.loc.line,
                    )
                )
            else:
                model.links[qname] = link

        for nhsat_decl in module.nhsats:
            nhsat = NhSat(
                name=nhsat_decl.name,
                namespace=ns,
                parent_ref=nhsat_decl.parent_ref,
                columns=[
                    Column(name=f.name, data_type=f.data_type) for f in nhsat_decl.fields
                ],
            )
            qname = nhsat.qualified_name
            if qname in model.nhsats:
                errors.append(
                    ResolverError(
                        message=(
                            f"Duplicate nhsat '{qname}' redefined"
                            f" in {module.source_file or '<string>'}:{nhsat_decl.loc.line}"
                        ),
                        source_file=module.source_file,
                        line=nhsat_decl.loc.line,
                    )
                )
            else:
                model.nhsats[qname] = nhsat

        for nhlink_decl in module.nhlinks:
            nhlink = NhLink(
                name=nhlink_decl.name,
                namespace=ns,
                hub_references=nhlink_decl.references,
                columns=[
                    Column(name=f.name, data_type=f.data_type) for f in nhlink_decl.fields
                ],
            )
            qname = nhlink.qualified_name
            if qname in model.nhlinks:
                errors.append(
                    ResolverError(
                        message=(
                            f"Duplicate nhlink '{qname}' redefined"
                            f" in {module.source_file or '<string>'}:{nhlink_decl.loc.line}"
                        ),
                        source_file=module.source_file,
                        line=nhlink_decl.loc.line,
                    )
                )
            else:
                model.nhlinks[qname] = nhlink

        for effsat_decl in module.effsats:
            effsat = EffSat(
                name=effsat_decl.name,
                namespace=ns,
                parent_ref=effsat_decl.parent_ref,
                columns=[
                    Column(name=f.name, data_type=f.data_type) for f in effsat_decl.fields
                ],
            )
            qname = effsat.qualified_name
            if qname in model.effsats:
                errors.append(
                    ResolverError(
                        message=(
                            f"Duplicate effsat '{qname}' redefined"
                            f" in {module.source_file or '<string>'}:{effsat_decl.loc.line}"
                        ),
                        source_file=module.source_file,
                        line=effsat_decl.loc.line,
                    )
                )
            else:
                model.effsats[qname] = effsat

        for samlink_decl in module.samlinks:
            if not samlink_decl.master_ref or not samlink_decl.duplicate_ref:
                errors.append(
                    ResolverError(
                        message=(
                            f"SamLink '{samlink_decl.name}' missing master or duplicate"
                            f" reference in"
                            f" {module.source_file or '<string>'}:{samlink_decl.loc.line}"
                        ),
                        source_file=module.source_file,
                        line=samlink_decl.loc.line,
                    )
                )
                continue
            samlink = SamLink(
                name=samlink_decl.name,
                namespace=ns,
                master_ref=samlink_decl.master_ref,
                duplicate_ref=samlink_decl.duplicate_ref,
                columns=[
                    Column(name=f.name, data_type=f.data_type) for f in samlink_decl.fields
                ],
            )
            qname = samlink.qualified_name
            if qname in model.samlinks:
                errors.append(
                    ResolverError(
                        message=(
                            f"Duplicate samlink '{qname}' redefined"
                            f" in {module.source_file or '<string>'}:{samlink_decl.loc.line}"
                        ),
                        source_file=module.source_file,
                        line=samlink_decl.loc.line,
                    )
                )
            else:
                model.samlinks[qname] = samlink

    # Post-resolution validation: satellite parent refs
    for sat in model.satellites.values():
        ref = sat.parent_ref
        ns_ref = f"{sat.namespace}.{ref}" if sat.namespace else ref
        if (
            ref not in model.hubs
            and ref not in model.links
            and ns_ref not in model.hubs
            and ns_ref not in model.links
        ):
            errors.append(
                ResolverError(
                    message=(
                        f"Satellite '{sat.qualified_name}'"
                        f" references unknown parent '{ref}'"
                    ),
                )
            )

    # Post-resolution validation: nhsat parent refs
    for nhsat in model.nhsats.values():
        ref = nhsat.parent_ref
        ns_ref = f"{nhsat.namespace}.{ref}" if nhsat.namespace else ref
        if (
            ref not in model.hubs
            and ref not in model.links
            and ns_ref not in model.hubs
            and ns_ref not in model.links
        ):
            errors.append(
                ResolverError(
                    message=(
                        f"NhSat '{nhsat.qualified_name}'"
                        f" references unknown parent '{ref}'"
                    ),
                )
            )

    # Post-resolution validation: effsat parent refs
    for effsat in model.effsats.values():
        ref = effsat.parent_ref
        ns_ref = f"{effsat.namespace}.{ref}" if effsat.namespace else ref
        if (
            ref not in model.hubs
            and ref not in model.links
            and ns_ref not in model.hubs
            and ns_ref not in model.links
        ):
            errors.append(
                ResolverError(
                    message=(
                        f"EffSat '{effsat.qualified_name}'"
                        f" references unknown parent '{ref}'"
                    ),
                )
            )

    if errors:
        raise ResolverErrors(errors)

    return model
