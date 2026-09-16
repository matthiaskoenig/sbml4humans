"""The data model of the report.

One pydantic class per SBML object with the attributes of the specification,
the `Report` of a document and the `LinkGraph` connecting the objects. Python
uses snake_case, the JSON of the frontend camelCase (`by_alias=True`).
"""

from typing import Literal

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
