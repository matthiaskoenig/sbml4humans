# Model

The container of everything a model is made of.

The model holds the lists of every element: the function definitions, the unit definitions, the compartments, the species, the parameters, the initial assignments, the rules, the constraints, the reactions and the events. It also sets the units which the elements inherit when they do not declare their own, in particular the unit of time, which exists nowhere else.

The report shows the model as the root of the report, its lists as the sections of the report, and its units in the attributes of the inspector.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [substanceUnits](#substanceunits) | [`UnitSIdRef`](datatypes.md#unitsidref) | optional | the units of the amounts of the species which do not declare their own | [core 4.2.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [timeUnits](#timeunits) | [`UnitSIdRef`](datatypes.md#unitsidref) | optional | the unit in which time is measured in the model | [core 4.2.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [volumeUnits](#volumeunits) | [`UnitSIdRef`](datatypes.md#unitsidref) | optional | the units of the size of the compartments with three dimensions | [core 4.2.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [areaUnits](#areaunits) | [`UnitSIdRef`](datatypes.md#unitsidref) | optional | the units of the size of the compartments with two dimensions | [core 4.2.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [lengthUnits](#lengthunits) | [`UnitSIdRef`](datatypes.md#unitsidref) | optional | the units of the size of the compartments with one dimension | [core 4.2.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [extentUnits](#extentunits) | [`UnitSIdRef`](datatypes.md#unitsidref) | optional | the units in which the extent of a reaction is measured | [core 4.2.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [conversionFactor](#conversionfactor) | [`SIdRef`](datatypes.md#sidref) | optional | the parameter which converts between the units of a species and the extent of a reaction | [core 4.2.6](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [listOfFunctionDefinitions](#listoffunctiondefinitions) | [`list`](datatypes.md#list) | optional | the user defined functions of the model | [core 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [listOfUnitDefinitions](#listofunitdefinitions) | [`list`](datatypes.md#list) | optional | the units the model defines | [core 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [listOfCompartments](#listofcompartments) | [`list`](datatypes.md#list) | optional | the compartments of the model | [core 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [listOfSpecies](#listofspecies) | [`list`](datatypes.md#list) | optional | the species of the model | [core 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [listOfParameters](#listofparameters) | [`list`](datatypes.md#list) | optional | the global parameters of the model | [core 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [listOfInitialAssignments](#listofinitialassignments) | [`list`](datatypes.md#list) | optional | the initial assignments of the model | [core 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [listOfRules](#listofrules) | [`list`](datatypes.md#list) | optional | the assignment, rate and algebraic rules of the model | [core 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [listOfConstraints](#listofconstraints) | [`list`](datatypes.md#list) | optional | the constraints of the model | [core 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [listOfReactions](#listofreactions) | [`list`](datatypes.md#list) | optional | the reactions of the model | [core 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [listOfEvents](#listofevents) | [`list`](datatypes.md#list) | optional | the events of the model | [core 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [comp:listOfSubmodels](#comp-listofsubmodels) | [`list`](datatypes.md#list) | optional | the models which this model instantiates | [comp 3.4.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [comp:listOfPorts](#comp-listofports) | [`list`](datatypes.md#list) | optional | the elements of the model which are meant to be used from outside | [comp 3.4.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [fbc:listOfGeneProducts](#fbc-listofgeneproducts) | [`list`](datatypes.md#list) | - | the genes and gene products the reactions of the model depend on | [fbc v3 3.3.2](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [fbc](#fbc) | `ModelFbc` | - | what the model says about the constraint based problem it describes | [fbc v3 3.3](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [fbc:strict](#fbc-strict) | [`boolean`](datatypes.md#boolean) | - | whether the model keeps to the restrictions of a linear or quadratic program | [fbc v3 3.3](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [fbc:activeObjective](#fbc-activeobjective) | [`SIdRef`](datatypes.md#sidref) | - | the objective which is optimised unless an analysis says otherwise | [fbc v3 3.3.1](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [fbc:listOfFluxBounds](#fbc-listoffluxbounds) | [`list`](datatypes.md#list) | - | the constraints of the fluxes of a Version 1 model | [fbc v1 3.3.1](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-1.release-1) |
| [fbc:listOfUserDefinedConstraints](#fbc-listofuserdefinedconstraints) | [`list`](datatypes.md#list) | - | the constraints of the model which the reaction network does not impose | [fbc v3 3.3.3](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [fbc:listOfObjectives](#fbc-listofobjectives) | [`list`](datatypes.md#list) | - | the objective functions of the constraint based model | [fbc v3 3.3.1](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [qual:listOfQualitativeSpecies](#qual-listofqualitativespecies) | [`list`](datatypes.md#list) | - | the entities of a qualitative model, which carry a level | [qual 3.4](https://sbml.org/documents/specifications/level-3/version-1/qual/) |
| [qual:listOfTransitions](#qual-listoftransitions) | [`list`](datatypes.md#list) | - | the rules which decide the level of the qualitative species | [qual 3.4](https://sbml.org/documents/specifications/level-3/version-1/qual/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="substanceunits"></span>**substanceUnits**

A species which does not set its substance units inherits this unit of the model. If neither is set, the amounts of that species have no declared unit, which is valid but makes the model harder to check.

The report shows the units of the model in the attributes of the inspector and renders them as a formula.

Default: a species which declares none has no declared substance units.

- `20233` (warning): The value of the attribute substanceUnits on a Model object should be either the units 'mole', 'item', 'avogadro', 'dimensionless', 'kilogram', 'gram', or the identifier of a UnitDefinition object based on these units.

<span id="timeunits"></span>**timeUnits**

This is the only place where the unit of time of a model is declared. It applies everywhere, in particular to the rate of every reaction and of every rate rule, which are per time.

The report shows the time units in the attributes of the model.

Default: time has no declared unit anywhere in the model.

- `20217` (warning): The value of the attribute 'timeUnits' on a Model object should be either the units 'second', 'dimensionless', or the identifier of a UnitDefinition object based on these units.

<span id="volumeunits"></span>**volumeUnits**

A compartment which does not declare its own units inherits its units from the model, and which of the three attributes applies depends on the spatial dimensions of the compartment: volume for three, area for two, length for one.

The report shows the volume units in the attributes of the model.

Default: a three dimensional compartment which declares none has no declared units.

- `20218` (warning): The value of the attribute 'volumeUnits' on a Model object should be either the units 'litre', 'dimensionless', or the identifier of a UnitDefinition object based on these units or a unit derived from 'metre'.
- `20513` (warning): If the attribute 'units' on a Compartment object having a 'spatialDimensions' attribute value of '3' has not been set, then the unit of measurement associated with the compartment's size is determined by the value of the enclosing Model object's 'volumeUnits' attribute. If neither the Compartment object's 'units' nor the enclosing Model object's 'volumeUnits' attributes are set, the unit of compartment size is undefined.

<span id="areaunits"></span>**areaUnits**

A two dimensional compartment, a membrane for example, which does not declare its own units inherits them from this attribute of the model.

The report shows the area units in the attributes of the model.

Default: a two dimensional compartment which declares none has no declared units.

- `20219` (warning): The value of the attribute 'areaUnits' on a Model object should be either 'dimensionless' or the identifier of a UnitDefinition object based on 'dimensionless' or a unit derived from 'metre'.
- `20512` (warning): If the attribute 'units' on a Compartment object having a 'spatialDimensions' attribute value of '2' has not been set, then the unit of measurement associated with the compartment's size is determined by the value of the enclosing Model object's 'areaUnits' attribute. If neither the Compartment object's 'units' nor the enclosing Model object's 'areaUnits' attributes are set, the unit of compartment size is undefined.

<span id="lengthunits"></span>**lengthUnits**

A one dimensional compartment which does not declare its own units inherits them from this attribute of the model.

The report shows the length units in the attributes of the model.

Default: a one dimensional compartment which declares none has no declared units.

- `20220` (warning): The value of the attribute 'lengthUnits' on a Model object should be either the units 'metre', 'dimensionless', or the identifier of a UnitDefinition object based on these units.
- `20511` (warning): If the attribute 'units' on a Compartment object having a 'spatialDimensions' attribute value of '1' has not been set, then the unit of measurement associated with the compartment's size is determined by the value of the enclosing Model object's 'lengthUnits' attribute. If neither the Compartment object's 'units' nor the enclosing Model object's 'lengthUnits' attributes are set, the unit of compartment size is undefined.

<span id="extentunits"></span>**extentUnits**

The extent of a reaction counts how often it has occurred, and its rate of change is what a kinetic law computes. The units of every kinetic law of the model are therefore the extent units divided by the time units, which also means that every reaction of a model has the same units.

The report shows the extent units in the attributes of the model and uses them when it derives the units of a kinetic law.

Default: the units of the kinetic laws of the model stay undefined.

- `20221` (warning): The value of the attribute extentUnits on a Model object should be either the units 'mole', 'item', 'avogadro', 'dimensionless', 'kilogram', 'gram', or the identifier of a UnitDefinition object based on these units.

<span id="conversionfactor"></span>**conversionFactor**

A species whose amount is not measured in the extent units of the reactions needs a factor to convert between the two, and SBML makes that conversion explicit instead of guessing it. The model can name a constant parameter which every species inherits when it does not name its own.

The report shows the referenced parameter with its value and its units in the attributes of the model.

Default: a species which names none has no conversion factor.

- `20216` (error): The value of the attribute 'conversionFactor' on a Model object must be the identifier of an existing Parameter object defined in the Model object's ListOfParameters.
- `20705` (error): A Parameter object referenced by the attribute 'conversionFactor' on a Species or Model object must have a value of 'true' for its attribute 'constant'.

<span id="listoffunctiondefinitions"></span>**listOfFunctionDefinitions**

The lists of the model group its elements by type. This one holds the [function definitions](functiondefinition.md).

The report shows the list as the section "Function definitions" of the report and counts its entries in the type bar.

- `20206` (error): Apart from the general Notes and Annotation subobjects permitted on all SBML components, a ListOfFunctionDefinitions container object may only contain FunctionDefinition objects.

<span id="listofunitdefinitions"></span>**listOfUnitDefinitions**

This list holds the [unit definitions](unitdefinition.md) which the elements of the model reference by their identifier.

The report shows the list as the section "Unit definitions" of the report.

- `20207` (error): Apart from the general Notes and Annotation subobjects permitted on all SBML components, a ListOfUnitDefinitions container object may only contain UnitDefinition objects.

<span id="listofcompartments"></span>**listOfCompartments**

This list holds the [compartments](compartment.md) the species of the model live in.

The report shows the list as the section "Compartments" of the report.

- `20208` (error): Apart from the general Notes and Annotation subobjects permitted on all SBML components, a ListOfCompartments container object may only contain Compartment objects.

<span id="listofspecies"></span>**listOfSpecies**

This list holds the [species](species.md), the pools whose quantities the model computes.

The report shows the list as the section "Species" of the report.

- `20209` (error): Apart from the general Notes and Annotation subobjects permitted on all SBML components, a ListOfSpecies container object may only contain Species objects.

<span id="listofparameters"></span>**listOfParameters**

This list holds the [parameters](parameter.md) which every mathematical expression of the model may use.

The report shows the list as the section "Parameters" of the report.

- `20210` (error): Apart from the general Notes and Annotation subobjects permitted on all SBML components, a ListOfParameters container object may only contain Parameter objects.

<span id="listofinitialassignments"></span>**listOfInitialAssignments**

This list holds the [initial assignments](initialassignment.md) which compute values at the start of a simulation.

The report shows the list as the section "Initial assignments" of the report.

- `20211` (error): Apart from the general Notes and Annotation subobjects permitted on all SBML components, a ListOfInitialAssignments container object may only contain InitialAssignment objects.

<span id="listofrules"></span>**listOfRules**

This list holds the three kinds of rule together: [assignment rules](assignmentrule.md), [rate rules](raterule.md) and [algebraic rules](algebraicrule.md).

The report separates them into three sections, because the three say very different things about a model.

- `20212` (error): Apart from the general Notes and Annotation subobjects permitted on all SBML components, a ListOfRules container object may only contain Rule objects.

<span id="listofconstraints"></span>**listOfConstraints**

This list holds the [constraints](constraint.md), the conditions a simulation of the model has to satisfy.

The report shows the list as the section "Constraints" of the report.

- `20213` (error): Apart from the general Notes and Annotation subobjects permitted on all SBML components, a ListOfConstraints container object may only contain Constraint objects.

<span id="listofreactions"></span>**listOfReactions**

This list holds the [reactions](reaction.md), the processes which change the quantities of the species.

The report shows the list as the section "Reactions" of the report.

- `20214` (error): Apart from the general Notes and Annotation subobjects permitted on all SBML components, a ListOfReactions container object may only contain Reaction objects.

<span id="listofevents"></span>**listOfEvents**

This list holds the [events](event.md), the discontinuous changes of the state of the model.

The report shows the list as the section "Events" of the report.

- `20215` (error): Apart from the general Notes and Annotation subobjects permitted on all SBML components, a ListOfEvents container object may only contain Event objects.

<span id="comp-listofsubmodels"></span>**comp:listOfSubmodels**

Every [submodel](submodel.md) instantiates a model definition of the document or a model of another file. A model without submodels is a model in the usual sense; a model with submodels stands for everything its submodels contain, after the deletions and the replacements have been applied.

The report shows the submodels of a model as a section of the report.

- `1020501` (error): There may be at most one instance of each of the following kinds of objects within a &lt;model&gt; or &lt;modelDefinition&gt; object using Hierarchical Model Composition: &lt;listOfSubmodels&gt; and &lt;listOfPorts&gt;.
- `1020502` (error): The various ListOf subobjects with a &lt;model&gt; object are optional, but if present, these container object must not be empty. Specifically, if any of the following classes of objects are present on the &lt;model&gt;, it must not be empty: &lt;listOfSubmodels&gt; and &lt;listOfPorts&gt;.
- `1020503` (error): Apart from the general notes and annotation subobjects permitted on all SBML objects, a &lt;listOfSubmodels&gt; container object may only contain &lt;submodel&gt; objects.

<span id="comp-listofports"></span>**comp:listOfPorts**

A [port](port.md) declares one element of the model as an intended point of interaction, the way a socket declares the interface of a device. Ports are advisory: nothing prevents a containing model from reaching into the model directly, but a modeller is asked to respect the interface.

The report shows the ports of a model as a section of the report.

Default: nothing of the model is declared as an interface.

- `1020501` (error): There may be at most one instance of each of the following kinds of objects within a &lt;model&gt; or &lt;modelDefinition&gt; object using Hierarchical Model Composition: &lt;listOfSubmodels&gt; and &lt;listOfPorts&gt;.
- `1020502` (error): The various ListOf subobjects with a &lt;model&gt; object are optional, but if present, these container object must not be empty. Specifically, if any of the following classes of objects are present on the &lt;model&gt;, it must not be empty: &lt;listOfSubmodels&gt; and &lt;listOfPorts&gt;.
- `1020504` (error): Apart from the general notes and annotation subobjects permitted on all SBML objects, a &lt;listOfPorts&gt; container object may only contain &lt;port&gt; objects.

<span id="fbc-listofgeneproducts"></span>**fbc:listOfGeneProducts**

Every [gene product](geneproduct.md) stands for one gene or one of its products and carries the label under which the reconstruction knows it. The reactions name them in their gene product association.

The report shows the gene products of a model as a section of the report.

<span id="fbc"></span>**fbc**

The block holds the two attributes which belong to the model as a whole: whether it keeps to the restrictions of a strict problem, and which of its objectives is the active one.

The report shows both in the inspector of a model of a document which uses fbc.

<span id="fbc-strict"></span>**fbc:strict**

A strict model can be handed to a solver which does not read arbitrary mathematics: every reaction has both flux bounds, every bound is a constant [parameter](parameter.md) with a value which is not missing and not infinite in the direction which would remove the bound, every stoichiometry is a constant number, every coefficient of a flux objective is finite, and no initial assignment touches a bound or a stoichiometry.

A model which is not strict may compute a bound during a simulation, with an initial assignment, a rule or an event, which is how a hybrid model changes the capacity of a reaction over time. The attribute therefore says how every other number of the report has to be read, and it is required from Version 2 of the package on; a Version 1 document has none.

The report shows it in the inspector of the model.

<span id="fbc-activeobjective"></span>**fbc:activeObjective**

A model may carry several [objectives](objective.md), for example the growth it was published with next to the alternatives it was studied with, and this attribute names the one which describes the published simulation. It is an attribute of the list of objectives, which the report does not carry as an object of its own, so it sits next to `strict` in the fbc block of the model.

The report links the objective in the inspector of the model, and the inspector of that objective shows the model under "referenced by".

<span id="fbc-listoffluxbounds"></span>**fbc:listOfFluxBounds**

A [flux bound](fluxbound.md) is how the first version of the package constrained a reaction. Version 2 removed the construct and replaced it by the two attributes of a [reaction](reaction.md) which name a parameter, so the list is empty for every document of a later version.

The report shows the flux bounds of a Version 1 model as a section of the report.

<span id="fbc-listofuserdefinedconstraints"></span>**fbc:listOfUserDefinedConstraints**

A [user defined constraint](userdefinedconstraint.md) bounds a combination of fluxes and parameters which the stoichiometry of the network leaves free, for example the ratio of two reactions or a shared budget. The list exists from Version 3 of the package on and is empty in every earlier document.

The report shows the user defined constraints of a model as a section of the report.

<span id="fbc-listofobjectives"></span>**fbc:listOfObjectives**

A model may define several [objectives](objective.md) and declares one of them as the active objective, the function which an analysis optimises unless it is told otherwise. The others are kept so that a model can carry the alternatives it was studied with.

The report shows the objectives of a model as a section of the report.

<span id="qual-listofqualitativespecies"></span>**qual:listOfQualitativeSpecies**

A model which uses the qual package holds its [qualitative species](qualitativespecies.md) in a list of their own, next to the species of the core. The two are not the same thing and a model does not mix them: an entity of a qualitative model has no amount and no concentration, it has a level.

The report shows them as a section of their own.

<span id="qual-listoftransitions"></span>**qual:listOfTransitions**

The [transitions](transition.md) are the dynamics of a qualitative model, what the reactions with their kinetic laws are to a kinetic one. Every one of them reads some qualitative species and changes others.

The report shows them as a section of their own.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [kind](#kind) | [`string`](datatypes.md#string) | whether the model is the model of the document or a model definition |
| [annotation](#annotation) | [`string`](datatypes.md#string) | the annotation element of the model as the file writes it |
| [rendered substance units](#rendered-substance-units) | [`latex`](datatypes.md#latex) | the substance units of the model rendered as a formula |
| [rendered time units](#rendered-time-units) | [`latex`](datatypes.md#latex) | the time units of the model rendered as a formula |
| [rendered volume units](#rendered-volume-units) | [`latex`](datatypes.md#latex) | the volume units of the model rendered as a formula |
| [rendered area units](#rendered-area-units) | [`latex`](datatypes.md#latex) | the area units of the model rendered as a formula |
| [rendered length units](#rendered-length-units) | [`latex`](datatypes.md#latex) | the length units of the model rendered as a formula |
| [rendered extent units](#rendered-extent-units) | [`latex`](datatypes.md#latex) | the extent units of the model rendered as a formula |

<span id="kind"></span>**kind**

A document contains at most one model, but the comp package adds model definitions, which are models that exist to be instantiated by a submodel. The report treats both the same way and marks which of the two an element is.

The kind is shown in the attributes of the inspector of a model, it is `model` or `modelDefinition`.

<span id="annotation"></span>**annotation**

The annotation of the model is where a tool writes what it knows about the model in its own vocabulary, next to the RDF the report reads as [annotations](sbase.md) and as [history](sbase.md). The report does not carry the XML of the model, which is the whole model, so it carries the annotation element alone.

The "XML" button in the header of the inspector shows it.

- `10401` (error): Every top-level element within an annotation element must have a namespace declared.
- `10402` (error): There cannot be more than one top-level element using a given namespace inside a given annotation element.
- `10403` (error): Top-level elements within an annotation element cannot use any SBML namespace, whether explicitly (by declaring the namespace to be one of the URIs "http://www.sbml.org/sbml/level1", "http://www.sbml.org/sbml/level2", "http://www.sbml.org/sbml/level2/version2", or "http://www.sbml.org/sbml/level2/version3", or "http://www.sbml.org/sbml/level2/version4", or "http://www.sbml.org/sbml/level2/version5" or "http://www.sbml.org/sbml/level3/version1/core"), or implicitly (by failing to declare any namespace).
- `10404` (error): A given SBML object may contain at most one &lt;annotation&gt; element.

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

## Validation rules

- `10701` (warning): The value of the 'sboTerm' attribute on a &lt;model&gt; is expected to be an SBO identifier (http://www.biomodels.net/SBO/). In SBML Level 2 prior to Version 4 the value is expected to be a term derived from SBO:0000004, "modeling framework"; in Version 4 and above it is expected to be a term derived from SBO:0000231 "occurring entity representation"
- `20202` (error): The order of subelements within a &lt;model&gt; element must be the following (where any one may be optional, but the ordering must be maintained): &lt;listOfFunctionDefinitions&gt;, &lt;listOfUnitDefinitions&gt;, &lt;listOfCompartmentTypes&gt;, &lt;listOfSpeciesTypes&gt;, &lt;listOfCompartments&gt;, &lt;listOfSpecies&gt;, &lt;listOfParameters&gt;, &lt;listOfInitialAssignments&gt;, &lt;listOfRules&gt;, &lt;listOfConstraints&gt;, &lt;listOfReactions&gt; and &lt;listOfEvents&gt;.
- `20203` (error): The &lt;listOf___&gt; containers in a &lt;model&gt; are optional, but if present, the lists cannot be empty. Specifically, if any of the following are present in a &lt;model&gt;, they must not be empty: &lt;listOfFunctionDefinitions&gt;, &lt;listOfUnitDefinitions&gt;, &lt;listOfCompartmentTypes&gt;, &lt;listOfSpeciesTypes&gt;, &lt;listOfCompartments&gt;, &lt;listOfSpecies&gt;, &lt;listOfParameters&gt;, &lt;listOfInitialAssignments&gt;, &lt;listOfRules&gt;, &lt;listOfConstraints&gt;, &lt;listOfReactions&gt; and &lt;listOfEvents&gt;.
- `20205` (error): There may be at most one instance of each of the following kind of element in a &lt;model&gt; object: ListOfFunctionDefinitions, ListOfUnitDefinitions, ListOfCompartments, ListOfSpecies, ListOfParameters, ListOfInitialAssignments, ListOfRules, ListOfConstraints, ListOfReactions and ListOfEvents.
- `20222` (error): A Model object may only have the following attributes, all of which are optional: 'metaid', 'sboTerm', 'id', 'name', 'substanceUnits', 'timeUnits', 'volumeUnits', 'areaUnits', 'lengthUnits', 'extentUnits' and 'conversionFactor'. No other attributes from the SBML Level 3 Core namespace are permitted on a Model object.

## Related elements

- [SBMLDocument](sbmldocument.md): the container of an SBML file, with its level, version and packages
- [Compartment](compartment.md): a bounded space in which species are located
- [Species](species.md): a pool of a chemical entity in a compartment
- [Parameter](parameter.md): a named value which the mathematics of the model can use
- [Reaction](reaction.md): a process which changes the quantities of species

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.2 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
