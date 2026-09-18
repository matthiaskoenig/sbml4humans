"""The link graph of a report.

Every SBML object of the report is a node, every reference between objects is
an edge from the referencing to the referenced object. References are SIds
resolved within the containing model, unit definitions and local parameters in
their own namespaces, model references against the model definitions of the
document. An unresolvable reference is logged and produces no edge.
"""

import logging
from collections.abc import Iterator

from sbml4humans.model import (
    Edge,
    EdgeKind,
    Event,
    LinkGraph,
    Model,
    ModifierSpeciesReference,
    Node,
    Reaction,
    Report,
    SBase,
    SpeciesReference,
)


logger = logging.getLogger(__name__)


class ModelIndex:
    """The SIds of one model resolved to pks."""

    def __init__(self, model: Model) -> None:
        """Index the elements of the model by their ids."""
        self.model = model
        self.sids: dict[str, str] = {}
        self.units: dict[str, str] = {}
        self.locals: dict[str, dict[str, str]] = {}
        for element in _elements(model):
            if element.id is not None:
                self.sids.setdefault(element.id, element.pk)
        for ud in model.list_of_unit_definitions:
            if ud.id is not None:
                self.units[ud.id] = ud.pk
        for reaction in model.list_of_reactions:
            if reaction.kinetic_law is not None:
                self.locals[reaction.kinetic_law.pk] = {
                    lp.id: lp.pk
                    for lp in reaction.kinetic_law.list_of_local_parameters
                    if lp.id is not None
                }

    def resolve(self, sid: str, kinetic_law_pk: str | None = None) -> str | None:
        """The pk of an element by SId, local parameters of the kinetic law first."""
        if kinetic_law_pk is not None and sid in self.locals.get(kinetic_law_pk, {}):
            return self.locals[kinetic_law_pk][sid]
        return self.sids.get(sid)


def _elements(model: Model) -> Iterator[SBase]:
    """All elements of a model with an SId namespace entry, nested ones included."""
    yield from model.list_of_function_definitions
    yield from model.list_of_compartments
    yield from model.list_of_species
    yield from model.list_of_parameters
    yield from model.list_of_initial_assignments
    yield from model.list_of_rules
    yield from model.list_of_constraints
    for reaction in model.list_of_reactions:
        yield reaction
        yield from reaction.list_of_reactants
        yield from reaction.list_of_products
        yield from reaction.list_of_modifiers
    for event in model.list_of_events:
        yield event
        yield from event.list_of_event_assignments
    yield from model.list_of_submodels
    yield from model.list_of_ports
    yield from model.list_of_gene_products
    yield from model.list_of_objectives


def _nested(model: Model) -> Iterator[SBase]:
    """All nodes of a model: every element and the objects nested in one.

    The nested objects are the kinetic law of a reaction with its local
    parameters and the trigger, the priority and the delay of an event. None of
    them is referenced by an SId, so they are nodes without being part of the
    namespace of the model.
    """
    yield from model.list_of_unit_definitions
    yield from _elements(model)
    for reaction in model.list_of_reactions:
        if reaction.kinetic_law is not None:
            yield reaction.kinetic_law
            yield from reaction.kinetic_law.list_of_local_parameters
    for event in model.list_of_events:
        yield from _event_children(event)


def _event_children(event: Event) -> Iterator[SBase]:
    """The trigger, the priority and the delay of an event, those it has."""
    for child in (event.trigger, event.priority, event.delay):
        if child is not None:
            yield child


class LinkGraphBuilder:
    """Collects the nodes and edges of a report."""

    def __init__(self, report: Report, symbols: dict[str, set[str]]) -> None:
        """Prepare the build for the report and the symbols of its maths."""
        self.report = report
        self.symbols = symbols
        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge] = []
        self.indices: dict[str, ModelIndex] = {}
        self.model_refs: dict[str, str] = {}

    def build(self) -> LinkGraph:
        """Build the graph."""
        self._collect_nodes()
        for model in self.report.models:
            self._model_edges(model)
        return LinkGraph(nodes=self.nodes, edges=self.edges)

    # ---------------------------------------------------------------------------------
    # nodes
    # ---------------------------------------------------------------------------------
    def _add_node(self, sbase: SBase, model_pk: str | None) -> None:
        """Add the node of an element and of its uncertainties."""
        self.nodes[sbase.pk] = Node(
            pk=sbase.pk,
            sbml_type=sbase.sbml_type,
            id=sbase.id,
            name=sbase.name,
            model=model_pk,
        )
        for uncertainty in sbase.uncertainties:
            self._add_node(uncertainty, model_pk)

    def _collect_nodes(self) -> None:
        """Every SBase of the report is a node."""
        self._add_node(self.report.document, None)
        for emd in self.report.external_model_definitions:
            self._add_node(emd, None)
            if emd.id is not None:
                self.model_refs[emd.id] = emd.pk
        for model in self.report.models:
            self._add_node(model, None)
            if model.id is not None:
                self.model_refs[model.id] = model.pk
            self.indices[model.pk] = ModelIndex(model)
            for element in _nested(model):
                self._add_node(element, model.pk)

    # ---------------------------------------------------------------------------------
    # edges
    # ---------------------------------------------------------------------------------
    def _edge(
        self,
        source: SBase,
        sid: str | None,
        kind: EdgeKind,
        index: ModelIndex,
        kinetic_law_pk: str | None = None,
    ) -> None:
        """Add the edge for a reference, log when the reference does not resolve."""
        if sid is None:
            return
        target = index.resolve(sid, kinetic_law_pk)
        if target is None:
            logger.warning(
                "%s of '%s' references unknown '%s'", kind.value, source.pk, sid
            )
            return
        self.edges.append(Edge(source=source.pk, target=target, kind=kind))

    def _units_edge(
        self,
        source: SBase,
        sid: str | None,
        index: ModelIndex,
        kind: EdgeKind = EdgeKind.UNITS,
    ) -> None:
        """Add the edge when the sid is a unit definition of the model.

        The kind is `units` for a units attribute and `port` for the unitRef of
        a port.
        """
        if sid is not None and sid in index.units:
            self.edges.append(
                Edge(source=source.pk, target=index.units[sid], kind=kind)
            )

    def _math_edges(
        self, source: SBase, index: ModelIndex, kinetic_law_pk: str | None = None
    ) -> None:
        """Add the math edges for the symbols of the math of the source."""
        for symbol in sorted(self.symbols.get(source.pk, set())):
            target = index.resolve(symbol, kinetic_law_pk)
            if target is not None:
                self.edges.append(
                    Edge(source=source.pk, target=target, kind=EdgeKind.MATH)
                )

    def _comp_edges(self, source: SBase, index: ModelIndex) -> None:
        """Add the replacement edges of an element."""
        if source.comp is None:
            return
        if source.comp.replaced_by is not None:
            self._edge(
                source,
                source.comp.replaced_by.submodel_ref,
                EdgeKind.REPLACED_BY,
                index,
            )
        for replaced in source.comp.replaced_elements:
            self._edge(source, replaced.submodel_ref, EdgeKind.REPLACED_ELEMENT, index)

    def _model_edges(self, model: Model) -> None:
        """The edges of all elements of a model."""
        index = self.indices[model.pk]
        # every element carries the comp and distrib extensions, the model itself
        # can be replaced as well
        for element in [model, *_nested(model)]:
            self._comp_edges(element, index)
            for uncertainty in element.uncertainties:
                self._math_edges(uncertainty, index)

        for key in ["substance", "time", "volume", "area", "length", "extent"]:
            self._units_edge(model, getattr(model, f"{key}_units"), index)
        if model.conversion_factor is not None:
            self._edge(
                model, model.conversion_factor.sid, EdgeKind.CONVERSION_FACTOR, index
            )

        for fd in model.list_of_function_definitions:
            self._math_edges(fd, index)
        for c in model.list_of_compartments:
            self._units_edge(c, c.units, index)
        for s in model.list_of_species:
            self._edge(s, s.compartment, EdgeKind.COMPARTMENT, index)
            self._units_edge(s, s.substance_units, index)
            if s.conversion_factor is not None:
                self._edge(
                    s, s.conversion_factor.sid, EdgeKind.CONVERSION_FACTOR, index
                )
        for p in model.list_of_parameters:
            self._units_edge(p, p.units, index)
        for ia in model.list_of_initial_assignments:
            self._edge(ia, ia.symbol, EdgeKind.SYMBOL, index)
            self._math_edges(ia, index)
        for rule in model.list_of_rules:
            variable = getattr(rule, "variable", None)
            self._edge(rule, variable, EdgeKind.VARIABLE, index)
            self._math_edges(rule, index)
        for constraint in model.list_of_constraints:
            self._math_edges(constraint, index)
        for reaction in model.list_of_reactions:
            self._reaction_edges(reaction, index)
        for event in model.list_of_events:
            self._event_edges(event, index)
        for submodel in model.list_of_submodels:
            target = self.model_refs.get(submodel.model_ref)
            if target is None:
                logger.warning(
                    "modelRef of '%s' references unknown '%s'",
                    submodel.pk,
                    submodel.model_ref,
                )
            else:
                self.edges.append(
                    Edge(source=submodel.pk, target=target, kind=EdgeKind.MODEL_REF)
                )
            self._edge(
                submodel,
                submodel.time_conversion_factor,
                EdgeKind.CONVERSION_FACTOR,
                index,
            )
            self._edge(
                submodel,
                submodel.extent_conversion_factor,
                EdgeKind.CONVERSION_FACTOR,
                index,
            )
        for port in model.list_of_ports:
            self._edge(port, port.id_ref, EdgeKind.PORT, index)
            if port.unit_ref is not None:
                self._units_edge(port, port.unit_ref, index, kind=EdgeKind.PORT)
            self._meta_id_edge(port, port.meta_id_ref, model)
        for gp in model.list_of_gene_products:
            self._edge(gp, gp.associated_species, EdgeKind.ASSOCIATED_SPECIES, index)
        for objective in model.list_of_objectives:
            for fo in objective.list_of_flux_objectives:
                self._edge(objective, fo.reaction, EdgeKind.FLUX_OBJECTIVE, index)

    def _participation_edges(
        self,
        reaction: Reaction,
        reference: SpeciesReference | ModifierSpeciesReference,
        kind: EdgeKind,
        index: ModelIndex,
    ) -> None:
        """The two edges of a participation, both of its kind.

        The reaction lists the reference and the reference names the species,
        so the reference is a node of the graph instead of an isolated one and
        the role of the participation is on both edges.
        """
        self.edges.append(Edge(source=reaction.pk, target=reference.pk, kind=kind))
        self._edge(reference, reference.species, kind, index)

    def _meta_id_edge(self, port: SBase, meta_id: str | None, model: Model) -> None:
        """A port referencing an element by metaId."""
        if meta_id is None:
            return
        for element in _nested(model):
            if element.meta_id == meta_id:
                self.edges.append(
                    Edge(source=port.pk, target=element.pk, kind=EdgeKind.PORT)
                )
                return
        logger.warning("port of '%s' references unknown metaId '%s'", port.pk, meta_id)

    def _reaction_edges(self, reaction: Reaction, index: ModelIndex) -> None:
        """The edges of a reaction, its participants and its kinetic law.

        A reaction names its reactants, its products and its modifiers, and
        each of those names one species (core §4.11.1 to §4.11.4), so the
        edge of a participation is two edges of its kind: one from the
        reaction to the reference and one from the reference to the species.
        """
        self._edge(reaction, reaction.compartment, EdgeKind.COMPARTMENT, index)
        for sr in reaction.list_of_reactants:
            self._participation_edges(reaction, sr, EdgeKind.REACTANT, index)
        for sr in reaction.list_of_products:
            self._participation_edges(reaction, sr, EdgeKind.PRODUCT, index)
        for m in reaction.list_of_modifiers:
            self._participation_edges(reaction, m, EdgeKind.MODIFIER, index)
        if reaction.fbc is not None:
            self._edge(
                reaction, reaction.fbc.lower_flux_bound, EdgeKind.FLUX_BOUND, index
            )
            self._edge(
                reaction, reaction.fbc.upper_flux_bound, EdgeKind.FLUX_BOUND, index
            )
            for gene_product in reaction.fbc.gene_products:
                self._edge(reaction, gene_product, EdgeKind.GENE_PRODUCT, index)
        klaw = reaction.kinetic_law
        if klaw is not None:
            self._math_edges(klaw, index, kinetic_law_pk=klaw.pk)
            for lp in klaw.list_of_local_parameters:
                self._units_edge(lp, lp.units, index)

    def _event_edges(self, event: Event, index: ModelIndex) -> None:
        """The edges of an event: those of its children and of its assignments.

        The math of an event belongs to its trigger, its priority and its
        delay (core §4.12.2 to §4.12.4), so every math edge starts at the
        object which reads the element, not at the event around it.
        """
        for child in _event_children(event):
            self._math_edges(child, index)
        for ea in event.list_of_event_assignments:
            self._edge(ea, ea.variable, EdgeKind.VARIABLE, index)
            self._math_edges(ea, index)


def build_link_graph(report: Report, symbols: dict[str, set[str]]) -> LinkGraph:
    """The nodes and edges of a report.

    Args:
        report: the report with its models, without link graph.
        symbols: the symbols of every math, keyed by the pk of its owner.
    """
    return LinkGraphBuilder(report, symbols).build()
