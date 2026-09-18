# Gap list: the packages fbc, qual and distrib

Read only audit of what the report carries of the three packages. Sources: the specifications under `/home/mkoenig/git/sbml-specifications`, `python-libsbml` 5.21.1 (the version `backend/uv.lock` pins; the worktree has no `.venv`, so the audit installed exactly that version into a scratchpad venv and ran `sbml4humans.sbmlinfo` against it out of tree), and the code of `backend/sbml4humans/{model,sbmlinfo,links,glossary}.py`, `frontend/src/report/columns/`, `frontend/src/components/inspector/attributes/`, `frontend/src/data/sbmlTypes.ts` and `glossary/packages.toml`.

Scope checked: 27 classes and 104 attributes (fbc 15 classes / 58 attributes, qual 8 classes / 29 attributes, distrib 4 classes / 17 attributes).

Legend of the tables: "spec" is the section of the package specification, the next columns are yes/no for the report model (`model.py`), the walk (`sbmlinfo.py`), the link graph (`links.py`), the table column (`report/columns/`), the inspector row (`components/inspector/attributes/`) and the glossary (`glossary/packages.toml`).

---

## 1. fbc (flux balance constraints)

### Which version the report supports

The report has no version logic at all. `sbmlinfo` asks for the `fbc` plugin and reads the attributes it happens to find, so what a reader sees depends entirely on which package version the document uses:

- **Version 1**: everything specific to V1 is lost. The bounds of a V1 model live in `FluxBound` objects under `model/listOfFluxBounds`, and the report models no `FluxBound`. Evidence (a V1 document built with libsbml, put through `SBMLDocumentInfo.from_sbml`): the two `FluxBound` objects of the model produce no report object and no graph node (`any node of type FluxBound? []`), while the reaction still gets an `fbc` block reading `{'lowerFluxBound': None, 'upperFluxBound': None, 'geneProductAssociation': None, 'geneProducts': []}`. A reader of a Version 1 FBA model sees a model with no bounds, and nothing tells them the bounds exist in the file.
- **Version 2**: the best supported case. Carried: species `chemicalFormula`/`charge`, reaction `lowerFluxBound`/`upperFluxBound`, `GeneProduct`, `Objective` with its `FluxObjective`s, and a flattened gene product association. Missing: `strict`, `activeObjective`, the `GeneProductAssociation` object and its `And`/`Or`/`GeneProductRef` tree.
- **Version 3** (which libsbml 5.21.1 fully supports and which the shipped example `resources/examples/fbc_example.xml` uses): additionally missing `FluxObjective.variableType` and `reaction2`, `UserDefinedConstraint`, `UserDefinedConstraintComponent`, `KeyValuePair`, and the widening of `charge` from integer to double.

`glossary/packages.toml` cites "Flux Balance Constraints, Version 2 Release 1" as the specification of the fbc entries, while the repository's own fbc example is a Version 3 document.

### What a Version 2 document carries that a Version 1 one does not

| construct | V1 | V2 | in the report |
| --- | --- | --- | --- |
| `Model` `strict` | not defined | required | no |
| `Model` `listOfFluxBounds` / `FluxBound` | yes | removed (deprecated) | no |
| `Model` `listOfGeneProducts` / `GeneProduct` | not defined | yes | yes |
| `Reaction` `lowerFluxBound`, `upperFluxBound` (SIdRef to a `Parameter`) | not defined | yes | yes |
| `Reaction` `geneProductAssociation` | not defined | yes | flattened to an infix string |
| `Species` `charge`, `chemicalFormula` | yes | yes | yes |
| `Objective`, `FluxObjective`, `activeObjective` | yes | yes | all but `activeObjective` |

### extended `Model`

| class | attribute | spec | model.py | sbmlinfo.py | links.py | column | inspector | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Model | `strict` | 3.3 "The attribute strict" | no | no | n/a | no | no | no |
| Model | `listOfObjectives` | 3.3.1 | yes (`list_of_objectives`) | yes | nodes | own table | own table | yes |
| Model | `listOfGeneProducts` | 3.3.2 | yes (`list_of_gene_products`) | yes | nodes | own table | own table | yes |
| Model | `listOfFluxBounds` (V1) | V1R1 "The FluxBound class" | no | no | no | no | no | no |
| Model | `listOfUserDefinedConstraints` (V3) | 3.3.3 | no | no | no | no | no | no |
| ListOfObjectives | `activeObjective` | 3.3.1 "The activeObjective attribute" | no | no | no | no | no | no |

Missing:

- **`strict`** (3.3). The single attribute that says whether the model is a well formed LP/QP: whether every reaction has bounds, whether every `FluxObjective` coefficient is a finite number, whether stoichiometries are constant. Without it a reader cannot tell a curated genome scale reconstruction from a hybrid model in which an `AssignmentRule` moves a bound during simulation, which changes how every other number in the report has to be read. `libsbml.FbcModelPlugin.isSetStrict()`/`getStrict()`.
- **`activeObjective`** (3.3.1). When a model defines several objectives, this names the one that is optimised. The report lists the objectives without marking which one is active, so a reader of a model with two objectives cannot tell which one describes the published simulation. `FbcModelPlugin.getActiveObjectiveId()`.
- **`FluxBound`** (fbc Version 1 Release 1, "The FluxBound class": `id`, `name`, `reaction`, `operation` of `greaterEqual`/`lessEqual`/`equal`/`greater`/`less`, `value`) - **class missing entirely**. Every constraint of a Version 1 model is invisible.
- **`UserDefinedConstraint`** (V3 3.14, `id`, `name`, `lowerBound`, `upperBound`, `listOfUserDefinedConstraintComponents`) and **`UserDefinedConstraintComponent`** (V3 3.15, `id`, `name`, `variable`, `variable2`, `coefficient`, `variableType`) - **classes missing entirely**. These are the constraints beyond the per reaction bounds (for example a ratio constraint between two fluxes); a reader of a V3 model with them sees a solution space that is wider than the one the model defines.
- **`KeyValuePair`** (V3 3.17, `id`, `name`, `key`, `value`, `uri`, attached to any `SBase` through `FbcSBasePlugin`) - **class missing entirely**. This is the fbc replacement for uncontrolled annotation, so any tool metadata written this way is dropped without a trace.

### extended `Species`

| class | attribute | spec | model.py | sbmlinfo.py | links.py | column | inspector | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Species | `chemicalFormula` | 3.4 | yes (`fbc.chemical_formula`) | yes | n/a | **no** | yes | yes |
| Species | `charge` | 3.4 | yes (`fbc.charge`, `int`) | yes | n/a | **no** | yes | yes |

Missing: no attribute is missing, but neither appears in the species table (`frontend/src/report/columns/core.ts`, `Species`). In `e_coli_core.xml.gz` 72 of 72 species carry a formula and a charge; a reader who wants to check the mass and charge balance of the model has to open all 72 species one after the other in the inspector.

### extended `Reaction`

| class | attribute | spec | model.py | sbmlinfo.py | links.py | column | inspector | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Reaction | `lowerFluxBound` | 3.8 | yes | yes | `fluxBound` edge | **no** | yes | yes |
| Reaction | `upperFluxBound` | 3.8 | yes | yes | `fluxBound` edge | **no** | yes | yes |
| Reaction | `geneProductAssociation` | 3.8 | infix string only | partially | `geneProduct` edge from the reaction | **no** | yes | yes |

Missing: no reaction table column for the bounds or the association. `e_coli_core` has 95 reactions with bounds and 138 with an association; the reaction table shows only the equation, so the flux capacities, the core content of the model, are one click away per reaction and never side by side.

### `Objective` and `FluxObjective`

| class | attribute | spec | model.py | sbmlinfo.py | links.py | column | inspector | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Objective | `id` | 3.6 | yes (SBase) | yes | node | yes | yes | yes |
| Objective | `name` | 3.6 | yes (SBase) | yes | node | yes | yes | yes |
| Objective | `type` | 3.6 | yes | yes | n/a | yes | yes | yes |
| Objective | `listOfFluxObjectives` | 3.6 | yes | yes | `fluxObjective` edges | count | nested table | yes |
| FluxObjective | `id` | 3.7 | **no** | no | no | no | no | no |
| FluxObjective | `name` | 3.7 | **no** | no | no | no | no | no |
| FluxObjective | `reaction` | 3.7 | yes | yes | `fluxObjective` edge, sourced from the `Objective` | nested | yes | **no** |
| FluxObjective | `reaction2` (V3) | 3.7 | **no** | no | no | no | no | no |
| FluxObjective | `coefficient` | 3.7 | yes | yes | n/a | nested | yes | **no** |
| FluxObjective | `variableType` (V3) | 3.7 | **no** | no | n/a | no | no | no |

Missing:

- **`FluxObjective` is not an `SBase` of the report** (3.7: it derives from `SBase` and carries `metaid`, `sboTerm`, `notes`, `annotation`, plus optional `id` and `name`). It is a plain `ReportModel` with `reaction` and `coefficient`, so it has no pk, no node, no annotations and no notes. A reader cannot follow a link to a flux objective, cannot see its SBO term (fbc defines SBO terms for objective components) and cannot see a note explaining why a reaction was given that weight.
- **`variableType`** (V3 3.7, `linear` or `quadratic`) and **`reaction2`**. Without `variableType` a quadratic objective is displayed as if it were linear: `Minimize: 1 R1 + [4 R2^2]/2` and `Minimize: 1 R1 + 4 R2` render identically. The repository's own `resources/examples/fbc_example.xml` writes `fbc:variableType="linear"` on all four of its flux objectives, and the report drops it.
- The `fluxObjective` edge is emitted with the **`Objective` as its source** (`links.py:281`), because the flux objective has no node. The graph therefore says "this objective references this reaction" and loses the coefficient that relates them.

### `GeneProduct`

| class | attribute | spec | model.py | sbmlinfo.py | links.py | column | inspector | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GeneProduct | `id` | 3.5 | yes (SBase) | yes | node | yes | yes | yes |
| GeneProduct | `name` | 3.5 | yes (SBase) | yes | node | yes | yes | yes |
| GeneProduct | `label` | 3.5 | yes | yes | n/a | yes | yes | yes |
| GeneProduct | `associatedSpecies` | 3.5 | yes | yes | `associatedSpecies` edge | yes | yes | yes |

Complete. The only gap is the reverse direction: a gene product does not show which reactions reference it, because the `geneProduct` edge runs from the reaction and nothing in the inspector of a gene product lists the incoming edges of that kind.

### `GeneProductAssociation`, `And`, `Or`, `GeneProductRef`

| class | attribute | spec | model.py | sbmlinfo.py | links.py | column | inspector | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GeneProductAssociation | `id` | 3.9 | **no** | no | no | no | no | no |
| GeneProductAssociation | `name` | 3.9 | **no** | no | no | no | no | no |
| GeneProductAssociation | `association` (the tree) | 3.9 | infix string | `root.toInfix()` | no | no | as text | yes |
| GeneProductRef | `id` | 3.11 | **no** | no | no | no | no | no |
| GeneProductRef | `name` | 3.11 | **no** | no | no | no | no | no |
| GeneProductRef | `geneProduct` | 3.11 | id collected into `fbc.gene_products` | yes | `geneProduct` edge from the reaction | no | chips | yes |
| And | `id`, `name` | 3.12 | **no** | no | no | no | no | no |
| And | `elements` (2 or more associations) | 3.12 | **no** (flattened) | no | no | no | no | no |
| Or | `id`, `name` | 3.13 | **no** | no | no | no | no | no |
| Or | `elements` (2 or more associations) | 3.13 | **no** (flattened) | no | no | no | no | no |

Missing:

- **The whole association tree as data** (3.9 to 3.13). `sbmlinfo.reaction_fbc` stores `root.toInfix()` and a flat sorted set of the referenced gene product ids. The nesting, which is the meaning of the construct (an `And` is an enzyme complex, an `Or` is an isozyme), survives only as parentheses inside one unstructured string. A reader cannot click a gene in the association, cannot see which subtree a gene belongs to, and the graph cannot answer "which reactions does this gene knock out on its own".
- **The `GeneProductAssociation`, `And`, `Or` and `GeneProductRef` objects** (3.9 to 3.11, 3.12, 3.13) are `SBase` in the specification, with `metaid`, `sboTerm`, `notes` and `annotation` and an optional `id`/`name`. All of that is discarded.

### Wrong rather than missing (fbc)

1. **The association string and the gene product chips use two different naming systems.** `libsbml.FbcAssociation.toInfix()` takes an optional `usingId` flag which defaults to `false`, so the string is rendered with the gene **labels**; `_gene_product_refs` collects the gene **ids**. Evidence from a V2 document with `g1/b0001`, `g2/b0002`, `g3/b0003`: the report produced `"geneProductAssociation": "(b0001 or (b0002 and b0003))"` next to `"geneProducts": ["g1", "g2", "g3"]`, and `ReactionAttributes.vue` shows both rows one under the other. The reader sees six names for three genes and no way to match them, and the linked chips are the ones that carry the less readable name. (In `e_coli_core` all 137 gene products carry a label.)
2. **Every reaction and every species of any fbc document gets a non-null `fbc` block.** `reaction_fbc` returns a `ReactionFbc` whenever the plugin exists, even when nothing is set, so `ReactionAttributes.vue` renders four rows of "-" for every reaction of a Version 1 document (where those attributes do not exist in the language at all) and for every unbounded reaction of a Version 2 one. `SpeciesFbc` has the same shape.
3. **`SpeciesFbc.charge` is typed `int`.** fbc Version 3 (3.4, "The charge attribute") widened `charge` to a signed **double** so that a pseudoisomer can carry a fractional charge, and libsbml exposes `FbcSpeciesPlugin.getChargeAsDouble()`. `sbmlinfo.species` calls `_attribute(fbc, "charge")`, which resolves to `getCharge()` and truncates.

### Example model in `backend/sbml4humans/resources/`

Yes, three, but none of Version 1:

- `examples/fbc_example.xml` - fbc **Version 3** (`comp` + `fbc`), objectives with `fbc:variableType`, reaction bounds, `strict="false"`, `activeObjective`. No gene products, no user defined constraints.
- `examples/fbc_mass_charge.xml` - fbc Version 2, `charge` and `chemicalFormula` on five species, `strict`.
- `models/fbc/e_coli_core.xml.gz` and `models/fbc/Recon3D.xml.gz` - fbc Version 2 genome scale models: 137 gene products, 138 associations with 54 `and` and 64 `or` nodes, 95 reactions with bounds, 72 species with formula and charge.

A small **Version 1** example is missing and would have to contain: a `listOfFluxBounds` with at least two `fluxBound` elements on the same reaction (`operation="greaterEqual"` and `operation="lessEqual"`, one of them with `value="INF"` to exercise the infinite bound), a `listOfObjectives` with `activeObjective` and two objectives of different `type` so that the active one is distinguishable, a `fluxObjective` with a negative coefficient, and species with `fbc:charge` and `fbc:chemicalFormula`. A small **Version 3** addition would need a `listOfUserDefinedConstraints` with one constraint over two reaction variables, a quadratic `fluxObjective` (`variableType="quadratic"` plus `reaction2`), a non-integer `charge` and a `listOfKeyValuePairs`.

---

## 2. qual (qualitative models)

**The package is not supported at all.** No class, no attribute, no list, no edge, no column, no inspector component, no glossary entry, no example. `frontend/src/data/sbmlTypes.ts` declares `export type SbmlPackage = "core" | "comp" | "fbc" | "distrib"` and `glossary.py` declares the same four packages in `PACKAGES`, so qual is absent from both ends of the pipeline.

Evidence: a two species, one transition qual model put through `SBMLDocumentInfo.from_sbml` produced a report whose only non-empty model list was `listOfCompartments` (1 entry) and whose link graph held three nodes (document, model, compartment) and zero edges. The sole trace of the package is the `qual` badge in `document.packages`, produced by the generic plugin loop in `sbmlinfo.document`.

### How libsbml exposes it (verified against python-libsbml 5.21.1)

`model.getPlugin("qual")` returns a `libsbml.QualModelPlugin` with `getNumQualitativeSpecies()`, `getQualitativeSpecies(i)`, `getListOfQualitativeSpecies()`, `getNumTransitions()`, `getTransition(i)`, `getListOfTransitions()`. The classes `QualitativeSpecies`, `Transition`, `Input`, `Output`, `FunctionTerm`, `DefaultTerm`, `ListOfQualitativeSpecies`, `ListOfTransitions`, `ListOfInputs`, `ListOfOutputs`, `ListOfFunctionTerms` all exist in `dir(libsbml)`, the package is in `SBMLExtensionRegistry` and its default package version is 1.

Every attribute follows the `isSetX()`/`getX()` convention the existing `_attribute` helper in `sbmlinfo.py` already uses, so the walk needs no new mechanism. Two details matter:

- `getInitialLevel()`, `getMaxLevel()`, `getThresholdLevel()`, `getOutputLevel()` return `2147483647` (int max) when unset, so the `isSet` guard is not optional.
- `sign`, `transitionEffect` on `Input` and `transitionEffect` on `Output` are returned as **integers**, and libsbml provides **no** `_toString` helper for them (unlike `UncertType_toString` for distrib or `FbcVariableType_toString` for fbc). Verified values: `INPUT_SIGN_POSITIVE=0`, `NEGATIVE=1`, `DUAL=2`, `UNKNOWN=3`, `VALUE_NOTSET=4`; `INPUT_TRANSITION_EFFECT_NONE=0`, `CONSUMPTION=1`, `UNKNOWN=2`; `OUTPUT_TRANSITION_EFFECT_PRODUCTION=0`, `ASSIGNMENT_LEVEL=1`, `UNKNOWN=2`. The report has to map them to the spec strings itself.
- Contrary to the UML caption in the specification ("Note that the DefaultTerm class is not derived from SBase"), libsbml implements `DefaultTerm` with the full `SBase` surface (`isSetMetaId`, `isSetSBOTerm`, `isSetNotes`, `getCVTerms`), and its type code renders as `DefaultTerm`. It can be treated like every other element of the report.

### extended `Model`

| class | attribute | spec | model.py | sbmlinfo.py | links.py | column | inspector | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Model | `listOfQualitativeSpecies` | 3.4 | **no** | no | no | no | no | no |
| Model | `listOfTransitions` | 3.4 | **no** | no | no | no | no | no |

### `QualitativeSpecies` - **class missing entirely**

| class | attribute | spec | model.py | sbmlinfo.py | links.py | column | inspector | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| QualitativeSpecies | `id` (required, SId) | 3.5 | no | no | no | no | no | no |
| QualitativeSpecies | `name` | 3.5 | no | no | no | no | no | no |
| QualitativeSpecies | `compartment` (required, SIdRef) | 3.5 | no | no | **no edge** | no | no | no |
| QualitativeSpecies | `constant` (required, boolean) | 3.5 | no | no | n/a | no | no | no |
| QualitativeSpecies | `initialLevel` (non-negative integer) | 3.5 | no | no | n/a | no | no | no |
| QualitativeSpecies | `maxLevel` (non-negative integer) | 3.5 | no | no | n/a | no | no | no |

What a reader loses: the entities of the model. In a logical model these are the nodes of the influence graph, in a Petri net the places. `initialLevel` is the initial state of the system and `maxLevel` says whether the variable is Boolean (`maxLevel=1`) or multi valued, which decides how every function term has to be read. `constant=true` marks an input of the system that no transition changes.

### `Transition` - **class missing entirely**

| class | attribute | spec | model.py | sbmlinfo.py | links.py | column | inspector | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Transition | `id` (optional, SId, no mathematical meaning) | 3.6 | no | no | no | no | no | no |
| Transition | `name` | 3.6 | no | no | no | no | no | no |
| Transition | `listOfInputs` (0 or 1, at least one `Input`) | 3.6 | no | no | no | no | no | no |
| Transition | `listOfOutputs` (0 or 1, at least one `Output`) | 3.6 | no | no | no | no | no | no |
| Transition | `listOfFunctionTerms` (exactly 1) | 3.6 | no | no | no | no | no | no |

What a reader loses: the entire dynamics. A transition is to a qualitative model what a reaction plus its kinetic law is to a kinetic one. Without it the report of a qual model is a list of compartments.

### `Input` - **class missing entirely**

| class | attribute | spec | model.py | sbmlinfo.py | links.py | column | inspector | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Input | `id` (optional; usable as `<ci>` in a function term, where it means the `thresholdLevel`) | 3.6.1 | no | no | no | no | no | no |
| Input | `name` | 3.6.1 | no | no | no | no | no | no |
| Input | `qualitativeSpecies` (required, SIdRef) | 3.6.1 | no | no | **no edge** | no | no | no |
| Input | `thresholdLevel` (non-negative integer) | 3.6.1 | no | no | n/a | no | no | no |
| Input | `transitionEffect` (required, `none` or `consumption`) | 3.6.1 | no | no | n/a | no | no | no |
| Input | `sign` (`positive`, `negative`, `dual`, `unknown`) | 3.6.1 | no | no | n/a | no | no | no |

`sign` is called out in the specification as existing "particularly for visualization purposes": it is what turns an influence graph into a picture of activation and inhibition. It is exactly the attribute a human readable report of a regulatory model should be showing, and the report has no place for it.

### `Output` - **class missing entirely**

| class | attribute | spec | model.py | sbmlinfo.py | links.py | column | inspector | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Output | `id` (optional; in a function term it means the `outputLevel`) | 3.6.2 | no | no | no | no | no | no |
| Output | `name` | 3.6.2 | no | no | no | no | no | no |
| Output | `qualitativeSpecies` (required, SIdRef) | 3.6.2 | no | no | **no edge** | no | no | no |
| Output | `outputLevel` (non-negative integer, required when `transitionEffect="production"`) | 3.6.2 | no | no | n/a | no | no | no |
| Output | `transitionEffect` (required, `production` or `assignmentLevel`) | 3.6.2 | no | no | n/a | no | no | no |

`transitionEffect` on the output is what distinguishes a logical model (`assignmentLevel`) from a Petri net (`production`); without it a reader cannot tell which of the two formalisms the file encodes.

### `ListOfFunctionTerms`, `DefaultTerm`, `FunctionTerm` - **classes missing entirely**

| class | attribute | spec | model.py | sbmlinfo.py | links.py | column | inspector | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ListOfFunctionTerms | `defaultTerm` (exactly one) | 3.6.3 | no | no | no | no | no | no |
| ListOfFunctionTerms | `functionTerm` (any number) | 3.6.3 | no | no | no | no | no | no |
| DefaultTerm | `resultLevel` (required, non-negative integer) | 3.6.4 | no | no | n/a | no | no | no |
| FunctionTerm | `resultLevel` (required, non-negative integer) | 3.6.5 | no | no | n/a | no | no | no |
| FunctionTerm | `math` (required, a boolean MathML expression) | 3.6.5 | no | no | **no math edges** | no | no | no |

The math of a function term is ordinary SBML MathML, so `mathml.math_info` and `math_symbols` render and index it with no change. The symbols it contains are ids of `QualitativeSpecies`, `Input` and `Output` objects (meaning respectively their level, their `thresholdLevel` and their `outputLevel`, 3.6.5), and qual ids share the core SId namespace (3.7), so `ModelIndex` resolves them once those objects are nodes.

### References the specification defines which the link graph does not have as an edge (qual)

1. `QualitativeSpecies.compartment` to `Compartment` (3.5) - the analogue of the existing `compartment` edge of a species.
2. `Input.qualitativeSpecies` to `QualitativeSpecies` (3.6.1) - the regulator side of the influence graph.
3. `Output.qualitativeSpecies` to `QualitativeSpecies` (3.6.2) - the regulated side.
4. `FunctionTerm.math` symbols to the `QualitativeSpecies`, `Input` and `Output` they name (3.6.5).

Edges 2 and 3 together are the influence graph, which is the single reason to draw a qual model at all; a `sign` on the input would classify each of them as activation or inhibition. None of the 17 kinds of `EdgeKind` covers them.

### What a reader of a qualitative model needs to see

In order: the qualitative species with `initialLevel`, `maxLevel` and `constant` (the state space); per transition, the inputs with `sign` and `thresholdLevel` and the outputs with `transitionEffect`, so that the regulators of each species are visible without reading MathML; the function terms as a table of "condition to result level" with the default term as the last row, which is the state transition table the specification describes in 3.6.6; and the influence graph as edges from input species to output species. A reader also needs to be told which formalism the file uses, which is readable from the output `transitionEffect` (`assignmentLevel` for a logical model, `production` for a Petri net) and from whether any input has `transitionEffect="consumption"`.

### Example model in `backend/sbml4humans/resources/`

**No.** Neither `examples/` nor `models/` contains a qual namespace (`grep -rl 'level3/version1/qual'` returns nothing).

The 49 curated BioModels in `resources/biomodels/` contain **no qual model either**. All 49 `.omex` archives were unzipped and scanned: each holds exactly one SBML file, every one of them is SBML **Level 2** (version 3 or 4), and no archive contains a single `qual:` element or any `fbc`, `qual` or `distrib` namespace declaration. The curated set is BIOMD0000000001 to 49, which predates the Level 3 packages.

A small qual example would have to contain: two compartments is unnecessary, one is enough; three `QualitativeSpecies` (one with `constant="true"` and a `maxLevel` but no `initialLevel`, to exercise the input-of-the-system case; one Boolean with `maxLevel="1"`; one multi valued with `maxLevel="2"` and an `initialLevel`); two `Transition` objects, the first with two `Input` elements of different `sign` (`positive` and `negative`) and different `transitionEffect` (`none` and `consumption`) and one with a `thresholdLevel`, the second with two `Output` elements of different `transitionEffect` (`assignmentLevel` and `production` with an `outputLevel`), so that both formalisms appear; each transition with a `listOfFunctionTerms` holding a `defaultTerm` and at least two `functionTerm` elements whose math references a qualitative species by id and an input by id, so that the math edges are exercised; and `name`, `metaid`, `notes` and an `annotation` on at least one qualitative species and one transition, so that the shared `SBase` rendering is exercised as well.

---

## 3. distrib (distributions)

### extended `SBase`

| class | attribute | spec | model.py | sbmlinfo.py | links.py | column | inspector | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SBase | `listOfUncertainties` | 3.9 | yes (`uncertainties`) | yes | nodes | n/a | yes | yes |

Carried correctly, including several uncertainties per element.

### `Uncertainty`

| class | attribute | spec | model.py | sbmlinfo.py | links.py | column | inspector | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Uncertainty | `id` (from `DistribBase`) | 3.8, 3.10.1 | yes (SBase) | yes | node | n/a | yes | yes |
| Uncertainty | `name` (from `DistribBase`) | 3.8, 3.10.1 | yes (SBase) | yes | node | n/a | yes | yes |
| Uncertainty | `listOfUncertParameters` | 3.10 | yes (`uncert_parameters`) | yes | n/a | n/a | nested table | yes |

Complete.

### `UncertParameter`

| class | attribute | spec | model.py | sbmlinfo.py | links.py | column | inspector | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UncertParameter | `type` (required, `UncertKind`) | 3.11.1 | yes | yes | n/a | n/a | yes | **no** |
| UncertParameter | `value` (double) | 3.11.2 | yes | yes | n/a | n/a | yes | **no** |
| UncertParameter | `var` (SIdRef) | 3.11.2 | yes | yes | **no edge** | n/a | yes, as plain text | **no** |
| UncertParameter | `units` (UnitSIdRef) | 3.11.3 | yes | yes | **no edge** | n/a | yes, as plain text | **no** |
| UncertParameter | `definitionURL` (ExternalRef) | 3.11.4 | yes | yes | n/a | n/a | yes, as a link | **no** |
| UncertParameter | `math` | 3.11.6 | yes | yes | math symbols, but attributed to the `Uncertainty` | n/a | yes | **no** |
| UncertParameter | `listOfUncertParameters` (for `distribution` and `externalParameter`) | 3.11.7 | **no** | no | no | n/a | no | no |
| UncertParameter | `id` (from `DistribBase`) | 3.8, 3.11.5 | **no** | no | no | n/a | no | no |
| UncertParameter | `name` (from `DistribBase`) | 3.8, 3.11.5 | **no** | no | no | n/a | no | no |
| UncertParameter | `metaid`, `sboTerm`, `notes`, `annotation` | 3.11.5 | **no** | no | no | n/a | no | no |

### `UncertSpan` - **class missing entirely**

| class | attribute | spec | model.py | sbmlinfo.py | links.py | column | inspector | glossary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UncertSpan | `varLower` (SIdRef) | 3.12 | **no** | no | no | n/a | no | no |
| UncertSpan | `valueLower` (double) | 3.12 | **no** | no | n/a | n/a | no | no |
| UncertSpan | `varUpper` (SIdRef) | 3.12 | **no** | no | no | n/a | no | no |
| UncertSpan | `valueUpper` (double) | 3.12 | **no** | no | n/a | n/a | no | no |

### The `type` values and what the report shows of them today

The 16 values of `UncertKind` (3.11.1 and the table of 3.10) split into three groups. libsbml reports the value as a string through `UncertParameter.getTypeAsString()`, which `sbmlinfo.uncertainties` uses, so the string is always right; what differs is whether the number behind it survives.

| `type` | class the spec requires | attributes that carry the number | shown by the report today |
| --- | --- | --- | --- |
| `coefficientOfVariation`, `kurtosis`, `mean`, `median`, `mode`, `sampleSize`, `skewness`, `standardDeviation`, `standardError`, `variance` (10 values) | `UncertParameter` | `value` or `var`, plus `units` | **fully** (the `var` as unlinked text) |
| `confidenceInterval`, `credibleInterval`, `interquartileRange`, `range` (4 values) | `UncertSpan` | `valueLower`/`varLower` and `valueUpper`/`varUpper`, plus `units` | **type only, every number lost** |
| `distribution` | `UncertParameter` | `definitionURL`, `math`, and child `UncertParameter`s | type, `definitionURL` and `math`; **the children lost** |
| `externalParameter` | either | any of the above, `definitionURL` required | the single value case only; **span ends and children lost** |

Evidence, from the shipped example `backend/sbml4humans/resources/examples/distrib_uncertainties.xml`, whose parameter `p1` carries `<distrib:uncertSpan distrib:type="range" distrib:valueLower="1" distrib:valueUpper="4"/>`. The report produces for that row:

```json
{"var": null, "value": null, "units": null, "type": "range", "definitionUrl": null, "math": null}
```

`UncertaintyAttributes.vue` renders it as a table row reading "range" followed by five empty cells. The same happened for a `confidenceInterval` defined by `varLower`/`varUpper`, and for a `distribution` with two `externalParameter` children (the children vanished).

Missing, with what a reader loses:

- **`UncertSpan` and its four attributes** (3.12). Four of the sixteen `UncertKind` values can only be expressed by an `UncertSpan`, and they are the ones a reader most wants: the 95 percent confidence interval and the range of a measured parameter. Today the report says the parameter has a range and refuses to say what it is, which is worse than saying nothing, and the defect is visible on the live site in a shipped example.
- **The nested `listOfUncertParameters`** (3.11.7). A `distribution` is fully defined by its child parameters: a Beta distribution is a `distribution` node with two `externalParameter` children for alpha and beta. Without them the report shows the name of a distribution and none of its parameters.
- **`id`, `name`, `metaid`, `sboTerm`, `notes` and `annotation` on an `UncertParameter`** (3.8, 3.11.5). The provenance of a measurement (which paper, which experiment) is exactly what a `notes` on an uncert parameter carries, and the package exists to record provenance.

### References the specification defines which the link graph does not have as an edge (distrib)

1. `UncertParameter.var` to the element with mathematical meaning it names (3.11.2). `UncertaintyAttributes.vue` prints it as plain text. A reader cannot jump from "the standard deviation of this parameter is the value of `sd_p1`" to `sd_p1`.
2. `UncertSpan.varLower` and `UncertSpan.varUpper` (3.12) - two more, once the class exists.
3. `UncertParameter.units` to the `UnitDefinition` it names (3.11.3). Every other `units` attribute of the report gets a `units` edge (`links._units_edge`); the one on an uncert parameter does not, because `_model_edges` only calls `_math_edges` for an uncertainty (`links.py:212-213`).

### Wrong rather than missing (distrib)

1. **The math of every `UncertParameter` is recorded under the pk of its `Uncertainty`.** `sbmlinfo.uncertainties` passes `fields["pk"]` (the uncertainty) as the owner of each parameter's math, so the symbols of all parameters of one uncertainty are merged into one set and every resulting `math` edge is sourced from the uncertainty. With one parameter carrying math this is invisible; with a `distribution` plus an `externalParameter` both carrying math the graph cannot say which of the two references what.
2. **The glossary promises what the report cannot deliver.** `glossary/packages.toml`, `types.distrib`, states that the package records "a mean, a standard deviation, a variance, a confidence interval or the distribution a value was drawn from". Of those, the confidence interval is precisely the one the report drops, and the distribution loses its parameters.

### Example model in `backend/sbml4humans/resources/`

Yes, four: `examples/distrib_uncertainties.xml`, `examples/distrib_distributions.xml`, `examples/distrib_comp.xml`, `examples/distrib_comp_flat.xml`, plus `models/comp/spt_liver.xml` and `models/comp/spt_body_flat.xml` which carry the namespace.

`distrib_uncertainties.xml` already exercises `mean`, `standardDeviation`, `range` (as an `uncertSpan` with `valueLower`/`valueUpper`) and `distribution` with a `definitionURL` and a `normal(2, 2)` csymbol, so the `UncertSpan` gap needs no new example to be reproduced, only the fix. `distrib_distributions.xml` exercises the other half of the package, the extended `csymbol` math (3.5, "Extended Math"), which the report does render through `mathml.py` as an ordinary function application.

What the existing examples do **not** exercise and a small addition would have to contain: an `uncertSpan` defined by `varLower`/`varUpper` rather than by values (to exercise the two missing edges), an `uncertParameter` with a `var` and a `units` (the third missing edge), a `distribution` with child `uncertParameter` elements of type `externalParameter` (the nested list), two `uncertainty` elements on one parameter with different `id`, `name` and `notes` (several measurements from different sources, which the specification calls out in 3.10), and an uncertainty on something other than a parameter, for example on a species and on an `assignmentRule`.

---

## Summary of the gaps

### Classes missing entirely from the report model (15)

- fbc (8): `FluxBound` (V1), `GeneProductAssociation`, `GeneProductRef`, `And`, `Or`, `UserDefinedConstraint` (V3), `UserDefinedConstraintComponent` (V3), `KeyValuePair` (V3).
- qual (6): `QualitativeSpecies`, `Transition`, `Input`, `Output`, `FunctionTerm`, `DefaultTerm`. (`ListOfFunctionTerms` is a container with no attributes of its own, but it carries the "exactly one default term" rule.)
- distrib (1): `UncertSpan`.

### Attributes missing from classes the report does model (13 plus the 29 of qual)

- fbc (6): `Model.strict`, `ListOfObjectives.activeObjective`, `FluxObjective.id`, `FluxObjective.name`, `FluxObjective.reaction2`, `FluxObjective.variableType`.
- distrib (7): `UncertParameter.id`, `UncertParameter.name`, `UncertParameter.listOfUncertParameters`, and the four `UncertSpan` attributes `varLower`, `valueLower`, `varUpper`, `valueUpper`.
- qual (29): all of them, since no qual class is modelled.

Additionally, four classes that the specification derives from `SBase` are modelled as plain values without pk, notes, annotations or SBO term: `FluxObjective`, `UncertParameter`, and (were they modelled at all) `GeneProductAssociation` and the `Association` subclasses.

### Attributes carried but shown in no table column (6)

`Species.fbc.chemicalFormula`, `Species.fbc.charge`, `Reaction.fbc.lowerFluxBound`, `Reaction.fbc.upperFluxBound`, `Reaction.fbc.geneProductAssociation`, `Reaction.fbc.geneProducts`. All are in the inspector, none is in the table, which for a genome scale model means the fbc content is only reachable one element at a time.

### References with no edge in the link graph (15, plus 2 mis-sourced)

- fbc (7): `ListOfObjectives.activeObjective` to `Objective`; `FluxBound.reaction` to `Reaction` (V1); `UserDefinedConstraint.lowerBound` and `.upperBound` to `Parameter` (V3); `UserDefinedConstraintComponent.variable`, `.variable2` and `.coefficient` to `Parameter` (V3).
- distrib (4): `UncertParameter.var`, `UncertSpan.varLower`, `UncertSpan.varUpper`, `UncertParameter.units`.
- qual (4): `QualitativeSpecies.compartment`, `Input.qualitativeSpecies`, `Output.qualitativeSpecies`, and the symbols of a `FunctionTerm` math.

Mis-sourced (2): the `fluxObjective` edge is emitted from the `Objective` instead of from the `FluxObjective`, and the `geneProduct` edge from the `Reaction` instead of from the `GeneProductRef`; in both cases because the referencing object is not a node.

### Wrong rather than missing (6)

1. The gene product association string is rendered with gene **labels** (`toInfix()` defaults to `usingId=false`) while the linked chips beside it carry gene **ids**.
2. An `UncertSpan` is read as a plain `UncertParameter`, so its numbers are silently dropped; reproducible in the shipped `distrib_uncertainties.xml`.
3. The nested `listOfUncertParameters` of a `distribution` parameter is silently dropped.
4. `ReactionFbc` and `SpeciesFbc` are constructed whenever the plugin exists, so every reaction of an fbc document shows four empty fbc rows even in Version 1, where the attributes do not exist.
5. `SpeciesFbc.charge` is an `int`, but fbc Version 3 defines `charge` as a double.
6. The math of an `UncertParameter` is registered under the pk of its parent `Uncertainty`, merging the symbols of all its parameters.

### Examples

| package | example ships | what is not exercised |
| --- | --- | --- |
| fbc | yes: `examples/fbc_example.xml` (V3), `examples/fbc_mass_charge.xml` (V2), `models/fbc/e_coli_core.xml.gz` and `Recon3D.xml.gz` (V2) | fbc Version 1 entirely (no `listOfFluxBounds` anywhere), and the V3 constructs `userDefinedConstraint`, `keyValuePair`, quadratic `fluxObjective`, non-integer `charge` |
| qual | **no**, and none of the 49 curated BioModels contains a qual model (all are SBML Level 2 with no package namespace) | everything |
| distrib | yes: `examples/distrib_uncertainties.xml`, `distrib_distributions.xml`, `distrib_comp.xml`, `distrib_comp_flat.xml` | spans defined by `varLower`/`varUpper`, `var` and `units` on a parameter, nested `uncertParameter` children, several uncertainties on one element, uncertainty on a non parameter element |
