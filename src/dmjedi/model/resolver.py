"""Resolves parsed DVML AST modules into a unified DataVaultModel."""

from dataclasses import dataclass

from dmjedi.lang.ast import DVMLModule
from dmjedi.model.core import Column, DataVaultModel, Hub, Link, Satellite


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

    if errors:
        raise ResolverErrors(errors)

    return model
