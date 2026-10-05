"""The validation of libsbml in the report.

libsbml reports an issue with its line and column, not with its element, so the
report records where every element starts (`ElementPositions`) and an issue
goes to the element which starts closest before it.
"""

import bisect
import logging

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
