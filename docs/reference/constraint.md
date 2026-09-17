# Constraint

A condition which a valid simulation of the model has to satisfy.

A constraint is an expression which has to stay true while a simulation runs, for example that a concentration stays inside the range in which a rate law was measured. It does not change anything in the model: as soon as it is violated, the results from that moment on are no longer valid, and the software has to tell the user.

The report shows the rendered condition and the message which explains a violation.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| math | `Math` | <span id="math"></span>the condition which has to stay true | [Section 4.10.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| message | `XHTML` | <span id="message"></span>the text which is shown when the condition is violated | [Section 4.10.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## Related elements

- [Model](model.md): the container of everything a model is made of
- [Parameter](parameter.md): a named value which the mathematics of the model can use

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.10 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
