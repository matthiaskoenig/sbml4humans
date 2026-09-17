# Species reference

The participation of a species in a reaction as a reactant or a product.

A species reference does not introduce a species, it points at one of the species of the model and says how much of it one reaction event consumes or produces. Its stoichiometry can itself be a variable of the model, which is what a model with a variable yield uses.

The report shows a species reference as an element of its own, with a link to the reaction it belongs to, the role it plays there and a link to the species.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| species | `SIdRef` | <span id="species"></span>the species which participates in the reaction | [Section 4.11.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| stoichiometry | `double` | <span id="stoichiometry"></span>how much of the species one reaction event consumes or produces | [Section 4.11.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| constant | `boolean` | <span id="constant"></span>whether the stoichiometry stays fixed during a simulation | [Section 4.11.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## Related elements

- [Reaction](reaction.md): a process which changes the quantities of species
- [Species](species.md): a pool of a chemical entity in a compartment
- [Modifier species reference](modifierspeciesreference.md): the participation of a species in a reaction as a modifier

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.11.3 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
