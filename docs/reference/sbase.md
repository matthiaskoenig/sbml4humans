# SBase

The attributes every element of an SBML model carries.

Almost every object of an SBML model derives from the abstract type `SBase`, which carries the identifier, the name, the term of the Systems Biology Ontology and the two places for annotation: the notes for human readers and the annotation for machine readable metadata. An element type adds its own attributes on top of these, and may make an inherited attribute required, for example the identifier of a species.

The report shows these attributes for every element: the id and the name in the first two columns of every table, the meta id and the SBO term in the attributes of the inspector, and the notes, the annotations, the history and the XML in the third column of the inspector.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| id | `SId` | <span id="id"></span>the identifier other elements of the model use to reference the element | [Section 3.2.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| name | `string` | <span id="name"></span>the readable name of the element | [Section 3.2.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| meta id | `ID` | <span id="meta-id"></span>the identifier the annotations of the element point at | [Section 3.2.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| sbo | `SBOTerm` | <span id="sbo"></span>the term of the Systems Biology Ontology which classifies the element | [Section 3.2.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| notes | `XHTML` | <span id="notes"></span>the free text the model author wrote about the element | [Section 3.2.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| annotations | `list` | <span id="annotations"></span>the controlled vocabulary terms which link the element to database entries | [Section 6.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| history | `ModelHistory` | <span id="history"></span>who created the element and when it was modified | [Section 6.6](https://sbml.org/documents/specifications/level-3/version-2/core/) |

## In the report

| field | type | meaning |
| --- | --- | --- |
| xml | `string` | <span id="xml"></span>the element as it is written in the SBML file |

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 3.2 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
