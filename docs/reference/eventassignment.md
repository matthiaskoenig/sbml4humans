# Event assignment

The new value an event gives to one element of the model.

An event assignment sets a compartment, a species, a stoichiometry or a parameter to the value of its formula at the moment the event is executed. The element must not be constant, because a constant cannot be changed by an event.

The report shows an event assignment as an element of its own, with a link to the element it changes and the rendered formula.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| variable | `SIdRef` | <span id="variable"></span>the element the assignment changes | [Section 4.12.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| math | `Math` | <span id="math"></span>the formula which computes the new value | [Section 4.12.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## Related elements

- [Event](event.md): an instantaneous change of the model when a condition becomes true
- [Assignment rule](assignmentrule.md): a formula which holds at every moment of the simulation

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.12.5 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
