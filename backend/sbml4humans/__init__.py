"""sbml4humans, the human readable report of SBML models.

`sbml4humans.sbmlinfo` creates the report of an SBML document, `sbml4humans.api`
serves it over http for the sbml4humans frontend, and `sbml4humans.show` opens
the report of a local file in the browser:

    from sbml4humans import show
    show("model.xml")
"""

__version__ = "0.6.0"

from sbml4humans.viewer import show, stop


__all__ = ["__version__", "show", "stop"]
