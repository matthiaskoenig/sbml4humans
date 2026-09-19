# LocalParameter

A named value which only one kinetic law uses.

A local parameter is defined inside a kinetic law, which keeps a constant that belongs to one reaction out of the global parameters. Its identifier is scoped to the whole reaction: within that reaction it shadows an element of the model with the same identifier, and in SBML core the math of the kinetic law is the only place which can read it. It can never be the target of an initial assignment, of a rule or of an event assignment.

The report shows a local parameter as an element of its own, with its value, its units and the reaction it belongs to.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [value](#value) | `double` | the value of the local parameter | [core 4.11.6](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [units](#units) | `UnitSIdRef` | the units of the value of the local parameter | [core 4.11.6](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="value"></span>**value**

The value is a literal number. Unlike a global parameter, a local parameter is always constant: nothing outside the kinetic law can see it, so nothing can change it.

The report shows the value in the table of local parameters and in the inspector.

<span id="units"></span>**units**

The units are a unit definition of the model or a base unit, and nothing is inherited when they are missing.

The report links the referenced unit definition and renders it as a formula.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [rendered units](#rendered-units) | `latex` | the units of the local parameter rendered as a formula |
| [derived units](#derived-units) | `latex` | the units of the value as the report derives them |

<span id="rendered-units"></span>**rendered units**

The report resolves the unit definition the local parameter references and renders it as a formula next to its identifier.

<span id="derived-units"></span>**derived units**

The report resolves the units of the local parameter and renders them as a formula, so that the units of a rate constant can be compared with the units the rate law needs.

## Related elements

- [KineticLaw](kineticlaw.md): the formula which gives the speed of a reaction
- [Parameter](parameter.md): a named value which the mathematics of the model can use
- [Reaction](reaction.md): a process which changes the quantities of species

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.11.6 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
