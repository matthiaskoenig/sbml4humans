# Gene product association

The genes a reaction needs, as the tree of operators over them.

A gene product association is what a genome scale reconstruction knows about the genetics of a reaction: which genes have to be expressed for the reaction to carry a flux. It belongs to one [reaction](reaction.md) and holds exactly one node, which is an [and](and.md), an [or](or.md) or a single [gene product reference](geneproductref.md).

The tree is the meaning of the construct, not a decoration of it. A knockout analysis removes a gene, evaluates the tree of every reaction and switches off the reactions whose tree becomes false, so an `and` and an `or` of the same genes describe two different organisms.

The report shows the association in the inspector of its reaction and gives every node of the tree a page of its own, so that a reader can follow a gene into the reactions which depend on it.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [association](#association) | `Association` | the single node the association holds | [fbc v3 3.9](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="association"></span>**association**

The node is an [and](and.md), an [or](or.md) or a [gene product reference](geneproductref.md); the last of them is the whole association of a reaction which depends on one gene alone.

The report renders the node and everything below it as the expression it stands for.

## Related elements

- [Reaction](reaction.md): a process which changes the quantities of species
- [And](and.md): the associations below it are all needed at once
- [Or](or.md): one of the associations below it suffices
- [Gene product reference](geneproductref.md): the leaf of an association: one gene product the reaction depends on
- [Gene product](geneproduct.md): a gene or one of its products which the reactions of the model depend on

## Specification

[SBML Level 3 Package: Flux Balance Constraints, Version 3 Release 1](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1), Section 3.9 (Olivier and Bergmann, COMBINE specification).
