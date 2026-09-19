# Or

One of the associations below it suffices.

An `or` is a set of alternatives: the isoenzymes of a reaction, or the several complexes which can catalyse it. The reaction runs as long as one of the nodes below it is satisfied, which is why a gene of an `or` alone is no knockout. It holds two or more nodes, each of which is an [and](and.md), an [or](or.md) or a [gene product reference](geneproductref.md).

The report shows it as the branches of the tree in the inspector of a reaction and links the nodes below it.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [associations](#associations) | [`list`](datatypes.md#list) | required | the alternative nodes, two or more of them | [fbc v3 3.13](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="associations"></span>**associations**

The order of the nodes carries no meaning: an `or` is a set of alternatives of which one suffices. The report keeps them in the order of the file.

- `2021103` (error): An &lt;Or&gt; object must have two or more concrete &lt;Association&gt; objects: &lt;GeneProductRef&gt;, &lt;And&gt;, or &lt;Or&gt;. No other elements from the SBML Level 3 Flux Balance Constraints namespace are permitted on an &lt;Or&gt; object.

## Validation rules

- `2021101` (error): An &lt;Or&gt; object may have the optional SBML Level 3 Core attributes 'metaid' and 'sboTerm'. No other attributes from the SBML Level 3 Core namespace are permitted on an &lt;Or&gt;.
- `2021102` (error): An &lt;Or&gt; object may have the optional SBML Level 3 Core subobjects for notes and annotations. No other elements from the SBML Level 3 Core namespace are permitted on an &lt;Or&gt;.
- `2021103` (error): An &lt;Or&gt; object must have two or more concrete &lt;Association&gt; objects: &lt;GeneProductRef&gt;, &lt;And&gt;, or &lt;Or&gt;. No other elements from the SBML Level 3 Flux Balance Constraints namespace are permitted on an &lt;Or&gt; object.

## Related elements

- [GeneProductAssociation](geneproductassociation.md): the genes a reaction needs, as the tree of operators over them
- [And](and.md): the associations below it are all needed at once
- [GeneProductRef](geneproductref.md): the leaf of an association: one gene product the reaction depends on

## Specification

[SBML Level 3 Package: Flux Balance Constraints, Version 3 Release 1](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1), Section 3.13 (Olivier and Bergmann, COMBINE specification).
