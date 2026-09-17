# Modifier species reference

The participation of a species in a reaction as a modifier.

A modifier is a species which appears in the rate formula of a reaction but is neither consumed nor produced by it, for example an enzyme or an inhibitor. SBML calls all of them modifiers and leaves the precise role to the term of the Systems Biology Ontology. A modifier has no stoichiometry.

The report shows a modifier species reference with a link to its reaction and to the species.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| species | `SIdRef` | <span id="species"></span>the species which modifies the reaction | [Section 4.11.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## Related elements

- [Reaction](reaction.md): a process which changes the quantities of species
- [Species](species.md): a pool of a chemical entity in a compartment
- [Species reference](speciesreference.md): the participation of a species in a reaction as a reactant or a product

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.11.4 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
