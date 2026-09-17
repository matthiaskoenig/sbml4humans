# SBML4Humans

[SBML4Humans](https://sbml4humans.de) renders [SBML](https://sbml.org) models as interactive, human readable reports: a Vue frontend on top of a FastAPI backend which creates the report of a model with [libsbml](https://sbml.org/software/libsbml/).

SBML is an XML format, and XML is written for programs: the mathematics of a model is content MathML, a unit is a product of base units spread over several elements, and an annotation is a URI in an RDF block, so reading a model in a text editor means reassembling it in your head. SBML4Humans gives the view of a model which the file itself does not give you, which is why it was started as the Google Summer of Code project "Interactive SBML report for Humans" ([NRNB GoogleSummerOfCode issue #164](https://github.com/nrnb/GoogleSummerOfCode/issues/164)). It reads models, it does not edit them and it does not simulate them.

![The report of the repressilator model, with the type rail, the element tables and the inspector of a selected species](docs/images/report-overview.png)

## Features

- one table per element type with the columns which matter for that type, sortable by every column and fast even for a genome scale reconstruction with tens of thousands of elements
- a search over the whole model and a rail which counts the elements of every type and filters the tables by type
- an inspector which shows one element in full: its attributes, the elements it references and the elements which reference it, its notes, its annotations and its history, and the raw XML of the element
- the mathematics typeset as formulas instead of MathML, and the units of every quantity rendered, including the units the report derives
- annotations resolved to the entries they identify, so a resource shows the name of the molecule, of the pathway or of the publication
- SBML of any level and version, plain or gzipped, and COMBINE archives with one report per SBML entry
- the comp, fbc and distrib packages of SBML Level 3
- example models which ship with the backend, from small models of a single feature over published models to the human reconstruction Recon3D
- every column, attribute, type and link kind explained where it is shown, from the same glossary the reference of the documentation is generated from
- the state of a report, that is the selected element, the search and the filter of types, is part of its url, so a report can be linked as it stands

## Documentation

The documentation is at [matthiaskoenig.github.io/sbml4humans](https://matthiaskoenig.github.io/sbml4humans/):

- [SBML](https://matthiaskoenig.github.io/sbml4humans/sbml/): what the format is, how a model is built from its elements and what the Level 3 packages add
- [Loading a model](https://matthiaskoenig.github.io/sbml4humans/inputs/): the three inputs, the accepted formats and the examples
- [Reading a report](https://matthiaskoenig.github.io/sbml4humans/report/): the type rail, the element tables, the search and the inspector
- [Reference](https://matthiaskoenig.github.io/sbml4humans/reference/): one page per element type with every attribute the report shows, the link kinds and the concepts the report adds
- [Development](https://matthiaskoenig.github.io/sbml4humans/development/): the repository layout, the setup of the backend and the frontend, the checks, the branches and the releases
- [Deployment](https://matthiaskoenig.github.io/sbml4humans/deployment/): the proxy, the certificates and the containers of the server

The sources of the site are in [`docs/`](docs), the site is built with [Zensical](https://zensical.org/) and published from `develop`.

## Funding

SBML4Humans was funded as part of [Google Summer of Code 2021](https://summerofcode.withgoogle.com/).

## License

- Source Code: [MIT](https://opensource.org/license/MIT), the full text is in [LICENSE](LICENSE)
- Documentation: [CC BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/)

&copy; 2021-2026 Matthias König
