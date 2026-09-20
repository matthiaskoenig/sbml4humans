# SBMLDocument

The container of an SBML file, with its level, version and packages.

An SBML file is one `sbml` element which declares the level and the version of the language it is written in, the packages it uses, and which contains at most one model. The level and the version decide which constructs are available and how they are interpreted, so they are the first thing to look at when reading an unfamiliar model.

The report shows one document per file of a submission, and a [Model](model.md) below it.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [level](#level) | [`positiveInteger`](datatypes.md#positiveinteger) | required | the level of SBML the file is written in | [core 4.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [version](#version) | [`positiveInteger`](datatypes.md#positiveinteger) | required | the version of the level the file is written in | [core 4.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [packages](#packages) | [`list`](datatypes.md#list) | optional | the Level 3 packages the file uses, with their version | [core 4.1.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="level"></span>**level**

A level is a major edition of the language; Level 3 is the current one and is the only level which supports packages. All constructs of a lower level can be mapped to Level 3, but a file of one level is not a file of another.

The report shows the level in the attributes of the document.

- `20102` (error): The &lt;sbml&gt; container element must declare the SBML Level using the attribute 'level', and this declaration must be consistent with the XML Namespace declared for the &lt;sbml&gt; element.
- `20105` (error): The attribute 'level' on the &lt;sbml&gt; container element must have a value of type 'positiveInteger'.

<span id="version"></span>**version**

A version is a minor revision within a level which corrects and refines the language. The `fast` attribute of a reaction, for example, exists in Level 3 Version 1 and is removed in Version 2.

The report shows the version next to the level in the attributes of the document.

- `20103` (error): The &lt;sbml&gt; container element must declare the SBML Version using the attribute 'version', and this declaration must be consistent with the XML Namespace declared for the &lt;sbml&gt; element.
- `20106` (error): The attribute 'version' on the &lt;sbml&gt; container element must have a value of type 'positiveInteger'.

<span id="packages"></span>**packages**

Level 3 is modular: a package adds features on top of the core and is identified by its XML namespace, and every file declares which packages it uses and whether a reader has to understand them. The report reads the packages comp, fbc, qual and distrib and shows the elements they add.

The report lists the prefix and the version of every declared package in the attributes of the document. The namespace of the core itself, which a file declares as well, is no package and is not listed.

Default: the file uses the core alone.

- `20104` (error): The &lt;sbml&gt; container element must declare the XML Namespace for any SBML Level 3 packages used within the SBML document. This declaration must be consistent with the values of the 'level' and 'version' attributes on the &lt;sbml&gt; element.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [annotation](#annotation) | [`string`](datatypes.md#string) | the annotation element of the document as the file writes it |

<span id="annotation"></span>**annotation**

The annotation of the `sbml` element is where a tool writes what it knows about the file in its own vocabulary, next to the RDF the report reads as [annotations](sbase.md). The report does not carry the XML of the document, which is the whole file, so it carries the annotation element alone.

The "XML" button in the header of the inspector shows it.

- `10401` (error): Every top-level element within an annotation element must have a namespace declared.
- `10402` (error): There cannot be more than one top-level element using a given namespace inside a given annotation element.
- `10403` (error): Top-level elements within an annotation element cannot use any SBML namespace, whether explicitly (by declaring the namespace to be one of the URIs "http://www.sbml.org/sbml/level1", "http://www.sbml.org/sbml/level2", "http://www.sbml.org/sbml/level2/version2", or "http://www.sbml.org/sbml/level2/version3", or "http://www.sbml.org/sbml/level2/version4", or "http://www.sbml.org/sbml/level2/version5" or "http://www.sbml.org/sbml/level3/version1/core"), or implicitly (by failing to declare any namespace).
- `10404` (error): A given SBML object may contain at most one &lt;annotation&gt; element.

## Validation rules

- `10719` (warning): The value of the 'sboTerm' attribute on the &lt;sbml&gt; object is expected to be an SBO identifier (http://www.biomodels.net/SBO/) referring to a modeling framework (i.e., terms derived from SBO:0000004, "modelling framework").
- `20101` (error): The &lt;sbml&gt; container element must declare the XML Namespace for SBML, and this declaration must be consistent with the values of the 'level' and 'version' attributes on the &lt;sbml&gt; element.
- `20108` (error): The &lt;sbml&gt; object may only have the optional attributes 'metaid' and 'sboTerm'.
- `20201` (error): An SBML document must contain a &lt;model&gt; element. The &lt;model&gt; element is optional in L3V2 and beyond.

## Related elements

- [Model](model.md): the container of everything a model is made of

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.1 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
