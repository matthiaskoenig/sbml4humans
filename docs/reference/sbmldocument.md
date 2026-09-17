# Document

The container of an SBML file, with its level, version and packages.

An SBML file is one `sbml` element which declares the level and the version of the language it is written in, the packages it uses, and which contains at most one model. The level and the version decide which constructs are available and how they are interpreted, so they are the first thing to look at when reading an unfamiliar model.

The report shows one document per file of a submission, and a [Model](model.md) below it.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| level | `positiveInteger` | <span id="level"></span>the level of SBML the file is written in | [Section 4.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| version | `positiveInteger` | <span id="version"></span>the version of the level the file is written in | [Section 4.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| packages | `list` | <span id="packages"></span>the Level 3 packages the file uses, with their version | [Section 4.1.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## Related elements

- [Model](model.md): the container of everything a model is made of

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.1 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
