# Or

One of the associations below it suffices.

An `or` is a set of alternatives: the isoenzymes of a reaction, or the several complexes which can catalyse it. The reaction runs as long as one of the nodes below it is satisfied, which is why a gene of an `or` alone is no knockout. It holds two or more nodes, each of which is an [and](and.md), an [or](or.md) or a [gene product reference](geneproductref.md).

The report shows it as the branches of the tree in the inspector of a reaction and links the nodes below it.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [associations](#associations) | `list` | the alternative nodes, two or more of them | [fbc v3 3.13](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="associations"></span>**associations**

The order of the nodes carries no meaning: an `or` is a set of alternatives of which one suffices. The report keeps them in the order of the file.

## Related elements

- [Gene product association](geneproductassociation.md): the genes a reaction needs, as the tree of operators over them
- [And](and.md): the associations below it are all needed at once
- [Gene product reference](geneproductref.md): the leaf of an association: one gene product the reaction depends on

## Specification

[SBML Level 3 Package: Flux Balance Constraints, Version 3 Release 1](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1), Section 3.13 (Olivier and Bergmann, COMBINE specification).
