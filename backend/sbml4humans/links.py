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
    Port,
    Reaction,
    ReplacedBy,
    ReplacedElement,
    Report,
    SBase,
    SBaseRefFields,
    SpeciesReference,
    Submodel,
)


logger = logging.getLogger(__name__)


class ModelIndex:
    """The identifiers of one model resolved to pks.

    SBML keeps the identifiers of a model in namespaces of their own (core
    §3.3, comp §3.4.3): the SIds of its elements, the unit identifiers of its
    unit definitions, the port identifiers of its ports, the meta ids of the
    file and the local parameters of every kinetic law. A comp reference names
    which of them it means, so each has its own index.
    """

    def __init__(self, model: Model) -> None:
        """Index the elements of the model by their identifiers."""
        self.model = model
        self.sids: dict[str, str] = {}
        self.units: dict[str, str] = {}
        self.ports: dict[str, str] = {}
        self.port_objects: dict[str, Port] = {}
        self.meta_ids: dict[str, str] = {}
        self.submodels: dict[str, Submodel] = {}
        self.deletions: dict[str, dict[str, str]] = {}
        self.locals: dict[str, dict[str, str]] = {}
        for element in _elements(model):
            if element.id is not None:
                self.sids.setdefault(element.id, element.pk)
        for element in _nested(model):
            if element.meta_id is not None:
                self.meta_ids.setdefault(element.meta_id, element.pk)
        for ud in model.list_of_unit_definitions:
            if ud.id is not None:
                self.units[ud.id] = ud.pk
        for port in model.list_of_ports:
            self.port_objects[port.pk] = port
            if port.id is not None:
                self.ports[port.id] = port.pk
        for submodel in model.list_of_submodels:
            self.submodels[submodel.pk] = submodel
            self.deletions[submodel.pk] = {
                deletion.id: deletion.pk
                for deletion in submodel.list_of_deletions
                if deletion.id is not None
            }
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

    def resolve_ref(self, ref: SBaseRefFields) -> str | None:
        """The pk of the element a comp reference names in this model.

        Exactly one of the four references of an `SBaseRef` is set and each of
        them names its own namespace (comp §3.7.1). A reference which sets none
        of them names nothing here: a replaced element which is scoped to a
        deletion carries that deletion instead.
        """
        if ref.port_ref is not None:
            return self.ports.get(ref.port_ref)
        if ref.id_ref is not None:
            return self.sids.get(ref.id_ref)
        if ref.unit_ref is not None:
            return self.units.get(ref.unit_ref)
        if ref.meta_id_ref is not None:
            return self.meta_ids.get(ref.meta_id_ref)
        return None


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
    parameters, the trigger, the priority and the delay of an event and the
    deletions of a submodel with the references below them. None of them is
    referenced by an SId, so they are nodes without being part of the namespace
    of the model.
    """
    yield from model.list_of_unit_definitions
    yield from _elements(model)
    for reaction in model.list_of_reactions:
        if reaction.kinetic_law is not None:
            yield reaction.kinetic_law
            yield from reaction.kinetic_law.list_of_local_parameters
    for event in model.list_of_events:
        yield from _event_children(event)
    for submodel in model.list_of_submodels:
        for deletion in submodel.list_of_deletions:
            yield from _ref_chain(deletion)
    for port in model.list_of_ports:
        if port.sbase_ref is not None:
            yield from _ref_chain(port.sbase_ref)


def _ref_chain(ref: SBaseRefFields) -> Iterator[SBaseRefFields]:
    """A comp reference and every reference below it (comp §3.7.2)."""
    yield ref
    if ref.sbase_ref is not None:
        yield from _ref_chain(ref.sbase_ref)


def _comp_refs(sbase: SBase) -> Iterator[SBaseRefFields]:
    """The replacements of an element, each with the references below it.

    An element says which elements of submodels it replaces and which element
    of a submodel replaces it (comp §3.6), and every one of those references is
    an element of the report of its own.
    """
    if sbase.comp is None:
        return
    if sbase.comp.replaced_by is not None:
        yield from _ref_chain(sbase.comp.replaced_by)
    for replaced in sbase.comp.replaced_elements:
        yield from _ref_chain(replaced)


def _names_an_element(ref: SBaseRefFields) -> bool:
    """Whether a comp reference names an element at all.

    A replaced element which is scoped to a deletion sets none of the four
    references of `SBaseRef` (comp §3.6.2), so it names nothing to resolve and
    nothing is missing when nothing resolves.
    """
    return any(
        value is not None
        for value in (ref.port_ref, ref.id_ref, ref.unit_ref, ref.meta_id_ref)
    )


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
        """Add the node of an element, of its uncertainties and of its replacements."""
        self.nodes[sbase.pk] = Node(
            pk=sbase.pk,
            sbml_type=sbase.sbml_type,
            id=sbase.id,
            name=sbase.name,
            model=model_pk,
        )
        for uncertainty in sbase.uncertainties:
            self._add_node(uncertainty, model_pk)
        for ref in _comp_refs(sbase):
            self._add_node(ref, model_pk)

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

    # ---------------------------------------------------------------------------------
    # comp: the references which reach into a submodel
    # ---------------------------------------------------------------------------------
    def _submodel_index(self, submodel: Submodel) -> ModelIndex | None:
        """The index of the model a submodel instantiates, None for an external one.

        A submodel instantiates a model definition of the document or an
        external model definition (comp §3.5.1). The document of an external
        one is not read, so the report has no model to resolve a reference in.
        """
        model_pk = self.model_refs.get(submodel.model_ref)
        return self.indices.get(model_pk) if model_pk is not None else None

    def _resolve_into(
        self, source: SBase, ref: SBaseRefFields, submodel: Submodel
    ) -> str | None:
        """The pk of the element a reference names inside a submodel.

        The reference is resolved in the model the submodel instantiates, and a
        reference which carries a reference of its own names a submodel of that
        model and goes on inside it (comp §3.7.2). Every step which does not
        resolve is logged and ends the chain.
        """
        index = self._submodel_index(submodel)
        if index is None:
            logger.warning(
                "reference of '%s' stops at submodel '%s': the model '%s' it "
                "instantiates is not part of the report",
                source.pk,
                submodel.pk,
                submodel.model_ref,
            )
            return None
        target = self._resolve_element(source, ref, index)
        if target is None:
            return None
        if ref.sbase_ref is None:
            return target
        nested_submodel = index.submodels.get(target)
        if nested_submodel is None:
            logger.warning(
                "nested reference of '%s' names '%s', which is no submodel",
                source.pk,
                target,
            )
            return None
        return self._resolve_into(source, ref.sbase_ref, nested_submodel)

    def _resolve_element(
        self, source: SBase, ref: SBaseRefFields, index: ModelIndex
    ) -> str | None:
        """The element a reference names in one model, a port being one name of one.

        A reference by port names the element the port stands for, so the edge
        ends at that element and not at the port, which is where the reference
        would stop halfway (comp §3.7.1).
        """
        target = index.resolve_ref(ref)
        if target is None:
            if _names_an_element(ref):
                logger.warning(
                    "reference of '%s' names no element of model '%s'",
                    source.pk,
                    index.model.pk,
                )
            return None
        port = index.port_objects.get(target)
        return self._port_target(port, index) if port is not None else target

    def _port_target(self, port: Port, index: ModelIndex) -> str | None:
        """The element a port names, through its nested reference where it has one."""
        target = self._resolve_element(port, port, index)
        if target is None or port.sbase_ref is None:
            return target
        submodel = index.submodels.get(target)
        if submodel is None:
            logger.warning(
                "nested reference of '%s' names '%s', which is no submodel",
                port.pk,
                target,
            )
            return None
        return self._resolve_into(port, port.sbase_ref, submodel)

    def _comp_edges(self, source: SBase, index: ModelIndex) -> None:
        """Add the replacement edges of an element.

        The element names its replacements, and every replacement names the
        submodel it reaches into and the element inside it (comp §3.6), the way
        a reaction names its species references and each of those its species.
        """
        if source.comp is None:
            return
        if source.comp.replaced_by is not None:
            replaced_by = source.comp.replaced_by
            self.edges.append(
                Edge(source=source.pk, target=replaced_by.pk, kind=EdgeKind.REPLACED_BY)
            )
            self._replacement_edges(replaced_by, EdgeKind.REPLACED_BY, index)
        for replaced in source.comp.replaced_elements:
            self.edges.append(
                Edge(
                    source=source.pk,
                    target=replaced.pk,
                    kind=EdgeKind.REPLACED_ELEMENT,
                )
            )
            self._replacement_edges(replaced, EdgeKind.REPLACED_ELEMENT, index)

    def _replacement_edges(
        self,
        replacement: ReplacedBy | ReplacedElement,
        kind: EdgeKind,
        index: ModelIndex,
    ) -> None:
        """The edges of one replacement: its element, its deletion and its factor.

        The edge of the replacement ends at the element of the submodel which
        the reference names. Where the reference cannot be resolved, because
        the model of the submodel is an external one or because the element is
        not there, it ends at the submodel itself, which is as far as the
        report can follow it.
        """
        submodel_pk = index.resolve(replacement.submodel_ref)
        if submodel_pk is None:
            logger.warning(
                "%s of '%s' references unknown submodel '%s'",
                kind.value,
                replacement.pk,
                replacement.submodel_ref,
            )
            return
        submodel = index.submodels[submodel_pk]
        target = self._resolve_into(replacement, replacement, submodel)
        self.edges.append(
            Edge(source=replacement.pk, target=target or submodel_pk, kind=kind)
        )
        if isinstance(replacement, ReplacedElement):
            self._deletion_edge(replacement, submodel_pk, index)
            self._edge(
                replacement,
                replacement.conversion_factor,
                EdgeKind.CONVERSION_FACTOR,
                index,
            )

    def _deletion_edge(
        self, replacement: ReplacedElement, submodel_pk: str, index: ModelIndex
    ) -> None:
        """The edge to the deletion a replacement stands for (comp §3.6.2)."""
        if replacement.deletion is None:
            return
        target = index.deletions.get(submodel_pk, {}).get(replacement.deletion)
        if target is None:
            logger.warning(
                "deletion of '%s' references unknown '%s' of submodel '%s'",
                replacement.pk,
                replacement.deletion,
                submodel_pk,
            )
            return
        self.edges.append(
            Edge(source=replacement.pk, target=target, kind=EdgeKind.DELETION)
        )

    def _submodel_edges(self, submodel: Submodel, index: ModelIndex) -> None:
        """The edges of a submodel: its model, its conversion factors, its deletions.

        A submodel lists its deletions and every deletion names the element of
        the instantiated model which it removes (comp §3.5.3).
        """
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
            submodel, submodel.time_conversion_factor, EdgeKind.CONVERSION_FACTOR, index
        )
        self._edge(
            submodel,
            submodel.extent_conversion_factor,
            EdgeKind.CONVERSION_FACTOR,
            index,
        )
        for deletion in submodel.list_of_deletions:
            self.edges.append(
                Edge(source=submodel.pk, target=deletion.pk, kind=EdgeKind.DELETION)
            )
            deleted = self._resolve_into(deletion, deletion, submodel)
            if deleted is not None:
                self.edges.append(
                    Edge(source=deletion.pk, target=deleted, kind=EdgeKind.DELETION)
                )

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
            self._submodel_edges(submodel, index)
        for port in model.list_of_ports:
            self._port_edge(port, index)
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

    def _port_edge(self, port: Port, index: ModelIndex) -> None:
        """The edge of a port to the element it names.

        A port names one element of its own model by its id, its unit id or its
        meta id (comp §3.4.3), and reaches into a submodel of it with a nested
        reference.
        """
        target = self._port_target(port, index)
        if target is None:
            return
        self.edges.append(Edge(source=port.pk, target=target, kind=EdgeKind.PORT))

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
        object which reads the element, not at the event around it, and the
        event names the three the way a reaction names its species references.
        """
        for child, kind in (
            (event.trigger, EdgeKind.TRIGGER),
            (event.priority, EdgeKind.PRIORITY),
            (event.delay, EdgeKind.DELAY),
        ):
            if child is not None:
                self.edges.append(Edge(source=event.pk, target=child.pk, kind=kind))
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
