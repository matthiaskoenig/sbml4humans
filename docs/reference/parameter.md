# Parameter

A named value which the mathematics of the model can use.

A parameter associates an identifier with a numerical value, and the flag "constant" decides whether it is a constant of the model or another variable of it. Kinetic constants, thresholds and conversion factors are parameters, and so is a quantity which a rule computes over time.

The report shows the value of a parameter, its units and the units it derives, and links every element which references it.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [value](#value) | [`double`](datatypes.md#double) | optional | the value of the parameter at the start of the simulation | [core 4.7.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [units](#units) | [`UnitSIdRef`](datatypes.md#unitsidref) | optional | the units of the value of the parameter | [core 4.7.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [constant](#constant) | [`boolean`](datatypes.md#boolean) | required | whether the value of the parameter stays fixed during a simulation | [core 4.7.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="value"></span>**value**

The value is a literal number. It is optional: a missing value means that it is unknown or that it is computed by an initial assignment or a rule, which can express things a literal number cannot.

The report shows the value in the table and in the inspector.

Default: the value is unknown or set by an initial assignment or a rule.

- `80702` (warning): As a principle of best modeling practice, the &lt;parameter&gt; should set an initial value rather than be left undefined. Doing so improves the portability of models between different simulation and analysis systems, and helps make it easier to detect potential errors in models.

<span id="units"></span>**units**

The units are a unit definition of the model or a base unit. A parameter inherits nothing from the model: when it declares no units, its value has none, which is why the units of a formula which uses it cannot always be checked.

The report links the referenced unit definition and renders it as a formula.

Default: the value has no declared units, a parameter inherits none from the model.

- `10311` (error): The syntax of unit identifiers (i.e., the values of the 'id' attribute on UnitDefinition, the 'units' attribute on Compartment, the 'units' attribute on Parameter, and the 'substanceUnits' attribute on Species) must conform to the syntax of the SBML type UnitSId.
- `10313` (error): Unit identifier references (i.e the 'units' attribute on &lt;Compartment&gt;, the 'units' attribute on &lt;Parameter&gt;, and the 'substanceUnits' attribute on &lt;Species&gt;) must be the identifier of a &lt;UnitDefinition&gt; in the &lt;Model&gt;, or the identifier of a predefined unit in SBML.
- `20702` (warning): If the attribute 'units' on a given Parameter object has not been set, then the unit of measurement associated with that parameter's value is undefined.
- `80701` (warning): As a principle of best modeling practice, the units of a &lt;parameter&gt; should be declared rather than be left undefined. Doing so improves the ability of software to check the consistency of units and helps make it easier to detect potential errors in models.

<span id="constant"></span>**constant**

A constant parameter keeps its value for the whole simulation and can only be set by an initial assignment. A parameter which is not constant is a variable of the model and is computed by a rule or changed by an event.

The report shows the flag as a mark in the column "constant".

- `20705` (error): A Parameter object referenced by the attribute 'conversionFactor' on a Species or Model object must have a value of 'true' for its attribute 'constant'.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [rendered units](#rendered-units) | [`latex`](datatypes.md#latex) | the units of the parameter rendered as a formula |
| [derived units](#derived-units) | [`latex`](datatypes.md#latex) | the units of the value as the report derives them |

<span id="rendered-units"></span>**rendered units**

The report resolves the unit definition the parameter references and renders it as a formula next to its identifier.

<span id="derived-units"></span>**derived units**

The report resolves the units of the parameter and renders them as a formula. A parameter without units is shown without derived units, because there is nothing to inherit.

## Validation rules

- `10703` (warning): The value of the 'sboTerm' attribute on a &lt;parameter&gt; is expected to be an SBO identifier (http://www.biomodels.net/SBO/) referring to a quantitative parameter defined in SBO (i.e., terms derived from SBO:0000002, "quantitative systems description parameter").
- `20706` (error): A Parameter object must have the required attributes 'id' and 'constant', and may have the optional attributes 'metaid', 'sboTerm', 'name', 'value' and 'units'. No other attributes from the SBML Level 3 Core namespace are permitted on a Parameter object.

## Related elements

- [Model](model.md): the container of everything a model is made of
- [UnitDefinition](unitdefinition.md): a named unit built from the base units of SBML
- [LocalParameter](localparameter.md): a named value which only one kinetic law uses

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.7 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
