"""The information of an SBML document rendered by the frontend.

`SBMLDocumentInfo` walks a libsbml `SBMLDocument` and builds the typed
`Report`: one object per SBML element with its attributes, math as latex and
formula, units as latex. The symbols of every math are collected for the link
graph (`sbml4humans.links`).
"""

import hashlib
import logging
import math
from pathlib import Path
from typing import Any, Literal

import libsbml
from pymetadata.core.miriam import BQB, BQM

from sbml4humans.links import build_link_graph
from sbml4humans.mathml import math_info, math_symbols
from sbml4humans.model import (
    AlgebraicRule,
    And,
    AssignmentRule,
    Association,
    Compartment,
    CompSBase,
    Constraint,
    ConversionFactor,
    Creator,
    CVTerm,
    DefaultTerm,
    Delay,
    Deletion,
    Event,
    EventAssignment,
    ExternalModelDefinition,
    FluxBound,
    FluxObjective,
    FunctionDefinition,
    FunctionTerm,
    GeneProduct,
    GeneProductAssociation,
    GeneProductRef,
    InitialAssignment,
    Input,
    KeyValuePair,
    KineticLaw,
    LocalParameter,
    Math,
    Model,
    ModelFbc,
    ModelHistory,
    ModifierSpeciesReference,
    Objective,
    Or,
    Output,
    Package,
    Parameter,
    Port,
    Priority,
    QualitativeSpecies,
    RateRule,
    Reaction,
    ReactionFbc,
    ReplacedBy,
    ReplacedElement,
    Report,
    SBaseRef,
    SBMLDocument,
    Species,
    SpeciesFbc,
    SpeciesReference,
    Submodel,
    Transition,
    Trigger,
    Uncertainty,
    UncertMeasure,
    UncertParameter,
    UncertSpan,
    Unit,
    UnitDefinition,
    UserDefinedConstraint,
    UserDefinedConstraintComponent,
)
from sbml4humans.sbml import read_sbml
from sbml4humans.units import udef_to_string


logger = logging.getLogger(__name__)

# libsbml reports the qualifier of a CVTerm as the integer of its constant, the
# constants carry the names of the pymetadata qualifiers
MODEL_QUALIFIERS: dict[int, BQM] = {getattr(libsbml, q.value): q for q in BQM}
BIOLOGICAL_QUALIFIERS: dict[int, BQB] = {getattr(libsbml, q.value): q for q in BQB}

DOCUMENT_SCOPE = "document"

# libsbml aliases `getId()` and `isSetId()` of these classes to the attribute
# which names what they set, for compatibility with the levels in which they
# had no id: the `symbol` of an initial assignment (core §4.8.2), the
# `variable` of an assignment or rate rule (§4.9.1) and the `variable` of an
# event assignment (§4.12.5). Their id is `getIdAttribute()`.
ALIASED_ID_CLASSES = (
    libsbml.InitialAssignment,
    libsbml.Rule,
    libsbml.EventAssignment,
)

# libsbml answers the sign of an input and the transition effect of an input and
# of an output as the integer of its constant and, unlike the enumerations of
# distrib and fbc, offers no `_toString` helper for them, so the report maps them
# to the words the specification defines (qual §3.6.1, §3.6.2). The constants
# `INPUT_SIGN_VALUE_NOTSET` and the two `UNKNOWN` of the transition effects mark
# an attribute libsbml could not read as one of those words and are left out:
# they are no value of the specification, and `isSet` guards the read anyway.
INPUT_SIGNS: dict[int, str] = {
    libsbml.INPUT_SIGN_POSITIVE: "positive",
    libsbml.INPUT_SIGN_NEGATIVE: "negative",
    libsbml.INPUT_SIGN_DUAL: "dual",
    libsbml.INPUT_SIGN_UNKNOWN: "unknown",
}
INPUT_TRANSITION_EFFECTS: dict[int, str] = {
    libsbml.INPUT_TRANSITION_EFFECT_NONE: "none",
    libsbml.INPUT_TRANSITION_EFFECT_CONSUMPTION: "consumption",
}
OUTPUT_TRANSITION_EFFECTS: dict[int, str] = {
    libsbml.OUTPUT_TRANSITION_EFFECT_PRODUCTION: "production",
    libsbml.OUTPUT_TRANSITION_EFFECT_ASSIGNMENT_LEVEL: "assignmentLevel",
}

# the classes whose aliased `getId()` names a target which is unique within the
# model, so that it keys the element as long as it carries no id of its own: a
# model has at most one initial assignment per symbol and at most one rule per
# variable (core §4.8.2, §4.9.1), while two events may assign one variable
KEYED_BY_TARGET_CLASSES = (libsbml.InitialAssignment, libsbml.Rule)


def _identifier(sbase: libsbml.SBase) -> str | None:
    """The id of an element as the file carries it, None when it has none."""
    if isinstance(sbase, ALIASED_ID_CLASSES):
        return sbase.getIdAttribute() if sbase.isSetIdAttribute() else None
    return sbase.getId() if sbase.isSetId() else None


def _attribute(sbase: Any, key: str) -> Any | None:
    """The attribute `key` of a libsbml object if it is set, else None."""
    key = f"{key[0].upper()}{key[1:]}"
    if getattr(sbase, f"isSet{key}")():
        return getattr(sbase, f"get{key}")()
    return None


def _number(value: float | None) -> float | None:
    """A float attribute, NaN (not JSON) becomes None."""
    if value is None or math.isnan(value):
        return None
    return value


class SBMLDocumentInfo:
    """Builds the `Report` of an `SBMLDocument`.

    Attributes:
        doc: the document.
        report: the report after `build`.
        symbols: the symbols of every math, keyed by the pk of the object
            carrying the math (kinetic law, rule, event, ...).
    """

    def __init__(self, doc: libsbml.SBMLDocument):
        """Prepare the build of the report of the document."""
        self.doc = doc
        self.symbols: dict[str, set[str]] = {}
        self.scope = DOCUMENT_SCOPE
        self.report: Report

    @staticmethod
    def read(source: Path | str) -> libsbml.SBMLDocument:
        """Read the document of a path or an SBML string."""
        return read_sbml(source)

    @classmethod
    def from_sbml(cls, source: Path | str) -> Report:
        """The report of the document at a path or in an SBML string."""
        return cls.from_doc(cls.read(source))

    @classmethod
    def from_doc(cls, doc: libsbml.SBMLDocument) -> Report:
        """The report of a document."""
        return cls(doc).build()

    def build(self) -> Report:
        """Build the report with its link graph."""
        models: list[Model] = []
        if self.doc.isSetModel():
            models.append(self.model(self.doc.getModel(), kind="model"))
        external: list[ExternalModelDefinition] = []
        doc_comp: libsbml.CompSBMLDocumentPlugin | None = self.doc.getPlugin("comp")
        if doc_comp:
            for md in doc_comp.getListOfModelDefinitions():
                models.append(self.model(md, kind="modelDefinition"))
            self.scope = DOCUMENT_SCOPE
            for emd in doc_comp.getListOfExternalModelDefinitions():
                external.append(self.external_model_definition(emd))

        self.scope = DOCUMENT_SCOPE
        self.report = Report(
            document=self.document(),
            models=models,
            external_model_definitions=external,
        )
        self.report.link_graph = build_link_graph(self.report, self.symbols)
        return self.report

    # ---------------------------------------------------------------------------------
    # base
    # ---------------------------------------------------------------------------------
    @staticmethod
    def annotation_xml(sbase: libsbml.SBase) -> str | None:
        """The annotation element of an element as the file writes it.

        The report carries it for the document and for the model, whose own xml
        is the whole file and therefore not part of the report, so that a non
        RDF annotation on either of them stays visible (core §3.2.6).
        """
        return sbase.getAnnotationString() if sbase.isSetAnnotation() else None

    @staticmethod
    def _sbml_type(sbase: libsbml.SBase) -> str:
        """The name of the libsbml class of the element."""
        return type(sbase).__name__

    @staticmethod
    def _key(sbase: libsbml.SBase, key: str | None = None, use_id: bool = True) -> str:
        """The bare key of an element: its id, else metaId, else `key` or a digest.

        `key` is a deterministic key derived from the parent of a nested
        element without an id or metaId (a species reference, a kinetic law,
        an event assignment, an uncertainty, ...). It replaces the digest of
        the xml, which is byte identical for siblings such as two reactant
        references without ids and would otherwise collide.

        An initial assignment and a rule without an id of their own are keyed
        by the symbol or the variable they set, which a model has at most one
        of them for. That is where the report has kept them since its first
        release, and it keeps the permalink of a rule of a Level 2 document,
        where these elements cannot carry an id at all, out of the digest.

        `use_id` is False for a `LocalParameter`: its id is a genuine id,
        required by SBML, but scoped to its own kinetic law, not to the model
        (two kinetic laws may each have a local parameter of the same id), so
        `key` (which includes the kinetic law) is used for the pk instead; the
        `id` field of the report object still carries the local parameter id.
        """
        if use_id:
            identifier = _identifier(sbase)
            if identifier is not None:
                return identifier
            if isinstance(sbase, KEYED_BY_TARGET_CLASSES) and sbase.isSetId():
                return sbase.getId()
        if sbase.isSetMetaId():
            return sbase.getMetaId()
        if key is not None:
            return key
        return hashlib.sha1(sbase.toSBML().encode("utf-8")).hexdigest()

    def _pk(
        self,
        sbase: libsbml.SBase,
        scope: str | None = None,
        sbml_type: str | None = None,
        key: str | None = None,
        use_id: bool = True,
    ) -> str:
        """The primary key `<scope>/<type>:<id>` of an element.

        The type is the `sbml_type` of the report object, which differs from the
        libsbml class for a comp model definition. The id falls back to the
        metaId, then to `key` and finally to the digest of the xml.
        """
        type_ = sbml_type or self._sbml_type(sbase)
        return f"{scope or self.scope}/{type_}:{self._key(sbase, key, use_id)}"

    def sbase(
        self,
        sbase: libsbml.SBase,
        scope: str | None = None,
        sbml_type: str | None = None,
        pk: str | None = None,
        key: str | None = None,
        use_id: bool = True,
    ) -> dict[str, Any]:
        """The fields of `SBase` of an element, for the constructor of its class.

        A known pk is passed in, every other pk is built from scope and type.
        A nested element without an id or metaId uses `key`, derived from its
        parent, instead of the digest of its xml (see `_key`).
        """
        xml = None
        if sbase.getTypeCode() not in {libsbml.SBML_DOCUMENT, libsbml.SBML_MODEL}:
            xml = sbase.toSBML()
        return {
            "pk": pk
            if pk is not None
            else self._pk(sbase, scope, sbml_type, key, use_id),
            "id": _identifier(sbase),
            "meta_id": sbase.getMetaId() if sbase.isSetMetaId() else None,
            "name": sbase.getName() if sbase.isSetName() else None,
            "sbo": sbase.getSBOTermID() if sbase.isSetSBOTerm() else None,
            "notes": sbase.getNotesString() if sbase.isSetNotes() else None,
            "cvterms": self.cvterms(sbase),
            "history": self.history(sbase),
            "xml": xml,
            "comp": self.comp_sbase(sbase, self._key(sbase, key, use_id)),
            "uncertainties": self.uncertainties(sbase, self._key(sbase, key, use_id)),
            "key_value_pairs": self.key_value_pairs(sbase),
        }

    @staticmethod
    def cvterms(sbase: libsbml.SBase) -> list[CVTerm]:
        """The annotations of an element, the SBO term as BQB_IS annotation."""
        cvterms: list[CVTerm] = []
        if sbase.isSetAnnotation():
            cvterms = [
                SBMLDocumentInfo.cvterm(sbase.getCVTerm(k))
                for k in range(sbase.getNumCVTerms())
            ]

        if sbase.isSetSBOTerm():
            sbo = sbase.getSBOTermID()
            if not any(sbo in r for cv in cvterms for r in cv.resources):
                sbo_term = CVTerm(
                    qualifier=BQB.IS.value,
                    resources=[f"https://identifiers.org/{sbo}"],
                )
                cvterms.insert(0, sbo_term)
        return cvterms

    @staticmethod
    def cvterm(cv: libsbml.CVTerm) -> CVTerm:
        """One annotation with its resources and the terms which qualify it.

        A CV term can carry terms of its own, which say how the relation of the
        term above them is meant, for example the evidence for it (core §6).
        """
        q_type = cv.getQualifierType()
        if q_type == libsbml.MODEL_QUALIFIER:
            qualifier = MODEL_QUALIFIERS[cv.getModelQualifierType()].value
        elif q_type == libsbml.BIOLOGICAL_QUALIFIER:
            qualifier = BIOLOGICAL_QUALIFIERS[cv.getBiologicalQualifierType()].value
        else:
            raise ValueError(f"Unsupported qualifier type: '{q_type}'")
        return CVTerm(
            qualifier=qualifier,
            resources=[cv.getResourceURI(r) for r in range(cv.getNumResources())],
            nested=[
                SBMLDocumentInfo.cvterm(cv.getNestedCVTerm(k))
                for k in range(cv.getNumNestedCVTerms())
            ],
        )

    @staticmethod
    def history(sbase: libsbml.SBase) -> ModelHistory | None:
        """The model history of an element."""
        if not sbase.isSetModelHistory():
            return None
        history: libsbml.ModelHistory = sbase.getModelHistory()
        creators = [
            Creator(
                given_name=_attribute(c, "givenName"),
                family_name=_attribute(c, "familyName"),
                organization=_attribute(c, "organization"),
                email=_attribute(c, "email"),
            )
            for c in (history.getCreator(k) for k in range(history.getNumCreators()))
        ]
        created = (
            history.getCreatedDate().getDateAsString()
            if history.isSetCreatedDate()
            else None
        )
        modified = [
            history.getModifiedDate(k).getDateAsString()
            for k in range(history.getNumModifiedDates())
        ]
        return ModelHistory(
            creators=creators, created_date=created, modified_dates=modified
        )

    def math(self, owner_pk: str, astnode: libsbml.ASTNode | None) -> Math | None:
        """The math of an element, its symbols are recorded for the link graph."""
        if astnode is None:
            return None
        self.symbols.setdefault(owner_pk, set()).update(math_symbols(astnode))
        return math_info(astnode)

    def units(self, sid: str | None, model: libsbml.Model) -> str | None:
        """The latex rendering of a unit sid of the model."""
        return udef_to_string(sid, model) if sid else None

    @staticmethod
    def conversion_factor(sbase: Any, model: libsbml.Model) -> ConversionFactor | None:
        """The conversion factor parameter of a model or species, if set."""
        if not sbase.isSetConversionFactor():
            return None
        sid: str = sbase.getConversionFactor()
        parameter: libsbml.Parameter | None = model.getParameter(sid)
        if parameter is None:
            return ConversionFactor(sid=sid)
        return ConversionFactor(
            sid=sid,
            value=_number(_attribute(parameter, "value")),
            units=_attribute(parameter, "units"),
        )

    # ---------------------------------------------------------------------------------
    # document and model
    # ---------------------------------------------------------------------------------
    def document(self) -> SBMLDocument:
        """The document with its packages."""
        doc = self.doc
        packages = [
            Package(
                prefix=doc.getPlugin(k).getPrefix(),
                version=doc.getPlugin(k).getPackageVersion(),
            )
            for k in range(doc.getNumPlugins())
        ]
        fields = self.sbase(
            doc,
            scope=DOCUMENT_SCOPE,
            pk=f"{DOCUMENT_SCOPE}/SBMLDocument:{DOCUMENT_SCOPE}",
        )
        return SBMLDocument(
            **fields,
            level=doc.getLevel(),
            version=doc.getVersion(),
            packages=packages,
            annotation_xml=self.annotation_xml(doc),
        )

    def model(
        self, model: libsbml.Model, kind: Literal["model", "modelDefinition"]
    ) -> Model:
        """A model or model definition with the lists of its elements."""
        self.scope = self._key(model)
        fields = self.sbase(model, sbml_type="Model")
        for key in ["substance", "time", "volume", "area", "length", "extent"]:
            sid = _attribute(model, f"{key}Units")
            fields[f"{key}_units"] = sid
            fields[f"{key}_units_latex"] = self.units(sid, model)
        return Model(
            **fields,
            kind=kind,
            annotation_xml=self.annotation_xml(model),
            conversion_factor=self.conversion_factor(model, model),
            list_of_function_definitions=[
                self.function_definition(fd)
                for fd in model.getListOfFunctionDefinitions()
            ],
            list_of_unit_definitions=[
                self.unit_definition(ud) for ud in model.getListOfUnitDefinitions()
            ],
            list_of_compartments=[
                self.compartment(c, model) for c in model.getListOfCompartments()
            ],
            list_of_species=[self.species(s, model) for s in model.getListOfSpecies()],
            list_of_parameters=[
                self.parameter(p, model) for p in model.getListOfParameters()
            ],
            list_of_initial_assignments=[
                self.initial_assignment(ia)
                for ia in model.getListOfInitialAssignments()
            ],
            list_of_rules=[self.rule(r) for r in model.getListOfRules()],
            list_of_constraints=[
                self.constraint(c) for c in model.getListOfConstraints()
            ],
            list_of_reactions=[
                self.reaction(r, model) for r in model.getListOfReactions()
            ],
            list_of_events=[self.event(e) for e in model.getListOfEvents()],
            list_of_submodels=self.submodels(model),
            list_of_ports=self.ports(model),
            list_of_gene_products=self.gene_products(model),
            list_of_objectives=self.objectives(model),
            list_of_flux_bounds=self.flux_bounds(model),
            list_of_user_defined_constraints=self.user_defined_constraints(model),
            list_of_qualitative_species=self.qualitative_species(model),
            list_of_transitions=self.transitions(model),
            fbc=self.model_fbc(model),
        )

    # ---------------------------------------------------------------------------------
    # core elements
    # ---------------------------------------------------------------------------------
    def function_definition(self, fd: libsbml.FunctionDefinition) -> FunctionDefinition:
        """A function definition."""
        fields = self.sbase(fd)
        return FunctionDefinition(
            **fields, math=self.math(fields["pk"], _attribute(fd, "math"))
        )

    def unit_definition(self, ud: libsbml.UnitDefinition) -> UnitDefinition:
        """A unit definition with its units and their rendered formula."""
        return UnitDefinition(
            **self.sbase(ud),
            units_latex=udef_to_string(ud),
            list_of_units=[self.unit(u) for u in ud.getListOfUnits()],
        )

    @staticmethod
    def unit(u: libsbml.Unit) -> Unit:
        """One unit of a unit definition.

        The kind is the name of the base unit, which libsbml returns as the
        integer of its constant, and the exponent is read as a double because
        Level 3 allows a fractional one (core §4.4.2).
        """
        return Unit(
            kind=libsbml.UnitKind_toString(u.getKind()) if u.isSetKind() else None,
            exponent=_number(u.getExponentAsDouble()) if u.isSetExponent() else None,
            scale=_attribute(u, "scale"),
            multiplier=_number(_attribute(u, "multiplier")),
        )

    def compartment(self, c: libsbml.Compartment, model: libsbml.Model) -> Compartment:
        """A compartment."""
        units = _attribute(c, "units")
        # `getSpatialDimensions` truncates the fractional dimensions of L3 to an
        # unsigned int; an L2 compartment without the attribute stays unset, the
        # specification defaults it to 3
        spatial_dimensions = (
            c.getSpatialDimensionsAsDouble() if c.isSetSpatialDimensions() else None
        )
        return Compartment(
            **self.sbase(c),
            spatial_dimensions=_number(spatial_dimensions),
            size=_number(_attribute(c, "size")),
            constant=_attribute(c, "constant"),
            units=units,
            units_latex=self.units(units, model),
            derived_units=udef_to_string(c.getDerivedUnitDefinition()),
        )

    def species(self, s: libsbml.Species, model: libsbml.Model) -> Species:
        """A species."""
        substance_units = _attribute(s, "substanceUnits")
        return Species(
            **self.sbase(s),
            compartment=s.getCompartment(),
            initial_amount=_number(_attribute(s, "initialAmount")),
            initial_concentration=_number(_attribute(s, "initialConcentration")),
            substance_units=substance_units,
            has_only_substance_units=_attribute(s, "hasOnlySubstanceUnits"),
            boundary_condition=_attribute(s, "boundaryCondition"),
            constant=_attribute(s, "constant"),
            units_latex=self.units(substance_units, model),
            derived_units=udef_to_string(s.getDerivedUnitDefinition()),
            conversion_factor=self.conversion_factor(s, model),
            fbc=self.species_fbc(s),
        )

    def parameter(self, p: libsbml.Parameter, model: libsbml.Model) -> Parameter:
        """A global parameter."""
        units = _attribute(p, "units")
        return Parameter(
            **self.sbase(p),
            value=_number(_attribute(p, "value")),
            constant=_attribute(p, "constant"),
            units=units,
            units_latex=self.units(units, model),
            derived_units=udef_to_string(p.getDerivedUnitDefinition()),
        )

    def initial_assignment(self, ia: libsbml.InitialAssignment) -> InitialAssignment:
        """An initial assignment."""
        fields = self.sbase(ia)
        return InitialAssignment(
            **fields,
            symbol=ia.getSymbol(),
            math=self.math(fields["pk"], _attribute(ia, "math")),
            derived_units=udef_to_string(ia.getDerivedUnitDefinition()),
        )

    def rule(self, rule: libsbml.Rule) -> AssignmentRule | RateRule | AlgebraicRule:
        """A rule, by its libsbml class."""
        fields = self.sbase(rule)
        math_ = self.math(fields["pk"], _attribute(rule, "math"))
        derived = udef_to_string(rule.getDerivedUnitDefinition())
        if isinstance(rule, libsbml.AssignmentRule):
            return AssignmentRule(
                **fields, variable=rule.getVariable(), math=math_, derived_units=derived
            )
        if isinstance(rule, libsbml.RateRule):
            return RateRule(
                **fields, variable=rule.getVariable(), math=math_, derived_units=derived
            )
        if isinstance(rule, libsbml.AlgebraicRule):
            return AlgebraicRule(**fields, math=math_, derived_units=derived)
        raise TypeError(rule)

    def constraint(self, c: libsbml.Constraint) -> Constraint:
        """A constraint."""
        fields = self.sbase(c)
        return Constraint(
            **fields,
            math=self.math(fields["pk"], _attribute(c, "math")),
            message=c.getMessageString() if c.isSetMessage() else None,
        )

    def reaction(self, r: libsbml.Reaction, model: libsbml.Model) -> Reaction:
        """A reaction with its participants, kinetic law and fbc extension."""
        fields = self.sbase(r)
        reaction_key = self._key(r)
        return Reaction(
            **fields,
            reversible=_attribute(r, "reversible"),
            fast=_attribute(r, "fast"),
            compartment=_attribute(r, "compartment"),
            list_of_reactants=[
                self.species_reference(sr, f"{reaction_key}.reactant.{sr.getSpecies()}")
                for sr in r.getListOfReactants()
            ],
            list_of_products=[
                self.species_reference(sr, f"{reaction_key}.product.{sr.getSpecies()}")
                for sr in r.getListOfProducts()
            ],
            list_of_modifiers=[
                ModifierSpeciesReference(
                    **self.sbase(m, key=f"{reaction_key}.modifier.{m.getSpecies()}"),
                    species=m.getSpecies(),
                )
                for m in r.getListOfModifiers()
            ],
            kinetic_law=self.kinetic_law(r.getKineticLaw(), model, reaction_key)
            if r.isSetKineticLaw()
            else None,
            equation=self._equation(r),
            fbc=self.reaction_fbc(r, reaction_key),
        )

    def species_reference(
        self, sr: libsbml.SpeciesReference, key: str
    ) -> SpeciesReference:
        """A reactant or product, `key` names it within its reaction and side."""
        return SpeciesReference(
            **self.sbase(sr, key=key),
            species=sr.getSpecies(),
            stoichiometry=_number(_attribute(sr, "stoichiometry")),
            constant=_attribute(sr, "constant"),
        )

    def kinetic_law(
        self, klaw: libsbml.KineticLaw, model: libsbml.Model, reaction_key: str
    ) -> KineticLaw:
        """The kinetic law of a reaction with its local parameters."""
        kinetic_law_key = f"{reaction_key}.kineticLaw"
        fields = self.sbase(klaw, key=kinetic_law_key)
        local_parameters = []
        for lp in self._kinetic_law_parameters(klaw):
            units = _attribute(lp, "units")
            local_parameters.append(
                LocalParameter(
                    **self.sbase(
                        lp,
                        sbml_type="LocalParameter",
                        key=f"{kinetic_law_key}.{lp.getId()}",
                        use_id=False,
                    ),
                    value=_number(_attribute(lp, "value")),
                    units=units,
                    units_latex=self.units(units, model),
                    derived_units=udef_to_string(lp.getDerivedUnitDefinition()),
                )
            )
        return KineticLaw(
            **fields,
            math=self.math(fields["pk"], _attribute(klaw, "math")),
            derived_units=udef_to_string(klaw.getDerivedUnitDefinition()),
            list_of_local_parameters=local_parameters,
        )

    @staticmethod
    def _kinetic_law_parameters(klaw: libsbml.KineticLaw) -> list[libsbml.Parameter]:
        """The parameters of a kinetic law, of a document of any level.

        Level 3 writes them as `<localParameter>` in a `<listOfLocalParameters>`
        and libsbml returns them from `getListOfLocalParameters`; Level 1 and
        Level 2 write them as `<parameter>` in a `<listOfParameters>`, where
        libsbml keeps them as `Parameter` objects of `getListOfParameters` and
        leaves `getListOfLocalParameters` empty (core §4.11.5, §4.11.6). Both
        carry the id, the value and the units the report shows, so the report
        has one `LocalParameter` for either.
        """
        if klaw.getLevel() >= 3:
            return list(klaw.getListOfLocalParameters())
        return list(klaw.getListOfParameters())

    @staticmethod
    def _equation(reaction: libsbml.Reaction) -> str:
        """The readable equation: half equations and a plain unicode arrow."""
        left = SBMLDocumentInfo._half_equation(reaction.getListOfReactants())
        right = SBMLDocumentInfo._half_equation(reaction.getListOfProducts())
        sep = "⇆" if reaction.getReversible() else "➞"
        return " ".join([left, sep, right])

    @staticmethod
    def _half_equation(species_list: libsbml.ListOfSpeciesReferences) -> str:
        """The half equation of the species references.

        An unset stoichiometry is 1.0 in L2 and NaN in L3 (set by an initial
        assignment or rule targeting the id of the species reference).
        """
        items = []
        for sr in species_list:
            stoichiometry: float = sr.getStoichiometry()
            species = sr.getSpecies()
            if math.isnan(stoichiometry):
                coefficient = sr.getId() if sr.isSetId() else "?"
                items.append(f"{coefficient} {species}")
            elif abs(stoichiometry - 1.0) < 1e-8:
                items.append(species)
            elif abs(stoichiometry + 1.0) < 1e-8:
                items.append(f"-{species}")
            else:
                items.append(f"{stoichiometry} {species}")
        return " + ".join(items)

    def event(self, e: libsbml.Event) -> Event:
        """An event with trigger, priority, delay and assignments."""
        fields = self.sbase(e)
        event_key = self._key(e)
        trigger = None
        if e.isSetTrigger():
            t: libsbml.Trigger = e.getTrigger()
            trigger_fields = self.sbase(t, key=f"{event_key}.trigger")
            trigger = Trigger(
                **trigger_fields,
                math=self.math(trigger_fields["pk"], _attribute(t, "math")),
                initial_value=_attribute(t, "initialValue"),
                persistent=_attribute(t, "persistent"),
            )
        priority = None
        if e.isSetPriority():
            p: libsbml.Priority = e.getPriority()
            priority_fields = self.sbase(p, key=f"{event_key}.priority")
            priority = Priority(
                **priority_fields,
                math=self.math(priority_fields["pk"], _attribute(p, "math")),
            )
        delay = None
        if e.isSetDelay():
            d: libsbml.Delay = e.getDelay()
            delay_fields = self.sbase(d, key=f"{event_key}.delay")
            delay = Delay(
                **delay_fields,
                math=self.math(delay_fields["pk"], _attribute(d, "math")),
            )
        assignments = []
        for ea in e.getListOfEventAssignments():
            ea_fields = self.sbase(ea, key=f"{event_key}.{ea.getVariable()}")
            assignments.append(
                EventAssignment(
                    **ea_fields,
                    variable=ea.getVariable(),
                    math=self.math(ea_fields["pk"], _attribute(ea, "math")),
                )
            )
        return Event(
            **fields,
            use_values_from_trigger_time=_attribute(e, "useValuesFromTriggerTime"),
            trigger=trigger,
            priority=priority,
            delay=delay,
            list_of_event_assignments=assignments,
        )

    # ---------------------------------------------------------------------------------
    # comp
    # ---------------------------------------------------------------------------------
    def _sbase_ref_fields(self, ref: libsbml.SBaseRef, key: str) -> dict[str, Any]:
        """The fields of a comp reference, for the constructor of its class.

        A reference is an `SBase` (comp §3.7), so it carries the fields of one
        next to the four references and the reference chain below it. `key` is
        the key its parent gives it, used for the pk when the reference carries
        neither an id nor a metaId.
        """
        nested = None
        if ref.isSetSBaseRef():
            nested_key = f"{self._key(ref, key)}.sBaseRef"
            nested = SBaseRef(
                **self._sbase_ref_fields(ref.getSBaseRef(), nested_key),
            )
        return {
            **self.sbase(ref, key=key),
            "port_ref": _attribute(ref, "portRef"),
            "id_ref": _attribute(ref, "idRef"),
            "unit_ref": _attribute(ref, "unitRef"),
            "meta_id_ref": _attribute(ref, "metaIdRef"),
            "sbase_ref": nested,
        }

    def comp_sbase(self, sbase: libsbml.SBase, key: str) -> CompSBase | None:
        """The comp extension of an element: replaced by and replaced elements.

        Args:
            sbase: the element carrying the extension.
            key: the key of the element, which keys its replacements.
        """
        plugin = sbase.getPlugin("comp")
        if not plugin or not isinstance(plugin, libsbml.CompSBasePlugin):
            return None
        replaced_by = None
        if plugin.isSetReplacedBy():
            rb: libsbml.ReplacedBy = plugin.getReplacedBy()
            replaced_by = ReplacedBy(
                **self._sbase_ref_fields(rb, f"{key}.replacedBy"),
                submodel_ref=rb.getSubmodelRef(),
            )
        replaced_elements = [
            ReplacedElement(
                **self._sbase_ref_fields(re, f"{key}.replacedElement.{index}"),
                submodel_ref=re.getSubmodelRef(),
                deletion=_attribute(re, "deletion"),
                conversion_factor=_attribute(re, "conversionFactor"),
            )
            for index, re in enumerate(plugin.getListOfReplacedElements() or [])
        ]
        if replaced_by is None and not replaced_elements:
            return None
        return CompSBase(replaced_by=replaced_by, replaced_elements=replaced_elements)

    def external_model_definition(
        self, emd: libsbml.ExternalModelDefinition
    ) -> ExternalModelDefinition:
        """A comp external model definition, scoped to the document."""
        return ExternalModelDefinition(
            **self.sbase(emd, scope=DOCUMENT_SCOPE),
            source=emd.getSource(),
            model_ref=_attribute(emd, "modelRef"),
            md5=_attribute(emd, "md5"),
        )

    def submodels(self, model: libsbml.Model) -> list[Submodel]:
        """The comp submodels of a model."""
        plugin: libsbml.CompModelPlugin | None = model.getPlugin("comp")
        if not plugin:
            return []
        return [
            Submodel(
                **self.sbase(s),
                model_ref=s.getModelRef(),
                time_conversion_factor=_attribute(s, "timeConversionFactor"),
                extent_conversion_factor=_attribute(s, "extentConversionFactor"),
                list_of_deletions=[
                    Deletion(
                        **self._sbase_ref_fields(d, f"{self._key(s)}.deletion.{index}")
                    )
                    for index, d in enumerate(s.getListOfDeletions())
                ],
            )
            for s in plugin.getListOfSubmodels()
        ]

    def ports(self, model: libsbml.Model) -> list[Port]:
        """The comp ports of a model."""
        plugin: libsbml.CompModelPlugin | None = model.getPlugin("comp")
        if not plugin:
            return []
        return [
            Port(**self._sbase_ref_fields(p, self._key(p)))
            for p in plugin.getListOfPorts()
        ]

    # ---------------------------------------------------------------------------------
    # fbc
    # ---------------------------------------------------------------------------------
    def gene_products(self, model: libsbml.Model) -> list[GeneProduct]:
        """The fbc gene products of a model."""
        plugin: libsbml.FbcModelPlugin | None = model.getPlugin("fbc")
        if not plugin:
            return []
        return [
            GeneProduct(
                **self.sbase(gp),
                label=_attribute(gp, "label"),
                associated_species=_attribute(gp, "associatedSpecies"),
            )
            for gp in plugin.getListOfGeneProducts()
        ]

    def model_fbc(self, model: libsbml.Model) -> ModelFbc | None:
        """The fbc extension of a model: its strictness and its active objective.

        `strict` is required from Version 2 on and does not exist in Version 1,
        where `isSetStrict` is False, and `activeObjective` is the attribute of
        the list of objectives (fbc §3.3, §3.3.1).
        """
        plugin: libsbml.FbcModelPlugin | None = model.getPlugin("fbc")
        if not plugin:
            return None
        active = plugin.getActiveObjectiveId()
        return ModelFbc(
            strict=_attribute(plugin, "strict"),
            active_objective=active or None,
        )

    def objectives(self, model: libsbml.Model) -> list[Objective]:
        """The fbc objectives of a model with their flux objectives."""
        plugin: libsbml.FbcModelPlugin | None = model.getPlugin("fbc")
        if not plugin:
            return []
        objectives = []
        for o in plugin.getListOfObjectives():
            objective_key = self._key(o)
            objectives.append(
                Objective(
                    **self.sbase(o),
                    type=_attribute(o, "type"),
                    list_of_flux_objectives=[
                        self.flux_objective(f, objective_key)
                        for f in o.getListOfFluxObjectives()
                    ],
                )
            )
        return objectives

    def flux_objective(
        self, f: libsbml.FluxObjective, objective_key: str
    ) -> FluxObjective:
        """One term of an objective, keyed by its objective and its reaction.

        `reaction2` and `variableType` were added in Version 3, where the type
        is required; a document of an earlier version sets neither of them.
        """
        return FluxObjective(
            **self.sbase(f, key=f"{objective_key}.fluxObjective.{f.getReaction()}"),
            reaction=f.getReaction(),
            reaction2=_attribute(f, "reaction2"),
            coefficient=_number(f.getCoefficient()) if f.isSetCoefficient() else None,
            variable_type=f.getVariableTypeAsString()
            if f.isSetVariableType()
            else None,
        )

    def flux_bounds(self, model: libsbml.Model) -> list[FluxBound]:
        """The flux bounds of a model, which only fbc Version 1 has.

        libsbml keeps the list empty for a document of a later version, where
        the bounds of a reaction are the two attributes which name a parameter.
        """
        plugin: libsbml.FbcModelPlugin | None = model.getPlugin("fbc")
        if not plugin:
            return []
        return [
            FluxBound(
                **self.sbase(fb, key=f"fluxBound.{index}"),
                reaction=_attribute(fb, "reaction"),
                operation=_attribute(fb, "operation"),
                value=_number(_attribute(fb, "value")),
            )
            for index, fb in enumerate(plugin.getListOfFluxBounds())
        ]

    @staticmethod
    def key_value_pairs(sbase: libsbml.SBase) -> list[KeyValuePair]:
        """The key value pairs of an element, the controlled annotation of fbc §3.17.

        libsbml reads them from the annotation of any element of a document
        which uses fbc, whatever its version, and exposes them on the fbc
        plugin of that element. It reads the key, the value and the uri back
        from a file, but not the identifier and the name the specification
        allows, so the report carries the three attributes which survive.
        """
        plugin = sbase.getPlugin("fbc")
        if not plugin or not isinstance(plugin, libsbml.FbcSBasePlugin):
            return []
        return [
            KeyValuePair(
                key=_attribute(kvp, "key"),
                value=_attribute(kvp, "value"),
                uri=_attribute(kvp, "uri"),
            )
            for kvp in plugin.getListOfKeyValuePairs()
        ]

    @staticmethod
    def species_fbc(s: libsbml.Species) -> SpeciesFbc | None:
        """The fbc extension of a species: its chemical formula and its charge.

        fbc Version 3 widened the charge from an integer to a double, and
        libsbml keeps the two in attributes of their own: `getCharge` reads the
        integer of a Version 1 or Version 2 document and returns zero for a
        Version 3 one, `getChargeAsDouble` the other way around, so the version
        of the plugin decides which of them is the charge of the file. An
        element which sets neither attribute carries no block rather than one
        of empty values.
        """
        plugin: libsbml.FbcSpeciesPlugin | None = s.getPlugin("fbc")
        if not plugin:
            return None
        charge = None
        if plugin.isSetCharge():
            charge = (
                plugin.getChargeAsDouble()
                if plugin.getPackageVersion() >= 3
                else float(plugin.getCharge())
            )
        formula = _attribute(plugin, "chemicalFormula")
        if charge is None and formula is None:
            return None
        return SpeciesFbc(chemical_formula=formula, charge=_number(charge))

    def reaction_fbc(
        self, r: libsbml.Reaction, reaction_key: str
    ) -> ReactionFbc | None:
        """The fbc extension of a reaction: bounds and gene product association.

        A reaction which sets none of the three, which is every reaction of a
        Version 1 document, where the attributes do not exist, carries no block
        rather than one of empty values.
        """
        plugin: libsbml.FbcReactionPlugin | None = r.getPlugin("fbc")
        if not plugin:
            return None
        lower = _attribute(plugin, "lowerFluxBound")
        upper = _attribute(plugin, "upperFluxBound")
        association = self.gene_product_association(plugin, reaction_key)
        if lower is None and upper is None and association is None:
            return None
        return ReactionFbc(
            lower_flux_bound=lower,
            upper_flux_bound=upper,
            gene_product_association=association,
        )

    def user_defined_constraints(
        self, model: libsbml.Model
    ) -> list[UserDefinedConstraint]:
        """The user defined constraints of a model, which fbc Version 3 added.

        libsbml keeps the list empty for a document of an earlier version,
        which has no way to write a constraint over more than one flux.
        """
        plugin: libsbml.FbcModelPlugin | None = model.getPlugin("fbc")
        if not plugin:
            return []
        constraints = []
        for index, udc in enumerate(plugin.getListOfUserDefinedConstraints()):
            key = self._key(udc, f"userDefinedConstraint.{index}")
            constraints.append(
                UserDefinedConstraint(
                    **self.sbase(udc, key=key),
                    lower_bound=_attribute(udc, "lowerBound"),
                    upper_bound=_attribute(udc, "upperBound"),
                    list_of_user_defined_constraint_components=[
                        UserDefinedConstraintComponent(
                            **self.sbase(c, key=f"{key}.component.{position}"),
                            variable=_attribute(c, "variable"),
                            variable2=_attribute(c, "variable2"),
                            coefficient=_attribute(c, "coefficient"),
                            variable_type=c.getVariableTypeAsString()
                            if c.isSetVariableType()
                            else None,
                        )
                        for position, c in enumerate(
                            udc.getListOfUserDefinedConstraintComponents()
                        )
                    ],
                )
            )
        return constraints

    def gene_product_association(
        self, plugin: libsbml.FbcReactionPlugin, reaction_key: str
    ) -> GeneProductAssociation | None:
        """The gene product association of a reaction, as the tree of fbc §3.9.

        Args:
            plugin: the fbc extension of the reaction.
            reaction_key: the key of the reaction, which keys the association
                and, through it, every node of its tree.
        """
        if not plugin.isSetGeneProductAssociation():
            return None
        gpa: libsbml.GeneProductAssociation = plugin.getGeneProductAssociation()
        key = f"{reaction_key}.geneProductAssociation"
        association = (
            self.association(gpa.getAssociation(), f"{self._key(gpa, key)}.association")
            if gpa.isSetAssociation()
            else None
        )
        return GeneProductAssociation(
            **self.sbase(gpa, key=key), association=association
        )

    def association(self, a: libsbml.FbcAssociation, key: str) -> Association:
        """One node of an association tree, with the nodes below it.

        A node is a reference to a gene product, or an `and` or an `or` of two
        or more nodes (fbc §3.10 to §3.13). `key` is the key its parent gives
        it, used for the pk when the node carries neither an id nor a metaId.
        """
        if isinstance(a, libsbml.GeneProductRef):
            return GeneProductRef(
                **self.sbase(a, key=key), gene_product=a.getGeneProduct()
            )
        # the type of the report is the name the specification gives the element,
        # which is the name of the libsbml class without its package prefix
        if isinstance(a, libsbml.FbcAnd):
            return And(
                **self.sbase(a, sbml_type="And", key=key),
                associations=self._associations(a, key),
            )
        if isinstance(a, libsbml.FbcOr):
            return Or(
                **self.sbase(a, sbml_type="Or", key=key),
                associations=self._associations(a, key),
            )
        raise TypeError(a)

    def _associations(self, a: libsbml.FbcAssociation, key: str) -> list[Association]:
        """The nodes below an `and` or an `or`, keyed by their position.

        FbcAnd and FbcOr expose `getNumAssociations` and `getAssociation`; the
        libsbml stubs declare neither of them on the base class.
        """
        return [
            self.association(
                a.getAssociation(k),  # ty: ignore[unresolved-attribute]
                f"{self._key(a, key)}.{k}",
            )
            for k in range(a.getNumAssociations())  # ty: ignore[unresolved-attribute]
        ]

    # ---------------------------------------------------------------------------------
    # qual
    # ---------------------------------------------------------------------------------
    def qualitative_species(self, model: libsbml.Model) -> list[QualitativeSpecies]:
        """The qualitative species of a model with their levels (qual §3.5).

        `getInitialLevel` and `getMaxLevel` answer the largest integer for an
        attribute the file does not set, so the levels are read through the
        `isSet` guard of `_attribute`.
        """
        plugin: libsbml.QualModelPlugin | None = model.getPlugin("qual")
        if not plugin:
            return []
        return [
            QualitativeSpecies(
                **self.sbase(qs),
                compartment=qs.getCompartment(),
                constant=_attribute(qs, "constant"),
                initial_level=_attribute(qs, "initialLevel"),
                max_level=_attribute(qs, "maxLevel"),
            )
            for qs in plugin.getListOfQualitativeSpecies()
        ]

    def transitions(self, model: libsbml.Model) -> list[Transition]:
        """The transitions of a model with their inputs, outputs and terms.

        The identifier of a transition is optional and has no mathematical
        meaning (qual §3.6), so a transition without one is keyed by its
        position and everything below it by that key.
        """
        plugin: libsbml.QualModelPlugin | None = model.getPlugin("qual")
        if not plugin:
            return []
        transitions = []
        for index, t in enumerate(plugin.getListOfTransitions()):
            key = self._key(t, f"transition.{index}")
            transitions.append(
                Transition(
                    **self.sbase(t, key=key),
                    list_of_inputs=[
                        self.qual_input(i, f"{key}.input.{position}")
                        for position, i in enumerate(t.getListOfInputs())
                    ],
                    list_of_outputs=[
                        self.qual_output(o, f"{key}.output.{position}")
                        for position, o in enumerate(t.getListOfOutputs())
                    ],
                    list_of_function_terms=[
                        self.function_term(ft, f"{key}.functionTerm.{position}")
                        for position, ft in enumerate(t.getListOfFunctionTerms())
                    ],
                    default_term=self.default_term(t, key),
                )
            )
        return transitions

    def qual_input(self, i: libsbml.Input, key: str) -> Input:
        """One input of a transition: the species it reads and the sign of it.

        `key` names the input within its transition, used for the pk when the
        input carries neither an id nor a metaId.
        """
        return Input(
            **self.sbase(i, key=key),
            qualitative_species=i.getQualitativeSpecies(),
            threshold_level=_attribute(i, "thresholdLevel"),
            transition_effect=INPUT_TRANSITION_EFFECTS.get(i.getTransitionEffect())
            if i.isSetTransitionEffect()
            else None,
            sign=INPUT_SIGNS.get(i.getSign()) if i.isSetSign() else None,
        )

    def qual_output(self, o: libsbml.Output, key: str) -> Output:
        """One output of a transition: the species it writes and how.

        `key` names the output within its transition, used for the pk when the
        output carries neither an id nor a metaId.
        """
        return Output(
            **self.sbase(o, key=key),
            qualitative_species=o.getQualitativeSpecies(),
            output_level=_attribute(o, "outputLevel"),
            transition_effect=OUTPUT_TRANSITION_EFFECTS.get(o.getTransitionEffect())
            if o.isSetTransitionEffect()
            else None,
        )

    def function_term(self, ft: libsbml.FunctionTerm, key: str) -> FunctionTerm:
        """One function term: the level its condition results in (qual §3.6.5).

        The math is ordinary MathML and its symbols are the identifiers of
        qualitative species, of inputs and of outputs, which the link graph
        resolves in the SId namespace of the model.
        """
        fields = self.sbase(ft, key=key)
        return FunctionTerm(
            **fields,
            result_level=_attribute(ft, "resultLevel"),
            math=self.math(fields["pk"], _attribute(ft, "math")),
        )

    def default_term(
        self, t: libsbml.Transition, transition_key: str
    ) -> DefaultTerm | None:
        """The default term of a transition: its level where no term holds.

        The specification notes that the class is not derived from `SBase`,
        while libsbml gives it the full surface of one and the report reads it
        as it reads every other element (qual §3.6.4).
        """
        if not t.isSetDefaultTerm():
            return None
        dt: libsbml.DefaultTerm = t.getDefaultTerm()
        return DefaultTerm(
            **self.sbase(dt, key=f"{transition_key}.defaultTerm"),
            result_level=_attribute(dt, "resultLevel"),
        )

    # ---------------------------------------------------------------------------------
    # distrib
    # ---------------------------------------------------------------------------------
    def uncertainties(self, sbase: libsbml.SBase, parent_key: str) -> list[Uncertainty]:
        """The distrib uncertainties of an element, keyed by parent and position.

        `parent_key` is the `_key` of `sbase`, an uncertainty without an id or
        metaId is keyed by its position in the list instead of the digest of
        its xml.
        """
        plugin = sbase.getPlugin("distrib")
        if not plugin or not isinstance(plugin, libsbml.DistribSBasePlugin):
            return []
        uncertainties = []
        for index, u in enumerate(plugin.getListOfUncertainties()):
            key = f"{parent_key}.uncertainty.{index}"
            fields = self.sbase(u, key=key)
            uncertainties.append(
                Uncertainty(
                    **fields,
                    uncert_parameters=self.uncert_parameters(u, self._key(u, key)),
                )
            )
        return uncertainties

    def uncert_parameters(
        self,
        parent: libsbml.Uncertainty | libsbml.UncertParameter,
        parent_key: str,
    ) -> list[UncertMeasure]:
        """The uncert parameters of an uncertainty or of a parameter.

        A parameter of the type `distribution` or `externalParameter` carries
        the parameters which define it as a list of its own, to any depth
        (distrib §3.11.7), and a parameter whose statistic is an interval is an
        `UncertSpan` with the two ends of that interval (distrib §3.12).
        libsbml keeps both classes in one list and names each of them after its
        class, which is the name a parameter without an id is keyed by.
        """
        measures: list[UncertMeasure] = []
        for index, p in enumerate(parent.getListOfUncertParameters()):
            key = f"{parent_key}.{p.getElementName()}.{index}"
            fields = self.sbase(p, key=key)
            fields |= {
                "type": p.getTypeAsString() if p.isSetType() else None,
                "var": _attribute(p, "var"),
                "value": _number(_attribute(p, "value")),
                "units": _attribute(p, "units"),
                "definition_url": _attribute(p, "definitionURL"),
                "math": self.math(fields["pk"], _attribute(p, "math")),
                "uncert_parameters": self.uncert_parameters(p, self._key(p, key)),
            }
            if isinstance(p, libsbml.UncertSpan):
                measures.append(
                    UncertSpan(
                        **fields,
                        value_lower=_number(_attribute(p, "valueLower")),
                        value_upper=_number(_attribute(p, "valueUpper")),
                        var_lower=_attribute(p, "varLower"),
                        var_upper=_attribute(p, "varUpper"),
                    )
                )
            else:
                measures.append(UncertParameter(**fields))
        return measures
