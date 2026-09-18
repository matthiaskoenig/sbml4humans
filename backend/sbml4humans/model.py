"""The data model of the report.

One pydantic class per SBML object with the attributes of the specification,
the `Report` of a document and the `LinkGraph` connecting the objects. Python
uses snake_case, the JSON of the frontend camelCase (`by_alias=True`).
"""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ReportModel(BaseModel):
    """Base of every class of the report: camelCase aliases in JSON."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# -------------------------------------------------------------------------------------
# value types
# -------------------------------------------------------------------------------------
class Math(ReportModel):
    """The math of an element as latex and as L3 formula string."""

    latex: str
    formula: str


class CVTerm(ReportModel):
    """An annotation: a qualifier (BQB or BQM of pymetadata) with its resources."""

    qualifier: str
    resources: list[str]


class Creator(ReportModel):
    """A creator of the model history."""

    given_name: str | None = None
    family_name: str | None = None
    organization: str | None = None
    email: str | None = None


class ModelHistory(ReportModel):
    """The history of an element: creators and dates."""

    creators: list[Creator] = Field(default_factory=list)
    created_date: str | None = None
    modified_dates: list[str] = Field(default_factory=list)


class SBaseRef(ReportModel):
    """A comp reference to an element by port, id, unit or metaId."""

    port_ref: str | None = None
    id_ref: str | None = None
    unit_ref: str | None = None
    meta_id_ref: str | None = None


class ReplacedBy(ReportModel):
    """The element of a submodel which replaces this element."""

    submodel_ref: str
    sbase_ref: SBaseRef


class ReplacedElement(ReportModel):
    """An element of a submodel which this element replaces."""

    submodel_ref: str
    sbase_ref: SBaseRef


class CompSBase(ReportModel):
    """The comp extension of an element."""

    replaced_by: ReplacedBy | None = None
    replaced_elements: list[ReplacedElement] = Field(default_factory=list)


class ConversionFactor(ReportModel):
    """The conversion factor parameter of a model or species."""

    sid: str
    value: float | None = None
    units: str | None = None


class Package(ReportModel):
    """An SBML package used by the document."""

    prefix: str
    version: int


# -------------------------------------------------------------------------------------
# base of the objects
# -------------------------------------------------------------------------------------
class SBase(ReportModel):
    """The attributes every SBML object shares."""

    pk: str
    sbml_type: str
    id: str | None = None
    meta_id: str | None = None
    name: str | None = None
    sbo: str | None = None
    notes: str | None = None
    cvterms: list[CVTerm] = Field(default_factory=list)
    history: ModelHistory | None = None
    xml: str | None = None
    comp: CompSBase | None = None
    uncertainties: list[Uncertainty] = Field(default_factory=list)


class UncertParameter(ReportModel):
    """A parameter of a distrib uncertainty."""

    var: str | None = None
    value: float | None = None
    units: str | None = None
    type: str | None = None
    definition_url: str | None = None
    math: Math | None = None


class Uncertainty(SBase):
    """A distrib uncertainty of an element."""

    sbml_type: Literal["Uncertainty"] = "Uncertainty"
    uncert_parameters: list[UncertParameter] = Field(default_factory=list)


SBase.model_rebuild()


# -------------------------------------------------------------------------------------
# core objects
# -------------------------------------------------------------------------------------
class SBMLDocument(SBase):
    """The document: level, version and the packages it uses."""

    sbml_type: Literal["SBMLDocument"] = "SBMLDocument"
    level: int
    version: int
    packages: list[Package] = Field(default_factory=list)


class FunctionDefinition(SBase):
    """A function definition with its lambda."""

    sbml_type: Literal["FunctionDefinition"] = "FunctionDefinition"
    math: Math | None = None


class Unit(ReportModel):
    """One factor of a unit definition: a base unit with exponent, scale and multiplier.

    A unit carries no identifier and nothing in SBML refers to it, so it is a
    nested object of its definition and not an element of the report with a
    primary key of its own.
    """

    kind: str | None = None
    exponent: float | None = None
    scale: int | None = None
    multiplier: float | None = None


class UnitDefinition(SBase):
    """A unit definition with its units and their rendered formula."""

    sbml_type: Literal["UnitDefinition"] = "UnitDefinition"
    units_latex: str | None = None
    list_of_units: list[Unit] = Field(default_factory=list)


class Compartment(SBase):
    """A compartment."""

    sbml_type: Literal["Compartment"] = "Compartment"
    spatial_dimensions: float | None = None
    size: float | None = None
    constant: bool | None = None
    units: str | None = None
    units_latex: str | None = None
    derived_units: str | None = None


class SpeciesFbc(ReportModel):
    """The fbc extension of a species."""

    chemical_formula: str | None = None
    charge: int | None = None


class Species(SBase):
    """A species."""

    sbml_type: Literal["Species"] = "Species"
    compartment: str
    initial_amount: float | None = None
    initial_concentration: float | None = None
    substance_units: str | None = None
    has_only_substance_units: bool | None = None
    boundary_condition: bool | None = None
    constant: bool | None = None
    units_latex: str | None = None
    derived_units: str | None = None
    conversion_factor: ConversionFactor | None = None
    fbc: SpeciesFbc | None = None


class Parameter(SBase):
    """A global parameter."""

    sbml_type: Literal["Parameter"] = "Parameter"
    value: float | None = None
    constant: bool | None = None
    units: str | None = None
    units_latex: str | None = None
    derived_units: str | None = None


class InitialAssignment(SBase):
    """An initial assignment of a symbol."""

    sbml_type: Literal["InitialAssignment"] = "InitialAssignment"
    symbol: str
    math: Math | None = None
    derived_units: str | None = None


class AssignmentRule(SBase):
    """An assignment rule of a variable."""

    sbml_type: Literal["AssignmentRule"] = "AssignmentRule"
    variable: str
    math: Math | None = None
    derived_units: str | None = None


class RateRule(SBase):
    """A rate rule of a variable."""

    sbml_type: Literal["RateRule"] = "RateRule"
    variable: str
    math: Math | None = None
    derived_units: str | None = None


class AlgebraicRule(SBase):
    """An algebraic rule."""

    sbml_type: Literal["AlgebraicRule"] = "AlgebraicRule"
    math: Math | None = None
    derived_units: str | None = None


Rule = Annotated[
    AssignmentRule | RateRule | AlgebraicRule, Field(discriminator="sbml_type")
]


class Constraint(SBase):
    """A constraint with its message."""

    sbml_type: Literal["Constraint"] = "Constraint"
    math: Math | None = None
    message: str | None = None


class SpeciesReference(SBase):
    """A reactant or product of a reaction."""

    sbml_type: Literal["SpeciesReference"] = "SpeciesReference"
    species: str
    stoichiometry: float | None = None
    constant: bool | None = None


class ModifierSpeciesReference(SBase):
    """A modifier of a reaction."""

    sbml_type: Literal["ModifierSpeciesReference"] = "ModifierSpeciesReference"
    species: str


class LocalParameter(SBase):
    """A local parameter of a kinetic law."""

    sbml_type: Literal["LocalParameter"] = "LocalParameter"
    value: float | None = None
    units: str | None = None
    units_latex: str | None = None
    derived_units: str | None = None


class KineticLaw(SBase):
    """The kinetic law of a reaction."""

    sbml_type: Literal["KineticLaw"] = "KineticLaw"
    math: Math | None = None
    derived_units: str | None = None
    list_of_local_parameters: list[LocalParameter] = Field(default_factory=list)


class ReactionFbc(ReportModel):
    """The fbc extension of a reaction.

    `gene_products` are the ids referenced by the association, so that the
    link graph does not parse the infix string.
    """

    lower_flux_bound: str | None = None
    upper_flux_bound: str | None = None
    gene_product_association: str | None = None
    gene_products: list[str] = Field(default_factory=list)


class Reaction(SBase):
    """A reaction with its participants and kinetic law.

    `equation` is the readable equation, its half equations joined by a plain
    unicode arrow: "⇆" (U+21C6) for a reversible reaction, "➞" (U+279E)
    otherwise.
    """

    sbml_type: Literal["Reaction"] = "Reaction"
    reversible: bool | None = None
    fast: bool | None = None
    compartment: str | None = None
    list_of_reactants: list[SpeciesReference] = Field(default_factory=list)
    list_of_products: list[SpeciesReference] = Field(default_factory=list)
    list_of_modifiers: list[ModifierSpeciesReference] = Field(default_factory=list)
    kinetic_law: KineticLaw | None = None
    equation: str
    fbc: ReactionFbc | None = None


class Trigger(SBase):
    """The trigger of an event: the condition which fires it."""

    sbml_type: Literal["Trigger"] = "Trigger"
    math: Math | None = None
    initial_value: bool | None = None
    persistent: bool | None = None


class Priority(SBase):
    """The priority of an event: the order of the events of one moment."""

    sbml_type: Literal["Priority"] = "Priority"
    math: Math | None = None


class Delay(SBase):
    """The delay of an event: the time between the trigger and the execution."""

    sbml_type: Literal["Delay"] = "Delay"
    math: Math | None = None


class EventAssignment(SBase):
    """An assignment executed by an event."""

    sbml_type: Literal["EventAssignment"] = "EventAssignment"
    variable: str
    math: Math | None = None


class Event(SBase):
    """An event with trigger, priority, delay and assignments."""

    sbml_type: Literal["Event"] = "Event"
    use_values_from_trigger_time: bool | None = None
    trigger: Trigger | None = None
    priority: Priority | None = None
    delay: Delay | None = None
    list_of_event_assignments: list[EventAssignment] = Field(default_factory=list)


# -------------------------------------------------------------------------------------
# comp
# -------------------------------------------------------------------------------------
class Submodel(SBase):
    """A comp submodel instantiating a model definition."""

    sbml_type: Literal["Submodel"] = "Submodel"
    model_ref: str
    time_conversion_factor: str | None = None
    extent_conversion_factor: str | None = None
    list_of_deletions: list[SBaseRef] = Field(default_factory=list)


class Port(SBase):
    """A comp port referencing an element of the model."""

    sbml_type: Literal["Port"] = "Port"
    port_ref: str | None = None
    id_ref: str | None = None
    unit_ref: str | None = None
    meta_id_ref: str | None = None


class ExternalModelDefinition(SBase):
    """A comp reference to a model in another document."""

    sbml_type: Literal["ExternalModelDefinition"] = "ExternalModelDefinition"
    source: str
    model_ref: str | None = None


# -------------------------------------------------------------------------------------
# fbc
# -------------------------------------------------------------------------------------
class GeneProduct(SBase):
    """An fbc gene product."""

    sbml_type: Literal["GeneProduct"] = "GeneProduct"
    label: str | None = None
    associated_species: str | None = None


class FluxObjective(ReportModel):
    """A weighted reaction of an objective."""

    reaction: str
    coefficient: float | None = None


class Objective(SBase):
    """An fbc objective."""

    sbml_type: Literal["Objective"] = "Objective"
    type: str | None = None
    list_of_flux_objectives: list[FluxObjective] = Field(default_factory=list)


# -------------------------------------------------------------------------------------
# model and report
# -------------------------------------------------------------------------------------
class Model(SBase):
    """A model or comp model definition with the lists of its elements."""

    sbml_type: Literal["Model"] = "Model"
    kind: Literal["model", "modelDefinition"] = "model"
    substance_units: str | None = None
    substance_units_latex: str | None = None
    time_units: str | None = None
    time_units_latex: str | None = None
    volume_units: str | None = None
    volume_units_latex: str | None = None
    area_units: str | None = None
    area_units_latex: str | None = None
    length_units: str | None = None
    length_units_latex: str | None = None
    extent_units: str | None = None
    extent_units_latex: str | None = None
    conversion_factor: ConversionFactor | None = None
    list_of_function_definitions: list[FunctionDefinition] = Field(default_factory=list)
    list_of_unit_definitions: list[UnitDefinition] = Field(default_factory=list)
    list_of_compartments: list[Compartment] = Field(default_factory=list)
    list_of_species: list[Species] = Field(default_factory=list)
    list_of_parameters: list[Parameter] = Field(default_factory=list)
    list_of_initial_assignments: list[InitialAssignment] = Field(default_factory=list)
    list_of_rules: list[Rule] = Field(default_factory=list)
    list_of_constraints: list[Constraint] = Field(default_factory=list)
    list_of_reactions: list[Reaction] = Field(default_factory=list)
    list_of_events: list[Event] = Field(default_factory=list)
    list_of_submodels: list[Submodel] = Field(default_factory=list)
    list_of_ports: list[Port] = Field(default_factory=list)
    list_of_gene_products: list[GeneProduct] = Field(default_factory=list)
    list_of_objectives: list[Objective] = Field(default_factory=list)


class Node(ReportModel):
    """A node of the link graph: one SBML object.

    Nodes are immutable values, so that they can be used in sets and as keys.
    """

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, frozen=True
    )

    pk: str
    sbml_type: str
    id: str | None = None
    name: str | None = None
    model: str | None = None


class EdgeKind(StrEnum):
    """The kinds of references between objects."""

    COMPARTMENT = "compartment"
    REACTANT = "reactant"
    PRODUCT = "product"
    MODIFIER = "modifier"
    VARIABLE = "variable"
    SYMBOL = "symbol"
    UNITS = "units"
    CONVERSION_FACTOR = "conversionFactor"
    FLUX_BOUND = "fluxBound"
    GENE_PRODUCT = "geneProduct"
    ASSOCIATED_SPECIES = "associatedSpecies"
    FLUX_OBJECTIVE = "fluxObjective"
    MODEL_REF = "modelRef"
    PORT = "port"
    REPLACED_BY = "replacedBy"
    REPLACED_ELEMENT = "replacedElement"
    MATH = "math"


class Edge(ReportModel):
    """A directed reference from one object to another.

    Edges are immutable values, so that they can be used in sets and as keys.
    """

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, frozen=True
    )

    source: str
    target: str
    kind: EdgeKind


class LinkGraph(ReportModel):
    """All objects of a report and the references between them."""

    nodes: dict[str, Node] = Field(default_factory=dict)
    edges: list[Edge] = Field(default_factory=list)


class Report(ReportModel):
    """The report of one SBML document."""

    document: SBMLDocument
    models: list[Model] = Field(default_factory=list)
    external_model_definitions: list[ExternalModelDefinition] = Field(
        default_factory=list
    )
    link_graph: LinkGraph = Field(default_factory=LinkGraph)


class ManifestEntry(ReportModel):
    """An entry of the manifest of a COMBINE archive."""

    location: str
    format: str
    master: bool = False


class Manifest(ReportModel):
    """The manifest of a COMBINE archive."""

    entries: list[ManifestEntry] = Field(default_factory=list)


class Debug(ReportModel):
    """Timing information of a report."""

    json_report_time: str


class ReportEntry(ReportModel):
    """The report of one SBML entry of an archive."""

    report: Report
    debug: Debug


class ReportResponse(ReportModel):
    """The response of the api: the manifest and one report per SBML entry."""

    uid: str
    manifest: Manifest
    reports: dict[str, ReportEntry]
