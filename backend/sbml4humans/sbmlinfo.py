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
    AssignmentRule,
    Compartment,
    CompSBase,
    Constraint,
    ConversionFactor,
    Creator,
    CVTerm,
    Event,
    EventAssignment,
    ExternalModelDefinition,
    FunctionDefinition,
    GeneProduct,
    InitialAssignment,
    KineticLaw,
    LocalParameter,
    Math,
    Model,
    ModelHistory,
    ModifierSpeciesReference,
    Objective,
    Package,
    Parameter,
    Port,
    RateRule,
    Reaction,
    ReactionFbc,
    Report,
    SBMLDocument,
    Species,
    SpeciesFbc,
    SpeciesReference,
    Submodel,
    Trigger,
    Uncertainty,
    UnitDefinition,
)
from sbml4humans.sbml import read_sbml
from sbml4humans.units import udef_to_string


logger = logging.getLogger(__name__)

# libsbml reports the qualifier of a CVTerm as the integer of its constant, the
# constants carry the names of the pymetadata qualifiers
MODEL_QUALIFIERS: dict[int, BQM] = {getattr(libsbml, q.value): q for q in BQM}
BIOLOGICAL_QUALIFIERS: dict[int, BQB] = {getattr(libsbml, q.value): q for q in BQB}

DOCUMENT_SCOPE = "document"


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

    @classmethod
    def from_sbml(cls, source: Path | str) -> Report:
        """The report of the document at a path or in an SBML string."""
        return cls.from_doc(read_sbml(source))

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
    def _sbml_type(sbase: libsbml.SBase) -> str:
        """The name of the libsbml class of the element."""
        return type(sbase).__name__

    def _pk(self, sbase: libsbml.SBase, scope: str | None = None) -> str:
        """The primary key `<scope>/<type>:<id>` of an element.

        The id falls back to the metaId and then to the digest of the xml.
        """
        key: str
        if sbase.isSetId():
            key = sbase.getId()
        elif sbase.isSetMetaId():
            key = sbase.getMetaId()
        else:
            key = hashlib.sha1(sbase.toSBML().encode("utf-8")).hexdigest()
        return f"{scope or self.scope}/{self._sbml_type(sbase)}:{key}"

    def sbase(self, sbase: libsbml.SBase, scope: str | None = None) -> dict[str, Any]:
        """The fields of `SBase` of an element, for the constructor of its class."""
        xml = None
        if sbase.getTypeCode() not in {libsbml.SBML_DOCUMENT, libsbml.SBML_MODEL}:
            xml = sbase.toSBML()
        return {
            "pk": self._pk(sbase, scope),
            "id": sbase.getId() if sbase.isSetId() else None,
            "meta_id": sbase.getMetaId() if sbase.isSetMetaId() else None,
            "name": sbase.getName() if sbase.isSetName() else None,
            "sbo": sbase.getSBOTermID() if sbase.isSetSBOTerm() else None,
            "notes": sbase.getNotesString() if sbase.isSetNotes() else None,
            "cvterms": self.cvterms(sbase),
            "history": self.history(sbase),
            "xml": xml,
            "comp": self.comp_sbase(sbase),
            "uncertainties": self.uncertainties(sbase),
        }

    @staticmethod
    def cvterms(sbase: libsbml.SBase) -> list[CVTerm]:
        """The annotations of an element, the SBO term as BQB_IS annotation."""
        cvterms: list[CVTerm] = []
        if sbase.isSetAnnotation():
            for k in range(sbase.getNumCVTerms()):
                cv: libsbml.CVTerm = sbase.getCVTerm(k)
                q_type = cv.getQualifierType()
                if q_type == libsbml.MODEL_QUALIFIER:
                    qualifier = MODEL_QUALIFIERS[cv.getModelQualifierType()].value
                elif q_type == libsbml.BIOLOGICAL_QUALIFIER:
                    qualifier = BIOLOGICAL_QUALIFIERS[
                        cv.getBiologicalQualifierType()
                    ].value
                else:
                    raise ValueError(f"Unsupported qualifier type: '{q_type}'")
                resources = [cv.getResourceURI(r) for r in range(cv.getNumResources())]
                cvterms.append(CVTerm(qualifier=qualifier, resources=resources))

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
        fields = self.sbase(doc, scope=DOCUMENT_SCOPE)
        fields["pk"] = f"{DOCUMENT_SCOPE}/SBMLDocument:{DOCUMENT_SCOPE}"
        return SBMLDocument(
            **fields, level=doc.getLevel(), version=doc.getVersion(), packages=packages
        )

    def model(
        self, model: libsbml.Model, kind: Literal["model", "modelDefinition"]
    ) -> Model:
        """A model or model definition with the lists of its elements."""
        self.scope = (
            model.getId() if model.isSetId() else self._pk(model, DOCUMENT_SCOPE)
        )
        fields = self.sbase(model)
        for key in ["substance", "time", "volume", "area", "length", "extent"]:
            sid = _attribute(model, f"{key}Units")
            fields[f"{key}_units"] = sid
            fields[f"{key}_units_latex"] = self.units(sid, model)
        return Model(
            **fields,
            kind=kind,
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
        """A unit definition."""
        return UnitDefinition(**self.sbase(ud), units_latex=udef_to_string(ud))

    def compartment(self, c: libsbml.Compartment, model: libsbml.Model) -> Compartment:
        """A compartment."""
        units = _attribute(c, "units")
        return Compartment(
            **self.sbase(c),
            spatial_dimensions=_number(_attribute(c, "spatialDimensions")),
            size=_number(_attribute(c, "size")),
            constant=_attribute(c, "constant"),
            units=units,
            units_latex=self.units(units, model),
            derived_units=udef_to_string(c.getDerivedUnitDefinition()),
        )

    def species(self, s: libsbml.Species, model: libsbml.Model) -> Species:
        """A species."""
        units = _attribute(s, "units")
        fbc: libsbml.FbcSpeciesPlugin | None = s.getPlugin("fbc")
        species_fbc = None
        if fbc:
            charge = (
                fbc.getCharge() if fbc.isSetCharge() and fbc.getCharge() != 0 else None
            )
            species_fbc = SpeciesFbc(
                chemical_formula=_attribute(fbc, "chemicalFormula"), charge=charge
            )
        return Species(
            **self.sbase(s),
            compartment=s.getCompartment(),
            initial_amount=_number(_attribute(s, "initialAmount")),
            initial_concentration=_number(_attribute(s, "initialConcentration")),
            substance_units=_attribute(s, "substanceUnits"),
            has_only_substance_units=_attribute(s, "hasOnlySubstanceUnits"),
            boundary_condition=_attribute(s, "boundaryCondition"),
            constant=_attribute(s, "constant"),
            units=units,
            units_latex=self.units(units, model),
            derived_units=udef_to_string(s.getDerivedUnitDefinition()),
            conversion_factor=self.conversion_factor(s, model),
            fbc=species_fbc,
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
        return Reaction(
            **fields,
            reversible=_attribute(r, "reversible"),
            fast=_attribute(r, "fast"),
            compartment=_attribute(r, "compartment"),
            list_of_reactants=[
                self.species_reference(sr) for sr in r.getListOfReactants()
            ],
            list_of_products=[
                self.species_reference(sr) for sr in r.getListOfProducts()
            ],
            list_of_modifiers=[
                ModifierSpeciesReference(**self.sbase(m), species=m.getSpecies())
                for m in r.getListOfModifiers()
            ],
            kinetic_law=self.kinetic_law(r.getKineticLaw(), model)
            if r.isSetKineticLaw()
            else None,
            equation=self._equation(r),
            fbc=self.reaction_fbc(r),
        )

    def species_reference(self, sr: libsbml.SpeciesReference) -> SpeciesReference:
        """A reactant or product."""
        return SpeciesReference(
            **self.sbase(sr),
            species=sr.getSpecies(),
            stoichiometry=_number(_attribute(sr, "stoichiometry")),
            constant=_attribute(sr, "constant"),
        )

    def kinetic_law(self, klaw: libsbml.KineticLaw, model: libsbml.Model) -> KineticLaw:
        """The kinetic law of a reaction with its local parameters."""
        fields = self.sbase(klaw)
        local_parameters = []
        for lp in klaw.getListOfLocalParameters():
            units = _attribute(lp, "units")
            local_parameters.append(
                LocalParameter(
                    **self.sbase(lp),
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
    def _equation(reaction: libsbml.Reaction) -> str:
        """The readable equation: half equations and an arrow entity."""
        left = SBMLDocumentInfo._half_equation(reaction.getListOfReactants())
        right = SBMLDocumentInfo._half_equation(reaction.getListOfProducts())
        sep = "&#8646;" if reaction.getReversible() else "&#10142;"
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
        pk = fields["pk"]
        trigger = None
        if e.isSetTrigger():
            t: libsbml.Trigger = e.getTrigger()
            trigger = Trigger(
                math=self.math(pk, _attribute(t, "math")),
                initial_value=_attribute(t, "initialValue"),
                persistent=_attribute(t, "persistent"),
            )
        assignments = []
        for ea in e.getListOfEventAssignments():
            ea_fields = self.sbase(ea)
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
            priority=self.math(pk, _attribute(e.getPriority(), "math"))
            if e.isSetPriority()
            else None,
            delay=self.math(pk, _attribute(e.getDelay(), "math"))
            if e.isSetDelay()
            else None,
            list_of_event_assignments=assignments,
        )

    # ---------------------------------------------------------------------------------
    # comp, fbc, distrib (Task 5)
    # ---------------------------------------------------------------------------------
    def comp_sbase(self, sbase: libsbml.SBase) -> CompSBase | None:
        """The comp extension of an element."""
        return None

    def uncertainties(self, sbase: libsbml.SBase) -> list[Uncertainty]:
        """The distrib uncertainties of an element."""
        return []

    def external_model_definition(
        self, emd: libsbml.ExternalModelDefinition
    ) -> ExternalModelDefinition:
        """A comp external model definition."""
        return ExternalModelDefinition(
            **self.sbase(emd, scope=DOCUMENT_SCOPE),
            source=emd.getSource(),
            model_ref=_attribute(emd, "modelRef"),
        )

    def submodels(self, model: libsbml.Model) -> list[Submodel]:
        """The comp submodels of a model."""
        return []

    def ports(self, model: libsbml.Model) -> list[Port]:
        """The comp ports of a model."""
        return []

    def gene_products(self, model: libsbml.Model) -> list[GeneProduct]:
        """The fbc gene products of a model."""
        return []

    def objectives(self, model: libsbml.Model) -> list[Objective]:
        """The fbc objectives of a model."""
        return []

    def reaction_fbc(self, r: libsbml.Reaction) -> ReactionFbc | None:
        """The fbc extension of a reaction."""
        return None
