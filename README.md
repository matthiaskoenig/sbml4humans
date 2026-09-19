# SBML4Humans

[![CI/CD](https://github.com/matthiaskoenig/sbml4humans/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/matthiaskoenig/sbml4humans/actions/workflows/ci-cd.yml)
[![PyPI version](https://img.shields.io/pypi/v/sbml4humans.svg)](https://pypi.org/project/sbml4humans/)
[![Python versions](https://img.shields.io/pypi/pyversions/sbml4humans.svg)](https://pypi.org/project/sbml4humans/)
[![Documentation](https://img.shields.io/badge/docs-sbml4humans-008080.svg)](https://matthiaskoenig.github.io/sbml4humans/)
[![MIT License](https://img.shields.io/github/license/matthiaskoenig/sbml4humans.svg)](https://opensource.org/license/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22827237.svg)](https://doi.org/10.5281/zenodo.22827237)

## About

The Systems Biology Markup Language ([SBML](https://sbml.org)) is the de facto standard for the representation and exchange of mathematical models of biological systems. It represents many different classes of phenomena in biology, among them metabolic networks, signaling pathways and regulatory networks, and supports models of arbitrary complexity, from a single process to a multi-scale model, and it is read and written by a large ecosystem of [software](https://sbml.org/software/). The [specification](https://sbml.org/documents/specifications/level-3/version-2/core/) gives the detailed overview, [Keating et al. 2020](https://doi.org/10.15252/msb.20199110) the high level introduction.

The information in SBML is organized as lists of components, such as compartments, species, parameters and reactions, written in XML. A parser reads such a file into a tree of the model and of the relations between its components, but SBML is difficult to read, to comprehend and to interpret for humans directly, and tools are needed which provide an abstraction layer to interact with the SBML objects and the relationships between them.

SBML4Humans provides that layer: an interactive and reactive report of an SBML model which allows humans, experts as well as novices, to comprehend the content of a model. A report renders the information of a model for human consumption as an interactive page, navigates between the components (which species take part in which reaction, which reaction a gene product catalyzes, in which formula a parameter appears), resolves the annotations of a component to the entries they identify, searches and filters the model down to the part which matters, and explains every type, column and attribute where it is shown. It reads models, it does not edit them and it does not simulate them.

A report carries the data model of the file: every level and version of SBML which libsbml reads, and the four Level 3 packages comp, fbc, qual and distrib with the objects and the references they add. The submodels, ports, deletions and replacements of a hierarchical model, the objectives, gene products and gene associations of a constraint based one, the qualitative species and transitions of a logical model and the uncertainties of a measured value are elements of the report like the species and the reactions of the core, each with its attributes, its annotations and its place in the graph of references.

[![The report of the repressilator model, with the type bar, the element tables and the inspector of a selected species](docs/images/report-overview.png)](docs/images/report-overview.png)

Use it at [sbml4humans.de](https://sbml4humans.de) with a file, a url or pasted SBML, or with one of the example models which ship with it.

Or use it from python, where the report of a local file opens in your browser and the file never leaves your machine ([Reports from python](https://matthiaskoenig.github.io/sbml4humans/python/)):

```python
from sbml4humans import show

show("model.xml")
```

## Documentation

The documentation is available at [matthiaskoenig.github.io/sbml4humans](https://matthiaskoenig.github.io/sbml4humans/): what [SBML](https://matthiaskoenig.github.io/sbml4humans/sbml/) is, how to [load a model](https://matthiaskoenig.github.io/sbml4humans/inputs/), how to [read a report](https://matthiaskoenig.github.io/sbml4humans/report/), the [reference](https://matthiaskoenig.github.io/sbml4humans/reference/) of every element type with its attributes, and, for contributors, the [development](https://matthiaskoenig.github.io/sbml4humans/development/) of the application.

If you have any questions or issues please [open an issue](https://github.com/matthiaskoenig/sbml4humans/issues).

## How to cite

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22827237.svg)](https://doi.org/10.5281/zenodo.22827237)

If you use SBML4Humans please cite the archived software on [Zenodo](https://doi.org/10.5281/zenodo.22827237):

> König, M., & Das, S. (2026). *SBML4Humans: interactive reports of SBML models* (Version 0.5.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.22841376

```bibtex
@software{koenig_sbml4humans,
  author    = {König, Matthias and Das, Sankha},
  title     = {SBML4Humans: interactive reports of SBML models},
  year      = {2026},
  month     = sep,
  version   = {0.5.0},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.22841376},
  url       = {https://doi.org/10.5281/zenodo.22841376},
}
```

## Funding

Matthias König is supported by the Federal Ministry of Education and Research (BMBF, Germany) within the research network Systems Medicine of the Liver ([LiSyM](https://lisym.org/), grant number 031L0054) and by the German Research Foundation (DFG) within the Research Unit Programme FOR 5151 "[QuaLiPerF](https://qualiperf.de) (Quantifying Liver Perfusion-Function Relationship in Complex Resection - A Systems Medicine Approach)" by grant number 436883643. The first version was funded by [Google Summer of Code 2021](https://summerofcode.withgoogle.com/).

## License

- Source Code: [MIT](https://opensource.org/license/MIT), the full text is in [LICENSE](LICENSE)
- Documentation: [CC BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/)

&copy; 2021-2026 Matthias König
