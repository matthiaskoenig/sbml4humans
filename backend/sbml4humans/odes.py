r"""The ordinary differential equations of a model, typeset by sbmlode.

`ode_system(doc, model)` builds the `OdeSystem` of the report of a document from the
typed target of sbmlode (`sbmlode.OdeSystem.typeset`): the ODEs, the rates of the
reactions, the assignment rules, the function definitions, the initial values, the
events and the constructs sbmlode does not support, the math as LaTeX for KaTeX.

Every symbol of the math which stands for an element of the report is wrapped as
`\htmlData{pk=<pk>}{<symbol>}`, which KaTeX renders as an element with the
attribute `data-pk`, so that the frontend links it without building a pk. The pk is
resolved with the identifiers of the model of the report (`links.ModelIndex`): an
SId or a local parameter through the kinetic law of its reaction; the element of a
construct sbmlode does not support also through its metaid (`_Links.unsupported`). A symbol without an element of the report, an id which
the flattening of comp makes up (`submodel__x`), stays as it is.

A pk consists of SIds (or metaids), `/` and `:`, so it holds no character which ends
the argument of `\htmlData` (`,`, `=`, `}`), and the symbols are typeset from ids,
never from names, see `sbmlode.text.check_sid`.
"""

import logging
import threading
from typing import cast

import libsbml
import sbmlode
from sbmlode.documents import TypesetEquation, TypesetSystem

from sbml4humans.links import ModelIndex
from sbml4humans.model import (
    Model,
    OdeEquation,
    OdeEvent,
    OdeOrigin,
    OdeSystem,
    OdeUnsupported,
)
from sbml4humans.validation import ReportDocuments, resolving_within


logger = logging.getLogger(__name__)

__all__ = ["analyse", "ode_system"]

#: libsbml aborts the process when two threads flatten comp models at once (the
#: `CompFlatteningConverter`, seen under concurrent reports of comp models), so the analysis
#: of sbmlode, which flattens a model with submodels, runs in one thread at a time
_ANALYSIS_LOCK = threading.Lock()


def analyse(
    doc: libsbml.SBMLDocument,
    documents: ReportDocuments | None = None,
    location: str = "",
) -> sbmlode.OdeSystem:
    """The ODE system of a document, analysed by sbmlode within the report.

    The external model definitions of the document resolve to the documents of the
    report alone (`resolving_within`), and one analysis runs at a time
    (`_ANALYSIS_LOCK`).

    Args:
        doc: the document, which is not changed
        documents: the documents of the report, which an external model definition
            may name; none if `None`
        location: the location of the document in the report

    Raises:
        ValueError: for a model sbmlode cannot analyse, e.g. one whose external
            model is not in the report
    """
    with (
        _ANALYSIS_LOCK,
        resolving_within(doc, documents or ReportDocuments({}), location),
    ):
        return sbmlode.OdeSystem.from_sbml(doc)


#: the type of the element of an unsupported construct, where the construct names one
_CONSTRUCT_TYPES = {"algebraic rule": "AlgebraicRule", "fast reaction": "Reaction"}


def _type_of(pk: str) -> str:
    """The type of the element of a pk, `Species` of `m/Species:S` (`sbmlinfo` writes it)."""
    return pk.partition("/")[2].partition(":")[0]


class _Links:
    """The pks of the symbols of sbmlode in the report of a model."""

    def __init__(self, model: Model) -> None:
        """Index the identifiers of the model.

        Args:
            model: the model of the report
        """
        self.index = ModelIndex(model)
        self.laws: dict[str, str] = {
            reaction.id: reaction.kinetic_law.pk
            for reaction in model.list_of_reactions
            if reaction.id is not None and reaction.kinetic_law is not None
        }

    def pk(self, symbol: sbmlode.system.Symbol | None) -> str | None:
        """The pk of the element a symbol stands for, `None` without one.

        Args:
            symbol: the symbol of sbmlode

        Returns:
            the pk, `None` for a symbol which is no element of the report
        """
        if symbol is None:
            return None
        return self.element(symbol.source)

    def element(self, source: tuple[str, ...]) -> str | None:
        """The pk of an element of the model, `(sid,)` or `(reaction, local id)`.

        A symbol of sbmlode is an SId, so it is resolved in the SIds alone: a metaid of
        the same text names another element.

        Args:
            source: what `sbmlode.system.Symbol.source` names

        Returns:
            the pk, `None` if the model has no such element
        """
        if len(source) == 2:
            law = self.laws.get(source[0])
            return (
                None if law is None else self.index.locals.get(law, {}).get(source[1])
            )
        return self.index.resolve(source[0])

    def unsupported(self, construct: str, label: str) -> str | None:
        """The pk of the element of a construct sbmlode does not support.

        sbmlode labels the element by its id, else by its metaid, else by a label of its
        own (`rule<k>`, the position of a rule), which may be the id of another element:
        the label is looked up as a metaid first and as an SId second, and an element
        of another type than the construct names (an algebraic rule, a fast reaction) is
        no element of it.

        Args:
            construct: the construct, `algebraic rule`, `fast reaction` or `delay`
            label: the label of its element

        Returns:
            the pk, `None` if the label names no element of the construct
        """
        expected = _CONSTRUCT_TYPES.get(construct)
        for pk in (self.index.meta_ids.get(label), self.index.resolve(label)):
            if pk is not None and (expected is None or _type_of(pk) == expected):
                return pk
        return None

    def wrap(self, symbol: sbmlode.system.Symbol, typeset: str) -> str:
        """A symbol as a link of KaTeX to its element, unchanged without one.

        Args:
            symbol: the symbol of sbmlode
            typeset: its typeset LaTeX

        Returns:
            the LaTeX of the symbol
        """
        pk = self.pk(symbol)
        return typeset if pk is None else rf"\htmlData{{pk={pk}}}{{{typeset}}}"


def _equation(
    links: _Links,
    variable: sbmlode.system.Symbol | None,
    lhs: str,
    lines: tuple[str, ...] | list[str],
    origin: OdeOrigin,
) -> OdeEquation:
    """An equation of the report."""
    return OdeEquation(
        variable=links.pk(variable), lhs=lhs, lines=list(lines), origin=origin
    )


def _typeset_equation(links: _Links, equation: TypesetEquation) -> OdeEquation:
    """An equation of the report from an equation of sbmlode."""
    # pydantic checks the origin: one sbmlode adds fails the system, not the report
    origin = cast("OdeOrigin", equation.origin)
    return _equation(links, equation.variable, equation.lhs, equation.lines, origin)


def _system(links: _Links, typeset: TypesetSystem) -> OdeSystem:
    """The system of the report from the typeset system of sbmlode."""
    return OdeSystem(
        odes=[_typeset_equation(links, e) for e in typeset.odes],
        reactions=[
            _equation(links, r.variable, r.symbol, r.lines, "reaction")
            for r in typeset.reactions
        ],
        assignments=[_typeset_equation(links, e) for e in typeset.assignments],
        functions=[
            _equation(links, f.variable, f.lhs, [f.rhs], "function")
            for f in typeset.functions
        ],
        initial=[_typeset_equation(links, e) for e in typeset.initial],
        events=[
            OdeEvent(
                event=links.pk(event.symbol),
                label=event.symbol.sid,
                trigger=event.trigger,
                delay=event.delay,
                priority=event.priority,
                initial_value=event.initial_value,
                persistent=event.persistent,
                use_values_from_trigger_time=event.use_trigger_values,
                assignments=[
                    _equation(links, a.variable, a.lhs, [a.rhs], "event")
                    for a in event.assignments
                ],
            )
            for event in typeset.events
        ],
        unsupported=[
            OdeUnsupported(
                kind=u.construct, element=links.unsupported(u.construct, u.element)
            )
            for u in typeset.unsupported
        ],
    )


def ode_system(
    doc: libsbml.SBMLDocument,
    model: Model,
    documents: ReportDocuments | None = None,
    location: str = "",
) -> tuple[OdeSystem | None, str | None]:
    """The ODE system of the model of a document, or the message of its failure.

    sbmlode flattens a model with submodels; the external model definitions it
    names are resolved to the documents of the report alone (`resolving_within`),
    never to a file or a url, so a model of a request reads nothing of the server.
    A failure of sbmlode, a model it refuses, an external model which is not in
    the report or an error in it, is logged with its traceback and returned as its
    message; the rest of the report does not depend on it.

    Args:
        doc: the document, which is not changed
        model: the report of its model, which the symbols link to
        documents: the documents of the report, which an external model
            definition may name; none if `None`
        location: the location of the document in the report

    Returns:
        the system and `None`, or `None` and the message of the failure
    """
    links = _Links(model)
    try:
        analysed = analyse(doc, documents, location)
        typeset = analysed.typeset("latex", "id", links.wrap)
        system = _system(links, typeset)
    except Exception as err:
        logger.exception("The ODE system of the model could not be built.")
        return None, str(err) or type(err).__name__
    return system, None
