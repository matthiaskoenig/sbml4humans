# ModifierSpeciesReference

The participation of a species in a reaction as a modifier.

A modifier is a species which appears in the rate formula of a reaction but is neither consumed nor produced by it, for example an enzyme or an inhibitor. SBML calls all of them modifiers and leaves the precise role to the term of the Systems Biology Ontology. A modifier has no stoichiometry.

The report shows a modifier species reference with a link to its reaction and to the species.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [species](#species) | `SIdRef` | the species which modifies the reaction | [core 4.11.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="species"></span>**species**

The value is the identifier of a species of the model. Every species which appears in the kinetic law of a reaction has to be declared as a reactant, a product or a modifier of it.

The report links the species in the list of modifiers of the reaction and in the inspector.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [reaction](#reaction) | `Reaction` | the reaction which lists this modifier |

<span id="reaction"></span>**reaction**

A modifier species reference is written inside the list of modifiers of one reaction. The report shows it as an element of its own, so it names the reaction it belongs to and links it.

The reaction is the first row of the inspector of a modifier species reference.

## Related elements

- [Reaction](reaction.md): a process which changes the quantities of species
- [Species](species.md): a pool of a chemical entity in a compartment
- [SpeciesReference](speciesreference.md): the participation of a species in a reaction as a reactant or a product

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.11.4 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
