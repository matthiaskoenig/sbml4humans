# Algebraic rule

An equation which has to hold at every moment of the simulation.

An algebraic rule states that an expression is zero: `0 = f(W)`. It constrains the elements of the model without saying which of them it determines, which is why a simulator has to solve it together with the rest of the system. A model must not be overdetermined, so at least one element of the equation has to be free, that is not constant and not determined by another rule or by the reactions.

The report shows the rendered equation and the units it produces; which element it determines follows from the rest of the model.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| math | `Math` | <span id="math"></span>the expression which has to be zero | [Section 4.9.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## In the report

| field | type | meaning |
| --- | --- | --- |
| derived units | `latex` | <span id="derived-units"></span>the units of the expression as the report derives them |

## Related elements

- [Assignment rule](assignmentrule.md): a formula which holds at every moment of the simulation
- [Rate rule](raterule.md): a formula which gives the rate of change of an element

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.9.2 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
