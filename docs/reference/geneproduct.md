# Gene product

A gene or one of its products which the reactions of the model depend on.

A gene product stands for a gene, a transcript or a protein which has to be present for a reaction to run. It exists so that the gene associations of a genome scale reconstruction, which used to be written into the notes of a reaction, have a place of their own and can be referenced.

Because the identifiers of a reconstruction do not follow the rules of an SBML identifier, a gene product carries them in its label, and it is recommended that it also carries an annotation which identifies the gene in a database.

The report shows the gene products of a model in a section of their own, with a link to the associated species, and links them from every reaction which names them.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| label | `string` | <span id="label"></span>the identifier under which the source of the model knows the gene | [Section 3.5](https://sbml.org/documents/specifications/level-3/version-1/fbc/) |
| associated species | `SIdRef` | <span id="associated-species"></span>the species of the model which stands for this gene product | [Section 3.5](https://sbml.org/documents/specifications/level-3/version-1/fbc/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## Related elements

- [Reaction](reaction.md): a process which changes the quantities of species
- [Species](species.md): a pool of a chemical entity in a compartment
- [Flux Balance Constraints (fbc)](fbc.md): the package which describes a constraint based model

## Specification

[SBML Level 3 Package: Flux Balance Constraints (fbc)](https://sbml.org/documents/specifications/level-3/version-1/fbc/), Section 3.5 (Olivier et al. 2026, Version 3 Release 1).
