# Species

A pool of a chemical entity in a compartment.

A species is a pool of entities which the model treats as indistinguishable: a metabolite, a protein, an ion, a gene. It is located in exactly one [compartment](compartment.md), it may participate in reactions, and its quantity is what most simulations compute. The quantity is an amount or a concentration, depending on the attribute "only substance units".

The report shows the initial quantity of a species, its units, the flags which say how it may change, and links its compartment and every reaction it takes part in.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [compartment](#compartment) | [`SIdRef`](datatypes.md#sidref) | required | the compartment the species is located in | [core 4.6.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [initialAmount](#initialamount) | [`double`](datatypes.md#double) | optional | the amount of the species when the simulation starts | [core 4.6.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [initialConcentration](#initialconcentration) | [`double`](datatypes.md#double) | optional | the concentration of the species when the simulation starts | [core 4.6.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [substanceUnits](#substanceunits) | [`UnitSIdRef`](datatypes.md#unitsidref) | optional | the units of the amount of the species | [core 4.6.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [hasOnlySubstanceUnits](#hasonlysubstanceunits) | [`boolean`](datatypes.md#boolean) | required | whether the identifier of the species stands for an amount instead of a concentration | [core 4.6.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [boundaryCondition](#boundarycondition) | [`boolean`](datatypes.md#boolean) | required | whether the quantity of the species is left unchanged by the reactions | [core 4.6.6](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [constant](#constant) | [`boolean`](datatypes.md#boolean) | required | whether the quantity of the species stays fixed during a simulation | [core 4.6.6](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [conversionFactor](#conversionfactor) | [`SIdRef`](datatypes.md#sidref) | optional | the parameter which converts the extent of a reaction into the quantity of the species | [core 4.6.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [fbc](#fbc) | [`SpeciesFbc`](datatypes.md#speciesfbc) | optional | the chemical formula and the charge which fbc adds to a species | [fbc v3 3.4](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [fbc:chemicalFormula](#fbc-chemicalformula) | [`string`](datatypes.md#string) | optional | the elemental composition of the species | [fbc v3 3.4](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [fbc:charge](#fbc-charge) | [`double`](datatypes.md#double) | optional | the charge of the species, counted in electrons | [fbc v3 3.4](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="compartment"></span>**compartment**

Every species names the compartment it is in; SBML has no default compartment. The size of that compartment is what converts between the amount and the concentration of the species.

The report links the compartment in the table and in the inspector.

- `20204` (error): If a model defines any species, then the model must also define at least one compartment. This is an implication of the fact that the 'compartment' attribute on the &lt;species&gt; element is not optional.
- `20601` (error): The value of 'compartment' in a &lt;species&gt; definition must be the identifier of an existing &lt;compartment&gt; defined in the model.
- `20614` (error): The 'compartment' attribute in a &lt;species&gt; is mandatory. A &lt;species&gt; definition in a model must include a value for this attribute.

<span id="initialamount"></span>**initialAmount**

The initial amount is the quantity of the species at the start of a simulation, measured in its substance units. A species sets either an initial amount or an initial concentration, never both, and it may set neither, in which case the value comes from an initial assignment or a rule.

The report shows the initial amount in the table and in the inspector.

Default: the quantity is unknown or set by an initial assignment or a rule.

- `20609` (error): A &lt;species&gt; cannot set values for both 'initialConcentration' and 'initialAmount' because they are mutually exclusive.
- `80601` (warning): As a principle of best modeling practice, the &lt;species&gt; should set an initial value (amount or concentration) rather than be left undefined. Doing so improves the portability of models between different simulation and analysis systems, and helps make it easier to detect potential errors in models.

<span id="initialconcentration"></span>**initialConcentration**

The initial concentration is the amount of the species divided by the size of its compartment at the start of a simulation. It excludes the initial amount, a species sets at most one of the two.

The report shows the initial concentration in the table and in the inspector.

Default: the quantity is unknown or set by an initial assignment or a rule.

- `20604` (error): If a &lt;species&gt; located in a &lt;compartment&gt; whose 'spatialDimensions' is set to '0', then that &lt;species&gt; definition cannot set 'initialConcentration'.
- `20609` (error): A &lt;species&gt; cannot set values for both 'initialConcentration' and 'initialAmount' because they are mutually exclusive.
- `80601` (warning): As a principle of best modeling practice, the &lt;species&gt; should set an initial value (amount or concentration) rather than be left undefined. Doing so improves the portability of models between different simulation and analysis systems, and helps make it easier to detect potential errors in models.

<span id="substanceunits"></span>**substanceUnits**

The substance units say what a quantity of one means, for example one mole, one millimole or one item. When the species does not declare them, it inherits the substance units of the model.

The report links the referenced unit definition and renders it as a formula.

Default: the substance units of the model.

- `10311` (error): The syntax of unit identifiers (i.e., the values of the 'id' attribute on UnitDefinition, the 'units' attribute on Compartment, the 'units' attribute on Parameter, and the 'substanceUnits' attribute on Species) must conform to the syntax of the SBML type UnitSId.
- `10313` (error): Unit identifier references (i.e the 'units' attribute on &lt;Compartment&gt;, the 'units' attribute on &lt;Parameter&gt;, and the 'substanceUnits' attribute on &lt;Species&gt;) must be the identifier of a &lt;UnitDefinition&gt; in the &lt;Model&gt;, or the identifier of a predefined unit in SBML.
- `20616` (warning): If the attribute 'substanceUnits' in a Species object has not been set, then the unit of measurement associated with the species' quantity is determined by the value of the enclosing Model object's 'substanceUnits' attribute. If neither the Species object's 'substanceUnits' attribute nor the enclosing Model object's 'substanceUnits' attribute are set, then the unit of that species' quantity is undefined.

<span id="hasonlysubstanceunits"></span>**hasOnlySubstanceUnits**

This flag decides what the identifier of the species means when it appears in a formula: with "true" it is an amount, with "false" it is an amount divided by the size of its compartment, that is a concentration. The flag is needed as its own attribute because the initial quantity and the units are both optional.

The report shows the flag as a mark in the column "only substance units" and uses it when it derives the units of the species.

<span id="boundarycondition"></span>**boundaryCondition**

A species on the boundary of the reaction system may appear as a reactant or a product, but the reactions do not determine its quantity; it is held by the modeller, for example as a constant supply of glucose. A species which is not a boundary condition is changed by every reaction it takes part in.

The report shows the flag as a mark in the column "boundary condition".

- `20610` (error): A &lt;species&gt;'s quantity cannot be determined simultaneously by both reactions and rules. More formally, if the identifier of a &lt;species&gt; definition having 'boundaryCondition'='false' and 'constant'='false' is referenced by a &lt;speciesReference&gt; anywhere in a model, then this identifier cannot also appear as the value of a 'variable' in an &lt;assignmentRule&gt; or a &lt;rateRule&gt;.
- `20611` (error): A &lt;species&gt; having boundaryCondition='false' cannot appear as a reactant or product in any reaction if that Species also has constant='true'.

<span id="constant"></span>**constant**

A constant species keeps its amount for the whole simulation, whatever happens around it, and only an initial assignment may set it. Its concentration may still change, because the compartment it is located in may change size. Together with the boundary condition, the flag says whether the species is a variable of the model or a given value.

The report shows the flag as a mark in the column "constant".

- `20610` (error): A &lt;species&gt;'s quantity cannot be determined simultaneously by both reactions and rules. More formally, if the identifier of a &lt;species&gt; definition having 'boundaryCondition'='false' and 'constant'='false' is referenced by a &lt;speciesReference&gt; anywhere in a model, then this identifier cannot also appear as the value of a 'variable' in an &lt;assignmentRule&gt; or a &lt;rateRule&gt;.
- `20611` (error): A &lt;species&gt; having boundaryCondition='false' cannot appear as a reactant or product in any reaction if that Species also has constant='true'.

<span id="conversionfactor"></span>**conversionFactor**

When the amount of a species is not measured in the extent units of the reactions, a constant parameter states the factor between the two, instead of leaving the conversion implicit. A factor on the species overrides the one of the model.

The report shows the referenced parameter with its value in the attributes of the species.

Default: the conversion factor of the model.

- `20617` (error): The value of the attribute 'conversionFactor' on a Species object must be the identifier of an existing Parameter object defined in the enclosing Model object.
- `20705` (error): A Parameter object referenced by the attribute 'conversionFactor' on a Species or Model object must have a value of 'true' for its attribute 'constant'.

<span id="fbc"></span>**fbc**

A constraint based model needs the elemental composition and the charge of a species to check that its reactions are balanced. Both are annotations of the species in the sense that they do not enter the mathematics of the model.

The report shows them in the inspector of a species of a model which uses fbc.

<span id="fbc-chemicalformula"></span>**fbc:chemicalFormula**

The formula must consist only of atomic names of the periodic table or user defined compounds, each of which takes the form of a single capital letter followed by zero or more lowercase letters, with an integer behind a symbol where more than one atom is present. The order should follow the Hill system: the carbon atoms first, then the hydrogen atoms, then every other element in alphabetical order, and every element including hydrogen in alphabetical order when the formula contains no carbon. `C10H12N5O13P3` is such a formula.

The report shows the formula in the inspector of the species.

- `2020301` (error): A SBML &lt;species&gt; object may have the optional attributes 'fbc:charge' and 'fbc:chemicalFormula'. No other attributes from the Flux Balance Constraints namespaces are permitted on a &lt;species&gt;.
- `2020303` (error): The value of attribute 'fbc:chemicalFormula' on the SBML &lt;species&gt; object must be set to a string consisting only of atomic names or user defined compounds and their occurrence.

<span id="fbc-charge"></span>**fbc:charge**

The charge is given in electrons, not in coulombs, and it is the charge of one entity of the species. Versions 1 and 2 of the package wrote it as an integer, Version 3 as a double, so that a species which stands for a pseudoisomer or an aggregate molecule can carry a charge which is not a whole number. Together with the chemical formula it is what a check of the charge balance of a reaction needs.

The report shows the charge in the inspector of the species.

- `2020301` (error): A SBML &lt;species&gt; object may have the optional attributes 'fbc:charge' and 'fbc:chemicalFormula'. No other attributes from the Flux Balance Constraints namespaces are permitted on a &lt;species&gt;.
- `2020302` (error): The value of attribute 'fbc:charge' on SBML &lt;species&gt; object must be of the data type integer.
- `2020304` (error): The value of attribute 'fbc:charge' on SBML &lt;species&gt; object must be of the data type double.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [rendered substance units](#rendered-substance-units) | [`latex`](datatypes.md#latex) | the substance units of the species rendered as a formula |
| [derived units](#derived-units) | [`latex`](datatypes.md#latex) | the units of the quantity of the species as the report derives them |

<span id="rendered-substance-units"></span>**rendered substance units**

The report resolves the unit definition the species references and renders it as a formula next to its identifier.

<span id="derived-units"></span>**derived units**

The report derives the units of a species from its substance units, from the units of its compartment and from the flag "only substance units", and renders the result as a formula. This is the unit a formula sees when it uses the identifier of the species.

## Validation rules

- `10713` (warning): The value of the 'sboTerm' attribute on a &lt;species&gt; is expected to be an SBO identifier (http://www.biomodels.net/SBO/). In SBML Level 2 prior to Version 4 it is expected to refer to a participant physical type (i.e., terms derived from SBO:0000236, "participant physical type"); in Versions 4 and above it is expected to refer to a material entity (i.e., terms derived from SBO:0000240, "material entity").
- `20623` (error): A Species object must have the required attributes 'id', 'compartment', 'hasOnlySubstanceUnits', 'boundaryCondition' and 'constant', and may have the optional attributes 'metaid', 'sboTerm', 'name', 'initialAmount', 'initialConcentration', 'substanceUnits' and 'conversionFactor'. No other attributes from the SBML Level 3 Core namespace are permitted on a Species object.

## Related elements

- [Compartment](compartment.md): a bounded space in which species are located
- [Reaction](reaction.md): a process which changes the quantities of species
- [SpeciesReference](speciesreference.md): the participation of a species in a reaction as a reactant or a product
- [Parameter](parameter.md): a named value which the mathematics of the model can use

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.6 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
