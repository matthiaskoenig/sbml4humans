# The complete SBML data model in the report

**Issue:** [#11](https://github.com/matthiaskoenig/sbml4humans/issues/11) - "Complete data model with references between objects (graph)": a better data model for visualization, the graph structure represented, components for rendering the individual SBML objects, a better complete overview of components.

**Goal:** the report carries the data model of SBML Level 3 core and of the packages comp, fbc, qual and distrib, every reference between two objects is an edge of the link graph, and every object the report carries is rendered, explained and documented.

**Evidence:** two audits of the current report against the specifications and against python-libsbml 5.21.1, with a table per class and the reproduction of every defect:

- [core and comp](2026-09-18-data-model-gaps-core-comp.md): 60 classes, 141 attributes, 120 gaps
- [fbc, qual and distrib](2026-09-18-data-model-gaps-packages.md): 27 classes, 104 attributes, about 50 gaps

## What is wrong today

Three defects lose data a reader is looking at, and they are not missing fields but silent losses:

1. **Every local parameter of a Level 2 model disappears.** The walk reads `KineticLaw.getListOfLocalParameters()`, which libsbml fills for Level 3 only; in Level 2 those parameters are `Parameter` objects in `getListOfParameters()`. 32 of the 49 curated BioModels which ship with the backend carry such parameters, 1473 of them in total, and none of them reaches the report: the kinetic law shows a formula whose constants have no value, no units and no link, and the link graph logs their symbols as unresolvable.
2. **An uncertainty which is a span loses its numbers.** A `distrib` `UncertSpan` is read as a plain `UncertParameter`, so the shipped example `distrib_uncertainties.xml` renders `<uncertSpan type="range" valueLower="1" valueUpper="4"/>` as the word "range" followed by five empty cells. Four of the sixteen kinds of uncertainty, among them the confidence interval, can only be written as a span.
3. **libsbml's identifier aliases corrupt the identity of four classes.** `InitialAssignment.getId()` returns the symbol, `Rule.getId()` the variable, `EventAssignment.getId()` the variable, and the report never calls `getIdAttribute()`. An `<algebraicRule id="ar1">` therefore reports no id and is keyed by a sha1 of its XML, so its permalink changes when its math changes, and an assignment rule whose variable is a species reference shadows that species reference in the index, which produces a self loop and mis-routes the symbols of the kinetic law.

Two further classes of defect are structural: the report models the gene product association of a reaction as one infix string, whose gene names are the labels while the ids beside it are the ids, and the comp replacement edges end at the submodel instead of at the element inside it which the reference names.

## What the report will carry

### Objects which are new

| package | classes |
| --- | --- |
| core | `Unit`, `Trigger`, `Priority`, `Delay`, `Message` as objects of the report rather than values, `LocalParameter` of a Level 2 kinetic law |
| comp | `Deletion`, the recursive `SBaseRef` child, `ReplacedElement.deletion` and `ReplacedElement.conversionFactor`, `ExternalModelDefinition.md5` |
| fbc | `FluxBound` (Version 1), `GeneProductAssociation` with its `And`, `Or` and `GeneProductRef` tree, `UserDefinedConstraint` and `UserDefinedConstraintComponent` (Version 3), `KeyValuePair` (Version 3) |
| qual | `QualitativeSpecies`, `Transition`, `Input`, `Output`, `FunctionTerm`, `DefaultTerm` |
| distrib | `UncertSpan`, the nested `listOfUncertParameters` of a distribution, and the `SBase` attributes of an `UncertParameter` |

### Attributes which are new

Every attribute the two gap lists mark as missing, among them `Model.strict` and `ListOfObjectives.activeObjective` of fbc, `FluxObjective.id`, `name` and `variableType`, the four attributes of an `UncertSpan`, the 29 attributes of qual, and the attributes of the core objects which become objects (`Trigger.persistent` and `initialValue` keep their place, `Priority` and `Delay` gain the `SBase` attributes they have in the file).

### The graph

Every reference of the specification becomes an edge, which adds these kinds: `input` and `output` (qual, the influence graph), `qualitativeSpecies`, `deletion`, `activeObjective`, `fluxBound` (fbc Version 1), `var` (distrib), and `geneProductRef`. Two corrections come with them:

- an edge starts at the object which carries the reference, not at its parent. The reactant, product and modifier edges start at the `SpeciesReference` and the `ModifierSpeciesReference`, which makes those 529 objects part of the graph instead of isolated nodes and lets `frontend/src/report/parentReaction.ts` go; the `fluxObjective` and `geneProduct` edges start at the `FluxObjective` and the `GeneProductRef`; the math edges of an uncert parameter start at that parameter instead of at its uncertainty.
- a reference which names an element inside a submodel (`comp` `ReplacedElement`, `ReplacedBy`, `Deletion`, `Port`) resolves through the `SBaseRef` to that element, and the edge ends there. Where it cannot be resolved, the edge ends at the submodel as it does today, and the report says so.

### Identity

`getIdAttribute()` replaces `getId()` for `InitialAssignment`, `Rule` and `EventAssignment`, so the id of the report is the id of the file. The primary key of an element without an id keeps its current shape. Port identifiers move out of the SId namespace of the index, as comp requires.

### What the report will not carry

The 22 `ListOf` containers do not become objects of the report. Core 4.2.7 allows notes and annotations on them, and a reader loses those, but one object per list would double the number of types in the rail, the reference and the glossary for a case which none of the 38 models which ship with the backend contains. The report keeps the list as the table of its elements. This is the one deliberate omission of this work; it is written down here so the next reader of the gap list does not take it for an oversight.

## How it is rendered

- `frontend/src/data/sbmlTypes.ts` gains the qual package and one entry per new element type, each with its mark, its colour and its icon, in the order of the specification.
- the element tables gain the columns a reader of that type needs: the qualitative species with their levels, the transitions with their inputs and outputs, the fbc columns which exist in no table today (the chemical formula and the charge of a species, the flux bounds and the gene association of a reaction), and the flux objectives of an objective.
- the inspector gains one attribute component per new type, and the components of the types which grew show what they gained: a unit definition shows its units as a table of kind, exponent, scale and multiplier next to the rendered formula, an uncertainty shows a span as an interval, a reaction shows its gene association as the tree it is.
- the link groups of the inspector gain the new kinds, and the influence of a qual input carries its sign.

## How it is explained

Every new type and every new attribute gets its entry in `glossary/*.toml` with its summary, its description and the section of its specification, so the tooltip of the report and the reference page of the site are generated from the same source; the `docs` check of the CI enforces that the glossary and the report model agree in both directions. `glossary/packages.toml` gains the qual package, `docs/sbml.md` its section, and the fbc entries are corrected to the version they describe.

## Examples

Three example models are added to `backend/sbml4humans/resources/examples/`, written for this repository so that every object is exercised by a report the CI builds:

- `qual_example.xml`: three qualitative species (a constant input of the system, a Boolean one and a multi valued one with an initial level), two transitions, inputs of both signs and both transition effects with a threshold level, outputs of both transition effects with an output level, function terms whose math names a species and an input, a default term, and notes and annotations on a species and on a transition.
- `fbc_bounds_v1.xml`: a Version 1 document with `fluxBound` objects, the only shape of fbc the report cannot read at all today.
- `distrib_spans.xml`: an uncertainty whose span is defined by `varLower` and `varUpper`, an uncert parameter with a `var` and `units`, a distribution with child parameters, two uncertainties on one parameter with different notes, and an uncertainty on a species and on a rule.

`comp_deletion.xml` covers `comp:deletion`, `comp:replacedBy`, the recursive `sBaseRef` and `md5`, none of which any shipped model contains, and the core example `constraint_event.xml`, a Level 3 Version 2 model, covers `<constraint>`, `<message>`, `<priority>` and a kinetic law with local parameters.

## Testing

- the backend tests read each new example and assert the objects, the attributes and the edges the specification requires, including the Level 2 local parameters of a curated BioModel and the identity of a rule with an id.
- the JSON schema is regenerated and the frontend types with it; the schema check of the CI diffs them.
- the frontend tests cover the new columns, the new inspector components and the glossary entry of every field, through the guard which reads the `field` of every attribute component.
- an end to end test walks the qual example the way the examples walk does, so the whole pipeline is exercised against a real document.

## Sequence

The work is done in waves, each of which leaves the repository green, the glossary complete and the reference regenerated:

1. the identity and local parameter defects of core, and the objects core gains
2. comp: the deletion, the recursive reference and the replacement edges
3. fbc: the association tree, the versions and the missing attributes
4. qual: the package end to end
5. distrib: the span, the nested parameters and the edges
6. the frontend of everything which the waves added
7. the documentation, the screenshots and the release notes
