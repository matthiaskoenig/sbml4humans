# Model

The container of everything a model is made of.

The model holds the lists of every element: the function definitions, the unit definitions, the compartments, the species, the parameters, the initial assignments, the rules, the constraints, the reactions and the events. It also sets the units which the elements inherit when they do not declare their own, in particular the unit of time, which exists nowhere else.

The report shows the model as the root of the report, its lists as the sections of the report, and its units in the attributes of the inspector.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [substance units](#substance-units) | `UnitSIdRef` | the units of the amounts of the species which do not declare their own | [core 4.2.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [time units](#time-units) | `UnitSIdRef` | the unit in which time is measured in the model | [core 4.2.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [volume units](#volume-units) | `UnitSIdRef` | the units of the size of the compartments with three dimensions | [core 4.2.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [area units](#area-units) | `UnitSIdRef` | the units of the size of the compartments with two dimensions | [core 4.2.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [length units](#length-units) | `UnitSIdRef` | the units of the size of the compartments with one dimension | [core 4.2.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [extent units](#extent-units) | `UnitSIdRef` | the units in which the extent of a reaction is measured | [core 4.2.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [conversion factor](#conversion-factor) | `SIdRef` | the parameter which converts between the units of a species and the extent of a reaction | [core 4.2.6](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [function definitions](#function-definitions) | `list` | the user defined functions of the model | [core 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [unit definitions](#unit-definitions) | `list` | the units the model defines | [core 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [compartments](#compartments) | `list` | the compartments of the model | [core 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [species](#species) | `list` | the species of the model | [core 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [parameters](#parameters) | `list` | the global parameters of the model | [core 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [initial assignments](#initial-assignments) | `list` | the initial assignments of the model | [core 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [rules](#rules) | `list` | the assignment, rate and algebraic rules of the model | [core 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [constraints](#constraints) | `list` | the constraints of the model | [core 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [reactions](#reactions) | `list` | the reactions of the model | [core 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [events](#events) | `list` | the events of the model | [core 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [submodels](#submodels) | `list` | the models which this model instantiates | [comp 3.4.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [ports](#ports) | `list` | the elements of the model which are meant to be used from outside | [comp 3.4.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [gene products](#gene-products) | `list` | the genes and gene products the reactions of the model depend on | [fbc v3 3.3.2](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [fbc](#fbc) | `ModelFbc` | what the model says about the constraint based problem it describes | [fbc v3 3.3](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [strict](#strict) | `boolean` | whether the model keeps to the restrictions of a linear or quadratic program | [fbc v3 3.3](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [active objective](#active-objective) | `SIdRef` | the objective which is optimised unless an analysis says otherwise | [fbc v3 3.3.1](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [flux bounds](#flux-bounds) | `list` | the constraints of the fluxes of a Version 1 model | [fbc v1 3.3.1](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-1.release-1) |
| [objectives](#objectives) | `list` | the objective functions of the constraint based model | [fbc v3 3.3.1](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="substance-units"></span>**substance units**

A species which does not set its substance units inherits this unit of the model. If neither is set, the amounts of that species have no declared unit, which is valid but makes the model harder to check.

The report shows the units of the model in the attributes of the inspector and renders them as a formula.

<span id="time-units"></span>**time units**

This is the only place where the unit of time of a model is declared. It applies everywhere, in particular to the rate of every reaction and of every rate rule, which are per time.

The report shows the time units in the attributes of the model.

<span id="volume-units"></span>**volume units**

A compartment which does not declare its own units inherits its units from the model, and which of the three attributes applies depends on the spatial dimensions of the compartment: volume for three, area for two, length for one.

The report shows the volume units in the attributes of the model.

<span id="area-units"></span>**area units**

A two dimensional compartment, a membrane for example, which does not declare its own units inherits them from this attribute of the model.

The report shows the area units in the attributes of the model.

<span id="length-units"></span>**length units**

A one dimensional compartment which does not declare its own units inherits them from this attribute of the model.

The report shows the length units in the attributes of the model.

<span id="extent-units"></span>**extent units**

The extent of a reaction counts how often it has occurred, and its rate of change is what a kinetic law computes. The units of every kinetic law of the model are therefore the extent units divided by the time units, which also means that every reaction of a model has the same units.

The report shows the extent units in the attributes of the model and uses them when it derives the units of a kinetic law.

<span id="conversion-factor"></span>**conversion factor**

A species whose amount is not measured in the extent units of the reactions needs a factor to convert between the two, and SBML makes that conversion explicit instead of guessing it. The model can name a constant parameter which every species inherits when it does not name its own.

The report shows the referenced parameter with its value and its units in the attributes of the model.

<span id="function-definitions"></span>**function definitions**

The lists of the model group its elements by type. This one holds the [function definitions](functiondefinition.md).

The report shows the list as the section "Function definitions" of the report and counts its entries in the type bar.

<span id="unit-definitions"></span>**unit definitions**

This list holds the [unit definitions](unitdefinition.md) which the elements of the model reference by their identifier.

The report shows the list as the section "Unit definitions" of the report.

<span id="compartments"></span>**compartments**

This list holds the [compartments](compartment.md) the species of the model live in.

The report shows the list as the section "Compartments" of the report.

<span id="species"></span>**species**

This list holds the [species](species.md), the pools whose quantities the model computes.

The report shows the list as the section "Species" of the report.

<span id="parameters"></span>**parameters**

This list holds the [parameters](parameter.md) which every mathematical expression of the model may use.

The report shows the list as the section "Parameters" of the report.

<span id="initial-assignments"></span>**initial assignments**

This list holds the [initial assignments](initialassignment.md) which compute values at the start of a simulation.

The report shows the list as the section "Initial assignments" of the report.

<span id="rules"></span>**rules**

This list holds the three kinds of rule together: [assignment rules](assignmentrule.md), [rate rules](raterule.md) and [algebraic rules](algebraicrule.md).

The report separates them into three sections, because the three say very different things about a model.

<span id="constraints"></span>**constraints**

This list holds the [constraints](constraint.md), the conditions a simulation of the model has to satisfy.

The report shows the list as the section "Constraints" of the report.

<span id="reactions"></span>**reactions**

This list holds the [reactions](reaction.md), the processes which change the quantities of the species.

The report shows the list as the section "Reactions" of the report.

<span id="events"></span>**events**

This list holds the [events](event.md), the discontinuous changes of the state of the model.

The report shows the list as the section "Events" of the report.

<span id="submodels"></span>**submodels**

Every [submodel](submodel.md) instantiates a model definition of the document or a model of another file. A model without submodels is a model in the usual sense; a model with submodels stands for everything its submodels contain, after the deletions and the replacements have been applied.

The report shows the submodels of a model as a section of the report.

<span id="ports"></span>**ports**

A [port](port.md) declares one element of the model as an intended point of interaction, the way a socket declares the interface of a device. Ports are advisory: nothing prevents a containing model from reaching into the model directly, but a modeller is asked to respect the interface.

The report shows the ports of a model as a section of the report.

<span id="gene-products"></span>**gene products**

Every [gene product](geneproduct.md) stands for one gene or one of its products and carries the label under which the reconstruction knows it. The reactions name them in their gene product association.

The report shows the gene products of a model as a section of the report.

<span id="fbc"></span>**fbc**

The block holds the two attributes which belong to the model as a whole: whether it keeps to the restrictions of a strict problem, and which of its objectives is the active one.

The report shows both in the inspector of a model of a document which uses fbc.

<span id="strict"></span>**strict**

A strict model can be handed to a solver which does not read arbitrary mathematics: every reaction has both flux bounds, every bound is a constant [parameter](parameter.md) with a value which is not missing and not infinite in the direction which would remove the bound, every stoichiometry is a constant number, every coefficient of a flux objective is finite, and no initial assignment touches a bound or a stoichiometry.

A model which is not strict may compute a bound during a simulation, with an initial assignment, a rule or an event, which is how a hybrid model changes the capacity of a reaction over time. The attribute therefore says how every other number of the report has to be read, and it is required from Version 2 of the package on; a Version 1 document has none.

The report shows it in the inspector of the model.

<span id="active-objective"></span>**active objective**

A model may carry several [objectives](objective.md), for example the growth it was published with next to the alternatives it was studied with, and this attribute names the one which describes the published simulation. It is an attribute of the list of objectives, which the report does not carry as an object of its own, so it sits next to `strict` in the fbc block of the model.

The report links the objective in the inspector of the model, and the inspector of that objective shows the model under "referenced by".

<span id="flux-bounds"></span>**flux bounds**

A [flux bound](fluxbound.md) is how the first version of the package constrained a reaction. Version 2 removed the construct and replaced it by the two attributes of a [reaction](reaction.md) which name a parameter, so the list is empty for every document of a later version.

The report shows the flux bounds of a Version 1 model as a section of the report.

<span id="objectives"></span>**objectives**

A model may define several [objectives](objective.md) and declares one of them as the active objective, the function which an analysis optimises unless it is told otherwise. The others are kept so that a model can carry the alternatives it was studied with.

The report shows the objectives of a model as a section of the report.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [kind](#kind) | `string` | whether the model is the model of the document or a model definition |
| [annotation](#annotation) | `string` | the annotation element of the model as the file writes it |
| [rendered substance units](#rendered-substance-units) | `latex` | the substance units of the model rendered as a formula |
| [rendered time units](#rendered-time-units) | `latex` | the time units of the model rendered as a formula |
| [rendered volume units](#rendered-volume-units) | `latex` | the volume units of the model rendered as a formula |
| [rendered area units](#rendered-area-units) | `latex` | the area units of the model rendered as a formula |
| [rendered length units](#rendered-length-units) | `latex` | the length units of the model rendered as a formula |
| [rendered extent units](#rendered-extent-units) | `latex` | the extent units of the model rendered as a formula |

<span id="kind"></span>**kind**

A document contains at most one model, but the comp package adds model definitions, which are models that exist to be instantiated by a submodel. The report treats both the same way and marks which of the two an element is.

The kind is shown in the attributes of the inspector of a model, it is `model` or `modelDefinition`.

<span id="annotation"></span>**annotation**

The annotation of the model is where a tool writes what it knows about the model in its own vocabulary, next to the RDF the report reads as [annotations](sbase.md) and as [history](sbase.md). The report does not carry the XML of the model, which is the whole model, so it carries the annotation element alone.

The "XML" button in the header of the inspector shows it.

<span id="rendered-substance-units"></span>**rendered substance units**

The report resolves the unit definition which the model declares for the amounts of its species and renders it as a formula, so that `mmol` is shown as the unit itself instead of as an identifier.

It is shown next to the substance units in the attributes of the model.

<span id="rendered-time-units"></span>**rendered time units**

The report resolves the unit definition which the model declares for time and renders it as a formula. Since the unit of time is declared nowhere else, this is where a reader sees whether a simulation runs in seconds, in minutes or in hours.

It is shown next to the time units in the attributes of the model.

<span id="rendered-volume-units"></span>**rendered volume units**

The report resolves the unit definition which the model declares for the size of its compartments with three dimensions and renders it as a formula.

It is shown next to the volume units in the attributes of the model.

<span id="rendered-area-units"></span>**rendered area units**

The report resolves the unit definition which the model declares for the size of its compartments with two dimensions and renders it as a formula.

It is shown next to the area units in the attributes of the model.

<span id="rendered-length-units"></span>**rendered length units**

The report resolves the unit definition which the model declares for the size of its compartments with one dimension and renders it as a formula.

It is shown next to the length units in the attributes of the model.

<span id="rendered-extent-units"></span>**rendered extent units**

The report resolves the unit definition which the model declares for the extent of its reactions and renders it as a formula. Together with the time units it says what the rate of every kinetic law is measured in.

It is shown next to the extent units in the attributes of the model.

## Related elements

- [Document](sbmldocument.md): the container of an SBML file, with its level, version and packages
- [Compartment](compartment.md): a bounded space in which species are located
- [Species](species.md): a pool of a chemical entity in a compartment
- [Parameter](parameter.md): a named value which the mathematics of the model can use
- [Reaction](reaction.md): a process which changes the quantities of species

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.2 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
