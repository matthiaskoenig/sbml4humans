# Report data model and link graph

Date: 2026-09-16. Status: approved design, sub-project 1 of 2 (the frontend redesign follows in its own spec).

## Goal

Replace the untyped dictionary of `SBMLDocumentInfo` by a pydantic data model that mirrors the SBML objects, serializes to JSON and is mirrored 1:1 in the frontend. The report consists of two parts: the preprocessed information of the SBMLDocument and a link graph connecting all objects, mainly through SIdRefs. Simplicity is the first criterion: one class per SBML object with the attributes of the specification, all relations in one graph, no cross links embedded in the objects.

## Non-goals

- No changes to the current frontend in this sub-project. The old frontend breaks with the new JSON, it is replaced by the redesigned frontend of sub-project 2. Until then the api is developed against its tests.
- No new report content beyond what the current report shows, except the L3 formula strings and the graph edges.
- No validation report, no simulation.

## Data model (`backend/sbml4humans/model.py`)

All classes are pydantic models with `alias_generator=to_camel` and `populate_by_name=True`. Python code uses snake_case, JSON uses camelCase (`model_dump(mode="json", by_alias=True)`).

### Base

`SBase`: `pk: str`, `sbml_type: str` (the libsbml class name, e.g. `Species`, `AssignmentRule`), `id: str | None`, `meta_id: str | None`, `name: str | None`, `sbo: str | None` (SBO term id), `notes: str | None` (html string), `cvterms: list[CVTerm]`, `history: ModelHistory | None`, `xml: str | None` (the SBML of the element, none for the document and models), `comp: CompSBase | None`, `uncertainties: list[Uncertainty]`.

- `CVTerm{qualifier: str (BQB/BQM value of pymetadata), resources: list[str]}`. The SBO term is added as `BQB_IS` cvterm to `https://identifiers.org/<sbo>` when it is not among the resources, as today.
- `ModelHistory{creators: list[Creator{given_name, family_name, organization, email}], created_date: str | None, modified_dates: list[str]}`.
- `CompSBase{replaced_by: ReplacedBy | None, replaced_elements: list[ReplacedElement]}`, both with `submodel_ref: str` and `sbase_ref: SBaseRef{port_ref, id_ref, unit_ref, meta_id_ref}` (all optional strings).
- `Uncertainty(SBase)` with `uncert_parameters: list[UncertParameter{var, value, units, type, definition_url, math: Math | None}]`.

### Shared value types

- `Math{latex: str, formula: str}`: latex from the xslt rendering (`mathml.py`), formula from `libsbml.formulaToL3String`.
- Units on an object are two fields: the SId `units: str | None` and its rendering `units_latex: str | None` (`units.py`); derived units are `derived_units: str | None` (latex).
- `ConversionFactor{sid: str, value: float | None, units: str | None}`.

### Objects

Every class extends `SBase` and adds only the attributes of the SBML specification:

| class | attributes |
| --- | --- |
| `SBMLDocument` | `level`, `version`, `packages: list[Package{prefix, version}]` |
| `Model` | `kind: "model" \| "modelDefinition"`, `substance_units`, `time_units`, `volume_units`, `area_units`, `length_units`, `extent_units` (each SId plus `*_latex`), `conversion_factor: ConversionFactor \| None`, and the lists below |
| `FunctionDefinition` | `math: Math \| None` |
| `UnitDefinition` | `units_latex` (the rendered definition) |
| `Compartment` | `spatial_dimensions: float \| None`, `size: float \| None` (NaN becomes None), `constant: bool \| None`, `units`, `units_latex`, `derived_units` |
| `Species` | `compartment: str`, `initial_amount`, `initial_concentration` (NaN becomes None), `substance_units`, `has_only_substance_units`, `boundary_condition`, `constant`, `units`, `units_latex`, `derived_units`, `conversion_factor`, `fbc: SpeciesFbc{chemical_formula, charge} \| None` |
| `Parameter` | `value: float \| None` (NaN becomes None), `constant`, `units`, `units_latex`, `derived_units` |
| `InitialAssignment` | `symbol: str`, `math`, `derived_units` |
| `AssignmentRule`, `RateRule` | `variable: str`, `math`, `derived_units` |
| `AlgebraicRule` | `math`, `derived_units` |
| `Constraint` | `math`, `message: str \| None` |
| `Reaction` | `reversible`, `fast`, `compartment: str \| None`, `list_of_reactants: list[SpeciesReference]`, `list_of_products: list[SpeciesReference]`, `list_of_modifiers: list[ModifierSpeciesReference]`, `kinetic_law: KineticLaw \| None`, `equation: str` (the readable equation as today), `fbc: ReactionFbc \| None` |
| `SpeciesReference` (SBase) | `species: str`, `stoichiometry: float \| None` (NaN becomes None), `constant` |
| `ModifierSpeciesReference` (SBase) | `species: str` |
| `KineticLaw` (SBase) | `math`, `derived_units`, `list_of_local_parameters: list[LocalParameter]` |
| `LocalParameter` (SBase) | `value`, `units`, `units_latex`, `derived_units` |
| `ReactionFbc` | `lower_flux_bound: str \| None`, `upper_flux_bound: str \| None` (parameter SIds), `gene_product_association: str \| None` (infix string) |
| `Event` | `use_values_from_trigger_time`, `trigger: Trigger{math, initial_value, persistent} \| None`, `priority: Math \| None`, `delay: Math \| None`, `list_of_event_assignments: list[EventAssignment]` |
| `EventAssignment` (SBase) | `variable: str`, `math` |
| `Submodel` | `model_ref: str`, `time_conversion_factor`, `extent_conversion_factor`, `list_of_deletions: list[SBaseRef]` |
| `Port` | `port_ref`, `id_ref`, `unit_ref`, `meta_id_ref` |
| `ExternalModelDefinition` | `source: str`, `model_ref: str \| None` |
| `GeneProduct` | `label`, `associated_species: str \| None` |
| `Objective` | `type: str`, `list_of_flux_objectives: list[FluxObjective{reaction, coefficient}]` |

The lists of `Model` use the SBML names: `list_of_function_definitions`, `list_of_unit_definitions`, `list_of_compartments`, `list_of_species`, `list_of_parameters`, `list_of_initial_assignments`, `list_of_rules: list[AssignmentRule | RateRule | AlgebraicRule]` (discriminated by `sbml_type`), `list_of_constraints`, `list_of_reactions`, `list_of_events`, `list_of_submodels`, `list_of_ports`, `list_of_gene_products`, `list_of_objectives`. Lists of packages the document does not use are empty.

The old flux bound values, the `assignment` and `port` fields of elements and the `species`/`reactions`/`reactant`/`product`/`modifier` pk lists are gone: the graph carries these relations.

### Report

`Report{document: SBMLDocument, models: list[Model], external_model_definitions: list[ExternalModelDefinition], link_graph: LinkGraph}`. The main model is the first entry of `models` with `kind="model"`, the comp model definitions follow with `kind="modelDefinition"`. A document without model has an empty `models` list.

### Primary keys

`pk = "<model id>/<sbml_type>:<id>"`. The model part is the id of the containing model (`kind` model or model definition), `document` for the document itself and for external model definitions, the model's own id for the model node. When an element has no id, its metaId is used, and when it has no metaId either, the sha1 digest of its SBML. The pk is unique within a report; comp model definitions no longer collide with the main model.

## Link graph (`backend/sbml4humans/links.py`)

`LinkGraph{nodes: dict[str, Node], edges: list[Edge]}` with `Node{pk, sbml_type, id, name, model: str | None}` (model is the pk of the containing model, none for the document) and `Edge{source: str, target: str, kind: EdgeKind}`. Every SBase of the report is a node, including species references, kinetic laws, local parameters and event assignments, so that every edge has an addressable source.

`EdgeKind` is a string enum, edges point from the referencing object to the referenced one:

| kind | source to target |
| --- | --- |
| `compartment` | species or reaction to compartment |
| `reactant`, `product`, `modifier` | reaction to species |
| `variable` | assignment rule, rate rule, event assignment to species, parameter or compartment |
| `symbol` | initial assignment to its symbol |
| `units` | any units attribute (model, compartment, species, parameter, local parameter) to a unit definition of the model |
| `conversionFactor` | model or species to the parameter |
| `fluxBound` | reaction to the bound parameters |
| `geneProduct` | reaction to every gene product of its association |
| `associatedSpecies` | gene product to species |
| `fluxObjective` | objective to reaction |
| `modelRef` | submodel to a model definition or external model definition |
| `port` | port to the element it references (id, unit or metaId reference) |
| `replacedBy`, `replacedElement` | element to the submodel of the replacement |
| `math` | function definition, initial assignment, rule, constraint, kinetic law, trigger, priority, delay, event assignment to every species, parameter, compartment, reaction, function definition or local parameter named in its math |

Resolution: SIds are resolved within the containing model (unit definitions and local parameters in their own namespaces), `modelRef` against the model definitions and external model definitions of the document. An unresolvable reference is logged at warning level and produces no edge. The set of symbols of a math is collected from the ASTNode names.

## Builder and serialization

- `sbmlinfo.py` keeps the entry point `SBMLDocumentInfo` but returns the typed report: `SBMLDocumentInfo.from_sbml(source) -> Report` and `SBMLDocumentInfo.from_doc(doc) -> Report`. Internally one method per object type builds the pydantic object from the libsbml object, the model method assembles the lists, and `links.build_link_graph(report)` runs on the finished objects together with the symbol sets collected per math during the build.
- `report.py` returns a typed `ReportResponse{uid: str, manifest: Manifest (pymetadata), reports: dict[str, ReportEntry{report: Report, debug: Debug{json_report_time: str}}]}`. The api returns `response.model_dump(mode="json", by_alias=True)`. The error contract (status 200 with `errors`, `warnings`, `info`) is unchanged.
- `python -m sbml4humans.schema` writes the JSON schema of `ReportResponse` to `frontend/src/schema/report.schema.json`. The CI job `schema` runs it and fails when the committed file differs, so the frontend types are always generated from the current backend model.

## Testing

- `tests/test_model.py`: every example model and archive builds a `Report`, dumps to JSON and validates back (`Report.model_validate`), pks are unique, every edge references existing nodes.
- `tests/test_links.py`: the repressilator has the expected `reactant`, `product`, `modifier` and `math` edges of one reaction, a comp model has `modelRef`, `port` and `replacedElement` edges, an fbc model has `fluxBound`, `geneProduct`, `associatedSpecies` and `fluxObjective` edges, a dangling reference produces no edge.
- `tests/test_sbmlinfo.py`: the equations, NaN handling and pk scheme, adapted to the typed objects.
- `tests/test_api.py`, `tests/test_report.py`: adapted to the new keys of the response.
- `tests/test_schema.py`: the schema module writes a schema equal to the committed one.

## Files

- new: `backend/sbml4humans/model.py`, `backend/sbml4humans/links.py`, `backend/sbml4humans/schema.py`, `backend/tests/test_model.py`, `backend/tests/test_links.py`, `backend/tests/test_schema.py`, `frontend/src/schema/report.schema.json`
- rewritten: `backend/sbml4humans/sbmlinfo.py`, `backend/sbml4humans/report.py`
- adapted: `backend/sbml4humans/api.py`, `backend/sbml4humans/mathml.py` (formula strings and symbol collection), the tests, `CLAUDE.md`, `.github/workflows/ci.yml`
