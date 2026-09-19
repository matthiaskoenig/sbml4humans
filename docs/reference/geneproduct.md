# GeneProduct

A gene or one of its products which the reactions of the model depend on.

A gene product stands for a gene, a transcript or a protein which has to be present for a reaction to run. It exists so that the gene associations of a genome scale reconstruction, which used to be written into the notes of a reaction, have a place of their own and can be referenced.

Because the identifiers of a reconstruction do not follow the rules of an SBML identifier, a gene product carries them in its label, and it is recommended that it also carries an annotation which identifies the gene in a database.

The report shows the gene products of a model in a section of their own, with a link to the associated species, and links them from every reaction which names them.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [label](#label) | [`string`](datatypes.md#string) | required | the identifier under which the source of the model knows the gene | [fbc v3 3.5](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [associatedSpecies](#associatedspecies) | [`SIdRef`](datatypes.md#sidref) | optional | the species of the model which stands for this gene product | [fbc v3 3.5](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="label"></span>**label**

The label carries the gene identifier as it is written in the reconstruction, for example `b3670` or `Rv0649`. It is required, because the identifier of the gene product itself has to follow the rules of an SBML identifier and the gene identifier usually does not.

The report shows the label in the column "label" and in the inspector.

- `2021204` (error): The attribute 'fbc:label' on a &lt;GeneProduct&gt; must be of the data type 'string'.
- `2021205` (error): The attribute 'fbc:label' on a &lt;GeneProduct&gt; must be unique among the set of all &lt;GeneProduct&gt; elements defined in the &lt;Model&gt;.

<span id="associatedspecies"></span>**associatedSpecies**

Some reconstructions model a gene product as a [species](species.md) which participates in reactions. The attribute connects the two, and when it is set it names an existing species of the model.

The report links the species in the column "associated species" and in the inspector.

- `2021207` (error): The attribute 'fbc:associatedSpecies' on a &lt;GeneProduct&gt; must be the identifier of an existing &lt;Species&gt; defined in the enclosing &lt;Model&gt;.

## Validation rules

- `2010301` (error): (Extends validation rule #10301 in the SBML Level 3 Version 1 Core specification.) Within a &lt;model&gt; object the values of the attributes id and fbc:id on every instance of the following classes of objects must be unique across the set of all id and fbc:id attribute values of all such objects in a model: the model itself, plus all contained &lt;functionDefinition&gt;, &lt;compartment&gt;, &lt;species&gt;, &lt;reaction&gt;, &lt;speciesReference&gt;, &lt;modifierSpeciesReference&gt;, &lt;event&gt;, and &lt;parameter&gt; objects, plus the &lt;fluxBound&gt;, &lt;objective&gt;, &lt;fluxObjective&gt;, &lt;geneProduct&gt; and &lt;geneProductAssociation&gt; objects defined by the Flux Balance Constraints package.
- `2021201` (error): A &lt;GeneProduct&gt; object may have the optional SBML Level 3 Core attributes 'metaid' and 'sboTerm'. No other attributes from the SBML Level 3 Core namespace are permitted on a &lt;GeneProduct&gt;.
- `2021202` (error): A &lt;GeneProduct&gt; object may have the optional SBML Level 3 Core subobjects for notes and annotations. No other elements from the SBML Level 3 Core namespace are permitted on a &lt;GeneProduct&gt;.
- `2021203` (error): A &lt;GeneProduct&gt; object must have the required attributes 'fbc:id' and 'fbc:label' may have the optional attributes 'fbc:name' and 'fbc:associatedSpecies'. No other attributes from the SBML Level 3 Flux Balance Constraints namespace are permitted on a &lt;GeneProduct&gt; object.

## Related elements

- [Reaction](reaction.md): a process which changes the quantities of species
- [Species](species.md): a pool of a chemical entity in a compartment
- [Flux Balance Constraints (fbc)](fbc.md): the package which describes a constraint based model

## Specification

[SBML Level 3 Package: Flux Balance Constraints, Version 3 Release 1](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1), Section 3.5 (Olivier and Bergmann, COMBINE specification).
