# SBML4Humans

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

SBML4Humans is released under the MIT license. If you use it in your work, please cite it as the [documentation](https://matthiaskoenig.github.io/sbml4humans/#how-to-cite) describes.
