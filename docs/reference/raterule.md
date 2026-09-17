# Rate rule

A formula which gives the rate of change of an element.

A rate rule states the derivative of a variable with respect to time: `dx/dt = f(W)`. It is how a model describes a change which is not the result of reactions, for example the growth of a compartment or an ordinary differential equation written directly. The element it changes must not be constant, and a species which is produced or consumed by a reaction may only have a rate rule when it is a boundary condition.

The report shows the variable, the rendered formula and the units the formula produces, which are the units of the variable per unit of time.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| variable | `SIdRef` | <span id="variable"></span>the element whose rate of change the rule gives | [Section 4.9.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| math | `Math` | <span id="math"></span>the formula which computes the rate of change | [Section 4.9.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## In the report

| field | type | meaning |
| --- | --- | --- |
| derived units | `latex` | <span id="derived-units"></span>the units of the formula as the report derives them |

## Related elements

- [Assignment rule](assignmentrule.md): a formula which holds at every moment of the simulation
- [Algebraic rule](algebraicrule.md): an equation which has to hold at every moment of the simulation
- [Reaction](reaction.md): a process which changes the quantities of species

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.9.4 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
