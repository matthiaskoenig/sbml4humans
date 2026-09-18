"""Reading SBML documents with libsbml.

`read_sbml` reads a document from a path or an SBML string and logs the errors
libsbml reports, the caller decides what to do with a document without model.
`package_plugins` gives the plugins of the Level 3 packages a document uses.
"""

import logging
from pathlib import Path

import libsbml


logger = logging.getLogger(__name__)


def read_sbml(source: Path | str) -> libsbml.SBMLDocument:
    """Read an SBMLDocument from a path or an SBML string.

    A string containing `<sbml` is parsed as SBML, every other source is read
    as a file. Reading errors are logged, the document is returned either way
    and has no model if the source could not be read.
    """
    doc: libsbml.SBMLDocument
    if isinstance(source, str) and "<sbml" in source:
        doc = libsbml.readSBMLFromString(source)
    else:
        doc = libsbml.readSBMLFromFile(str(source))

    if doc.getNumErrors() > 0:
        error_id = doc.getError(0).getErrorId()
        if error_id == libsbml.XMLFileUnreadable:
            message = "Unreadable SBML file"
        elif error_id == libsbml.XMLFileOperationError:
            message = "Problems reading SBML file: XMLFileOperationError"
        else:
            message = "SBMLDocumentErrors encountered while reading the SBML file."
        logger.error("`read_sbml` error '%s': %s", source, message)
        for k in range(doc.getNumErrors()):
            log_sbml_error(doc.getError(k))

    return doc


def package_plugins(doc: libsbml.SBMLDocument) -> list[libsbml.SBMLDocumentPlugin]:
    """The plugins of the Level 3 packages a document declares, in their order.

    A package is declared by a namespace of its own on the `<sbml>` element
    (core §4.1.3). libsbml implements the math of Level 3 Version 2 as a plugin
    of the document as well, which carries the namespace of core itself, under
    the prefix the file gives that namespace: none where the root declares it
    as the default namespace, and one more plugin with the prefix of its own
    where the root declares it a second time. Neither is a package the file
    uses, so the plugins of the core namespace are left out.
    """
    core: str = libsbml.SBMLNamespaces.getSBMLNamespaceURI(
        doc.getLevel(), doc.getVersion()
    )
    plugins: list[libsbml.SBMLDocumentPlugin] = [
        doc.getPlugin(k) for k in range(doc.getNumPlugins())
    ]
    return [plugin for plugin in plugins if plugin.getURI() != core]


def log_sbml_error(error: libsbml.SBMLError) -> None:
    """Log an SBMLError with the level of its severity."""
    message = (
        f"E{error.getErrorId()}: {error.getCategoryAsString()} "
        f"({error.getSeverityAsString()}) line {error.getLine()}: "
        f"{error.getShortMessage()}"
    )
    severity = error.getSeverity()
    if severity == libsbml.LIBSBML_SEV_WARNING:
        logger.warning(message)
    elif severity in (libsbml.LIBSBML_SEV_ERROR, libsbml.LIBSBML_SEV_FATAL):
        logger.error(message)
    else:
        logger.info(message)
