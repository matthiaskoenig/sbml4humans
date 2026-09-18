# SBase

The attributes every element of an SBML model carries.

Almost every object of an SBML model derives from the abstract type `SBase`, which carries the identifier, the name, the term of the Systems Biology Ontology and the two places for annotation: the notes for human readers and the annotation for machine readable metadata. An element type adds its own attributes on top of these, and may make an inherited attribute required, for example the identifier of a species.

The report shows these attributes for every element: the id and the name in the first two columns of every table, the meta id and the SBO term in the attributes of the inspector, and the notes, the annotations, the history and the XML in the third column of the inspector.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [id](#id) | `SId` | the identifier other elements of the model use to reference the element | [core 3.2.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [name](#name) | `string` | the readable name of the element | [core 3.2.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [metaId](#metaid) | `ID` | the identifier the annotations of the element point at | [core 3.2.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [sbo](#sbo) | `SBOTerm` | the term of the Systems Biology Ontology which classifies the element | [core 3.2.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [notes](#notes) | `XHTML` | the free text the model author wrote about the element | [core 3.2.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [annotations](#annotations) | `list` | the controlled vocabulary terms which link the element to database entries | [core 6.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [history](#history) | `ModelHistory` | who created the element and when it was modified | [core 6.6](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [replacements](#replacements) | `CompSBase` | how the element replaces an element of a submodel or is replaced by one | [comp 3.6](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [replaced by](#replaced-by) | `ReplacedBy` | the element of a submodel which takes the place of this element | [comp 3.6.4](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [replaced elements](#replaced-elements) | `list` | the elements of submodels which this element takes the place of | [comp 3.6.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [uncertainties](#uncertainties) | `list` | the statistical measures of the value of the element | [distrib 3.9](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf) |

<span id="id"></span>**id**

The id is the name of the element inside the model. It is unique within a model and is what the math of a rule, of a kinetic law or of an event assignment writes when it refers to the element. Some types make the id required, for example a species, a compartment or a parameter cannot be referenced without one.

The report shows the id in the first column of every table and uses it as the label of every link to the element.

<span id="name"></span>**name**

The name is meant for human readers and has no meaning inside the model: it is not used for cross references and it does not have to be unique. A model which uses short identifiers usually carries the readable label here, for example "glucose 6-phosphate" for the species `g6p`.

The report shows the name in the second column of every table, next to the id.

<span id="metaid"></span>**metaId**

The meta id exists so that the RDF metadata in the annotation of an element can name the element it describes. It is unique within the whole file, not only within the model, and it has no meaning for the mathematics of the model.

The report shows the meta id in the attributes of the inspector and uses it as a fallback label when an element has no id.

<span id="sbo"></span>**sbo**

The Systems Biology Ontology is a set of controlled terms for the parts of a model, for example "simple chemical" for a species or "mass action rate law" for a kinetic law. The term makes the intention of the model author explicit for software which understands the ontology, and a model stays interpretable without it.

The report shows the term in the attributes of the inspector and links it to its entry on identifiers.org.

<span id="notes"></span>**notes**

The notes hold XHTML written for human readers: a description of what the element stands for, the assumptions behind a rate law, the source of a value. They are the place where the story of a model is told, and many published models carry their documentation here.

The report renders the notes of the selected element in the third column of the inspector, with a restricted set of markup.

<span id="annotations"></span>**annotations**

An annotation relates the element to an entry of an external database, for example to a ChEBI compound, a UniProt protein or a Gene Ontology process. Every relation names a qualifier, such as "is" or "is part of", so that the meaning of the reference is explicit. The qualifiers are those of MIRIAM and the entries are named by their identifiers.org url.

The report groups the annotations of an element by qualifier, resolves the label of every entry and links it to the resource.

<span id="history"></span>**history**

The history is part of the standard annotation and records the creators of an element with their affiliation and electronic mail address, the date of creation and the dates of the modifications.

The report shows the history of the selected element below its annotations.

<span id="replacements"></span>**replacements**

Replacements are the glue of a composed model. An element may state that it replaces elements of submodels, in which case every reference to those elements points at it afterwards, or that it is itself replaced by an element of a submodel. Two elements of different submodels are connected by letting one element of the containing model replace both.

The report shows the rows "replaced by" and "replaced elements" in the inspector of every element which carries them.

<span id="replaced-by"></span>**replaced by**

An element which is replaced disappears from the composed model: every reference to it points at the element of the submodel instead. The submodel is named by its identifier, the element inside it by a port, an identifier, a unit identifier or a meta id, the same four ways a [port](port.md) names an element.

The report links the submodel and shows the named element next to it.

<span id="replaced-elements"></span>**replaced elements**

Every entry names a submodel and one element inside it which this element replaces. It is how a species of the containing model is connected to the species of two submodels: the containing species replaces both, and the three become one pool.

The report lists the submodel and the named element of every replacement in the inspector.

<span id="uncertainties"></span>**uncertainties**

Any element with a mathematical meaning or with math of its own may carry uncertainties, and it may carry several of them, because measures from different experiments or different publications may overlap or contradict each other and each set belongs together.

The report lists the uncertainties of an element in its inspector with the number of their parameters, and shows every [uncertainty](uncertainty.md) as an element of its own.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [xml](#xml) | `string` | the element as it is written in the SBML file |

<span id="xml"></span>**xml**

The report keeps the XML of every element so that a modeller can see what the file actually contains, including the parts of a package the report does not display.

The XML view is the last section of the third column of the inspector.

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 3.2 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
