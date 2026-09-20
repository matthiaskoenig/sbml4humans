# ListOf

A list of a model or of an element which states something of its own.

SBML groups the elements of one type in a list: the species of a model in its `listOfSpecies`, the reactants of a reaction in its `listOfReactants`, the units of a unit definition in its `listOfUnits`. Every such list is an object of a class of its own which derives from [SBase](sbase.md), so a list may carry a meta id, an SBO term, notes and an annotation, and from Level 3 Version 2 on an id and a name. A note which says where the species of a model come from, or an annotation which relates all of them to one pathway, is written on the list and on none of its elements. A list has no attributes besides these, and what it states has no effect on the mathematics of the model.

Up to Level 3 Version 1 a list had to hold at least one element. Level 3 Version 2 allows an empty list, so that a file can keep what it says about the list, for example a note which explains why a model has no rules.

The lists of most models state nothing, and the report does not show them: the elements of a list are the rows of their table, or the rows of their owner in the inspector. A list which states at least one of the above is an element of the report. The report has one type for the lists of every class and of every package, which the name of the list in the file tells apart. Such a list is linked from the heading of the table of its elements and from the row "lists" in the inspector of the element which owns it, the model for a `listOfSpecies` and the reaction for a `listOfReactants`; an empty list has no table, so its owner is where it is found. The inspector of a list shows its name in the file and the number of its elements next to the shared attributes, its notes and its annotations, and its XML is the list without its elements. A list without an id is named after its owner and its name in the file, `J0.listOfReactants`, and a list of the model by that name alone.

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [list](#list) | [`string`](datatypes.md#string) | the name the list has in the file, which says what it lists |
| [size](#size) | [`integer`](datatypes.md#integer) | the number of elements the list holds |

<span id="list"></span>**list**

Every list of SBML is an XML element with a name of its own, `listOfSpecies`, `listOfReactants` or `listOfPorts`, and that name is all which tells the lists of a file apart: a list needs neither an id nor a meta id. The name is written without the prefix of its package.

The report shows the name in the attributes of the inspector of the list, and names a list without an id by it.

<span id="size"></span>**size**

The report keeps the elements of a list where it shows them, as the rows of their table or in the inspector of their owner, and the list carries their number alone. The number is zero for an empty list, which Level 3 Version 2 allows and which a file writes to say something about it.

The report shows the number in the attributes of the inspector of the list.

## Related elements

- [Model](model.md): the container of everything a model is made of
- [Reaction](reaction.md): a process which changes the quantities of species
- [UnitDefinition](unitdefinition.md): a named unit built from the base units of SBML
- [Port](port.md): an element of the model which other models are meant to connect to

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.2.7 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
