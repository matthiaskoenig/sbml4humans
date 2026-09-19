# Compartment

A bounded space in which species are located.

A compartment is the place where something is: a cell, an organelle, a membrane, the extracellular space. Every species of a model has to be located in one, which is why a model with species always has at least one compartment. A compartment does not have to correspond to a physical structure, it is whatever the model treats as one well mixed space.

The report shows the size of a compartment, the units of that size and the units it derives, and links the species which are located in it.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [spatialDimensions](#spatialdimensions) | [`double`](datatypes.md#double) | optional | the number of dimensions of the compartment | [core 4.5.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [size](#size) | [`double`](datatypes.md#double) | optional | the size of the compartment at the start of the simulation | [core 4.5.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [units](#units) | [`UnitSIdRef`](datatypes.md#unitsidref) | optional | the units of the size of the compartment | [core 4.5.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [constant](#constant) | [`boolean`](datatypes.md#boolean) | required | whether the size of the compartment stays fixed during a simulation | [core 4.5.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="spatialdimensions"></span>**spatialDimensions**

Three dimensions means the size is a volume, two means an area, one means a length. The value does not enter the mathematics of the model, but it decides which units of the model a compartment inherits when it does not declare its own.

The report shows the dimensions in the column "dimensions" and in the inspector.

Default: no units are inherited from the model, because there is no basis to choose between volume, area and length.

- `20518` (warning): If neither the attribute 'units' nor the attribute 'spatialDimensions' on a Compartment object is set, the unit associated with that compartment's size is undefined.

<span id="size"></span>**size**

The size is the volume, the area or the length of the compartment, depending on its dimensions. It is optional: a missing size means that the value is unknown or that it is computed by an initial assignment or a rule, it does not mean one. When the compartment is not constant, the size can change during a simulation.

The report shows the size in the table and in the inspector, and the identifier of a compartment stands for its size in every formula of the model.

Default: the size is unknown or set by an initial assignment or a rule.

- `20501` (error): The size of a &lt;compartment&gt; must not be set if the compartment's 'spatialDimensions' attribute has value '0'.
- `80501` (warning): As a principle of best modeling practice, the size of a &lt;compartment&gt; should be set to a value rather than be left undefined. Doing so improves the portability of models between different simulation and analysis systems, and helps make it easier to detect potential errors in models.

<span id="units"></span>**units**

The units are either a unit definition of the model or one of the base units. When they are not declared, the compartment inherits the volume, area or length units of the model according to its dimensions, and when the model does not declare those either, the size has no units.

The report links the referenced unit definition and renders it as a formula.

Default: the volume, area or length units of the model, according to the dimensions of the compartment.

- `10311` (error): The syntax of unit identifiers (i.e., the values of the 'id' attribute on UnitDefinition, the 'units' attribute on Compartment, the 'units' attribute on Parameter, and the 'substanceUnits' attribute on Species) must conform to the syntax of the SBML type UnitSId.
- `10313` (error): Unit identifier references (i.e the 'units' attribute on &lt;Compartment&gt;, the 'units' attribute on &lt;Parameter&gt;, and the 'substanceUnits' attribute on &lt;Species&gt;) must be the identifier of a &lt;UnitDefinition&gt; in the &lt;Model&gt;, or the identifier of a predefined unit in SBML.
- `20502` (error): If a &lt;compartment&gt; definition has a 'spatialDimensions' value of '0', then its 'units' attribute must not be set. If the compartment has no dimensions, then no units can be associated with a non-existent size.
- `20518` (warning): If neither the attribute 'units' nor the attribute 'spatialDimensions' on a Compartment object is set, the unit associated with that compartment's size is undefined.

<span id="constant"></span>**constant**

A constant compartment keeps its size for the whole simulation and can only be given a value by an initial assignment. A compartment which is not constant can be changed by a rule or by an event, which is how a growing cell is modelled.

The report shows the flag as a mark in the column "constant".

- `20503` (error): If a &lt;compartment&gt; definition has a 'spatialDimensions' value of '0', then its 'constant' attribute value must either default to or be set to 'true'. If the compartment has no dimensions, then its size can never change.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [rendered units](#rendered-units) | [`latex`](datatypes.md#latex) | the units of the size rendered as a formula |
| [derived units](#derived-units) | [`latex`](datatypes.md#latex) | the units of the size as the report derives them |

<span id="rendered-units"></span>**rendered units**

The report resolves the unit definition the compartment references and renders it as a formula, so that the table shows the unit itself and not only its identifier.

<span id="derived-units"></span>**derived units**

The report derives the units of a compartment from its own units, or from the units of the model which it inherits, and renders them as a formula. Derived units make it visible what a value means even when the model does not declare units everywhere.

## Validation rules

- `10712` (warning): The value of the 'sboTerm' attribute on a &lt;compartment&gt; is expected to be an SBO identifier (http://www.biomodels.net/SBO/). In SBML Level 2 prior to Version 4 it is expected to refer to a participant physical type (i.e., terms derived from SBO:0000236, "participant physical type"); in Versions 4 and above it is expected to refer to a material entity (i.e., terms derived from SBO:0000240, "material entity").
- `20517` (error): A Compartment object must have the required attributes 'id' and 'constant', and may have the optional attributes 'metaid', 'sboTerm', 'name', 'spatialDimensions', 'size' and 'units'. No other attributes from the SBML Level 3 Core namespace are permitted on a Compartment object.

## Related elements

- [Model](model.md): the container of everything a model is made of
- [Species](species.md): a pool of a chemical entity in a compartment
- [UnitDefinition](unitdefinition.md): a named unit built from the base units of SBML

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.5 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
