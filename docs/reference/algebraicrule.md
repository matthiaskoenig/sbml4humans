# AlgebraicRule

An equation which has to hold at every moment of the simulation.

An algebraic rule states that an expression is zero: `0 = f(W)`. It constrains the elements of the model without saying which of them it determines, which is why a simulator has to solve it together with the rest of the system. A model must not be overdetermined, so at least one element of the equation has to be free, that is not constant and not determined by another rule or by the reactions.

The report shows the rendered equation and the units it produces; which element it determines follows from the rest of the model.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [math](#math) | `Math` | the expression which has to be zero | [core 4.9.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="math"></span>**math**

The math is an arbitrary expression which returns a number, and the rule says that this number is zero at all times.

The report renders the expression in the column "math" and in the inspector.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [derived units](#derived-units) | `latex` | the units of the expression as the report derives them |

<span id="derived-units"></span>**derived units**

The report derives the units of the expression from the units of the quantities it uses. The terms of an equation should all have the same units.

## Related elements

- [AssignmentRule](assignmentrule.md): a formula which holds at every moment of the simulation
- [RateRule](raterule.md): a formula which gives the rate of change of an element

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.9.2 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
