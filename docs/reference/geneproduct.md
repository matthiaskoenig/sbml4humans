# GeneProduct

A gene or one of its products which the reactions of the model depend on.

A gene product stands for a gene, a transcript or a protein which has to be present for a reaction to run. It exists so that the gene associations of a genome scale reconstruction, which used to be written into the notes of a reaction, have a place of their own and can be referenced.

Because the identifiers of a reconstruction do not follow the rules of an SBML identifier, a gene product carries them in its label, and it is recommended that it also carries an annotation which identifies the gene in a database.

The report shows the gene products of a model in a section of their own, with a link to the associated species, and links them from every reaction which names them.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [label](#label) | `string` | the identifier under which the source of the model knows the gene | [fbc v3 3.5](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [associatedSpecies](#associatedspecies) | `SIdRef` | the species of the model which stands for this gene product | [fbc v3 3.5](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="label"></span>**label**

The label carries the gene identifier as it is written in the reconstruction, for example `b3670` or `Rv0649`. It is required, because the identifier of the gene product itself has to follow the rules of an SBML identifier and the gene identifier usually does not.

The report shows the label in the column "label" and in the inspector.

<span id="associatedspecies"></span>**associatedSpecies**

Some reconstructions model a gene product as a [species](species.md) which participates in reactions. The attribute connects the two, and when it is set it names an existing species of the model.

The report links the species in the column "associated species" and in the inspector.

## Related elements

- [Reaction](reaction.md): a process which changes the quantities of species
- [Species](species.md): a pool of a chemical entity in a compartment
- [Flux Balance Constraints (fbc)](fbc.md): the package which describes a constraint based model

## Specification

[SBML Level 3 Package: Flux Balance Constraints, Version 3 Release 1](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1), Section 3.5 (Olivier and Bergmann, COMBINE specification).
