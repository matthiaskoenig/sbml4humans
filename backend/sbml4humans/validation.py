"""The validation of libsbml in the report.

libsbml reports an issue with its line and column, not with its element, so the
report records where every element starts (`ElementPositions`) and an issue
goes to the element which starts closest before it.

The comp validator instantiates every submodel of the main model, along the
whole tree of the model definitions and the external model definitions it
names, which grows with the product of the submodels of every level. A
document whose main model expands to more than `MAX_SUBMODEL_INSTANCES`
instances (`submodel_instances`) is not validated, only the issues of reading
it are reported.

Importing this module replaces the resolvers of the process-wide resolver
registry of libsbml by `ReportResolver`, for every user of libsbml in the
process (also a program which calls `sbml4humans.show`): outside of a
validation it resolves files like the file resolver of libsbml, and a resolver
of urls or another one which was registered before is gone.
"""

import bisect
import logging
from collections.abc import Mapping
from contextvars import ContextVar
from dataclasses import dataclass

import libsbml

from sbml4humans.external import normalize_location, resolve_source
from sbml4humans.model import Model, Report, Severity, ValidationIssue


logger = logging.getLogger(__name__)

# the submodel instances of a main model which are validated; 1,000 instances
# (three levels of ten submodels) are checked within a fifth of a second, ten
# times as many take seconds and a hundred times as many more than a minute
MAX_SUBMODEL_INSTANCES = 1000

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


class ReportDocuments:
    """The documents of a report, which alone the comp validator may resolve.

    libsbml asks the resolver for the `source` of an external model definition
    together with the location uri of the document which names it, its base.
    The base is the location uri of a document of the report, as libsbml read
    it or as the resolver answered it, so a source is resolved against the
    location of that document in the report (`resolve_source`), the way the
    report resolves it, also along a chain of external model definitions.
    """

    def __init__(self, documents: Mapping[str, libsbml.SBMLDocument]) -> None:
        """The documents of a report keyed by their location in it."""
        self._documents: dict[str, libsbml.SBMLDocument] = {}
        by_uri: dict[str, list[str]] = {}
        for location, doc in documents.items():
            normalized = normalize_location(location)
            if normalized is None:
                continue
            self._documents[normalized] = doc
            uri = doc.getLocationURI()
            if uri:
                by_uri.setdefault(uri, []).append(normalized)
        # a uri which two documents share names neither of them
        self._locations = {
            uri: locations[0]
            for uri, locations in by_uri.items()
            if len(locations) == 1
        }

    def location_of(self, uri: str) -> str | None:
        """The location in the report of the document with a location uri."""
        return self._locations.get(uri)

    def find(self, source: str, base: str | None) -> libsbml.SBMLDocument | None:
        """The document a source names, seen from the document at `base`."""
        if base is None:
            return None
        target = resolve_source(base, source)
        return self._documents.get(target) if target is not None else None


@dataclass(frozen=True)
class _Validation:
    """The validation of a document of a report, while it runs."""

    documents: ReportDocuments
    location: str
    uri: str

    def find(self, source: str, base_uri: str) -> libsbml.SBMLDocument | None:
        """The document of the report a source names, seen from `base_uri`.

        The validated document has the base of its own location uri, which is
        empty for a document read from a string.
        """
        base = self.location if base_uri == self.uri else None
        if base is None:
            base = self.documents.location_of(base_uri)
        return self.documents.find(source, base)


# the validation which runs in this context, None outside of one
_VALIDATION: ContextVar[_Validation | None] = ContextVar("validation", default=None)


class ReportResolver(libsbml.SBMLResolver):
    """The resolver of libsbml, confined to the report while it validates.

    The comp validator reads the document an external model definition names
    through the resolver registry of libsbml, which would read any path and,
    with a resolver for it, any url. While a document is validated this one
    answers only the documents of the report and never reads a file or a url;
    at every other time it is the file resolver of libsbml.
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
        validation = _VALIDATION.get()
        if validation is None:
            return self._files.resolve(uri, baseUri)
        doc = validation.find(uri, baseUri)
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
        """The uri of a document: one of the report while validating.

        The uri of a document of the report is its location uri, which libsbml
        gives as the base of the sources of that document.
        """
        validation = _VALIDATION.get()
        if validation is None:
            return self._files.resolveUri(uri, baseUri)
        doc = validation.find(uri, baseUri)
        if doc is None:
            return None
        resolved = libsbml.SBMLUri(doc.getLocationURI() or uri)
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

_NO_DOCUMENTS = ReportDocuments({})


def validate(
    doc: libsbml.SBMLDocument,
    positions: ElementPositions,
    documents: ReportDocuments = _NO_DOCUMENTS,
    location: str = "",
) -> list[ValidationIssue]:
    """Check the consistency of a document and return all of its issues.

    Args:
        doc: the document to check.
        positions: where the elements of the report of the document start.
        documents: the documents of the report, the only ones the comp
            validator can read.
        location: the location of the document in the report, against which
            its sources are resolved.

    Returns:
        The issues of the document, in the order of libsbml.
    """
    token = _VALIDATION.set(_Validation(documents, location, doc.getLocationURI()))
    try:
        doc.checkConsistency()
    finally:
        _VALIDATION.reset(token)
    return issues_of(doc, positions)


def submodel_instances(reports: Mapping[str, Report], location: str) -> int:
    """The comp submodel instances the main model of an entry expands to.

    The model a submodel instantiates is a model definition of its document or
    the model an external model definition of it names, as `ExternalModels`
    resolved it to another entry of the report; an instance counts with the
    instances of its model. A model which instantiates itself, directly or
    along a chain, counts its instances up to the cycle, which libsbml reports
    as an error of its own.

    Args:
        reports: the report of every entry by its location.
        location: the location of the entry.

    Returns:
        The number of submodel instances, 0 for a document without a main model.
    """
    counted: dict[tuple[str, str], int] = {}

    def target(entry: str, model_ref: str) -> tuple[str, Model] | None:
        """The entry and the model a submodel of a model of `entry` names."""
        report = reports[entry]
        for model in report.models:
            if model.id == model_ref:
                return entry, model
        for emd in report.external_model_definitions:
            other = emd.resolution.entry
            if emd.id != model_ref or other is None or other not in reports:
                continue
            for model in reports[other].models:
                if model.pk == emd.resolution.model:
                    return other, model
        return None

    def instances(entry: str, model: Model, chain: frozenset[tuple[str, str]]) -> int:
        """The instances of the submodels of a model, along a chain of models."""
        key = (entry, model.pk)
        if key in counted:
            return counted[key]
        total = 0
        for submodel in model.list_of_submodels:
            total += 1
            found = target(entry, submodel.model_ref)
            if found is not None and (found[0], found[1].pk) not in chain | {key}:
                total += instances(*found, chain | {key})
        counted[key] = total
        return total

    for model in reports[location].models:
        if model.kind == "model":
            return instances(location, model, frozenset())
    return 0
