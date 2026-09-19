# GeneProductRef

The leaf of an association: one gene product the reaction depends on.

A gene product reference is where an association names a gene. It carries the identifier of a [gene product](geneproduct.md) of the model and nothing else, so it is the place at which the tree of a reaction meets the list of the genes.

The report makes it an element of its own because the reference is where the file writes the identifier: the link to the gene product starts here, and the same gene may be named by several references of one reaction.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [geneProduct](#geneproduct) | `SIdRef` | the gene product this leaf of the association names | [fbc v3 3.11](https://doi.org/10.1515/jib-2026-0006) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="geneproduct"></span>**geneProduct**

The attribute is required and names a [gene product](geneproduct.md) of the same model. The report shows the label of that gene product, which is the identifier the reconstruction uses, and links the element behind it.

## Related elements

- [GeneProduct](geneproduct.md): a gene or one of its products which the reactions of the model depend on
- [GeneProductAssociation](geneproductassociation.md): the genes a reaction needs, as the tree of operators over them
- [And](and.md): the associations below it are all needed at once
- [Or](or.md): one of the associations below it suffices

## Specification

[SBML Level 3 Package: Flux Balance Constraints, Version 3 Release 1](https://doi.org/10.1515/jib-2026-0006), Section 3.11 (Olivier and Bergmann, COMBINE specification).
