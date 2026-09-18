# And

The associations below it are all needed at once.

An `and` is a complex: every gene below it has to be expressed for the reaction to run, and the loss of one of them stops the reaction. It holds two or more nodes, each of which is an [and](and.md), an [or](or.md) or a [gene product reference](geneproductref.md), so the operators nest to any depth.

The report shows it as the branches of the tree in the inspector of a reaction and links the nodes below it.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [associations](#associations) | `list` | the nodes which are all needed, two or more of them | [fbc v3 3.12](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="associations"></span>**associations**

The order of the nodes carries no meaning: an `and` is a set of conditions which hold at the same time. The report keeps them in the order of the file.

## Related elements

- [Gene product association](geneproductassociation.md): the genes a reaction needs, as the tree of operators over them
- [Or](or.md): one of the associations below it suffices
- [Gene product reference](geneproductref.md): the leaf of an association: one gene product the reaction depends on

## Specification

[SBML Level 3 Package: Flux Balance Constraints, Version 3 Release 1](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1), Section 3.12 (Olivier and Bergmann, COMBINE specification).
