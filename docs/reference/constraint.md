# Constraint

A condition which a valid simulation of the model has to satisfy.

A constraint is an expression which has to stay true while a simulation runs, for example that a concentration stays inside the range in which a rate law was measured. It does not change anything in the model: as soon as it is violated, the results from that moment on are no longer valid, and the software has to tell the user.

The report shows the rendered condition and the message which explains a violation.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [math](#math) | `Math` | the condition which has to stay true | [core 4.10.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [message](#message) | `XHTML` | the text which is shown when the condition is violated | [core 4.10.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="math"></span>**math**

The math is an expression which returns a boolean value. It is checked at the start of the simulation and at every moment after it.

The report renders the condition in the column "math" and in the inspector.

<span id="message"></span>**message**

The message is XHTML written for the user of a simulation, for example "the concentration of S1 left the range of the rate law". It is the place where the model author explains why the constraint exists.

The report shows the message next to the condition.

## Related elements

- [Model](model.md): the container of everything a model is made of
- [Parameter](parameter.md): a named value which the mathematics of the model can use

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.10 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
