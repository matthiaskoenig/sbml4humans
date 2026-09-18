# Gap list: SBML Level 3 Version 2 core and the comp package

Read-only audit of what the sbml4humans report carries of SBML L3V2 core (`components.tex` §4, `preliminary.tex` §3, `annotations.tex` §6) and of the Hierarchical Model Composition package (comp `syntax.tex` §3). Nothing was changed. Every claim below was checked against the specification text, against the L3V2 and comp RelaxNG grammars (`RelaxNG/sbml-core/sbml-core-l3v2.rng`, `RelaxNG/sbml-core/sbml-sbase-l3v2.rng`, `RelaxNG/sbml-comp/sbml-comp.rng`) and against python-libsbml 5.21.1.

## How to read the tables

| column | meaning |
| --- | --- |
| in the specification | the attribute or element as the specification names it, with its section |
| in `model.py` | the field of the pydantic class, or `-` |
| read in `sbmlinfo.py` | whether `SBMLDocumentInfo` fills it |
| edge in `links.py` | the `EdgeKind` built for the reference, or `-` for a non-reference attribute, or `MISSING` for a reference with no edge |
| column | the element table column (`frontend/src/report/columns/`) |
| inspector row | the row of `frontend/src/components/inspector/attributes/` or of `AttributesColumn.vue` |
| glossary entry | `glossary/core.toml` / `glossary/packages.toml` |

The glossary is checked against the report model by `sbml4humans.glossary --check` in CI, so the glossary column is mechanically `yes` for every field of `model.py` and `no` for everything that is not in `model.py`. It is repeated per row only where it is not implied.

`id` and `name` come from `SBase` and are the first two columns (`ID_COLUMNS`) of every element table, so they are not repeated per class.

## Summary

- classes checked: **60** (43 core, 17 comp)
- attribute rows checked: **141** (104 core, 37 comp)
- gaps: **120**
  - missing class: **31** (5 core objects, 22 `ListOf` containers, 4 comp objects)
  - missing attribute: **61** (not counting the 6 `SBase` attributes on each of the 22 missing `ListOf` containers, which would add 132)
  - missing edge: **21**
  - wrong: **7**

## 1. `SBase` (core §3.2)

| class | attribute | in the specification | in `model.py` | read in `sbmlinfo.py` | edge in `links.py` | column | inspector row | glossary entry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SBase | `id` | §3.2.1 (L3V2 only), §3.3.1 | `id` | yes | - | yes | title | yes |
| SBase | `name` | §3.2.2 | `name` | yes | - | yes | title | yes |
| SBase | `metaid` | §3.2.3 | `meta_id` | yes | - | no | yes | yes |
| SBase | `sboTerm` | §3.2.4 | `sbo` | yes | - | no | yes | yes |
| SBase | `notes` | §3.2.5 | `notes` | yes | - | no | notes panel | yes |
| SBase | `annotation` | §3.2.6, §6 | `cvterms`, `history` | partial | - | no | annotations panel | yes |

### Missing

- **`annotation`, non-RDF content (§3.2.6).** `sbmlinfo.cvterms` keeps only the RDF CV terms (qualifier plus resource URIs) and `sbmlinfo.history` keeps the dc/vCard history. Everything else in the `<annotation>` element is dropped from the typed report. It survives only in the `xml` field, and `SBMLDocumentInfo.sbase` sets `xml = None` for `SBML_DOCUMENT` and `SBML_MODEL`, so a non-RDF annotation on the `<model>` or on the `<sbml>` element is invisible in every part of the report. Verified: a model carrying `<mysim:molecule mysim:weight="18.02"/>` produces `cvterms == []`, `xml is None`, `notes is None`. §3.2.6 exists precisely so that tools can put their own vocabulary there; a reader of the report cannot see that a model carries such an annotation at all, and cannot see which tool wrote it.
- **`annotation`, nested CV terms (§6, "nested content").** `sbmlinfo.cvterms` reads `getNumResources()` but never `getNumNestedCVTerms()`/`getNestedCVTerm()`, which libsbml exposes. Nested terms are how evidence codes and protein modifications are attached to an annotation (§6, and the two worked examples in `annotations.tex`). A reader loses the qualification of an annotation and sees only the bare resource.

### Not a gap

`sboTerm` is additionally surfaced as a synthetic `BQB_IS` CV term pointing at `https://identifiers.org/<sbo>` when no resource already names it (`sbmlinfo.cvterms`), so the SBO term is resolvable in the annotations panel. The `ModelHistory` of any `SBase` is read, not only of the `Model`.

## 2. Core, class by class

### 2.1 `SBMLDocument`, the SBML container (§4.1)

| class | attribute | in the specification | in `model.py` | read | edge | column | inspector row | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SBMLDocument | `level` | §4.1 | `level` | yes | - | no table | yes | yes |
| SBMLDocument | `version` | §4.1 | `version` | yes | - | no table | yes | yes |
| SBMLDocument | `id`, `name` | §4.1.1 (L3V2 only) | `id`, `name` | yes | - | no table | title | yes |
| SBMLDocument | `model` element | §4.1.2 | `Report.models` | yes | MISSING | - | - | yes |
| SBMLDocument | `xmlns:<prefix>` | §4.1.3 | `Package.prefix` (prefix only) | partial | - | no table | yes | yes |
| SBMLDocument | `<prefix>:required` | §4.1.3 | - | no | - | no | no | no |

### Missing

- **`<prefix>:required` (§4.1.3).** §4.1.3 requires every L3 package to declare it, and its value says whether a tool that does not understand the package may still interpret the model. `Package` carries only `prefix` and `version` (`getPackageVersion()`). libsbml exposes `SBMLDocumentPlugin.getRequired()`/`isSetRequired()`. Without it a reader cannot tell a package that changes the mathematics (comp with `required="true"`) from one that only annotates.
- **The namespace URI of a package (§4.1.3).** Only the prefix is kept, and §4.1.3 states explicitly that the prefix is arbitrary. libsbml exposes `getURI()`. Two documents using the same package under different prefixes look different in the report and the same package under different prefixes cannot be recognised.
- **No edge `SBMLDocument` -> `Model`.** The document is a node in every report but has no edge at all. Measured over the 24 example models plus the 14 comp models that ship with the backend: 38 of 38 `SBMLDocument` nodes are isolated. In the graph the document is a floating dot and a reader cannot walk from it into the model.

### 2.2 `Model` (§4.2)

| class | attribute | in the specification | in `model.py` | read | edge | column | inspector row | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Model | `substanceUnits` | §4.2.2 | `substance_units` (+`_latex`) | yes | `units` | no table | yes | yes |
| Model | `timeUnits` | §4.2.3 | `time_units` | yes | `units` | no table | yes | yes |
| Model | `volumeUnits`, `areaUnits`, `lengthUnits` | §4.2.4 | `volume_units`, `area_units`, `length_units` | yes | `units` | no table | yes | yes |
| Model | `extentUnits` | §4.2.5 | `extent_units` | yes | `units` | no table | yes | yes |
| Model | `conversionFactor` | §4.2.6 | `conversion_factor` | yes | `conversionFactor` | no table | yes | yes |
| Model | the 10 `ListOf` children | §4.2.7 | `list_of_*` (plain lists) | yes | MISSING | rail sections | - | yes |

### Missing

- **The 10 `ListOf` container classes as objects (§4.2.7).** See §2.16 below.
- **`xml` for the `Model`** (see §1): a non-RDF model annotation is invisible.
- **No containment edge `Model` -> its elements.** `Node.model` names the model of a node, so a grouping exists, but there is no edge, so a graph view cannot draw the model as a parent.

### 2.3 `FunctionDefinition` (§4.3)

| class | attribute | in the specification | in `model.py` | read | edge | column | inspector row | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FunctionDefinition | `id` (required) | §4.3.1 | `id` | yes | - | yes | title | yes |
| FunctionDefinition | `math` | §4.3.2 | `math` | yes | `math` (symbols) | yes | yes | yes |

No missing attributes. One observation: `mathml.math_symbols` records a user function call (`isUserFunction()`) as a symbol, and `_math_edges` therefore builds an edge from the caller to the function definition, but with the same kind `math` as a plain variable read (§4.3.4). A reader cannot tell "calls this function" from "reads this parameter".

### 2.4 `UnitDefinition` (§4.4.1) and `Unit` (§4.4.2)

| class | attribute | in the specification | in `model.py` | read | edge | column | inspector row | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UnitDefinition | `id` (required) | §4.4.1 | `id` | yes | - | yes | title | yes |
| UnitDefinition | `listOfUnits` | §4.4.1 | `units_latex` (rendering) | rendered | MISSING | `unitsLatex` | `unitsLatex` | yes |
| Unit | `kind` | §4.4.2 | - | no | - | no | no | no |
| Unit | `exponent` | §4.4.2 | - | no | - | no | no | no |
| Unit | `scale` | §4.4.2 | - | no | - | no | no | no |
| Unit | `multiplier` | §4.4.2 | - | no | - | no | no | no |

### Missing

- **`Unit` is missing entirely (§4.4.2).** The report replaces the whole `listOfUnits` with a single latex string built by `units.udef_to_string`, which runs every unit through pint (`Q_(multiplier * 10**scale, kind) ** abs(exponent)`, then `to_compact()`) and applies string rewrites (`"60.0 s"` -> `"1 min"`, `"3600.0 s"` -> `"1 hr"`, `"86.4 ks"` -> `"1 day"`). A reader can never see the four attributes the file actually contains, cannot check the rendering against the source, and cannot see that a unit was written as `kilogram` with `scale="-3"` rather than as `gram`. libsbml exposes all four (`getKind()` with `UnitKind_toString`, `getExponentAsDouble()`, `getScale()`, `getMultiplier()`).
- **An empty `listOfUnits` cannot be distinguished (§4.4.1, L3V2).** L3V2 allows an empty `ListOfUnits` and defines it as an undefined unit ("A model component that references this UnitDefinition is taken to have *no* defined unit"). `udef_to_string` renders both an empty definition and a dimensionless one as `-`.
- **No edge `UnitDefinition` -> `Unit`.** Consequence of the missing class: a unit definition has no outgoing structure. Measured over the shipped examples, 273 of 513 `UnitDefinition` nodes are isolated (they get an edge only when something references them).
- **No node for a base unit (§4.4.2, table of base units).** `links._units_edge` builds an edge only when the sid is a `UnitDefinition` of the model, so `units="litre"` on a compartment is an unlinked string in the table. The 33 base units of `tab:unitkind` (§4.4.2) are a closed, known set and could be nodes.

### 2.5 `Compartment` (§4.5)

| class | attribute | in the specification | in `model.py` | read | edge | column | inspector row | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Compartment | `spatialDimensions` | §4.5.2 | `spatial_dimensions` | yes (`AsDouble`) | - | yes | yes | yes |
| Compartment | `size` | §4.5.3 | `size` | yes | - | yes | yes | yes |
| Compartment | `units` | §4.5.4 | `units` (+`_latex`) | yes | `units` | yes | yes | yes |
| Compartment | `constant` | §4.5.5 | `constant` | yes | - | yes | yes | yes |

Complete. `getSpatialDimensionsAsDouble()` is used, so the fractional dimensions L3 allows are not truncated.

### 2.6 `Species` (§4.6)

| class | attribute | in the specification | in `model.py` | read | edge | column | inspector row | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Species | `compartment` (required) | §4.6.3 | `compartment` | yes | `compartment` | yes | yes | yes |
| Species | `initialAmount` | §4.6.4 | `initial_amount` | yes | - | yes | yes | yes |
| Species | `initialConcentration` | §4.6.4 | `initial_concentration` | yes | - | yes | yes | yes |
| Species | `substanceUnits` | §4.6.4 | `substance_units` (+`_latex`) | yes | `units` | yes | yes | yes |
| Species | `hasOnlySubstanceUnits` | §4.6.5 | `has_only_substance_units` | yes | - | yes | yes | yes |
| Species | `boundaryCondition` | §4.6.6 | `boundary_condition` | yes | - | yes | yes | yes |
| Species | `constant` | §4.6.6 | `constant` | yes | - | yes | yes | yes |
| Species | `conversionFactor` | §4.6.7 | `conversion_factor` | yes | `conversionFactor` | no | yes | yes |

Complete.

### 2.7 `Parameter` (§4.7)

| class | attribute | in the specification | in `model.py` | read | edge | column | inspector row | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Parameter | `value` | §4.7.2 | `value` | yes | - | yes | yes | yes |
| Parameter | `units` | §4.7.3 | `units` (+`_latex`) | yes | `units` | yes | yes | yes |
| Parameter | `constant` | §4.7.4 | `constant` | yes | - | yes | yes | yes |

Complete.

### 2.8 `InitialAssignment` (§4.8)

| class | attribute | in the specification | in `model.py` | read | edge | column | inspector row | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| InitialAssignment | `id` | §4.8.1 (L3V2 only) | `id` (holds `symbol`) | **no** | - | yes (wrong value) | title | yes |
| InitialAssignment | `symbol` (required) | §4.8.2 | `symbol` | yes | `symbol` | yes | yes | yes |
| InitialAssignment | `math` | §4.8.3 | `math` | yes | `math` | yes | yes | yes |

### Missing

- **`id` (§4.8.1).** libsbml aliases `InitialAssignment::getId()`/`isSetId()` to the `symbol` attribute; the real L3V2 id is `getIdAttribute()`, which `sbmlinfo` never calls. Verified on an L3V2 document: `isSetId() == True`, `getId() == 'S1'` (the symbol), `getIdAttribute() == ''`. A reader sees the symbol where the id column promises an id, and an initial assignment that does carry an id cannot be found by it. See §4, item 2.

### 2.9 Rules (§4.9)

| class | attribute | in the specification | in `model.py` | read | edge | column | inspector row | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AlgebraicRule | `id` | §3.2.1, §4.9.2 | `id` | **no** | - | yes (always empty) | title | yes |
| AlgebraicRule | `math` | §4.9.2 | `math` | yes | `math` | yes | yes | yes |
| AssignmentRule | `id` | §3.2.1, §4.9.3 | `id` (holds `variable`) | **no** | - | yes (wrong value) | title | yes |
| AssignmentRule | `variable` (required) | §4.9.1 | `variable` | yes | `variable` | yes | yes | yes |
| AssignmentRule | `math` | §4.9.3 | `math` | yes | `math` | yes | yes | yes |
| RateRule | `id` | §3.2.1, §4.9.4 | `id` (holds `variable`) | **no** | - | yes (wrong value) | title | yes |
| RateRule | `variable` (required) | §4.9.1 | `variable` | yes | `variable` | yes | yes | yes |
| RateRule | `math` | §4.9.4 | `math` | yes | `math` | yes | yes | yes |

### Missing

- **`id` on all three rule classes (§3.2.1, `Rule` inherits it from `SBase` in L3V2).** `Rule::getId()` is aliased to `variable`, so `AssignmentRule`/`RateRule` report the variable as their id and `AlgebraicRule`, which has no variable, reports `isSetId() == False` even when `id` is set. Verified on an L3V2 document with `<algebraicRule id="ar1" name="my rule" sboTerm="SBO:0000064">`: the report gives `id = None`, `name = "my rule"`, `sbo = "SBO:0000064"` and `pk = "m/AlgebraicRule:d3500b31f7030ecc85277da65c93717d039809ee"`. See §4, items 2 and 3.

### 2.10 `Constraint` (§4.10) and `Message` (§4.10.2)

| class | attribute | in the specification | in `model.py` | read | edge | column | inspector row | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Constraint | `math` | §4.10.1 | `math` | yes | `math` | yes | yes | yes |
| Constraint | `message` | §4.10.2 | `message` (raw string) | partial | - | yes (as text) | yes (as text) | yes |
| Message | XHTML content | §4.10.2 | - | no | - | no | no | no |

### Missing

- **`Message` is not a class (§4.10.2).** The report stores `Constraint.getMessageString()`, which returns the `<message>` wrapper together with the XHTML content. Verified: `'<message>\n  <p xmlns="http://www.w3.org/1999/xhtml">S1 is <b>too</b> large</p>\n</message>'`. The frontend renders it with `ValueText` (`{{ text }}`), which escapes, so the reader sees the literal XML. §4.10.2 says the XHTML of a message "must follow the same restrictions as for Notes objects", so it should go through `report/notes.ts` and be rendered, exactly like `notes`. See §4, item 6.

### 2.11 `Reaction` (§4.11.1)

| class | attribute | in the specification | in `model.py` | read | edge | column | inspector row | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Reaction | `id` (required) | §4.11.1 | `id` | yes | - | yes | title | yes |
| Reaction | `reversible` (required) | §4.11.1 | `reversible` | yes | - | yes | yes | yes |
| Reaction | `fast` | §4.11.1 ("removed" in L3V2) | `fast` | yes (always `None` in L3V2) | - | yes | yes | yes |
| Reaction | `compartment` | §4.11.1 | `compartment` | yes | `compartment` | yes | yes | yes |
| Reaction | `listOfReactants` | §4.11.1 | `list_of_reactants` | yes | `reactant` (from the reaction) | equation | yes | yes |
| Reaction | `listOfProducts` | §4.11.1 | `list_of_products` | yes | `product` (from the reaction) | equation | yes | yes |
| Reaction | `listOfModifiers` | §4.11.1 | `list_of_modifiers` | yes | `modifier` (from the reaction) | equation | yes | yes |
| Reaction | `kineticLaw` | §4.11.1 | `kinetic_law` | yes | MISSING | `kineticLaw.math` | yes | yes |

No missing attributes. `fast` is correctly `None` for an L3V2 document (`isSetFast() == False`, verified), but neither the column nor the glossary says that the attribute exists only up to L3V1, so a reader of an L3V2 report sees an always-empty column. See §4, item 7.

### 2.12 `SpeciesReference` (§4.11.3) and `ModifierSpeciesReference` (§4.11.4)

| class | attribute | in the specification | in `model.py` | read | edge | column | inspector row | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SpeciesReference | `id` | §4.11.3 | `id` | yes | - | no table | - | yes |
| SpeciesReference | `species` (required) | §4.11.2 | `species` | yes | MISSING (the edge starts at the reaction) | no table | yes | yes |
| SpeciesReference | `stoichiometry` | §4.11.3 | `stoichiometry` | yes | - | no table | yes | yes |
| SpeciesReference | `constant` (required) | §4.11.3 | `constant` | yes | - | no table | yes | yes |
| ModifierSpeciesReference | `species` (required) | §4.11.4 | `species` | yes | MISSING (the edge starts at the reaction) | no table | yes | yes |

### Missing

- **No edge from a species reference to its species (§4.11.2).** `links._reaction_edges` builds `Edge(source=reaction.pk, target=species, kind=reactant|product|modifier)`, so the species reference itself has no outgoing edge, and nothing points at it either. Measured over the shipped examples: **522 of 522 `SpeciesReference` nodes and 7 of 7 `ModifierSpeciesReference` nodes are isolated**; on a single curated BioModel (`BIOMD0000000001`), 34 of 34. The frontend has to work around this: `SpeciesReferenceAttributes.vue` calls `report/parentReaction.ts` to re-derive the parent reaction by scanning, instead of following an edge.
- **No containment edge `Reaction` -> `SpeciesReference`/`KineticLaw` (§4.11.1).**

### 2.13 `KineticLaw` (§4.11.5) and `LocalParameter` (§4.11.6)

| class | attribute | in the specification | in `model.py` | read | edge | column | inspector row | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| KineticLaw | `math` | §4.11.5 | `math` | yes | `math` | on the reaction | yes | yes |
| KineticLaw | `listOfLocalParameters` | §4.11.5 | `list_of_local_parameters` | **L3 only** | MISSING | no | yes | yes |
| LocalParameter | `id` (required, `LocalSId` in L3V2) | §4.11.6, §3.1.11 | `id` | yes | - | no table | yes | yes |
| LocalParameter | `value` | §4.11.6 | `value` | yes | - | no table | yes | yes |
| LocalParameter | `units` | §4.11.6 | `units` (+`_latex`) | yes | `units` | no table | yes | yes |

### Missing / wrong

- **Local parameters of Level 2 documents are silently dropped.** `sbmlinfo.kinetic_law` iterates `klaw.getListOfLocalParameters()` only. For a Level 2 document libsbml keeps the kinetic law's parameters as `Parameter` objects in `getListOfParameters()` and leaves `getListOfLocalParameters()` empty. Verified on `BIOMD0000000003` (L2V4): `kl.getNumParameters() == 1`, `kl.getNumLocalParameters() == 0`, and the report's `list_of_local_parameters` is empty. Across the 49 curated BioModels shipping in `backend/sbml4humans/resources/biomodels/`, **32 have kinetic-law parameters and 1473 parameters in total are lost**. See §4, item 1.
- **`KineticLaw.id` is not in the SId namespace.** `links._elements` does not yield kinetic laws, so the L3V2 `id` of a kinetic law resolves to nothing. Minor: core defines no reference to a kinetic law id.

### 2.14 `Event` (§4.12.1)

| class | attribute | in the specification | in `model.py` | read | edge | column | inspector row | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Event | `useValuesFromTriggerTime` (required) | §4.12.1 | `use_values_from_trigger_time` | yes | - | yes | yes | yes |
| Event | `trigger` (required) | §4.12.1 | `trigger` (value object) | partial | MISSING | `trigger.math` | yes | yes |
| Event | `delay` | §4.12.1 | `delay` (bare `Math`) | partial | MISSING | `delay` | yes | yes |
| Event | `priority` | §4.12.1 | `priority` (bare `Math`) | partial | MISSING | `priority` | yes | yes |
| Event | `listOfEventAssignments` | §4.12.1 | `list_of_event_assignments` | yes | MISSING | `listOfEventAssignments` | yes | yes |

### 2.15 `Trigger` (§4.12.2), `Priority` (§4.12.3), `Delay` (§4.12.4), `EventAssignment` (§4.12.5)

| class | attribute | in the specification | in `model.py` | read | edge | column | inspector row | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Trigger | `math` | §4.12.2 | `Trigger.math` | yes | `math` (from the **event**) | `trigger.math` | yes | yes |
| Trigger | `persistent` (required) | §4.12.2 | `persistent` | yes | - | `trigger.persistent` | yes | yes |
| Trigger | `initialValue` (required) | §4.12.2 | `initial_value` | yes | - | `trigger.initialValue` | yes | yes |
| Trigger | `id`, `name`, `metaid`, `sboTerm`, `notes`, `annotation` | §3.2 | - | no | - | no | no | no |
| Priority | `math` | §4.12.3 | `Event.priority` (`Math`) | yes | `math` (from the event) | `priority` | yes | yes |
| Priority | `id`, `name`, `metaid`, `sboTerm`, `notes`, `annotation` | §3.2 | - | no | - | no | no | no |
| Delay | `math` | §4.12.4 | `Event.delay` (`Math`) | yes | `math` (from the event) | `delay` | yes | yes |
| Delay | `id`, `name`, `metaid`, `sboTerm`, `notes`, `annotation` | §3.2 | - | no | - | no | no | no |
| EventAssignment | `id` | §3.2.1 | `id` (holds `variable`) | **no** | - | nested table | yes | yes |
| EventAssignment | `variable` (required) | §4.12.5 | `variable` | yes | `variable` | nested table | yes | yes |
| EventAssignment | `math` | §4.12.5 | `math` | yes | `math` | nested table | yes | yes |

### Missing

- **`Trigger`, `Priority` and `Delay` are not objects (§4.12.2-4).** All three are `SBase` in L3V2 (verified with libsbml: `<trigger id="t1">`, `<delay id="d1">`, `<priority id="pr1">` all give `getIdAttribute()` back). `Trigger` is a plain `ReportModel` with three fields, and `Priority` and `Delay` are reduced to a bare `Math`. Their `id`, `name`, `metaid`, `sboTerm`, `notes` and `annotation` are dropped (18 attributes), none of them is a node, and none can be opened in the inspector. The `sboTerm` of a trigger is how a model says what kind of condition it is; the `notes` of a delay is where a modeller explains it.
- **The math symbols of the trigger, the priority and the delay are all attributed to the event.** `sbmlinfo.event` passes the event's `pk` as the owner of all three maths (`self.math(pk, ...)`), so the symbols merge into one set and `links._math_edges` emits them all from the event. A reader cannot tell whether a species is read by the trigger condition or by the delay expression.
- **`EventAssignment.id` (§3.2.1).** `EventAssignment::getId()` is aliased to `variable` (verified: `getId() == 'S1'`, `getIdAttribute() == 'ea1'`). `sbmlinfo` already knows this for the pk (`use_id=False`) but still writes the variable into the `id` field.
- **No containment edge `Event` -> `EventAssignment`.** An event assignment gets a `variable` edge and `math` edges, so it is not isolated, but nothing connects it to its event.

### 2.16 The `ListOf` containers (§4.2.7, §4.4.1, §4.11.1, §4.11.5, §4.12.1)

All 16 core `ListOf` classes are missing entirely: `ListOfFunctionDefinitions`, `ListOfUnitDefinitions`, `ListOfCompartments`, `ListOfSpecies`, `ListOfParameters`, `ListOfInitialAssignments`, `ListOfRules`, `ListOfConstraints`, `ListOfReactions`, `ListOfEvents` (§4.2.7), `ListOfUnits` (§4.4.1), `ListOfReactants`, `ListOfProducts`, `ListOfModifiers` (§4.11.1), `ListOfLocalParameters` (§4.11.5) and `ListOfEventAssignments` (§4.12.1). In `model.py` they are plain python lists.

§4.2.7 is explicit about why this matters: "the fact that the container classes are derived from SBase means that software tools can add information about the lists themselves into each list container's Annotation, a feature that a number of today's software tools exploit", and L3V2 allows a list to be empty so "model writers [can] add Annotation and Notes objects to a given list even when the list is empty in a model; this can be useful, for instance, to let a modeler explain *why* the components are absent from the model". A reader of the report never sees that explanation, never sees an `sboTerm` on a list, and (L3V2) never sees a list's `id` or `name`. Each container carries the 6 `SBase` attributes, so this is 96 attributes not counted in the summary.

## 3. comp, class by class

### 3.1 The extended `SBML` class (comp §3.1, §3.3)

| class | attribute | in the specification | in `model.py` | read | edge | column | inspector row | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SBML (comp) | `comp:required` | comp §3.1 | - | no | - | no | no | no |
| SBML (comp) | `listOfModelDefinitions` | comp §3.3.1 | `Report.models` with `kind="modelDefinition"` | yes | MISSING | rail | - | yes (`Model.kind`) |
| SBML (comp) | `listOfExternalModelDefinitions` | comp §3.3.1 | `Report.external_model_definitions` | yes | MISSING | no table | - | yes |
| ModelDefinition | (all of `Model`) | comp §3.3.1 | `Model` with `kind="modelDefinition"` | yes | - | rail | yes | yes |

`ModelDefinition` is carried as a `Model` with `kind="modelDefinition"` and its `sbml_type` is `"Model"`, which is a deliberate and defensible choice, not a gap. Note however that `ExternalModelDefinition` and `Model` are in `DOCUMENT_TYPES`, which `frontend/src/data/sbmlTypes.ts` never feeds into `COLUMNS` or `TypeBar.vue`, so a document's external model definitions have no section of their own in the report and are reachable only through search or through a submodel's `modelRef` link.

### Missing

- **`comp:required` (comp §3.1).** See §2.1.

### 3.2 `ExternalModelDefinition` (comp §3.3.2)

| class | attribute | in the specification | in `model.py` | read | edge | column | inspector row | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ExternalModelDefinition | `id` (required) | comp §3.3.2 | `id` | yes | - | no table | title | yes |
| ExternalModelDefinition | `name` | comp §3.3.2 | `name` | yes | - | no table | title | yes |
| ExternalModelDefinition | `source` (required) | comp §3.3.2 | `source` | yes | - | no table | yes | yes |
| ExternalModelDefinition | `modelRef` | comp §3.3.2 | `model_ref` | yes | MISSING | no table | yes (plain text) | yes |
| ExternalModelDefinition | `md5` | comp §3.3.2 | - | no | - | no | no | no |

### Missing

- **`md5` (comp §3.3.2).** The checksum of the document at `source`. libsbml exposes `getMd5()`/`isSetMd5()`. Without it a reader has no way to tell whether the file the report resolved (or the file they themselves would fetch) is the file the composed model was written against, which is the whole point of the attribute.
- **No edge for `modelRef` (comp §3.3.2).** The target lives in another document, so an edge inside one report is not always possible, but the report says nothing at all: `ExternalModelDefinitionAttributes.vue` renders `modelRef` with `ValueText` as a plain string. Within a COMBINE archive, where `report.py` already produces one report per SBML entry, the target usually *is* in the response and could be linked.

### 3.3 The extended `Model` class (comp §3.4) and `Port` (comp §3.4.3)

| class | attribute | in the specification | in `model.py` | read | edge | column | inspector row | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Model (comp) | `listOfSubmodels` | comp §3.4.1 | `list_of_submodels` | yes | MISSING | rail | - | yes |
| Model (comp) | `listOfPorts` | comp §3.4.2 | `list_of_ports` | yes | MISSING | rail | - | yes |
| Port | `id` (required, `PortSId`) | comp §3.4.3 | `id` | yes | - | yes | title | yes |
| Port | `name` | comp §3.4.3 | `name` | yes | - | yes | title | yes |
| Port | `portRef` | comp §3.7.1 | `port_ref` | yes | MISSING | text | text | yes |
| Port | `idRef` | comp §3.7.1 | `id_ref` | yes | `port` | link | link | yes |
| Port | `unitRef` | comp §3.7.1 | `unit_ref` | yes | `port` | link | link | yes |
| Port | `metaIdRef` | comp §3.7.1 | `meta_id_ref` | yes | `port` | link | link | yes |
| Port | `sBaseRef` (recursive) | comp §3.7.2 | - | no | - | no | no | no |

### Missing

- **The recursive `sBaseRef` child (comp §3.7.2).** libsbml exposes `SBaseRef.getSBaseRef()`/`isSetSBaseRef()`. A port that reaches into a sub-submodel ("the ability to refer to elements buried within (say) a sub-submodel configuration") shows only its first hop, and the chain the modeller wrote is lost.
- **No edge for `portRef` on a `Port`.** comp §3.4.3 restriction 4 forbids a port referring to another port of the same model, so a `Port.portRef` names a port of a *submodel*; that reference is not drawn.

### 3.4 `Submodel` (comp §3.5) and `Deletion` (comp §3.5.3)

| class | attribute | in the specification | in `model.py` | read | edge | column | inspector row | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Submodel | `id` (required) | comp §3.5.1 | `id` | yes | - | yes | title | yes |
| Submodel | `name` | comp §3.5.1 | `name` | yes | - | yes | title | yes |
| Submodel | `modelRef` (required) | comp §3.5.1 | `model_ref` | yes | `modelRef` | link | link | yes |
| Submodel | `timeConversionFactor` | comp §3.5.1, §3.8.2 | `time_conversion_factor` | yes | `conversionFactor` | link | link | yes |
| Submodel | `extentConversionFactor` | comp §3.5.1, §3.8.2 | `extent_conversion_factor` | yes | `conversionFactor` | link | link | yes |
| Submodel | `listOfDeletions` | comp §3.5.2 | `list_of_deletions: list[SBaseRef]` | partial | MISSING | count | nested table | yes |
| Deletion | `id` | comp §3.5.3 | - | no | - | no | no | no |
| Deletion | `name` | comp §3.5.3 | - | no | - | no | no | no |
| Deletion | `metaid`, `sboTerm`, `notes`, `annotation` | comp §3.7 (`SBaseRef` is `SBase`) | - | no | - | no | no | no |
| Deletion | `portRef`, `idRef`, `unitRef`, `metaIdRef` | comp §3.7.1 | via `SBaseRef` | yes | MISSING | nested table | nested table | yes |
| Deletion | `sBaseRef` (recursive) | comp §3.7.2 | - | no | - | no | no | no |

### Missing

- **`Deletion` is missing as a class (comp §3.5.3).** `Submodel.list_of_deletions` is typed `list[SBaseRef]`, a four-field value object. A deletion therefore has no `pk`, is not a node, cannot be opened in the inspector, and loses its `id`, `name`, `metaid`, `sboTerm`, `notes` and `annotation`. comp §3.5.3 gives the `id` a purpose ("it may be useful for creating submodels that can be manipulated more directly by other submodels ... it is legitimate for an enclosing model definition to delete a deletion") and the `name` exists "in situations when deletions are displayed to modelers", which is exactly what this report does.
- **No edge from a deletion to the element it removes (comp §3.5.3).** The report shows the raw ref string in a nested table of `SubmodelAttributes.vue` and nothing more. A reader cannot see what the composed model actually loses, which is the one question a deletion raises.

### 3.5 Replacements (comp §3.6) and `SBaseRef` (comp §3.7)

| class | attribute | in the specification | in `model.py` | read | edge | column | inspector row | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SBase (comp) | `listOfReplacedElements` | comp §3.6.1 | `CompSBase.replaced_elements` | yes | `replacedElement` (to the submodel) | no | yes | yes |
| SBase (comp) | `replacedBy` | comp §3.6.3 | `CompSBase.replaced_by` | yes | `replacedBy` (to the submodel) | no | yes | yes |
| ReplacedElement | `submodelRef` (required) | comp §3.6.2 | `submodel_ref` | yes | `replacedElement` | no | link | yes |
| ReplacedElement | `deletion` | comp §3.6.2 | - | no | - | no | no | no |
| ReplacedElement | `conversionFactor` | comp §3.6.2, §3.8.1 | - | no | - | no | no | no |
| ReplacedElement | `portRef`, `idRef`, `unitRef`, `metaIdRef` | comp §3.7.1 | `sbase_ref` | yes | MISSING | no | label only | yes |
| ReplacedElement | `sBaseRef` (recursive) | comp §3.7.2 | - | no | - | no | no | no |
| ReplacedElement | `id`, `name`, `metaid`, `sboTerm`, `notes`, `annotation` | comp §3.7 | - | no | - | no | no | no |
| ReplacedBy | `submodelRef` (required) | comp §3.6.4 | `submodel_ref` | yes | `replacedBy` | no | link | yes |
| ReplacedBy | `portRef`, `idRef`, `unitRef`, `metaIdRef` | comp §3.7.1 | `sbase_ref` | yes | MISSING | no | label only | yes |
| ReplacedBy | `sBaseRef` (recursive) | comp §3.7.2 | - | no | - | no | no | no |
| ReplacedBy | `id`, `name`, `metaid`, `sboTerm`, `notes`, `annotation` | comp §3.7 | - | no | - | no | no | no |
| SBaseRef | `portRef` | comp §3.7.1 | `port_ref` | yes | MISSING | - | - | yes |
| SBaseRef | `idRef` | comp §3.7.1 | `id_ref` | yes | MISSING | - | - | yes |
| SBaseRef | `unitRef` | comp §3.7.1 | `unit_ref` | yes | MISSING | - | - | yes |
| SBaseRef | `metaIdRef` | comp §3.7.1 | `meta_id_ref` | yes | MISSING | - | - | yes |
| SBaseRef | `sBaseRef` (recursive) | comp §3.7.2 | - | no | - | no | no | no |
| SBaseRef | `id`, `name`, `metaid`, `sboTerm`, `notes`, `annotation` | comp §3.7 (`SBaseRef.datatype` includes `SBase.datatype`) | - | no | - | no | no | no |

### Missing

- **`ReplacedElement.deletion` (comp §3.6.2).** One of the three attributes the class adds to `SBaseRef`. Without it a reader cannot see that a replacement is scoped to a previously declared deletion.
- **`ReplacedElement.conversionFactor` (comp §3.6.2, §3.8.1).** This attribute changes the mathematics of the composed model: §3.6.2 says the replaced object's value is "possibly modified by either this object's conversionFactor attribute or the relevant submodel's conversion factors". The report carries `Submodel.timeConversionFactor` and `extentConversionFactor` but not this one, so a reader sees only part of the conversion story.
- **`SBaseRef`, `ReplacedElement` and `ReplacedBy` are not `SBase` in the report (comp §3.7).** The comp RelaxNG defines `SBaseRef.datatype` as including `SBase.datatype`, so all three carry `id`, `name`, `metaid`, `sboTerm`, `notes` and `annotation`; the report models them as plain value objects with no `pk`, no node and none of those six attributes (18 attributes).
- **The recursive `sBaseRef` child on all of them (comp §3.7.2).**
- **No edge to the replaced or replacing element (comp §3.6.2, §3.6.4).** `links._comp_edges` resolves only `submodel_ref` and emits `replacedElement`/`replacedBy` to the `Submodel`. The element inside the submodel that is actually replaced, named by the `SBaseRef`, gets no edge. In the shipped comp models, 52 `replacedElement` edges all end at a submodel, and `AttributesColumn.vue` prints the ref as a grey label next to the link. Replacement is the central relationship of the package and the graph does not carry it. A reader cannot answer "which species does this species replace".

## 4. Wrong, not missing

1. **Local parameters of Level 2 models are dropped.** `sbmlinfo.kinetic_law` reads `klaw.getListOfLocalParameters()`, which libsbml leaves empty for L2 documents (they are `Parameter` objects in `getListOfParameters()`). Evidence: on `BIOMD0000000003` (L2V4), `getNumParameters() == 1`, `getNumLocalParameters() == 0`, report `list_of_local_parameters == []`. Across the 49 curated BioModels that ship in the package, 32 models and 1473 parameters. Consequence for a reader: the kinetic law of most BioModels shows a formula whose constants have no value, no unit and no link, and `links._math_edges` cannot resolve those symbols, so they are logged as unknown and produce no edge.
2. **`id` on `InitialAssignment`, `AssignmentRule`, `RateRule` and `EventAssignment` is the `symbol`/`variable`, not the id.** libsbml aliases `getId()` for backward compatibility; `getIdAttribute()` gives the real L3V2 `id`, and `sbmlinfo.sbase` never calls it. Verified on an L3V2 document: `AssignmentRule` with `id="rule_sr1" variable="sr1"` reports `id == "sr1"`. The id column of the rule tables therefore shows the target, and a real id is never shown.
3. **An `AlgebraicRule` gets a digest pk.** `AlgebraicRule::isSetId()` is `False` even when `id` is set (it is aliased to the non-existent `variable`), so `_key` falls through to `hashlib.sha1(sbase.toSBML())`. Verified: `pk == "m/AlgebraicRule:d3500b31f7030ecc85277da65c93717d039809ee"` for `<algebraicRule id="ar1">`. The pk is what the report page puts in the route, so the permalink of an algebraic rule is an opaque digest that changes whenever the math changes.
4. **A rule or initial assignment targeting a `SpeciesReference` shadows that species reference.** `links._elements` yields rules and initial assignments (whose `id` is the variable/symbol, see item 2) before it yields the species references of the reactions, and `ModelIndex.__init__` uses `setdefault`, so the rule wins. Reproduced with an L3V2 model whose `<assignmentRule variable="sr1">` sets the stoichiometry of `<speciesReference id="sr1">`: the graph contains `variable m/AssignmentRule:sr1 -> m/AssignmentRule:sr1` (a self-loop instead of an edge to the species reference) and `math m/KineticLaw:R1.kineticLaw -> m/AssignmentRule:sr1` (the `<ci>sr1</ci>` of the kinetic law resolves to the rule instead of the species reference). Variable stoichiometry is exactly the L3 feature this pattern exists for.
5. **Port ids leak into the SId namespace.** `links._elements` yields `model.list_of_ports`, so every `PortSId` lands in `ModelIndex.sids`. comp §3.4.3 states that `PortSId` is a separate namespace and that "it is possible for a PortSId value to be the same as some SId value in the model, without causing an identifier collision". Reproduced: a model with a port `comp:id="Vmax"` and a rule whose math is `<ci>Vmax</ci>` yields `sids["Vmax"] == "m/Port:Vmax"` and the edge `math m/AssignmentRule:p1 -> m/Port:Vmax`. The report invents a link where the specification says there is none, instead of logging an unresolved symbol.
6. **A constraint message is XHTML rendered as escaped text.** See §2.10. `Constraint.getMessageString()` returns the `<message>` wrapper and the XHTML, `ConstraintAttributes.vue` renders it with `ValueText`, and the constraint table column has kind `text`. The reader sees raw markup including the `xmlns` attribute. §4.10.2 puts a message under the same rules as `notes`, and `report/notes.ts` already exists to render exactly that.
7. **`Reaction.fast` is presented without its version.** §4.11.1 removed `fast` in L3V2 ("the fast attribute has been removed: every Reaction in a Level 3 Version 2 model is equivalent to an SBML Level 3 Version 1 Reaction with a fast value of false"). The value is correctly `None` for an L3V2 document, but the column, the inspector row and the glossary entry give no hint that the attribute cannot exist, so an L3V2 report carries a permanently empty column.

## 5. Every reference of the specification with no edge in the link graph

| # | reference | specification | today |
| --- | --- | --- | --- |
| 1 | `SBMLDocument` -> `Model` | core §4.1.2 | no edge; 38 of 38 document nodes isolated in the shipped examples |
| 2 | `SBMLDocument` -> `ExternalModelDefinition` | comp §3.3.1 | no edge |
| 3 | `SpeciesReference` -> `Species` | core §4.11.2 | the edge starts at the `Reaction`; 522 of 522 species reference nodes isolated |
| 4 | `ModifierSpeciesReference` -> `Species` | core §4.11.4 | the edge starts at the `Reaction`; 7 of 7 isolated |
| 5 | `Reaction` -> `SpeciesReference` / `ModifierSpeciesReference` | core §4.11.1 | no containment edge |
| 6 | `Reaction` -> `KineticLaw` | core §4.11.1 | no containment edge |
| 7 | `KineticLaw` -> `LocalParameter` | core §4.11.5 | no containment edge |
| 8 | `Event` -> `Trigger` / `Priority` / `Delay` | core §4.12.1 | the objects do not exist |
| 9 | `Event` -> `EventAssignment` | core §4.12.1 | no containment edge |
| 10 | `Model` -> its elements | core §4.2.7 | no containment edge (`Node.model` only) |
| 11 | `UnitDefinition` -> `Unit` | core §4.4.1 | the objects do not exist; 273 of 513 unit definition nodes isolated |
| 12 | any `units` attribute -> a base unit | core §4.4.2 | base units are not nodes, so `units="litre"` is an unlinked string |
| 13 | `Trigger` / `Priority` / `Delay` math symbols | core §4.12.2-4 | all attributed to the `Event`, so the three cannot be told apart |
| 14 | `ReplacedElement` -> the replaced element in the submodel | comp §3.6.2 | edge goes to the `Submodel` only (52 such edges in the shipped comp models) |
| 15 | `ReplacedBy` -> the replacing element in the submodel | comp §3.6.4 | edge goes to the `Submodel` only |
| 16 | `Deletion` -> the deleted element | comp §3.5.3 | no object, no edge |
| 17 | `ReplacedElement.deletion` -> the `Deletion` | comp §3.6.2 | attribute not read |
| 18 | `ReplacedElement.conversionFactor` -> the `Parameter` | comp §3.6.2, §3.8.1 | attribute not read |
| 19 | `ExternalModelDefinition.modelRef` -> the model in the referenced document | comp §3.3.2 | plain text, no edge, no indication of resolution |
| 20 | `Port.portRef` -> the port of a submodel | comp §3.7.1, §3.4.3 | plain text, no edge |
| 21 | a recursive `sBaseRef` chain | comp §3.7.2 | the child is not read at all |

One further observation, not counted as a missing edge: a `math` edge is emitted with the same kind for a variable read and for a call to a `FunctionDefinition` (core §4.3.4), so the two cannot be distinguished in the graph.

## 6. Example models shipping with the backend

`backend/sbml4humans/resources/` ships 24 small examples, 14 comp models (the icg, dex and spt families), the repressilator, a glucose model, two fbc models and 49 curated BioModels as COMBINE archives.

**comp is shipped and partly exercised.** Counted over `resources/examples/` and `resources/models/`: 64 `comp:submodel`, 139 `comp:port`, 139 `comp:idRef`, 52 `comp:replacedElement`, 52 `comp:portRef`, 12 `comp:externalModelDefinition`, 2 `comp:modelDefinition`. `minimal_model_comp.xml` and `model_composition.xml` are the small examples; `icg_body.xml`, `dex_body.xml` and `spt_body.xml` are the real ones.

**What no shipped model exercises** (count 0 in every file):

- comp: `comp:deletion` and `comp:listOfDeletions`, `comp:replacedBy`, the recursive `comp:sBaseRef`, `comp:md5`, `comp:unitRef`, `comp:metaIdRef`, and a `conversionFactor` or `deletion` attribute on a `comp:replacedElement`. So the `replacedBy` edge kind, the `port` edge for a `unitRef` or a `metaIdRef` and `links._meta_id_edge` have no example behind them.
- core: `<constraint>` and `<message>` (0 occurrences in the examples, the comp models, the repressilator, the glucose model and all 49 BioModels), `<priority>` (0), `<localParameter>` (0 in L3 form; the L2 kinetic-law parameters of the BioModels never reach the report, see §4 item 1). `<algebraicRule>` appears once, `<delay>` once, `<functionDefinition>` twice.

**A small example that would close the comp part** would be one document with: a `listOfModelDefinitions` holding two model definitions and a `listOfExternalModelDefinitions` entry carrying `source`, `modelRef`, `md5` and `name`; two submodels, one with a `listOfDeletions` containing a `<deletion>` with `id`, `name`, `notes` and an `idRef`, the other with `timeConversionFactor` and `extentConversionFactor`; a species with a `listOfReplacedElements` entry carrying `submodelRef`, `idRef`, `conversionFactor` and `deletion`, and a second entry using `metaIdRef`; a parameter with a `replacedBy` using `portRef`; a port per ref kind (`idRef`, `unitRef`, `metaIdRef`, `portRef`); and one `sBaseRef` nested two levels deep to reach an element of a sub-submodel.

**A small core example** would add: a `<constraint>` with a `<message>` containing real XHTML; an `<event>` with a `<priority>`, a `<delay>` and a `<trigger>` that each carry `id`, `metaid`, `sboTerm` and `notes`; a `<kineticLaw>` with a `<listOfLocalParameters>`; a `<unitDefinition>` with several `<unit>` elements using non-trivial `exponent`, `scale` and `multiplier`, and one with an empty `<listOfUnits>`; an `<algebraicRule id=...>`, an `<assignmentRule id=... variable=...>` and an `<initialAssignment id=... symbol=...>` to pin the id handling of §4 item 2; an `<assignmentRule>` whose `variable` is a `<speciesReference id=...>` to pin §4 item 4; `notes`, `annotation` and `sboTerm` on a `<listOfSpecies>` and on an empty `<listOfConstraints>`; and a non-RDF `<annotation>` on the `<model>` and on the `<sbml>` element.
