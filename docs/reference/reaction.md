# Reaction

A process which changes the quantities of species.

A reaction is any process which changes how much of a species there is: a chemical conversion, a transport across a membrane, a binding, a degradation. It names the species it consumes as reactants and the species it produces as products, each with a stoichiometry, and it may name modifiers which influence its speed without being changed. How fast it runs is given by its [kinetic law](kineticlaw.md), which is optional: without one the speed of the reaction is undefined.

The report shows the equation of a reaction, its kinetic law and the units of that law, and lists its reactants, products and modifiers with links to the species.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| reversible | `boolean` | <span id="reversible"></span>whether the reaction can also run backwards | [Section 4.11.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| fast | `boolean` | <span id="fast"></span>whether the reaction was declared to be much faster than the others | [Section 4.11.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| compartment | `SIdRef` | <span id="compartment"></span>the compartment in which the reaction takes place | [Section 4.11.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| reactants | `list` | <span id="reactants"></span>the species the reaction consumes, with their stoichiometry | [Section 4.11.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| products | `list` | <span id="products"></span>the species the reaction produces, with their stoichiometry | [Section 4.11.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| modifiers | `list` | <span id="modifiers"></span>the species which influence the reaction without being consumed | [Section 4.11.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| kinetic law | `KineticLaw` | <span id="kinetic-law"></span>the formula which gives the speed of the reaction | [Section 4.11.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| fbc | `ReactionFbc` | <span id="fbc"></span>the flux bounds and the gene association which fbc adds to a reaction | [Section 3.8](https://sbml.org/documents/specifications/level-3/version-1/fbc/) |
| lower flux bound | `SIdRef` | <span id="lower-flux-bound"></span>the parameter which holds the smallest flux the reaction may carry | [Section 3.8](https://sbml.org/documents/specifications/level-3/version-1/fbc/) |
| upper flux bound | `SIdRef` | <span id="upper-flux-bound"></span>the parameter which holds the largest flux the reaction may carry | [Section 3.8](https://sbml.org/documents/specifications/level-3/version-1/fbc/) |
| gene product association | `string` | <span id="gene-product-association"></span>the logical expression of the genes under which the reaction can run | [Section 3.9](https://sbml.org/documents/specifications/level-3/version-1/fbc/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## In the report

| field | type | meaning |
| --- | --- | --- |
| equation | `string` | <span id="equation"></span>the reaction written as a chemical equation |
| gene products | `list` | <span id="gene-products"></span>the gene products named by the association of the reaction |

## Related elements

- [Species](species.md): a pool of a chemical entity in a compartment
- [Species reference](speciesreference.md): the participation of a species in a reaction as a reactant or a product
- [Modifier species reference](modifierspeciesreference.md): the participation of a species in a reaction as a modifier
- [Kinetic law](kineticlaw.md): the formula which gives the speed of a reaction
- [Compartment](compartment.md): a bounded space in which species are located

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.11 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
