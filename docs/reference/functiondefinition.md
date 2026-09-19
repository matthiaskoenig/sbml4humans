# FunctionDefinition

A named function which the mathematics of the model can call.

A function definition gives a name to a formula with arguments, so that a rate law which appears in many reactions is written once. The capabilities are deliberately limited: a function may only use its own arguments and other functions, it cannot read a species or a parameter, and it cannot call itself.

The report shows the body of the function as rendered mathematics, in the table and in the inspector.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [math](#math) | `Math` | the formula of the function, with its arguments | [core 4.3.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="math"></span>**math**

The math of a function definition is a MathML lambda expression: it declares the arguments and the expression which is computed from them. It is the only place in SBML core where a lambda is allowed.

The report renders the formula and shows it in the column "math" and in the inspector.

## Related elements

- [Model](model.md): the container of everything a model is made of

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.3 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
