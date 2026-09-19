# LocalParameter

A named value which only one kinetic law uses.

A local parameter is defined inside a kinetic law, which keeps a constant that belongs to one reaction out of the global parameters. Its identifier is scoped to the whole reaction: within that reaction it shadows an element of the model with the same identifier, and in SBML core the math of the kinetic law is the only place which can read it. It can never be the target of an initial assignment, of a rule or of an event assignment.

The report shows a local parameter as an element of its own, with its value, its units and the reaction it belongs to.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [value](#value) | [`double`](datatypes.md#double) | optional | the value of the local parameter | [core 4.11.6](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [units](#units) | [`UnitSIdRef`](datatypes.md#unitsidref) | optional | the units of the value of the local parameter | [core 4.11.6](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="value"></span>**value**

The value is a literal number. Unlike a global parameter, a local parameter is always constant: nothing outside the kinetic law can see it, so nothing can change it.

The report shows the value in the table of local parameters and in the inspector.

Default: the value is unknown, and no construct of the model can set it.

<span id="units"></span>**units**

The units are a unit definition of the model or a base unit, and nothing is inherited when they are missing.

The report links the referenced unit definition and renders it as a formula.

Default: the value has no declared units, a local parameter inherits none from the model.

- `10311` (error): The syntax of unit identifiers (i.e., the values of the 'id' attribute on UnitDefinition, the 'units' attribute on Compartment, the 'units' attribute on Parameter, and the 'substanceUnits' attribute on Species) must conform to the syntax of the SBML type UnitSId.
- `10313` (error): Unit identifier references (i.e the 'units' attribute on &lt;Compartment&gt;, the 'units' attribute on &lt;Parameter&gt;, and the 'substanceUnits' attribute on &lt;Species&gt;) must be the identifier of a &lt;UnitDefinition&gt; in the &lt;Model&gt;, or the identifier of a predefined unit in SBML.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [rendered units](#rendered-units) | [`latex`](datatypes.md#latex) | the units of the local parameter rendered as a formula |
| [derived units](#derived-units) | [`latex`](datatypes.md#latex) | the units of the value as the report derives them |

<span id="rendered-units"></span>**rendered units**

The report resolves the unit definition the local parameter references and renders it as a formula next to its identifier.

<span id="derived-units"></span>**derived units**

The report resolves the units of the local parameter and renders them as a formula, so that the units of a rate constant can be compared with the units the rate law needs.

## Validation rules

- `10303` (error): The value of the 'id' field of each parameter defined locally within a &lt;kineticLaw&gt; must be unique across the set of all such parameter definitions in that &lt;kineticLaw&gt;.
- `10718` (warning): The value of the 'sboTerm' attribute on a &lt;localParameter&gt; is expected to be an SBO identifier (http://www.biomodels.net/SBO/) referring to a quantitative parameter (i.e., terms derived from SBO:0000002, "quantitive systems description parameter").
- `21124` (error): The 'constant' attribute on a &lt;parameter&gt; local to a &lt;kineticLaw&gt; cannot have a value other than 'true'. The values of parameters local to &lt;kineticLaw&gt; definitions cannot be changed, and therefore they are always constant.
- `21172` (error): A LocalParameter object must have the required attribute 'id' and may have the optional attributes 'metaid', 'sboTerm', 'name', 'value' and 'units'. No other attributes from the SBML Level 3 Core namespace are permitted on a LocalParameter object.
- `21173` (error): The 'id' attribute of a &lt;localParameter&gt; object must not be the same as the 'species' attribute of any &lt;speciesReference&gt; in the same &lt;reaction&gt;.

## Related elements

- [KineticLaw](kineticlaw.md): the formula which gives the speed of a reaction
- [Parameter](parameter.md): a named value which the mathematics of the model can use
- [Reaction](reaction.md): a process which changes the quantities of species

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.11.6 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
