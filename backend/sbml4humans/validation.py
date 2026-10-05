"""The validation of libsbml in the report.

libsbml reports an issue with its line and column, not with its element, so the
report records where every element starts (`ElementPositions`) and an issue
goes to the element which starts closest before it.
"""

import bisect
import logging
from collections.abc import Mapping
from contextvars import ContextVar

import libsbml

from sbml4humans.model import Severity, ValidationIssue


logger = logging.getLogger(__name__)

_ERRORS = frozenset(
    {
        libsbml.LIBSBML_SEV_ERROR,
        libsbml.LIBSBML_SEV_FATAL,
        libsbml.LIBSBML_SEV_SCHEMA_ERROR,
    }
)
_WARNINGS = frozenset(
    {libsbml.LIBSBML_SEV_WARNING, libsbml.LIBSBML_SEV_GENERAL_WARNING}
)


def _depth(sbase: libsbml.SBase) -> int:
    """How deep an element is nested below the document."""
    depth = 0
    parent: libsbml.SBase | None = sbase.getParentSBMLObject()
    while parent is not None:
        depth += 1
        parent = parent.getParentSBMLObject()
    return depth


class ElementPositions:
    """Where every element of a report starts in its file.

    Of two elements which start at the same position the one nested deeper
    wins, which is the element the position belongs to.
    """

    def __init__(self, document_pk: str) -> None:
        """Positions of no element yet; the document is where nothing starts."""
        self.document_pk = document_pk
        self._keys: list[tuple[int, int, int]] = []
        self._pks: list[str] = []

    def add(self, sbase: libsbml.SBase, pk: str) -> None:
        """Record the start of an element, ignoring an element without a line."""
        line = sbase.getLine()
        if line <= 0:
            return
        key = (line, sbase.getColumn(), _depth(sbase))
        index = bisect.bisect_right(self._keys, key)
        self._keys.insert(index, key)
        self._pks.insert(index, pk)

    def pk_at(self, line: int, column: int) -> str:
        """The pk of the element which starts closest at or before a position."""
        if line <= 0:
            return self.document_pk
        index = bisect.bisect_right(self._keys, (line, column, 1 << 30))
        return self._pks[index - 1] if index > 0 else self.document_pk


def _severity(error: libsbml.SBMLError) -> Severity:
    """The severity of the report for one of libsbml."""
    severity = error.getSeverity()
    if severity in _ERRORS:
        return "error"
    if severity in _WARNINGS:
        return "warning"
    return "info"


def issues_of(
    doc: libsbml.SBMLDocument, positions: ElementPositions
) -> list[ValidationIssue]:
    """The issues of the error log of a document, in its order, each once."""
    issues: list[ValidationIssue] = []
    seen: set[tuple[int, int, int, str]] = set()
    for k in range(doc.getNumErrors()):
        error: libsbml.SBMLError = doc.getError(k)
        line, column = error.getLine(), error.getColumn()
        message = error.getMessage().strip()
        key = (error.getErrorId(), line, column, message)
        if key in seen:
            continue
        seen.add(key)
        issues.append(
            ValidationIssue(
                rule=error.getErrorId(),
                severity=_severity(error),
                category=error.getCategoryAsString(),
                short_message=error.getShortMessage(),
                message=message,
                line=line,
                column=column,
                pk=positions.pk_at(line, column),
            )
        )
    return issues


# the documents the comp validator may resolve while a document is validated,
# keyed by the source of an external model definition, None outside of one
_DOCUMENTS: ContextVar[Mapping[str, libsbml.SBMLDocument] | None] = ContextVar(
    "validation_documents", default=None
)


class ReportResolver(libsbml.SBMLResolver):
    """The resolver of libsbml, confined to the report while it validates.

    The comp validator reads the document an external model definition names
    through the resolver registry of libsbml, which would read any path and,
    with a resolver for it, any url. While a document is validated this one
    answers only the documents of the report; at every other time it is the
    file resolver of libsbml.
    """

    def __init__(self) -> None:
        """A resolver which keeps the file resolver of libsbml to delegate to."""
        super().__init__()
        self._files = libsbml.SBMLFileResolver()

    # the SWIG base class declares its methods with `*args`
    def resolve(  # ty: ignore[invalid-method-override]
        self,
        uri: str,
        baseUri: str = "",
    ) -> libsbml.SBMLDocument | None:
        """The document at a uri: one of the report while validating."""
        documents = _DOCUMENTS.get()
        if documents is None:
            return self._files.resolve(uri, baseUri)
        doc = documents.get(uri)
        if doc is None:
            return None
        # the caller of a resolver owns the document it returns
        clone: libsbml.SBMLDocument = doc.clone()
        clone.thisown = False
        return clone

    def resolveUri(  # ty: ignore[invalid-method-override]
        self,
        uri: str,
        baseUri: str = "",
    ) -> libsbml.SBMLUri | None:
        """The uri of a document: one of the report while validating."""
        documents = _DOCUMENTS.get()
        if documents is None:
            return self._files.resolveUri(uri, baseUri)
        if uri not in documents:
            return None
        resolved = libsbml.SBMLUri(uri)
        resolved.thisown = False
        return resolved

    def clone(self) -> ReportResolver:
        """The registry keeps the one instance, so a clone is the instance."""
        return self


def _install_resolver() -> ReportResolver:
    """Replace the resolvers of the registry of libsbml by the report resolver."""
    registry = libsbml.SBMLResolverRegistry.getInstance()
    while registry.getNumResolvers() > 0:
        registry.removeResolver(0)
    resolver = ReportResolver()
    registry.addResolver(resolver)
    return resolver


# kept referenced, so that python does not collect the director libsbml calls
_RESOLVER = _install_resolver()


def validate(
    doc: libsbml.SBMLDocument,
    positions: ElementPositions,
    documents: Mapping[str, libsbml.SBMLDocument],
) -> list[ValidationIssue]:
    """Check the consistency of a document and return all of its issues.

    `documents` are the documents of the report which the external model
    definitions of the document name, keyed by their `source`: the only ones
    the comp validator can read.

    Args:
        doc: the document to check.
        positions: where the elements of the report of the document start.
        documents: the documents the comp validator may resolve.

    Returns:
        The issues of the document, in the order of libsbml.
    """
    token = _DOCUMENTS.set(documents)
    try:
        doc.checkConsistency()
    finally:
        _DOCUMENTS.reset(token)
    return issues_of(doc, positions)
