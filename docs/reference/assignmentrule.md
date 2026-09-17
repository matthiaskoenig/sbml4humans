# Assignment rule

A formula which holds at every moment of the simulation.

An assignment rule states that a variable of the model equals an expression, at all times, and not only at the start: `x = f(V)`. It is the way to define a quantity which follows from others, for example a total concentration or a saturation. The element it assigns to must not be constant, and no other rule may assign to the same element.

The report shows the variable, the rendered formula and the units the formula produces.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| variable | `SIdRef` | <span id="variable"></span>the element the rule assigns to | [Section 4.9.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| math | `Math` | <span id="math"></span>the formula which computes the value of the variable | [Section 4.9.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## In the report

| field | type | meaning |
| --- | --- | --- |
| derived units | `latex` | <span id="derived-units"></span>the units of the formula as the report derives them |

## Related elements

- [Rate rule](raterule.md): a formula which gives the rate of change of an element
- [Algebraic rule](algebraicrule.md): an equation which has to hold at every moment of the simulation
- [Initial assignment](initialassignment.md): a formula which computes the value of an element at the start of the simulation

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.9.3 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
