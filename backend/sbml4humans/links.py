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
    And,
    Association,
    Edge,
    EdgeKind,
    Event,
    GeneProductAssociation,
    GeneProductRef,
    LinkGraph,
    Model,
    ModifierSpeciesReference,
    Node,
    Objective,
    Or,
    Port,
    Reaction,
    ReplacedBy,
    ReplacedElement,
    Report,
    SBase,
    SBaseRefFields,
    SpeciesReference,
    Submodel,
    Transition,
    Uncertainty,
    UncertParameter,
    UncertSpan,
    UserDefinedConstraint,
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
    """All elements of a model with an SId namespace entry, nested ones included.

    The ports of a model are not among them: comp §3.4.3 keeps the port
    identifiers in a namespace of their own, so a port may carry the identifier
    of an element of its model without naming it, and only a reference which
    says that it means a port resolves against them.
    """
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
        yield from _association_tree(reaction)
    for event in model.list_of_events:
        yield event
        yield from event.list_of_event_assignments
    yield from model.list_of_submodels
    yield from model.list_of_gene_products
    yield from model.list_of_flux_bounds
    for constraint in model.list_of_user_defined_constraints:
        yield constraint
        yield from constraint.list_of_user_defined_constraint_components
    for objective in model.list_of_objectives:
        yield objective
        yield from objective.list_of_flux_objectives
    yield from model.list_of_qualitative_species
    for transition in model.list_of_transitions:
        yield transition
        # an input and an output may carry an identifier, and a function term
        # names it to mean the threshold level or the output level (qual §3.6.5)
        yield from transition.list_of_inputs
        yield from transition.list_of_outputs


def _nested(model: Model) -> Iterator[SBase]:
    """All nodes of a model: every element and the objects nested in one.

    The nested objects are the kinetic law of a reaction with its local
    parameters, the trigger, the priority and the delay of an event and the
    deletions of a submodel with the references below them. None of them is
    referenced by an SId, and neither is a port, so they are nodes without
    being part of the SId namespace of the model.
    """
    yield from model.list_of_unit_definitions
    yield from _elements(model)
    yield from model.list_of_ports
    for reaction in model.list_of_reactions:
        if reaction.kinetic_law is not None:
            yield reaction.kinetic_law
            yield from reaction.kinetic_law.list_of_local_parameters
    for event in model.list_of_events:
        yield from _event_children(event)
    for transition in model.list_of_transitions:
        yield from _transition_terms(transition)
    for submodel in model.list_of_submodels:
        for deletion in submodel.list_of_deletions:
            yield from _ref_chain(deletion)
    for port in model.list_of_ports:
        if port.sbase_ref is not None:
            yield from _ref_chain(port.sbase_ref)


def _association_tree(reaction: Reaction) -> Iterator[SBase]:
    """The gene product association of a reaction and every node of its tree.

    The association, the `and` and `or` nodes below it and the references to
    the gene products are elements of the report which carry an identifier of
    the SId namespace of the model (fbc §3.2).
    """
    if reaction.fbc is None or reaction.fbc.gene_product_association is None:
        return
    association = reaction.fbc.gene_product_association
    yield association
    if association.association is not None:
        yield from _association_nodes(association.association)


def _association_nodes(node: Association) -> Iterator[SBase]:
    """A node of an association tree and every node below it (fbc §3.10)."""
    yield node
    if isinstance(node, And | Or):
        for child in node.associations:
            yield from _association_nodes(child)


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


def _with_extensions(sbase: SBase) -> Iterator[SBase]:
    """An element and every object its extensions nest in it.

    distrib gives any element uncertainties, each with its measures (distrib
    §3.9), and comp gives it replacements, each with the chain of references
    below it (comp §3.6). All of them are `SBase` in turn and carry the two
    extensions themselves.
    """
    yield sbase
    for uncertainty in sbase.uncertainties:
        yield from _with_extensions(uncertainty)
        for measure in _uncert_measures(uncertainty):
            yield from _with_extensions(measure)
    for ref in _comp_refs(sbase):
        yield from _with_extensions(ref)


def _uncert_measures(owner: Uncertainty | UncertParameter) -> Iterator[UncertParameter]:
    """The parameters of an uncertainty, the ones nested in one included.

    A parameter of the type `distribution` or `externalParameter` is defined by
    parameters of its own, to any depth (distrib §3.11.7).
    """
    for measure in owner.uncert_parameters:
        yield measure
        yield from _uncert_measures(measure)


def _transition_terms(transition: Transition) -> Iterator[SBase]:
    """The function terms of a transition and its default term (qual §3.6.3).

    A term carries no identifier the specification puts in a namespace, so it
    is a node of the graph without being part of the SId namespace of the
    model, the way the trigger of an event is.
    """
    yield from transition.list_of_function_terms
    if transition.default_term is not None:
        yield transition.default_term


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
        for element in _with_extensions(sbase):
            self.nodes[element.pk] = Node(
                pk=element.pk,
                sbml_type=element.sbml_type,
                id=element.id,
                name=element.name,
                model=model_pk,
            )

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
    # distrib: the uncertainties of an element and their measures
    # ---------------------------------------------------------------------------------
    def _uncertainty_edges(self, element: SBase, index: ModelIndex) -> None:
        """The edges of the uncertainties of an element.

        An uncertainty is a child of the element whose value it describes
        (distrib §3.9), so the element names it, the way a reaction names its
        kinetic law, and the uncertainty names its measures.
        """
        for uncertainty in element.uncertainties:
            self.edges.append(
                Edge(
                    source=element.pk,
                    target=uncertainty.pk,
                    kind=EdgeKind.UNCERTAINTY,
                )
            )
            self._uncert_edges(uncertainty, index)

    def _uncert_edges(
        self, owner: Uncertainty | UncertParameter, index: ModelIndex
    ) -> None:
        """The edges of the parameters of an uncertainty or of a parameter.

        The owner names every parameter it carries, the way an uncertainty is
        read: the measures of one uncertainty belong together and a
        distribution is defined by the parameters below it. Every parameter
        names what it refers to itself, the element of its `var` and, for a
        span, of its `varLower` and its `varUpper` (distrib §3.11.2, §3.12),
        the unit definition of its units and the elements of its math.
        """
        for measure in owner.uncert_parameters:
            self.edges.append(
                Edge(
                    source=owner.pk,
                    target=measure.pk,
                    kind=EdgeKind.UNCERT_PARAMETER,
                )
            )
            self._edge(measure, measure.var, EdgeKind.VAR, index)
            if isinstance(measure, UncertSpan):
                self._edge(measure, measure.var_lower, EdgeKind.VAR, index)
                self._edge(measure, measure.var_upper, EdgeKind.VAR, index)
            self._units_edge(measure, measure.units, index)
            self._math_edges(measure, index)
            self._uncert_edges(measure, index)

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
        self,
        source: SBase,
        ref: SBaseRefFields,
        submodel: Submodel,
        ports: frozenset[str] = frozenset(),
    ) -> str | None:
        """The pk of the element a reference names inside a submodel.

        The reference is resolved in the model the submodel instantiates, and a
        reference which carries a reference of its own names a submodel of that
        model and goes on inside it (comp §3.7.2). Every step which does not
        resolve is logged and ends the chain. `ports` are the pks of the ports
        the resolution passes through, which end it where it runs in a circle.
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
        target = self._resolve_element(source, ref, index, ports)
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
        return self._resolve_into(source, ref.sbase_ref, nested_submodel, ports)

    def _resolve_element(
        self,
        source: SBase,
        ref: SBaseRefFields,
        index: ModelIndex,
        ports: frozenset[str] = frozenset(),
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
        return self._port_target(port, index, ports) if port is not None else target

    def _port_target(
        self, port: Port, index: ModelIndex, ports: frozenset[str] = frozenset()
    ) -> str | None:
        """The element a port names, through its nested reference where it has one.

        A port which reaches into a submodel may name a port of that submodel
        in turn. A model which instantiates itself, which libsbml reads and only
        its validation rejects, lets that chain come back to a port it already
        passed, so the resolution stops there and says so.
        """
        if port.pk in ports:
            logger.warning("reference runs in a circle through port '%s'", port.pk)
            return None
        ports = ports | {port.pk}
        target = self._resolve_element(port, port, index, ports)
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
        return self._resolve_into(port, port.sbase_ref, submodel, ports)

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
        """The edges of one replacement: its submodel, its element, its deletion.

        A replacement names two elements, the submodel it reaches into and the
        element of that submodel which is replaced (comp §3.6.2, §3.6.4), and
        both edges carry the kind of the replacement, the way a reaction and
        its species reference both carry the kind of the participation. Where
        the reference to the element cannot be resolved, because the model of
        the submodel is an external one or because the element is not part of
        it, the edge to the submodel is the only one, which is as far as the
        report can follow the replacement. A submodel reference which names no
        submodel at all is logged and leaves the replacement with the edges
        which do not depend on it.
        """
        submodel = self._replacement_submodel(replacement, kind, index)
        if submodel is not None:
            self.edges.append(
                Edge(source=replacement.pk, target=submodel.pk, kind=kind)
            )
            target = self._resolve_into(replacement, replacement, submodel)
            if target is not None:
                self.edges.append(Edge(source=replacement.pk, target=target, kind=kind))
            if isinstance(replacement, ReplacedElement):
                self._deletion_edge(replacement, submodel.pk, index)
        if isinstance(replacement, ReplacedElement):
            self._edge(
                replacement,
                replacement.conversion_factor,
                EdgeKind.CONVERSION_FACTOR,
                index,
            )

    @staticmethod
    def _replacement_submodel(
        replacement: ReplacedBy | ReplacedElement, kind: EdgeKind, index: ModelIndex
    ) -> Submodel | None:
        """The submodel a replacement reaches into, None where it names none.

        The `submodelRef` of a replacement is an SId of the containing model
        which has to name a submodel (comp §3.6.2, rule comp-21004), and a file
        can get that wrong without libsbml refusing to read it.
        """
        submodel_pk = index.resolve(replacement.submodel_ref)
        if submodel_pk is None:
            logger.warning(
                "%s of '%s' references unknown submodel '%s'",
                kind.value,
                replacement.pk,
                replacement.submodel_ref,
            )
            return None
        submodel = index.submodels.get(submodel_pk)
        if submodel is None:
            logger.warning(
                "%s of '%s' names '%s', which is no submodel",
                kind.value,
                replacement.pk,
                submodel_pk,
            )
        return submodel

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
        # can be replaced as well, and so can the objects the extensions nest
        for element in [model, *_nested(model)]:
            for carrier in _with_extensions(element):
                self._comp_edges(carrier, index)
                self._uncertainty_edges(carrier, index)

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
        if model.fbc is not None:
            self._edge(
                model, model.fbc.active_objective, EdgeKind.ACTIVE_OBJECTIVE, index
            )
        for objective in model.list_of_objectives:
            self._objective_edges(objective, index)
        for bound in model.list_of_flux_bounds:
            self._edge(bound, bound.reaction, EdgeKind.FLUX_BOUND, index)
        for constraint in model.list_of_user_defined_constraints:
            self._constraint_edges(constraint, index)
        for qs in model.list_of_qualitative_species:
            self._edge(qs, qs.compartment, EdgeKind.COMPARTMENT, index)
        for transition in model.list_of_transitions:
            self._transition_edges(transition, index)

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
        The reaction names its kinetic law as well, and the math edges start at
        the kinetic law, which holds the formula (core §4.11.5).
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
            association = reaction.fbc.gene_product_association
            if association is not None:
                self._association_edges(reaction, association, index)
        klaw = reaction.kinetic_law
        if klaw is not None:
            self.edges.append(
                Edge(source=reaction.pk, target=klaw.pk, kind=EdgeKind.KINETIC_LAW)
            )
            self._math_edges(klaw, index, kinetic_law_pk=klaw.pk)
            for lp in klaw.list_of_local_parameters:
                self._units_edge(lp, lp.units, index)

    def _constraint_edges(
        self, constraint: UserDefinedConstraint, index: ModelIndex
    ) -> None:
        """The edges of a user defined constraint and of its components.

        The constraint names the parameters which bound it, which is the same
        relation a reaction has to its flux bounds, and it names its components;
        every component names the reaction or the parameter it weighs and the
        parameter which holds its coefficient (fbc §3.14, §3.15).
        """
        self._edge(constraint, constraint.lower_bound, EdgeKind.FLUX_BOUND, index)
        self._edge(constraint, constraint.upper_bound, EdgeKind.FLUX_BOUND, index)
        for component in constraint.list_of_user_defined_constraint_components:
            self.edges.append(
                Edge(
                    source=constraint.pk,
                    target=component.pk,
                    kind=EdgeKind.CONSTRAINT_COMPONENT,
                )
            )
            self._edge(component, component.variable, EdgeKind.VARIABLE, index)
            self._edge(component, component.variable2, EdgeKind.VARIABLE, index)
            self._edge(component, component.coefficient, EdgeKind.COEFFICIENT, index)

    def _objective_edges(self, objective: Objective, index: ModelIndex) -> None:
        """The edges of an objective: its flux objectives and their reactions.

        The objective lists its terms and every term names the reaction, or in
        Version 3 the two reactions, whose flux it weighs (fbc §3.6, §3.7), the
        way a reaction names its species references and each of those a species.
        """
        for fo in objective.list_of_flux_objectives:
            self.edges.append(
                Edge(source=objective.pk, target=fo.pk, kind=EdgeKind.FLUX_OBJECTIVE)
            )
            self._edge(fo, fo.reaction, EdgeKind.FLUX_OBJECTIVE, index)
            self._edge(fo, fo.reaction2, EdgeKind.FLUX_OBJECTIVE, index)

    def _association_edges(
        self,
        reaction: Reaction,
        association: GeneProductAssociation,
        index: ModelIndex,
    ) -> None:
        """The edges of the gene product association of a reaction.

        The reaction names its association, every node of the tree names the
        nodes below it, all of them with the kind of the association, and the
        reference at a leaf names the gene product it stands for (fbc §3.9 to
        §3.13). The reference is where the file writes the identifier of the
        gene product, so that is where the `geneProduct` edge starts.
        """
        self.edges.append(
            Edge(
                source=reaction.pk,
                target=association.pk,
                kind=EdgeKind.GENE_PRODUCT_ASSOCIATION,
            )
        )
        if association.association is None:
            return
        self._association_node_edges(association.pk, association.association, index)

    def _association_node_edges(
        self, parent_pk: str, node: Association, index: ModelIndex
    ) -> None:
        """The edge from a node of an association tree to one below it."""
        self.edges.append(
            Edge(
                source=parent_pk,
                target=node.pk,
                kind=EdgeKind.GENE_PRODUCT_ASSOCIATION,
            )
        )
        if isinstance(node, GeneProductRef):
            self._edge(node, node.gene_product, EdgeKind.GENE_PRODUCT, index)
            return
        for child in node.associations:
            self._association_node_edges(node.pk, child, index)

    def _transition_edges(self, transition: Transition, index: ModelIndex) -> None:
        """The edges of a transition: its influences and its terms.

        The transition lists its inputs and its outputs and each of those names
        one qualitative species (qual §3.6.1, §3.6.2), so an influence is two
        edges of its kind, the way a participation of a reaction is: the edge
        starts where the file writes the reference, at the input and at the
        output, and the two kinds together are the influence graph of the
        model. The math of a function term names qualitative species, inputs
        and outputs, and every one of those symbols is an edge of the term.
        """
        for qual_input in transition.list_of_inputs:
            self.edges.append(
                Edge(source=transition.pk, target=qual_input.pk, kind=EdgeKind.INPUT)
            )
            self._edge(
                qual_input, qual_input.qualitative_species, EdgeKind.INPUT, index
            )
        for qual_output in transition.list_of_outputs:
            self.edges.append(
                Edge(source=transition.pk, target=qual_output.pk, kind=EdgeKind.OUTPUT)
            )
            self._edge(
                qual_output, qual_output.qualitative_species, EdgeKind.OUTPUT, index
            )
        for term in transition.list_of_function_terms:
            self.edges.append(
                Edge(source=transition.pk, target=term.pk, kind=EdgeKind.FUNCTION_TERM)
            )
            self._math_edges(term, index)
        if transition.default_term is not None:
            self.edges.append(
                Edge(
                    source=transition.pk,
                    target=transition.default_term.pk,
                    kind=EdgeKind.DEFAULT_TERM,
                )
            )

    def _event_edges(self, event: Event, index: ModelIndex) -> None:
        """The edges of an event: those of its children and of its assignments.

        The math of an event belongs to its trigger, its priority, its delay
        and its event assignments (core §4.12.2 to §4.12.5), so every math
        edge starts at the object which reads the element, not at the event
        around it, and the event names each of them the way a reaction names
        its species references.
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
            self.edges.append(
                Edge(source=event.pk, target=ea.pk, kind=EdgeKind.EVENT_ASSIGNMENT)
            )
            self._edge(ea, ea.variable, EdgeKind.VARIABLE, index)
            self._math_edges(ea, index)


def build_link_graph(report: Report, symbols: dict[str, set[str]]) -> LinkGraph:
    """The nodes and edges of a report.

    Args:
        report: the report with its models, without link graph.
        symbols: the symbols of every math, keyed by the pk of its owner.
    """
    return LinkGraphBuilder(report, symbols).build()
