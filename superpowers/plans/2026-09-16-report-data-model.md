# Report Data Model and Link Graph Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the untyped report dictionary of `SBMLDocumentInfo` by a pydantic `Report` that mirrors the SBML objects and carries a link graph of all references, served as JSON with an exported JSON schema.

**Architecture:** `model.py` defines one pydantic class per SBML object plus `Report`, `LinkGraph`, `Node`, `Edge`. `sbmlinfo.py` walks a libsbml document and builds the objects, collecting the symbols of every math on the way. `links.py` turns the finished report into nodes and edges by resolving SIds within their model. `report.py` and `api.py` return a typed `ReportResponse`; `schema.py` writes its JSON schema for the frontend.

**Tech Stack:** Python 3.14, pydantic 2, python-libsbml, pymetadata (manifest, qualifiers), lxml (math rendering), pint (units), FastAPI, pytest, ruff, ty, uv.

**Spec:** `docs/superpowers/specs/2026-09-16-report-data-model-design.md`

## Global Constraints

- Python >= 3.14, run everything from `backend/` with `uv run ...`.
- Every module, class and function has a google style docstring and full type annotations; `uv run ruff check .`, `uv run ruff format --check .` and `uv run ty check` must pass after every task (`error-on-warning = true`, suppress only with rule specific `# ty: ignore[rule]`).
- Python field names are snake_case, JSON keys are camelCase (pydantic `alias_generator=to_camel`), dumps use `model_dump(mode="json", by_alias=True)`.
- `pk = "<model id>/<sbml_type>:<id>"`, fallback metaId, then sha1 of the element xml; `document` as model part for the document and external model definitions.
- Edges point from the referencing object to the referenced object; an unresolvable reference is logged with `logger.warning` and produces no edge.
- The api error contract stays: status 200 with `{"errors": [message, traceback], "warnings": [], "info": {...}}`.
- Commit messages: plain, no co-author lines, no em dashes. Never edit `release-notes/`.
- The current frontend is not touched except for the generated `frontend/src/schema/report.schema.json`.

---

## File structure

- Create `backend/sbml4humans/model.py`: all pydantic classes (`SBase` and the SBML objects, `Report`, `LinkGraph`, `Node`, `Edge`, `EdgeKind`, `ReportResponse`).
- Create `backend/sbml4humans/links.py`: `build_link_graph(report, symbols)`.
- Create `backend/sbml4humans/schema.py`: writes the JSON schema.
- Rewrite `backend/sbml4humans/sbmlinfo.py`: `SBMLDocumentInfo` building a `Report`.
- Modify `backend/sbml4humans/mathml.py`: add `math_info` and `math_symbols`.
- Rewrite `backend/sbml4humans/report.py`: typed `ReportResponse`.
- Modify `backend/sbml4humans/api.py`: dump the typed response.
- Tests: `backend/tests/test_model.py`, `test_links.py`, `test_schema.py`, rewrite `test_sbmlinfo.py`, adapt `test_mathml.py`, `test_report.py`, `test_api.py`.
- Generated: `frontend/src/schema/report.schema.json`. CI: `.github/workflows/ci.yml` schema job. Docs: `CLAUDE.md`.

---

### Task 1: Base classes and value types of the model

**Files:**
- Create: `backend/sbml4humans/model.py`
- Test: `backend/tests/test_model.py`

**Interfaces:**
- Produces: `ReportModel` (pydantic base with camelCase aliases), `Math`, `CVTerm`, `Creator`, `ModelHistory`, `SBaseRef`, `ReplacedBy`, `ReplacedElement`, `CompSBase`, `UncertParameter`, `Uncertainty`, `SBase`, `ConversionFactor`, `Package`.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_model.py
"""Tests of the report data model."""

from sbml4humans.model import CVTerm, Math, SBase


def test_json_uses_camel_case() -> None:
    """Fields are snake_case in python and camelCase in JSON."""
    sbase = SBase(pk="m/SBase:x", sbml_type="SBase", id="x", meta_id="meta_x")
    data = sbase.model_dump(mode="json", by_alias=True)
    assert data["metaId"] == "meta_x"
    assert data["sbmlType"] == "SBase"
    assert "meta_id" not in data


def test_validation_accepts_both_spellings() -> None:
    """JSON is validated back from the aliases and from the field names."""
    from_alias = SBase.model_validate({"pk": "p", "sbmlType": "SBase", "metaId": "m"})
    from_name = SBase.model_validate({"pk": "p", "sbml_type": "SBase", "meta_id": "m"})
    assert from_alias == from_name


def test_sbase_defaults() -> None:
    """Optional attributes default to None and the lists to empty."""
    sbase = SBase(pk="p", sbml_type="SBase")
    assert sbase.id is None
    assert sbase.cvterms == []
    assert sbase.history is None
    assert sbase.comp is None
    assert sbase.uncertainties == []


def test_math_and_cvterm() -> None:
    """Value types hold their fields."""
    math = Math(latex=r"\mathit{x}", formula="x")
    assert math.formula == "x"
    cvterm = CVTerm(qualifier="BQB_IS", resources=["https://identifiers.org/chebi/CHEBI:1"])
    assert cvterm.model_dump(mode="json", by_alias=True)["resources"] == cvterm.resources
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_model.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sbml4humans.model'`

- [ ] **Step 3: Declare pydantic as a direct dependency**

pydantic is only a transitive dependency of fastapi and pymetadata so far. Run from `backend/`:

```bash
uv add "pydantic>=2.12"
```

This adds it to `[project.dependencies]` in `backend/pyproject.toml` (move the line under the comment of the report dependencies) and updates `uv.lock`; commit both with this task.

- [ ] **Step 4: Write the base classes**

```python
# backend/sbml4humans/model.py
"""The data model of the report.

One pydantic class per SBML object with the attributes of the specification,
the `Report` of a document and the `LinkGraph` connecting the objects. Python
uses snake_case, the JSON of the frontend camelCase (`by_alias=True`).
"""

from typing import Annotated, Any, Literal

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
    uncertainties: list["Uncertainty"] = Field(default_factory=list)


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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_model.py -v && uv run ruff check . && uv run ruff format --check . && uv run ty check`
Expected: 4 passed, all checks passed. (`Annotated`, `Any` and `Literal` are used by Task 2; if ruff flags them unused now, keep only `Literal` and add the others in Task 2.)

- [ ] **Step 6: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock backend/sbml4humans/model.py backend/tests/test_model.py
git commit -m "Add the base classes and value types of the report model"
```

---

### Task 2: SBML objects, Report and link graph types

**Files:**
- Modify: `backend/sbml4humans/model.py` (append)
- Test: `backend/tests/test_model.py` (append)

**Interfaces:**
- Produces: `SBMLDocument`, `Model`, `FunctionDefinition`, `UnitDefinition`, `Compartment`, `Species`, `SpeciesFbc`, `Parameter`, `InitialAssignment`, `AssignmentRule`, `RateRule`, `AlgebraicRule`, `Rule` (union), `Constraint`, `SpeciesReference`, `ModifierSpeciesReference`, `LocalParameter`, `KineticLaw`, `ReactionFbc`, `Reaction`, `Trigger`, `EventAssignment`, `Event`, `Submodel`, `Port`, `ExternalModelDefinition`, `GeneProduct`, `FluxObjective`, `Objective`, `Node`, `EdgeKind`, `Edge`, `LinkGraph`, `Report`, `Debug`, `ReportEntry`, `ReportResponse`. Every object class has `sbml_type: Literal["<Name>"] = "<Name>"`.

- [ ] **Step 1: Write the failing tests**

```python
# append to backend/tests/test_model.py
from sbml4humans.model import (
    AlgebraicRule,
    AssignmentRule,
    Compartment,
    Edge,
    EdgeKind,
    LinkGraph,
    Model,
    Node,
    RateRule,
    Report,
    SBMLDocument,
    Species,
)


def _model() -> Model:
    """A model with one compartment and species."""
    return Model(
        pk="m/Model:m",
        id="m",
        kind="model",
        list_of_compartments=[Compartment(pk="m/Compartment:c", id="c", size=1.0)],
        list_of_species=[Species(pk="m/Species:s", id="s", compartment="c")],
        list_of_rules=[
            AssignmentRule(pk="m/AssignmentRule:r1", variable="s", math=None),
            RateRule(pk="m/RateRule:r2", variable="c", math=None),
            AlgebraicRule(pk="m/AlgebraicRule:r3", math=None),
        ],
    )


def test_sbml_type_is_fixed_per_class() -> None:
    """Every object carries its sbml type as literal."""
    species = Species(pk="m/Species:s", id="s", compartment="c")
    assert species.sbml_type == "Species"
    assert species.model_dump(mode="json", by_alias=True)["sbmlType"] == "Species"


def test_rules_are_discriminated_by_sbml_type() -> None:
    """The rules of a model validate back into their classes."""
    data = _model().model_dump(mode="json", by_alias=True)
    model = Model.model_validate(data)
    assert [type(r).__name__ for r in model.list_of_rules] == [
        "AssignmentRule",
        "RateRule",
        "AlgebraicRule",
    ]


def test_report_round_trip() -> None:
    """A report dumps to JSON and validates back unchanged."""
    graph = LinkGraph(
        nodes={
            "m/Species:s": Node(pk="m/Species:s", sbml_type="Species", id="s", model="m/Model:m"),
            "m/Compartment:c": Node(pk="m/Compartment:c", sbml_type="Compartment", id="c", model="m/Model:m"),
        },
        edges=[Edge(source="m/Species:s", target="m/Compartment:c", kind=EdgeKind.COMPARTMENT)],
    )
    report = Report(
        document=SBMLDocument(pk="document/SBMLDocument:document", level=3, version=2),
        models=[_model()],
        link_graph=graph,
    )
    data = report.model_dump(mode="json", by_alias=True)
    assert data["linkGraph"]["edges"][0]["kind"] == "compartment"
    assert data["models"][0]["listOfSpecies"][0]["compartment"] == "c"
    assert Report.model_validate(data) == report
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_model.py -v`
Expected: FAIL with `ImportError: cannot import name 'AlgebraicRule'`

- [ ] **Step 3: Append the object classes**

```python
# append to backend/sbml4humans/model.py


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


class UnitDefinition(SBase):
    """A unit definition with its rendered units."""

    sbml_type: Literal["UnitDefinition"] = "UnitDefinition"
    units_latex: str | None = None


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
    units: str | None = None
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
    """A reaction with its participants and kinetic law."""

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


class Trigger(ReportModel):
    """The trigger of an event."""

    math: Math | None = None
    initial_value: bool | None = None
    persistent: bool | None = None


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
    priority: Math | None = None
    delay: Math | None = None
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
    coefficient: float


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
    """A node of the link graph: one SBML object."""

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
    """A directed reference from one object to another."""

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
    manifest: dict[str, Any]
    reports: dict[str, ReportEntry]
```

Add `from enum import StrEnum` to the imports at the top of the module. `manifest` is the dump of the pymetadata `Manifest`, kept as a plain dictionary so that the schema of the report does not depend on the pymetadata internals.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_model.py -v && uv run ruff check . && uv run ruff format --check . && uv run ty check`
Expected: 7 passed, all checks passed.

- [ ] **Step 5: Commit**

```bash
git add backend/sbml4humans/model.py backend/tests/test_model.py
git commit -m "Add the SBML objects, the report and the link graph types"
```

---

### Task 3: Math info and symbols

**Files:**
- Modify: `backend/sbml4humans/mathml.py`
- Test: `backend/tests/test_mathml.py` (append)

**Interfaces:**
- Consumes: `Math` from `sbml4humans.model`.
- Produces: `math_info(astnode: libsbml.ASTNode) -> Math`, `math_symbols(astnode: libsbml.ASTNode) -> set[str]`.

- [ ] **Step 1: Write the failing tests**

```python
# append to backend/tests/test_mathml.py
def test_math_info() -> None:
    """The math of a node is rendered as latex and as formula."""
    astnode = libsbml.parseL3Formula("k1 * S1 / (KM + S1)")
    info = mathml.math_info(astnode)
    assert info.formula == "k1 * S1 / (KM + S1)"
    assert r"\mathit{S1}" in info.latex


def test_math_symbols() -> None:
    """The symbols of a math are the names of its ASTNodes, without functions."""
    astnode = libsbml.parseL3Formula("piecewise(f(x, 2), x > y, time)")
    assert mathml.math_symbols(astnode) == {"f", "x", "y", "time"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_mathml.py -v -k "math_info or math_symbols"`
Expected: FAIL with `AttributeError: module 'sbml4humans.mathml' has no attribute 'math_info'`

- [ ] **Step 3: Add the functions**

```python
# backend/sbml4humans/mathml.py, add to the imports
from sbml4humans.model import Math

# append at the end of the module


def math_info(astnode: libsbml.ASTNode) -> Math:
    """The math of a node as latex and as L3 formula string."""
    return Math(latex=astnode_to_latex(astnode), formula=libsbml.formulaToL3String(astnode))


def math_symbols(astnode: libsbml.ASTNode) -> set[str]:
    """The names referenced by a math: variables, function names and csymbols.

    The `time` csymbol is reported by libsbml as name `time`, it is kept and
    simply never resolves to an element.
    """
    symbols: set[str] = set()
    if astnode.isName() or astnode.isFunction() and astnode.isUserFunction():
        symbols.add(astnode.getName())
    for k in range(astnode.getNumChildren()):
        symbols |= math_symbols(astnode.getChild(k))
    return symbols
```

If `isUserFunction` does not exist on the ASTNode of the installed libsbml, use `astnode.getType() == libsbml.AST_FUNCTION` instead. The lambda arguments of a function definition are bound variables and appear as symbols too; they never resolve to an element, which is fine.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_mathml.py -v && uv run ruff check . && uv run ruff format --check . && uv run ty check`
Expected: all passed, all checks passed.

- [ ] **Step 5: Commit**

```bash
git add backend/sbml4humans/mathml.py backend/tests/test_mathml.py
git commit -m "Render math as formula and collect the symbols of a math"
```

---

### Task 4: Builder of the core objects

**Files:**
- Rewrite: `backend/sbml4humans/sbmlinfo.py`
- Rewrite: `backend/tests/test_sbmlinfo.py`

**Interfaces:**
- Consumes: the model classes of Task 2, `math_info`, `math_symbols` of Task 3, `udef_to_string` of `units.py`, `read_sbml` of `sbml.py`, `BQB`, `BQM` of pymetadata.
- Produces: `SBMLDocumentInfo` with `from_sbml(source) -> Report`, `from_doc(doc) -> Report`, `build() -> Report`, the attribute `symbols: dict[str, set[str]]` (pk of the object carrying a math to the symbols of its math) and `static _half_equation(species_list) -> str`. Comp, fbc and distrib content is added in Task 5, the link graph in Task 6.

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_sbmlinfo.py
"""Tests of the report information of a document."""

import libsbml
import pytest

from sbml4humans.model import Model, Report
from sbml4humans.resources import EXAMPLES_DIR, REPRESSILATOR_SBML
from sbml4humans.sbmlinfo import SBMLDocumentInfo


@pytest.fixture(scope="module")
def repressilator() -> Report:
    """The report of the repressilator."""
    return SBMLDocumentInfo.from_sbml(REPRESSILATOR_SBML)


def test_document(repressilator: Report) -> None:
    """The document carries level, version and its pk."""
    doc = repressilator.document
    assert doc.pk == "document/SBMLDocument:document"
    assert (doc.level, doc.version) == (2, 3)
    assert doc.xml is None


def test_model_and_lists(repressilator: Report) -> None:
    """The main model has the lists of its elements."""
    assert len(repressilator.models) == 1
    model: Model = repressilator.models[0]
    assert model.kind == "model"
    assert model.pk == "BIOMD0000000012/Model:BIOMD0000000012"
    assert [c.id for c in model.list_of_compartments] == ["cell"]
    assert [s.id for s in model.list_of_species] == ["PX", "PY", "PZ", "X", "Y", "Z"]
    assert len(model.list_of_reactions) == 12
    assert len(model.list_of_rules) == 9
    assert [u.id for u in model.list_of_unit_definitions] == ["volume", "substance", "time"]


def test_pks_are_scoped_by_model(repressilator: Report) -> None:
    """Element pks carry the model id, the type and the id."""
    species = repressilator.models[0].list_of_species[0]
    assert species.pk == "BIOMD0000000012/Species:PX"
    assert species.compartment == "cell"


def test_reaction(repressilator: Report) -> None:
    """A reaction has its participants, equation and kinetic law."""
    reaction = repressilator.models[0].list_of_reactions[0]
    assert reaction.id == "Reaction1"
    assert [r.species for r in reaction.list_of_reactants] == ["X"]
    assert reaction.list_of_products == []
    assert reaction.equation == "X &#10142; "
    assert reaction.kinetic_law is not None
    assert reaction.kinetic_law.math is not None
    assert reaction.kinetic_law.math.formula == "kd_mRNA * X"
    assert reaction.list_of_reactants[0].pk == "BIOMD0000000012/SpeciesReference:_420934"


def test_math_symbols_are_collected(repressilator: Report) -> None:
    """The symbols of every math are collected by the pk of its owner."""
    info = SBMLDocumentInfo(libsbml.readSBMLFromFile(str(REPRESSILATOR_SBML)))
    info.build()
    reaction = info.report.models[0].list_of_reactions[0]
    assert reaction.kinetic_law is not None
    assert info.symbols[reaction.kinetic_law.pk] == {"kd_mRNA", "X"}


def test_variable_stoichiometry() -> None:
    """Reactions with variable (NaN) stoichiometry get an equation."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "reaction.xml")
    equations = {r.id: r.equation for r in report.models[0].list_of_reactions}
    assert equations["v1"] == "x &#10142; y"
    assert equations["v2"] == "x &#10142; 2.0 y"
    assert equations["v3"] == "f1 x &#10142; f2 y"
    assert equations["v4"] == "v4_x x &#10142; v4_y y"


def test_nan_values_become_none() -> None:
    """NaN attributes are not JSON and are reported as unset."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "reaction.xml")
    reaction = next(r for r in report.models[0].list_of_reactions if r.id == "v3")
    assert reaction.list_of_reactants[0].stoichiometry is None


@pytest.mark.parametrize(
    "stoichiometry, expected",
    [
        (1.0, "x"),
        (-1.0, "-x"),
        (2.0, "2.0 x"),
        (-2.5, "-2.5 x"),
        (0.0, "0.0 x"),
        (float("nan"), "sr x"),
    ],
)
def test_half_equation(stoichiometry: float, expected: str) -> None:
    """Half equations for the different stoichiometries."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    reaction = model.createReaction()
    sr = reaction.createReactant()
    sr.setId("sr")
    sr.setSpecies("x")
    sr.setStoichiometry(stoichiometry)
    assert SBMLDocumentInfo._half_equation(reaction.getListOfReactants()) == expected


def test_half_equation_nan_without_id() -> None:
    """A variable stoichiometry without species reference id is marked."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    reaction = model.createReaction()
    sr = reaction.createReactant()
    sr.setSpecies("x")
    sr.setStoichiometry(float("nan"))
    assert SBMLDocumentInfo._half_equation(reaction.getListOfReactants()) == "? x"


def test_document_without_model() -> None:
    """A document without model has no models."""
    report = SBMLDocumentInfo.from_sbml(
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" version="2"/>'
    )
    assert report.models == []


def test_sbo_is_added_as_cvterm() -> None:
    """The SBO term of an element is reported as BQB_IS annotation."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "annotation.xml")
    model = report.models[0]
    annotated = [s for s in model.list_of_species if s.sbo]
    assert annotated
    species = annotated[0]
    assert any(
        cv.qualifier == "BQB_IS" and f"https://identifiers.org/{species.sbo}" in cv.resources
        for cv in species.cvterms
    )
```

Keep `test_read_sbml_from_string_and_path`, `test_read_sbml_invalid` and `test_udef_to_string` of the current file unchanged below these tests.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_sbmlinfo.py -v`
Expected: FAIL with `ImportError` (no `Report` returned yet, `from_doc` missing).

- [ ] **Step 3: Rewrite the builder**

```python
# backend/sbml4humans/sbmlinfo.py
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
from typing import Any

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
    FluxObjective,
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
    ReplacedBy,
    ReplacedElement,
    Report,
    SBase,
    SBaseRef,
    SBMLDocument,
    Species,
    SpeciesFbc,
    SpeciesReference,
    Submodel,
    Trigger,
    Uncertainty,
    UncertParameter,
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
                    qualifier = BIOLOGICAL_QUALIFIERS[cv.getBiologicalQualifierType()].value
                else:
                    raise ValueError(f"Unsupported qualifier type: '{q_type}'")
                resources = [cv.getResourceURI(r) for r in range(cv.getNumResources())]
                cvterms.append(CVTerm(qualifier=qualifier, resources=resources))

        if sbase.isSetSBOTerm():
            sbo = sbase.getSBOTermID()
            if not any(sbo in r for cv in cvterms for r in cv.resources):
                sbo_term = CVTerm(
                    qualifier=BQB.IS.value, resources=[f"https://identifiers.org/{sbo}"]
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
        created = history.getCreatedDate().getDateAsString() if history.isSetCreatedDate() else None
        modified = [
            history.getModifiedDate(k).getDateAsString()
            for k in range(history.getNumModifiedDates())
        ]
        return ModelHistory(creators=creators, created_date=created, modified_dates=modified)

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
            Package(prefix=doc.getPlugin(k).getPrefix(), version=doc.getPlugin(k).getPackageVersion())
            for k in range(doc.getNumPlugins())
        ]
        fields = self.sbase(doc, scope=DOCUMENT_SCOPE)
        fields["pk"] = f"{DOCUMENT_SCOPE}/SBMLDocument:{DOCUMENT_SCOPE}"
        return SBMLDocument(**fields, level=doc.getLevel(), version=doc.getVersion(), packages=packages)

    def model(self, model: libsbml.Model, kind: str) -> Model:
        """A model or model definition with the lists of its elements."""
        self.scope = model.getId() if model.isSetId() else self._pk(model, DOCUMENT_SCOPE)
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
                self.function_definition(fd) for fd in model.getListOfFunctionDefinitions()
            ],
            list_of_unit_definitions=[
                self.unit_definition(ud) for ud in model.getListOfUnitDefinitions()
            ],
            list_of_compartments=[self.compartment(c, model) for c in model.getListOfCompartments()],
            list_of_species=[self.species(s, model) for s in model.getListOfSpecies()],
            list_of_parameters=[self.parameter(p, model) for p in model.getListOfParameters()],
            list_of_initial_assignments=[
                self.initial_assignment(ia) for ia in model.getListOfInitialAssignments()
            ],
            list_of_rules=[self.rule(r) for r in model.getListOfRules()],
            list_of_constraints=[self.constraint(c) for c in model.getListOfConstraints()],
            list_of_reactions=[self.reaction(r, model) for r in model.getListOfReactions()],
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
        return FunctionDefinition(**fields, math=self.math(fields["pk"], _attribute(fd, "math")))

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
            charge = fbc.getCharge() if fbc.isSetCharge() and fbc.getCharge() != 0 else None
            species_fbc = SpeciesFbc(chemical_formula=_attribute(fbc, "chemicalFormula"), charge=charge)
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
            return AssignmentRule(**fields, variable=rule.getVariable(), math=math_, derived_units=derived)
        if isinstance(rule, libsbml.RateRule):
            return RateRule(**fields, variable=rule.getVariable(), math=math_, derived_units=derived)
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
            list_of_reactants=[self.species_reference(sr) for sr in r.getListOfReactants()],
            list_of_products=[self.species_reference(sr) for sr in r.getListOfProducts()],
            list_of_modifiers=[
                ModifierSpeciesReference(**self.sbase(m), species=m.getSpecies())
                for m in r.getListOfModifiers()
            ],
            kinetic_law=self.kinetic_law(r.getKineticLaw(), model) if r.isSetKineticLaw() else None,
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
            priority=self.math(pk, _attribute(e.getPriority(), "math")) if e.isSetPriority() else None,
            delay=self.math(pk, _attribute(e.getDelay(), "math")) if e.isSetDelay() else None,
            list_of_event_assignments=assignments,
        )
```

The methods `comp_sbase`, `uncertainties`, `external_model_definition`, `submodels`, `ports`, `gene_products`, `objectives` and `reaction_fbc` are added in Task 5. For this task add them as minimal stubs returning `None` or `[]` so the module imports:

```python
    # ---------------------------------------------------------------------------------
    # comp, fbc, distrib (Task 5)
    # ---------------------------------------------------------------------------------
    def comp_sbase(self, sbase: libsbml.SBase) -> CompSBase | None:
        """The comp extension of an element."""
        return None

    def uncertainties(self, sbase: libsbml.SBase) -> list[Uncertainty]:
        """The distrib uncertainties of an element."""
        return []

    def external_model_definition(self, emd: libsbml.ExternalModelDefinition) -> ExternalModelDefinition:
        """A comp external model definition."""
        return ExternalModelDefinition(**self.sbase(emd, scope=DOCUMENT_SCOPE), source=emd.getSource(), model_ref=_attribute(emd, "modelRef"))

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
```

`build` calls `build_link_graph` of Task 6. Until Task 6 exists, create `backend/sbml4humans/links.py` with the stub:

```python
"""The link graph of a report (built in Task 6)."""

from sbml4humans.model import LinkGraph, Report


def build_link_graph(report: Report, symbols: dict[str, set[str]]) -> LinkGraph:
    """The nodes and edges of the report."""
    return LinkGraph()
```

Remove `clean_empty`, `_get_sbase_attribute`, `_add_links`, `_conversion_factor`, the old `model_dict` and every old method: the file is replaced by the code above. `report.py` still expects `info.info` and `info.doc`; it breaks in this task and is rewritten in Task 7, so run only `tests/test_sbmlinfo.py`, `tests/test_model.py` and `tests/test_mathml.py` here.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_sbmlinfo.py tests/test_model.py tests/test_mathml.py -v && uv run ruff check . && uv run ruff format --check . && uv run ty check`
Expected: all passed, all checks passed. Format the long lines with `uv run ruff format .` before checking. Note: `test_reaction` asserts the pk of the first reactant of `Reaction1`; if the metaId differs, print `reaction.list_of_reactants[0].pk` once and fix the expected value, the point of the test is the `<model>/<type>:<metaId>` scheme.

- [ ] **Step 5: Commit**

```bash
git add backend/sbml4humans/sbmlinfo.py backend/sbml4humans/links.py backend/tests/test_sbmlinfo.py
git commit -m "Build the typed report of the core SBML objects"
```

---

### Task 5: Builder of comp, fbc and distrib content

**Files:**
- Modify: `backend/sbml4humans/sbmlinfo.py` (replace the stubs of Task 4)
- Test: `backend/tests/test_sbmlinfo.py` (append)

**Interfaces:**
- Produces: the comp, fbc and distrib methods listed in Task 4 with content.

- [ ] **Step 1: Write the failing tests**

```python
# append to backend/tests/test_sbmlinfo.py
from sbml4humans.resources import COMP_ICG_BODY, FBC_ECOLI_CORE_SBML


def test_comp_model_definitions() -> None:
    """Model definitions are further models of the report."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "model_definitions.xml")
    assert [(m.id, m.kind) for m in report.models] == [
        ("model_definitions", "model"),
        ("m1", "modelDefinition"),
    ]
    assert report.models[1].list_of_species[0].pk.startswith("m1/Species:")


def test_comp_submodels_ports_and_replacements() -> None:
    """Submodels, ports, external model definitions and replacements are reported."""
    report = SBMLDocumentInfo.from_sbml(COMP_ICG_BODY)
    model = report.models[0]
    assert [(s.id, s.model_ref) for s in model.list_of_submodels] == [("LI", "liver")]
    assert [(e.id, e.source, e.model_ref) for e in report.external_model_definitions] == [
        ("liver", "icg_liver.xml", "icg_liver")
    ]
    assert report.external_model_definitions[0].pk == "document/ExternalModelDefinition:liver"
    port = model.list_of_ports[0]
    assert (port.id, port.id_ref) == ("Vre_tissue_port", "Vre_tissue")
    species = next(s for s in model.list_of_species if s.id == "Cli_plasma_icg")
    assert species.comp is not None
    replaced = species.comp.replaced_elements[0]
    assert (replaced.submodel_ref, replaced.sbase_ref.port_ref) == ("LI", "icg_ext_port")


def test_fbc() -> None:
    """Flux bounds, gene product associations, gene products and objectives are reported."""
    report = SBMLDocumentInfo.from_sbml(FBC_ECOLI_CORE_SBML)
    model = report.models[0]
    reaction = next(r for r in model.list_of_reactions if r.id == "R_PFK")
    assert reaction.fbc is not None
    assert reaction.fbc.lower_flux_bound == "cobra_0_bound"
    assert reaction.fbc.upper_flux_bound == "cobra_default_ub"
    assert reaction.fbc.gene_product_association == "(b3916 or b1723)"
    assert sorted(reaction.fbc.gene_products) == ["G_b1723", "G_b3916"]
    assert len(model.list_of_gene_products) == 137
    objective = model.list_of_objectives[0]
    assert objective.id == "obj"
    assert [(f.reaction, f.coefficient) for f in objective.list_of_flux_objectives] == [
        ("R_BIOMASS_Ecoli_core_w_GAM", 1.0)
    ]


def test_distrib_uncertainties() -> None:
    """Uncertainties of the distrib package are reported with their parameters."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "distrib_uncertainties.xml")
    model = report.models[0]
    with_uncertainty = [
        e for e in model.list_of_parameters + model.list_of_species if e.uncertainties
    ]
    assert with_uncertainty
    uncertainty = with_uncertainty[0].uncertainties[0]
    assert uncertainty.sbml_type == "Uncertainty"
    assert uncertainty.uncert_parameters
    assert uncertainty.uncert_parameters[0].type is not None
```

The gene product ids `G_b3916`, `G_b1723` follow the naming of the e_coli_core model (`G_` prefix of the gene product id, the association uses the labels). If the association references the ids differently, print `reaction.fbc.gene_products` once and fix the expectation; the requirement is that the list holds the ids of the `GeneProduct` elements referenced by the association.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_sbmlinfo.py -v -k "comp or fbc or distrib"`
Expected: FAIL (empty lists and None from the stubs).

- [ ] **Step 3: Replace the stubs**

```python
    # ---------------------------------------------------------------------------------
    # comp
    # ---------------------------------------------------------------------------------
    @staticmethod
    def _sbase_ref(ref: libsbml.SBaseRef) -> SBaseRef:
        """The comp reference of an element."""
        return SBaseRef(
            port_ref=_attribute(ref, "portRef"),
            id_ref=_attribute(ref, "idRef"),
            unit_ref=_attribute(ref, "unitRef"),
            meta_id_ref=_attribute(ref, "metaIdRef"),
        )

    def comp_sbase(self, sbase: libsbml.SBase) -> CompSBase | None:
        """The comp extension of an element: replaced by and replaced elements."""
        plugin = sbase.getPlugin("comp")
        if not plugin or not isinstance(plugin, libsbml.CompSBasePlugin):
            return None
        replaced_by = None
        if plugin.isSetReplacedBy():
            rb: libsbml.ReplacedBy = plugin.getReplacedBy()
            replaced_by = ReplacedBy(submodel_ref=rb.getSubmodelRef(), sbase_ref=self._sbase_ref(rb))
        replaced_elements = [
            ReplacedElement(submodel_ref=re.getSubmodelRef(), sbase_ref=self._sbase_ref(re))
            for re in plugin.getListOfReplacedElements()
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
                list_of_deletions=[self._sbase_ref(d) for d in s.getListOfDeletions()],
            )
            for s in plugin.getListOfSubmodels()
        ]

    def ports(self, model: libsbml.Model) -> list[Port]:
        """The comp ports of a model."""
        plugin: libsbml.CompModelPlugin | None = model.getPlugin("comp")
        if not plugin:
            return []
        return [
            Port(**self.sbase(p), **self._sbase_ref(p).model_dump())
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

    def objectives(self, model: libsbml.Model) -> list[Objective]:
        """The fbc objectives of a model."""
        plugin: libsbml.FbcModelPlugin | None = model.getPlugin("fbc")
        if not plugin:
            return []
        return [
            Objective(
                **self.sbase(o),
                type=_attribute(o, "type"),
                list_of_flux_objectives=[
                    FluxObjective(reaction=f.getReaction(), coefficient=f.getCoefficient())
                    for f in o.getListOfFluxObjectives()
                ],
            )
            for o in plugin.getListOfObjectives()
        ]

    def reaction_fbc(self, r: libsbml.Reaction) -> ReactionFbc | None:
        """The fbc extension of a reaction: bounds and gene product association."""
        plugin: libsbml.FbcReactionPlugin | None = r.getPlugin("fbc")
        if not plugin:
            return None
        association = None
        gene_products: list[str] = []
        if plugin.isSetGeneProductAssociation():
            root: libsbml.FbcAssociation = plugin.getGeneProductAssociation().getAssociation()
            association = root.toInfix()
            gene_products = sorted(self._gene_product_refs(root))
        return ReactionFbc(
            lower_flux_bound=_attribute(plugin, "lowerFluxBound"),
            upper_flux_bound=_attribute(plugin, "upperFluxBound"),
            gene_product_association=association,
            gene_products=gene_products,
        )

    @staticmethod
    def _gene_product_refs(association: libsbml.FbcAssociation) -> set[str]:
        """The gene product ids referenced by an association tree."""
        if isinstance(association, libsbml.GeneProductRef):
            return {association.getGeneProduct()}
        refs: set[str] = set()
        for k in range(association.getNumAssociations()):
            refs |= SBMLDocumentInfo._gene_product_refs(association.getAssociation(k))
        return refs

    # ---------------------------------------------------------------------------------
    # distrib
    # ---------------------------------------------------------------------------------
    def uncertainties(self, sbase: libsbml.SBase) -> list[Uncertainty]:
        """The distrib uncertainties of an element."""
        plugin = sbase.getPlugin("distrib")
        if not plugin or not isinstance(plugin, libsbml.DistribSBasePlugin):
            return []
        uncertainties = []
        for u in plugin.getListOfUncertainties():
            fields = self.sbase(u)
            parameters = [
                UncertParameter(
                    var=_attribute(p, "var"),
                    value=_number(_attribute(p, "value")),
                    units=_attribute(p, "units"),
                    type=p.getTypeAsString() if p.isSetType() else None,
                    definition_url=_attribute(p, "definitionURL"),
                    math=self.math(fields["pk"], _attribute(p, "math")),
                )
                for p in u.getListOfUncertParameters()
            ]
            uncertainties.append(Uncertainty(**fields, uncert_parameters=parameters))
        return uncertainties
```

`FbcAnd` and `FbcOr` expose `getNumAssociations()` and `getAssociation(k)`; `GeneProductRef` does not, which is why it is checked first. `Port(**self.sbase(p), **self._sbase_ref(p).model_dump())` works because `Port` has exactly the four reference fields of `SBaseRef` (snake_case dump, `populate_by_name=True`).

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_sbmlinfo.py tests/test_model.py tests/test_mathml.py -v && uv run ruff format . && uv run ruff check . && uv run ty check`
Expected: all passed, all checks passed.

- [ ] **Step 5: Commit**

```bash
git add backend/sbml4humans/sbmlinfo.py backend/tests/test_sbmlinfo.py
git commit -m "Report the comp, fbc and distrib content of a document"
```

---

### Task 6: Link graph

**Files:**
- Rewrite: `backend/sbml4humans/links.py`
- Test: `backend/tests/test_links.py`

**Interfaces:**
- Consumes: `Report`, `Model`, `Node`, `Edge`, `EdgeKind`, `LinkGraph` of Task 2; `symbols: dict[str, set[str]]` of Task 4.
- Produces: `build_link_graph(report: Report, symbols: dict[str, set[str]]) -> LinkGraph`.

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_links.py
"""Tests of the link graph."""

import logging

import pytest

from sbml4humans.model import Edge, EdgeKind, Report
from sbml4humans.resources import COMP_ICG_BODY, EXAMPLES_DIR, FBC_ECOLI_CORE_SBML, REPRESSILATOR_SBML
from sbml4humans.sbmlinfo import SBMLDocumentInfo


def _edges(report: Report, source: str | None = None, kind: EdgeKind | None = None) -> set[tuple[str, str, str]]:
    """The edges of the report as tuples, filtered by source and kind."""
    return {
        (e.source, e.target, e.kind.value)
        for e in report.link_graph.edges
        if (source is None or e.source == source) and (kind is None or e.kind == kind)
    }


@pytest.fixture(scope="module")
def repressilator() -> Report:
    """The report of the repressilator."""
    return SBMLDocumentInfo.from_sbml(REPRESSILATOR_SBML)


def test_every_sbase_is_a_node(repressilator: Report) -> None:
    """Document, model, elements and nested elements are nodes."""
    nodes = repressilator.link_graph.nodes
    model = repressilator.models[0]
    assert repressilator.document.pk in nodes
    assert model.pk in nodes
    assert nodes[model.pk].model is None
    species = model.list_of_species[0]
    assert nodes[species.pk].model == model.pk
    assert nodes[species.pk].sbml_type == "Species"
    reaction = model.list_of_reactions[0]
    assert reaction.list_of_reactants[0].pk in nodes
    assert reaction.kinetic_law is not None
    assert reaction.kinetic_law.pk in nodes


def test_edges_reference_nodes(repressilator: Report) -> None:
    """Every edge connects two existing nodes."""
    nodes = repressilator.link_graph.nodes
    for edge in repressilator.link_graph.edges:
        assert edge.source in nodes
        assert edge.target in nodes


def test_reaction_edges(repressilator: Report) -> None:
    """A reaction links to its species and the symbols of its kinetic law."""
    m = "BIOMD0000000012"
    reaction = f"{m}/Reaction:Reaction1"
    assert _edges(repressilator, source=reaction) == {
        (reaction, f"{m}/Species:X", "reactant"),
    }
    kinetic_law = repressilator.models[0].list_of_reactions[0].kinetic_law
    assert kinetic_law is not None
    assert _edges(repressilator, source=kinetic_law.pk) == {
        (kinetic_law.pk, f"{m}/Parameter:kd_mRNA", "math"),
        (kinetic_law.pk, f"{m}/Species:X", "math"),
    }


def test_species_and_rule_edges(repressilator: Report) -> None:
    """Species link to their compartment, rules to their variable and symbols."""
    m = "BIOMD0000000012"
    assert (f"{m}/Species:PX", f"{m}/Compartment:cell", "compartment") in _edges(repressilator)
    variable_edges = _edges(repressilator, kind=EdgeKind.VARIABLE)
    assert len(variable_edges) == 9
    assert all(t.startswith(f"{m}/Parameter:") for _, t, _ in variable_edges)
    assert _edges(repressilator, kind=EdgeKind.MATH)


def test_units_edges(repressilator: Report) -> None:
    """Units attributes link to the unit definitions of the model."""
    m = "BIOMD0000000012"
    units_edges = _edges(repressilator, kind=EdgeKind.UNITS)
    assert units_edges
    assert all(t.startswith(f"{m}/UnitDefinition:") for _, t, _ in units_edges)


def test_comp_edges() -> None:
    """Submodels, ports and replacements are edges."""
    report = SBMLDocumentInfo.from_sbml(COMP_ICG_BODY)
    m = "icg_body"
    assert (f"{m}/Submodel:LI", "document/ExternalModelDefinition:liver", "modelRef") in _edges(report)
    assert (f"{m}/Port:Vre_tissue_port", f"{m}/Compartment:Vre_tissue", "port") in _edges(report)
    assert (f"{m}/Species:Cli_plasma_icg", f"{m}/Submodel:LI", "replacedElement") in _edges(report)


def test_fbc_edges() -> None:
    """Flux bounds, gene products, associated species and objectives are edges."""
    report = SBMLDocumentInfo.from_sbml(FBC_ECOLI_CORE_SBML)
    m = "e_coli_core"
    reaction = f"{m}/Reaction:R_PFK"
    edges = _edges(report, source=reaction)
    assert (reaction, f"{m}/Parameter:cobra_0_bound", "fluxBound") in edges
    assert (reaction, f"{m}/Parameter:cobra_default_ub", "fluxBound") in edges
    assert (reaction, f"{m}/GeneProduct:G_b3916", "geneProduct") in edges
    assert (f"{m}/Objective:obj", f"{m}/Reaction:R_BIOMASS_Ecoli_core_w_GAM", "fluxObjective") in _edges(report)


def test_dangling_reference_is_logged(caplog: pytest.LogCaptureFixture) -> None:
    """An unresolvable reference produces no edge and a warning."""
    sbml = """<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" version="2">
      <model id="m">
        <listOfCompartments><compartment id="c" constant="true"/></listOfCompartments>
        <listOfSpecies><species id="s" compartment="missing" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/></listOfSpecies>
      </model>
    </sbml>"""
    with caplog.at_level(logging.WARNING, logger="sbml4humans.links"):
        report = SBMLDocumentInfo.from_sbml(sbml)
    assert _edges(report, kind=EdgeKind.COMPARTMENT) == set()
    assert "missing" in caplog.text


def test_edge_is_hashable_value() -> None:
    """Edges compare by value."""
    assert Edge(source="a", target="b", kind=EdgeKind.MATH) == Edge(source="a", target="b", kind=EdgeKind.MATH)
```

`units` edges of the repressilator: the model defines `volume`, `substance` and `time`, which redefine the default units of L2. Compartments and species of L2 models reference them implicitly, so if no `units` attribute is set in the file the `units_edges` set may be empty; in that case change `test_units_edges` to use `EXAMPLES_DIR / "reaction_with_units.xml"` and the model id of that file.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_links.py -v`
Expected: FAIL (the stub returns an empty graph).

- [ ] **Step 3: Write the graph builder**

```python
# backend/sbml4humans/links.py
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
    Node,
    Reaction,
    Report,
    SBase,
    SBaseRef,
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
    """All nodes of a model: every element, kinetic laws and local parameters."""
    yield from model.list_of_unit_definitions
    yield from _elements(model)
    for reaction in model.list_of_reactions:
        if reaction.kinetic_law is not None:
            yield reaction.kinetic_law
            yield from reaction.kinetic_law.list_of_local_parameters


def _uncertainties(sbase: SBase) -> Iterator[SBase]:
    """The uncertainty nodes of an element."""
    yield from sbase.uncertainties


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
            pk=sbase.pk, sbml_type=sbase.sbml_type, id=sbase.id, name=sbase.name, model=model_pk
        )
        for uncertainty in _uncertainties(sbase):
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
    def _edge(self, source: SBase, sid: str | None, kind: EdgeKind, index: ModelIndex, kinetic_law_pk: str | None = None) -> None:
        """Add the edge for a reference, log when the reference does not resolve."""
        if sid is None:
            return
        target = index.resolve(sid, kinetic_law_pk)
        if target is None:
            logger.warning("%s of '%s' references unknown '%s'", kind.value, source.pk, sid)
            return
        self.edges.append(Edge(source=source.pk, target=target, kind=kind))

    def _units_edge(self, source: SBase, sid: str | None, index: ModelIndex) -> None:
        """Add the units edge when the sid is a unit definition of the model."""
        if sid is not None and sid in index.units:
            self.edges.append(Edge(source=source.pk, target=index.units[sid], kind=EdgeKind.UNITS))

    def _math_edges(self, source: SBase, index: ModelIndex, kinetic_law_pk: str | None = None) -> None:
        """Add the math edges for the symbols of the math of the source."""
        for symbol in sorted(self.symbols.get(source.pk, set())):
            target = index.resolve(symbol, kinetic_law_pk)
            if target is not None:
                self.edges.append(Edge(source=source.pk, target=target, kind=EdgeKind.MATH))

    def _comp_edges(self, source: SBase, index: ModelIndex) -> None:
        """Add the replacement edges of an element."""
        if source.comp is None:
            return
        if source.comp.replaced_by is not None:
            self._edge(source, source.comp.replaced_by.submodel_ref, EdgeKind.REPLACED_BY, index)
        for replaced in source.comp.replaced_elements:
            self._edge(source, replaced.submodel_ref, EdgeKind.REPLACED_ELEMENT, index)

    def _model_edges(self, model: Model) -> None:
        """The edges of all elements of a model."""
        index = self.indices[model.pk]
        for key in ["substance", "time", "volume", "area", "length", "extent"]:
            self._units_edge(model, getattr(model, f"{key}_units"), index)
        if model.conversion_factor is not None:
            self._edge(model, model.conversion_factor.sid, EdgeKind.CONVERSION_FACTOR, index)

        for fd in model.list_of_function_definitions:
            self._math_edges(fd, index)
        for c in model.list_of_compartments:
            self._units_edge(c, c.units, index)
            self._comp_edges(c, index)
        for s in model.list_of_species:
            self._edge(s, s.compartment, EdgeKind.COMPARTMENT, index)
            self._units_edge(s, s.units, index)
            if s.conversion_factor is not None:
                self._edge(s, s.conversion_factor.sid, EdgeKind.CONVERSION_FACTOR, index)
            self._comp_edges(s, index)
        for p in model.list_of_parameters:
            self._units_edge(p, p.units, index)
            self._comp_edges(p, index)
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
                logger.warning("modelRef of '%s' references unknown '%s'", submodel.pk, submodel.model_ref)
            else:
                self.edges.append(Edge(source=submodel.pk, target=target, kind=EdgeKind.MODEL_REF))
        for port in model.list_of_ports:
            self._edge(port, port.id_ref, EdgeKind.PORT, index)
            if port.unit_ref is not None:
                self._units_edge(port, port.unit_ref, index)
            self._meta_id_edge(port, port.meta_id_ref, model)
        for gp in model.list_of_gene_products:
            self._edge(gp, gp.associated_species, EdgeKind.ASSOCIATED_SPECIES, index)
        for objective in model.list_of_objectives:
            for fo in objective.list_of_flux_objectives:
                self._edge(objective, fo.reaction, EdgeKind.FLUX_OBJECTIVE, index)

    def _meta_id_edge(self, port: SBase, meta_id: str | None, model: Model) -> None:
        """A port referencing an element by metaId."""
        if meta_id is None:
            return
        for element in _nested(model):
            if element.meta_id == meta_id:
                self.edges.append(Edge(source=port.pk, target=element.pk, kind=EdgeKind.PORT))
                return
        logger.warning("port of '%s' references unknown metaId '%s'", port.pk, meta_id)

    def _reaction_edges(self, reaction: Reaction, index: ModelIndex) -> None:
        """The edges of a reaction, its participants and its kinetic law."""
        self._edge(reaction, reaction.compartment, EdgeKind.COMPARTMENT, index)
        for sr in reaction.list_of_reactants:
            self._edge(reaction, sr.species, EdgeKind.REACTANT, index)
        for sr in reaction.list_of_products:
            self._edge(reaction, sr.species, EdgeKind.PRODUCT, index)
        for m in reaction.list_of_modifiers:
            self._edge(reaction, m.species, EdgeKind.MODIFIER, index)
        self._comp_edges(reaction, index)
        if reaction.fbc is not None:
            self._edge(reaction, reaction.fbc.lower_flux_bound, EdgeKind.FLUX_BOUND, index)
            self._edge(reaction, reaction.fbc.upper_flux_bound, EdgeKind.FLUX_BOUND, index)
            for gene_product in reaction.fbc.gene_products:
                self._edge(reaction, gene_product, EdgeKind.GENE_PRODUCT, index)
        klaw = reaction.kinetic_law
        if klaw is not None:
            self._math_edges(klaw, index, kinetic_law_pk=klaw.pk)
            for lp in klaw.list_of_local_parameters:
                self._units_edge(lp, lp.units, index)

    def _event_edges(self, event: Event, index: ModelIndex) -> None:
        """The edges of an event: the symbols of trigger, priority and delay, the assignments."""
        self._math_edges(event, index)
        self._comp_edges(event, index)
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
```

The `SBaseRef` import is unused if ty or ruff say so: remove it. `_edge` on a rule uses `getattr(rule, "variable", None)` because algebraic rules have no variable.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_links.py tests/test_sbmlinfo.py tests/test_model.py tests/test_mathml.py -v && uv run ruff format . && uv run ruff check . && uv run ty check`
Expected: all passed, all checks passed. `test_species_and_rule_edges` assumes that all 9 rules of the repressilator target parameters; if some target species, replace the `all(...)` line by `assert variable_edges` and keep the count. If `test_reaction_edges` reports an extra edge (for example the `time` symbol or a `units` edge from a kinetic law), inspect the printed set once: `math` edges must contain exactly the resolvable symbols of the math, nothing else.

- [ ] **Step 5: Commit**

```bash
git add backend/sbml4humans/links.py backend/tests/test_links.py
git commit -m "Build the link graph of a report"
```

---

### Task 7: Typed report response in report.py and api.py

**Files:**
- Rewrite: `backend/sbml4humans/report.py`
- Modify: `backend/sbml4humans/api.py:110-150`
- Modify: `backend/tests/test_report.py`, `backend/tests/test_api.py`

**Interfaces:**
- Consumes: `SBMLDocumentInfo.from_sbml`, `Report`, `ReportEntry`, `ReportResponse`, `Debug`.
- Produces: `report_for_sbml(source, uid="") -> ReportEntry`, `report_for_path(path) -> ReportResponse`, `report_for_bytes(content) -> ReportResponse`. The api dumps with `model_dump(mode="json", by_alias=True)`.

- [ ] **Step 1: Update the tests**

In `backend/tests/test_report.py` replace `_check_report` and the tests reading dictionary keys:

```python
from sbml4humans.model import ReportResponse


def _check_report(response: ReportResponse) -> None:
    """Check the structure of the report response of a path."""
    assert len(response.uid) == 32
    assert response.manifest["entries"]
    assert response.reports
    for location, entry in response.reports.items():
        assert location.startswith("./")
        assert entry.report.document.level in {1, 2, 3}
        assert entry.debug.json_report_time.endswith(" [s]")


def test_report_for_sbml_file() -> None:
    """A single SBML file is wrapped in an archive with one master model."""
    response = report_for_path(REPRESSILATOR_SBML)
    assert list(response.reports) == ["./model.xml"]
    assert response.reports["./model.xml"].report.models[0].id == "BIOMD0000000012"


def test_report_for_omex_has_all_sbml_entries() -> None:
    """Every SBML entry of an archive gets its own report."""
    response = report_for_path(OMEX_ICGMODEL)
    assert len(response.reports) == 3
    assert "./models/icg_body.xml" in response.reports


def test_report_for_sbml_string() -> None:
    """Report data is created from an SBML string."""
    entry = report_for_sbml(REPRESSILATOR_SBML.read_text(encoding="utf-8"))
    assert entry.report.models[0].id == "BIOMD0000000012"
    assert entry.debug.json_report_time.endswith(" [s]")


def test_report_json_is_camel_case() -> None:
    """The JSON of a response uses camelCase keys."""
    data = report_for_path(REPRESSILATOR_SBML).model_dump(mode="json", by_alias=True)
    report = data["reports"]["./model.xml"]["report"]
    assert set(report) == {"document", "models", "externalModelDefinitions", "linkGraph"}
    assert report["models"][0]["listOfSpecies"][0]["sbmlType"] == "Species"
    assert data["reports"]["./model.xml"]["debug"]["jsonReportTime"].endswith(" [s]")
```

`test_report_for_bytes_*` and `test_uid_differs_between_reports` use `response.uid`/`response.reports` instead of `data["uid"]`/`data["reports"]`. `test_report_for_bytes_gzipped_sbml` asserts `list(response.reports) == ["./model.xml"]`.

In `backend/tests/test_api.py` replace `_check_report`:

```python
def _check_report(data: dict[str, Any]) -> None:
    """Check report data returned by the api."""
    assert "errors" not in data
    assert set(data) == {"uid", "manifest", "reports"}
    for entry in data["reports"].values():
        assert set(entry) == {"report", "debug"}
        assert set(entry["report"]) == {"document", "models", "externalModelDefinitions", "linkGraph"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_report.py tests/test_api.py -v`
Expected: FAIL (`report.py` still accesses `info.info`).

- [ ] **Step 3: Rewrite report.py and adapt api.py**

```python
# backend/sbml4humans/report.py
"""Report data for SBML models and COMBINE archives.

The report of a model is the `Report` created by `SBMLDocumentInfo`. A single
SBML file is wrapped in a COMBINE archive with one master model, so that the
frontend always receives an archive manifest with one report per SBML entry.
"""

import gzip
import logging
import tempfile
import time
import uuid
from pathlib import Path

from pymetadata.omex import EntryFormat, ManifestEntry, Omex

from sbml4humans.model import Debug, ReportEntry, ReportResponse
from sbml4humans.sbmlinfo import SBMLDocumentInfo


logger = logging.getLogger(__name__)

# location of a single SBML file in the archive created for it
SBML_LOCATION = "./model.xml"
GZIP_MAGIC = b"\x1f\x8b"


def report_for_sbml(source: Path | str, uid: str = "") -> ReportEntry:
    """Create the report of a single SBML document.

    Args:
        source: path to an SBML file or SBML string.
        uid: identifier of the request, only used for logging.

    Raises:
        ValueError: if no model could be read from the source.
    """
    start = time.perf_counter()
    info = SBMLDocumentInfo(SBMLDocumentInfo.read(source))
    if info.doc.getModel() is None:
        raise ValueError(
            f"No SBML model could be read from '{source}':\n"
            f"{info.doc.getErrorLog().toString()}"
        )
    report = info.build()
    elapsed = round(time.perf_counter() - start, 3)
    logger.info("report created for '%s' in %s s", uid, elapsed)
    return ReportEntry(report=report, debug=Debug(json_report_time=f"{elapsed} [s]"))


def report_for_path(path: Path) -> ReportResponse:
    """Create the reports of an SBML file or a COMBINE archive.

    Returns the archive manifest and one report per SBML entry of the archive.
    """
    uid = uuid.uuid4().hex
    omex = _omex_for_path(path)
    reports = {
        entry.location: report_for_sbml(omex.get_path(entry.location), uid=uid)
        for entry in omex.manifest.entries
        if entry.is_sbml()
    }
    return ReportResponse(uid=uid, manifest=omex.manifest.model_dump(), reports=reports)


def report_for_bytes(content: bytes) -> ReportResponse:
    """Create the reports of the content of an SBML file or COMBINE archive."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "model"
        path.write_bytes(content)
        return report_for_path(path)
```

Keep `_omex_for_path` and `_is_gzipped` unchanged. `SBMLDocumentInfo.read` is a new static method in `sbmlinfo.py`, so that `report_for_sbml` can check the model before building:

```python
    @staticmethod
    def read(source: Path | str) -> libsbml.SBMLDocument:
        """Read the document of a path or an SBML string."""
        return read_sbml(source)
```

and `from_sbml` becomes `return cls.from_doc(cls.read(source))`.

In `api.py` the three report endpoints and the example endpoint return the dump:

```python
@api.get("/api/examples/{example_id}", tags=["examples"])
def example(example_id: str) -> dict[str, Any]:
    """Create the report data of an example."""
    example: ExampleMetaData | None = load_examples().get(example_id)
    if example is None:
        raise ExampleNotFoundError(example_id)
    return _dump(report_for_path(example.file))


@api.post("/api/file", tags=["reports"])
def report_from_file(source: UploadFile) -> dict[str, Any]:
    """Create the report data of an uploaded SBML file or COMBINE archive."""
    return _dump(report_for_bytes(source.file.read()))


@api.get("/api/url", tags=["reports"])
def report_from_url(url: str) -> dict[str, Any]:
    """Create the report data of an SBML file or COMBINE archive behind a url."""
    return _dump(report_for_bytes(download(url)))


@api.post("/api/content", tags=["reports"])
async def report_from_content(request: Request) -> dict[str, Any]:
    """Create the report data of the SBML content in the request body."""
    content = await request.body()
    return _dump(await run_in_threadpool(report_for_bytes, content))


def _dump(response: ReportResponse) -> dict[str, Any]:
    """The JSON of a response with camelCase keys."""
    return response.model_dump(mode="json", by_alias=True)
```

with `from sbml4humans.model import ReportResponse` added to the imports.

- [ ] **Step 4: Run the whole suite**

Run: `cd backend && uv run pytest -q && uv run ruff format . && uv run ruff check . && uv run ty check`
Expected: all passed, all checks passed.

- [ ] **Step 5: Commit**

```bash
git add backend/sbml4humans/report.py backend/sbml4humans/api.py backend/sbml4humans/sbmlinfo.py backend/tests/test_report.py backend/tests/test_api.py
git commit -m "Serve the typed report response"
```

---

### Task 8: JSON schema export and CI check

**Files:**
- Create: `backend/sbml4humans/schema.py`
- Create: `frontend/src/schema/report.schema.json` (generated)
- Test: `backend/tests/test_schema.py`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Produces: `schema_json() -> str` and `python -m sbml4humans.schema [path]` writing the schema of `ReportResponse`; `SCHEMA_PATH` pointing to `frontend/src/schema/report.schema.json`.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_schema.py
"""Tests of the JSON schema export."""

import json

from sbml4humans.schema import SCHEMA_PATH, schema_json


def test_schema_describes_the_response() -> None:
    """The schema is the JSON schema of the report response."""
    schema = json.loads(schema_json())
    assert schema["title"] == "ReportResponse"
    assert set(schema["properties"]) == {"uid", "manifest", "reports"}
    assert "Species" in schema["$defs"]
    assert "listOfSpecies" in schema["$defs"]["Model"]["properties"]


def test_committed_schema_is_current() -> None:
    """The schema of the frontend equals the schema of the current model."""
    assert SCHEMA_PATH.read_text(encoding="utf-8") == schema_json(), (
        "run `uv run python -m sbml4humans.schema` and commit the schema"
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_schema.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sbml4humans.schema'`

- [ ] **Step 3: Write the schema module and generate the file**

```python
# backend/sbml4humans/schema.py
"""The JSON schema of the api response.

The frontend generates its TypeScript types from the schema, which mirrors the
pydantic model by construction. Run `python -m sbml4humans.schema` after a
change of the model and commit the schema.
"""

import json
import sys
from pathlib import Path

from sbml4humans.model import ReportResponse


SCHEMA_PATH = (
    Path(__file__).resolve().parents[2] / "frontend" / "src" / "schema" / "report.schema.json"
)


def schema_json() -> str:
    """The JSON schema of `ReportResponse` with camelCase properties."""
    schema = ReportResponse.model_json_schema(by_alias=True)
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str]) -> None:
    """Write the schema to the given path or to `SCHEMA_PATH`."""
    path = Path(argv[1]) if len(argv) > 1 else SCHEMA_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(schema_json(), encoding="utf-8")
    print(f"schema written to {path}")


if __name__ == "__main__":
    main(sys.argv)
```

Generate the file: `cd backend && uv run python -m sbml4humans.schema`.

Add the job to `.github/workflows/ci.yml` after the `test` job (same checkout and uv steps as `test`):

```yaml
  schema:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v7
        with:
          persist-credentials: false
      - name: Install uv and set the python version
        uses: astral-sh/setup-uv@v10.0.1
        with:
          python-version: "3.14"
          enable-cache: true
      - name: Install the backend
        working-directory: backend
        run: uv sync
      - name: Check that the committed JSON schema is current
        working-directory: backend
        run: |
          uv run python -m sbml4humans.schema /tmp/report.schema.json
          diff /tmp/report.schema.json ../frontend/src/schema/report.schema.json
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_schema.py -v && uv run ruff check . && uv run ruff format --check . && uv run ty check`
Expected: 2 passed, all checks passed.

- [ ] **Step 5: Commit**

```bash
git add backend/sbml4humans/schema.py backend/tests/test_schema.py frontend/src/schema/report.schema.json .github/workflows/ci.yml
git commit -m "Export the JSON schema of the report response"
```

---

### Task 9: Round trip of all examples and documentation

**Files:**
- Test: `backend/tests/test_model.py` (append)
- Modify: `CLAUDE.md`, `README.md`

- [ ] **Step 1: Write the failing test**

```python
# append to backend/tests/test_model.py
from pathlib import Path

import pytest

from sbml4humans.resources import API_EXAMPLES_MODEL, BIOMODELS_CURATED_PATH
from sbml4humans.sbmlinfo import SBMLDocumentInfo

BIOMODELS = sorted(BIOMODELS_CURATED_PATH.glob("BIOMD*.omex"))[:5]


@pytest.mark.parametrize("path", API_EXAMPLES_MODEL, ids=lambda path: path.name)
def test_examples_round_trip(path: Path) -> None:
    """Every example builds a report which survives the JSON round trip."""
    report = SBMLDocumentInfo.from_sbml(path)
    data = report.model_dump(mode="json", by_alias=True)
    assert Report.model_validate(data) == report
    nodes = report.link_graph.nodes
    pks = [n.pk for n in nodes.values()]
    assert len(pks) == len(set(pks))
    for edge in report.link_graph.edges:
        assert edge.source in nodes and edge.target in nodes
```

- [ ] **Step 2: Run test to verify it fails or passes**

Run: `cd backend && uv run pytest tests/test_model.py -v`
Expected: PASS for all examples. A failure here is a real defect of the builder or graph (a NaN reaching JSON, a duplicate pk, a dangling edge): fix the builder, not the test.

- [ ] **Step 3: Update the documentation**

In `CLAUDE.md` replace the architecture paragraph on the report with:

```markdown
**`model.py`, `sbmlinfo.py`, `links.py` - the report.** `model.py` is the pydantic data model: one class per SBML object with the attributes of the specification (`Species`, `Reaction` with `SpeciesReference` and `KineticLaw`, the comp and fbc objects), `Model` with the SBML lists (`list_of_species`, ...), `Report{document, models, external_model_definitions, link_graph}`. Python is snake_case, JSON camelCase (`model_dump(mode="json", by_alias=True)`). `sbmlinfo.SBMLDocumentInfo` walks the libsbml document and builds the objects, math as `Math{latex, formula}` (`mathml.py`) and units as latex (`units.py`), and records the symbols of every math. `links.build_link_graph` turns the report into `LinkGraph{nodes, edges}`: every SBase is a node with `pk = "<model id>/<type>:<id>"`, every reference (compartment, reactant, variable, units, math symbols, modelRef, port, flux bounds, ...) an `Edge{source, target, kind}` from the referencing to the referenced object; unresolvable references are logged, never edges. `schema.py` writes the JSON schema of `ReportResponse` to `frontend/src/schema/report.schema.json`, run it after every model change (the CI diffs it).
```

Add to the commands block of `CLAUDE.md`: `uv run python -m sbml4humans.schema   # regenerate the JSON schema after a model change`.

In `README.md` add one sentence to the backend section: "The JSON schema of the api response is generated from the pydantic model into `frontend/src/schema/report.schema.json` with `uv run python -m sbml4humans.schema`."

- [ ] **Step 4: Run everything**

Run: `cd backend && uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run ty check`
Expected: all passed, all checks passed. Then start the api and check a report end to end:

```bash
cd backend && uv run uvicorn sbml4humans.api:api --port 1444 &
sleep 5
curl -s http://localhost:1444/api/examples/BIOMD0000000012 | python3 -c "import json,sys; d=json.load(sys.stdin); r=d['reports']['./model.xml']['report']; print(r['models'][0]['listOfSpecies'][0]['pk'], len(r['linkGraph']['edges']))"
kill %1
```

Expected: `BIOMD0000000012/Species:PX` and a positive number of edges.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_model.py CLAUDE.md README.md
git commit -m "Round trip every example through the report model and document it"
```
