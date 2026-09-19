# SpeciesReference

The participation of a species in a reaction as a reactant or a product.

A species reference does not introduce a species, it points at one of the species of the model and says how much of it one reaction event consumes or produces. Its stoichiometry can itself be a variable of the model, which is what a model with a variable yield uses.

The report shows a species reference as an element of its own, with a link to the reaction it belongs to, the role it plays there and a link to the species.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [species](#species) | `SIdRef` | - | the species which participates in the reaction | [core 4.11.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [stoichiometry](#stoichiometry) | `double` | - | how much of the species one reaction event consumes or produces | [core 4.11.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [constant](#constant) | `boolean` | - | whether the stoichiometry stays fixed during a simulation | [core 4.11.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="species"></span>**species**

The value is the identifier of a species of the model. Whether the species is consumed or produced follows from the list the reference appears in.

The report links the species in the table of the reaction and in the inspector.

<span id="stoichiometry"></span>**stoichiometry**

The stoichiometry is the factor with which the rate of the reaction enters the change of the species. A missing value means that it is unknown or that it is computed elsewhere, and when the reference is not constant, a rule or an event may change it during the simulation.

The report shows the stoichiometry in the list of reactants and products of a reaction and in the inspector.

<span id="constant"></span>**constant**

A constant species reference keeps its stoichiometry for the whole simulation and can only be set by an initial assignment. A reference which is not constant may be changed by a rule or by an event.

The report shows the flag as a mark in the inspector of the species reference.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [reaction](#reaction) | [`Reaction`](reaction.md) | the reaction which lists this species reference |
| [role](#role) | `string` | whether the reference is a reactant, a product or a modifier of its reaction |

<span id="reaction"></span>**reaction**

A species reference is written inside the list of reactants or of products of one reaction. The report shows it as an element of its own, so it names the reaction it belongs to and links it; the link of that reaction to the reference is what says which reaction it is.

The reaction is the first row of the inspector of a species reference.

<span id="role"></span>**role**

SBML says the role of a participant by the list it stands in and not by an attribute of its own. The report reads it from the link of the reaction to the reference and shows it as `reactant`, `product` or, for a [modifier species reference](modifierspeciesreference.md), `modifier`.

The role is shown in the inspector, below the reaction.

## Related elements

- [Reaction](reaction.md): a process which changes the quantities of species
- [Species](species.md): a pool of a chemical entity in a compartment
- [ModifierSpeciesReference](modifierspeciesreference.md): the participation of a species in a reaction as a modifier

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.11.3 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
