# SBML4Humans

[![CI/CD](https://github.com/matthiaskoenig/sbml4humans/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/matthiaskoenig/sbml4humans/actions/workflows/ci-cd.yml)
[![PyPI version](https://img.shields.io/pypi/v/sbml4humans.svg)](https://pypi.org/project/sbml4humans/)
[![Python versions](https://img.shields.io/pypi/pyversions/sbml4humans.svg)](https://pypi.org/project/sbml4humans/)
[![Documentation](https://img.shields.io/badge/docs-sbml4humans-008080.svg)](https://matthiaskoenig.github.io/sbml4humans/)
[![MIT License](https://img.shields.io/github/license/matthiaskoenig/sbml4humans.svg)](https://opensource.org/license/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22827237.svg)](https://doi.org/10.5281/zenodo.22827237)

SBML4Humans creates interactive, human readable reports of [SBML](https://sbml.org) models: one table per element type, a search over everything, and an inspector which follows every reference between the objects of a model, for SBML core and the packages comp, fbc, qual and distrib.

The package opens the report of a file of your machine in the browser. The file is read by a local server and never leaves the machine:

```python
from sbml4humans import show

show("model.xml")
```

```bash
sbml4humans model.xml
```

The web application is at [sbml4humans.de](https://sbml4humans.de), the documentation at [matthiaskoenig.github.io/sbml4humans](https://matthiaskoenig.github.io/sbml4humans/), with [Reports from python](https://matthiaskoenig.github.io/sbml4humans/python/) for this package, and the source at [github.com/matthiaskoenig/sbml4humans](https://github.com/matthiaskoenig/sbml4humans).

If you use SBML4Humans in your work, please cite it as the [documentation](https://matthiaskoenig.github.io/sbml4humans/#how-to-cite) describes.

## Funding

Matthias König is supported by the Federal Ministry of Education and Research (BMBF, Germany) within the research network Systems Medicine of the Liver ([LiSyM](https://lisym.org/), grant number 031L0054) and by the German Research Foundation (DFG) within the Research Unit Programme FOR 5151 "[QuaLiPerF](https://qualiperf.de) (Quantifying Liver Perfusion-Function Relationship in Complex Resection - A Systems Medicine Approach)" by grant number 436883643. The first version was funded by [Google Summer of Code 2021](https://summerofcode.withgoogle.com/).

## License

- Source Code: [MIT](https://opensource.org/license/MIT), the full text is in [LICENSE](https://github.com/matthiaskoenig/sbml4humans/blob/develop/LICENSE)
- Documentation: [CC BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/)

&copy; 2021-2026 Matthias König
