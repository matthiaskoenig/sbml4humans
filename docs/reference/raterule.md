# RateRule

A formula which gives the rate of change of an element.

A rate rule states the derivative of a variable with respect to time: `dx/dt = f(W)`. It is how a model describes a change which is not the result of reactions, for example the growth of a compartment or an ordinary differential equation written directly. The element it changes must not be constant, and a species which is produced or consumed by a reaction may only have a rate rule when it is a boundary condition.

The report shows the variable, the rendered formula and the units the formula produces, which are the units of the variable per unit of time.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [variable](#variable) | `SIdRef` | the element whose rate of change the rule gives | [core 4.9.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [math](#math) | `Math` | the formula which computes the rate of change | [core 4.9.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="variable"></span>**variable**

The variable names the compartment, species, species reference or parameter which changes. It must not be constant, and no other rule may determine the same variable.

The report links the named element in the column "variable" and in the inspector.

<span id="math"></span>**math**

The math is an arbitrary expression which returns a number. Its units should be the units of the variable divided by the time units of the model.

The report renders the formula in the column "math" and in the inspector.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [derived units](#derived-units) | `latex` | the units of the formula as the report derives them |

<span id="derived-units"></span>**derived units**

The report derives the units of the formula from the units of the quantities it uses. They should be the units of the variable per unit of time of the model.

## Related elements

- [AssignmentRule](assignmentrule.md): a formula which holds at every moment of the simulation
- [AlgebraicRule](algebraicrule.md): an equation which has to hold at every moment of the simulation
- [Reaction](reaction.md): a process which changes the quantities of species

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.9.4 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
