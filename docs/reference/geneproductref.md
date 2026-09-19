# GeneProductRef

The leaf of an association: one gene product the reaction depends on.

A gene product reference is where an association names a gene. It carries the identifier of a [gene product](geneproduct.md) of the model and nothing else, so it is the place at which the tree of a reaction meets the list of the genes.

The report makes it an element of its own because the reference is where the file writes the identifier: the link to the gene product starts here, and the same gene may be named by several references of one reaction.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [geneProduct](#geneproduct) | [`SIdRef`](datatypes.md#sidref) | required | the gene product this leaf of the association names | [fbc v3 3.11](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="geneproduct"></span>**geneProduct**

The attribute is required and names a [gene product](geneproduct.md) of the same model. The report shows the identifier the reference writes and links the gene product behind it.

- `2020904` (error): The attribute 'fbc:geneProduct' on a &lt;GeneProductRef&gt; must be of the data type 'SIdRef'.
- `2020908` (error): The attribute 'fbc:geneProduct' on a &lt;GeneProductRef&gt; if set, must refer to 'id' of a &lt;GeneProduct&gt; in the &lt;Model&gt;.

## Validation rules

- `2020901` (error): A &lt;GeneProductRef&gt; object may have the optional SBML Level 3 Core attributes 'metaid' and 'sboTerm'. No other attributes from the SBML Level 3 Core namespace are permitted on a &lt;GeneProductRef&gt;.
- `2020902` (error): A &lt;GeneProductRef&gt; object may have the optional SBML Level 3 Core subobjects for notes and annotations. No other elements from the SBML Level 3 Core namespace are permitted on a &lt;GeneProductRef&gt;.
- `2020903` (error): A &lt;GeneProductRef&gt; object must have the required attribute 'fbc:geneProduct' and may have the optional attribute 'fbc:id'. No other attributes from the SBML Level 3 Flux Balance Constraints namespace are permitted on a &lt;&gt; object.

## Related elements

- [GeneProduct](geneproduct.md): a gene or one of its products which the reactions of the model depend on
- [GeneProductAssociation](geneproductassociation.md): the genes a reaction needs, as the tree of operators over them
- [And](and.md): the associations below it are all needed at once
- [Or](or.md): one of the associations below it suffices

## Specification

[SBML Level 3 Package: Flux Balance Constraints, Version 3 Release 1](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1), Section 3.11 (Olivier and Bergmann, COMBINE specification).
