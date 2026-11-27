"""Report identities around the shared Rust equation and source generator.

The application supplies its closed set of SBML documents and opaque element
keys. The shared core owns parsing, comp expansion, mathematical analysis and
LaTeX; this module only adapts the resulting data to the report schema.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import libsbml

from sbml4humans.links import ModelIndex
from sbml4humans.model import Model, OdeSystem
from sbml4humans.validation import MAX_EXPANDED_ELEMENTS, ReportDocuments


if TYPE_CHECKING:
    import sbmlsim_core


logger = logging.getLogger(__name__)

__all__ = ["analyse", "ode_system"]


def analyse(
    doc: libsbml.SBMLDocument,
    documents: ReportDocuments | None = None,
    location: str = "",
    budget: int | None = None,
) -> sbmlsim_core.OdeSystem:
    """Analyze a document using only explicitly supplied companion sources.

    No libSBML converter or filesystem resolver runs here. The core receives
    original source bytes, never the paths of an untrusted source.
    """
    import sbmlsim_core

    source = (
        libsbml.writeSBMLToString(doc).encode()
        if documents is None
        else documents.source_bytes(location, doc)
    )
    comp = doc.getModel().getPlugin("comp") if doc.getModel() is not None else None
    companions = (
        documents.sources(exclude=doc)
        if documents is not None and comp is not None and comp.getNumSubmodels() > 0
        else {}
    )
    return sbmlsim_core.OdeSystem.from_sbml(
        source,
        documents=companions,
        location=location or "./model.xml",
        max_expanded_elements=MAX_EXPANDED_ELEMENTS if budget is None else budget,
    )


def _links(model: Model) -> dict[str, object]:
    """Supply source identities without interpreting any mathematical expression."""
    index = ModelIndex(model)
    symbols: dict[str, str] = {}
    groups = [
        model.list_of_function_definitions,
        model.list_of_compartments,
        model.list_of_species,
        model.list_of_parameters,
        model.list_of_reactions,
        model.list_of_events,
    ]
    for group in groups:
        for obj in group:
            if obj.id is not None:
                symbols.setdefault(obj.id, obj.pk)
    local_links: list[dict[str, object]] = []
    for reaction in model.list_of_reactions:
        for reference in (
            *reaction.list_of_reactants,
            *reaction.list_of_products,
            *reaction.list_of_modifiers,
        ):
            if reference.id is not None:
                symbols.setdefault(reference.id, reference.pk)
        if reaction.id is not None and reaction.kinetic_law is not None:
            local_links.extend(
                {"reaction": reaction.id, "index": position, "link": parameter.pk}
                for position, parameter in enumerate(
                    reaction.kinetic_law.list_of_local_parameters
                )
            )
    metadata: list[dict[str, str]] = []
    for label, pk in index.meta_ids.items():
        kind = pk.partition("/")[2].partition(":")[0]
        metadata.extend(
            {"kind": lookup_kind, "metaid": label, "link": pk}
            for lookup_kind in ("", kind)
        )
    return {"symbols": symbols, "locals": local_links, "metadata": metadata}


def _system(value: dict[str, Any]) -> OdeSystem:
    """Validate the shared equation result against the application report contract."""
    return OdeSystem.model_validate(value)


def ode_system(
    doc: libsbml.SBMLDocument,
    model: Model,
    documents: ReportDocuments | None = None,
    location: str = "",
    budget: int | None = None,
) -> tuple[OdeSystem | None, str | None]:
    """Return linked equations or an ordinary input diagnostic without losing the report."""
    try:
        try:
            analysed = analyse(doc, documents, location, budget)
            value = analysed.typeset(_links(model))
        except ValueError as error:
            message = str(error) or type(error).__name__
            logger.warning(
                "The ODE system of the model could not be built: %s",
                " ".join(message.split()),
            )
            return None, message
        return _system(value), None
    except Exception as error:
        logger.exception("The ODE system of the model could not be built.")
        return None, str(error) or type(error).__name__
