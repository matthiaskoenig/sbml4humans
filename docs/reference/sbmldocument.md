# Document

The container of an SBML file, with its level, version and packages.

An SBML file is one `sbml` element which declares the level and the version of the language it is written in, the packages it uses, and which contains at most one model. The level and the version decide which constructs are available and how they are interpreted, so they are the first thing to look at when reading an unfamiliar model.

The report shows one document per file of a submission, and a [Model](model.md) below it.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [level](#level) | `positiveInteger` | the level of SBML the file is written in | [core 4.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [version](#version) | `positiveInteger` | the version of the level the file is written in | [core 4.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [packages](#packages) | `list` | the Level 3 packages the file uses, with their version | [core 4.1.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="level"></span>**level**

A level is a major edition of the language; Level 3 is the current one and is the only level which supports packages. All constructs of a lower level can be mapped to Level 3, but a file of one level is not a file of another.

The report shows the level in the attributes of the document.

<span id="version"></span>**version**

A version is a minor revision within a level which corrects and refines the language. The `fast` attribute of a reaction, for example, exists in Level 3 Version 1 and is removed in Version 2.

The report shows the version next to the level in the attributes of the document.

<span id="packages"></span>**packages**

Level 3 is modular: a package adds features on top of the core and is identified by its XML namespace, and every file declares which packages it uses and whether a reader has to understand them. The report reads the packages comp, fbc and distrib and shows the elements they add.

The report lists the prefix and the version of every declared package in the attributes of the document.

## Related elements

- [Model](model.md): the container of everything a model is made of

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.1 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
