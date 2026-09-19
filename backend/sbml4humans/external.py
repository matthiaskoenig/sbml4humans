"""The models which external model definitions name.

An `ExternalModelDefinition` of comp names a model of another document by the
`source` of that document and the `modelRef` of the model in it (comp §3.3.2).
The report never fetches a document. It resolves a source against the documents
it was given, which are the SBML entries of one COMBINE archive: `ExternalModels`
holds the reports of all entries by their manifest location and answers which
model of which entry a definition names, and why where it names none.
"""

import logging
import posixpath
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from urllib.parse import unquote

from sbml4humans.model import (
    ExternalModelDefinition,
    ExternalModelResolution,
    Model,
    Report,
    ResolutionStatus,
)


logger = logging.getLogger(__name__)

# a uri with a scheme (RFC 3986 §3.1), which names a document outside of the archive
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def normalize_location(location: str) -> str | None:
    """The path of a location inside the archive, None where it has none.

    A manifest writes the location of an entry relative to the root of the
    archive, `./models/a.xml`, and a leading slash names that root as well. A
    location which names the root itself or leaves it is no entry.
    """
    path = posixpath.normpath(location.lstrip("/"))
    if path == "." or path == ".." or path.startswith("../"):
        return None
    return path


def resolve_source(location: str, source: str) -> str | None:
    """The normalized location a source names, seen from the entry at `location`.

    A relative source is resolved against the directory of the entry which
    names it, the way a relative uri is resolved against its document. A source
    with a scheme names a document outside of the archive and a source which
    leaves the root of the archive names none of its entries, both are None.
    """
    if not source or SCHEME.match(source):
        return None
    path = unquote(source)
    if path.startswith("/"):
        return normalize_location(path)
    base = normalize_location(location)
    if base is None:
        return None
    return normalize_location(posixpath.join(posixpath.dirname(base), path))


@dataclass(frozen=True)
class ExternalModel:
    """A model and the manifest location of the entry whose report holds it."""

    location: str
    model: Model


class ExternalModels:
    """Resolves the external model definitions of the reports of one archive."""

    def __init__(
        self,
        reports: Mapping[str, Report],
        checksums: Mapping[str, str] | None = None,
        locations: Iterable[str] = (),
    ) -> None:
        """Index the reports.

        Args:
            reports: the report of every SBML entry by its manifest location.
            checksums: the md5 of every entry as hex digits, by its location.
            locations: the locations of the entries without a report.
        """
        self.reports = reports
        self.checksums = checksums or {}
        # the manifest location of every entry by its normalized location
        self.entries: dict[str, str] = {}
        for location in (*locations, *reports):
            normalized = normalize_location(location)
            if normalized is not None:
                self.entries[normalized] = location
        self._models: dict[tuple[str, str], ExternalModel] = {}
        self._resolutions: dict[tuple[str, str], ExternalModelResolution] = {}

    def resolve_all(self) -> None:
        """Write the resolution of every external model definition of the reports."""
        for location, report in self.reports.items():
            for emd in report.external_model_definitions:
                emd.resolution = self.resolve(location, emd)

    def model(
        self, location: str, emd: ExternalModelDefinition
    ) -> ExternalModel | None:
        """The model a definition of the entry at `location` names, if it names one."""
        self.resolve(location, emd)
        return self._models.get((location, emd.pk))

    def resolve(
        self, location: str, emd: ExternalModelDefinition
    ) -> ExternalModelResolution:
        """How far the definition of the entry at `location` can be followed.

        A definition which names no model is logged once, however many
        references of the model end at it.
        """
        key = (location, emd.pk)
        if key in self._resolutions:
            return self._resolutions[key]
        resolution = self._resolutions[key] = self._resolve(location, emd, frozenset())
        if resolution.status != ResolutionStatus.RESOLVED:
            logger.warning(
                "external model definition '%s' of '%s' is not resolved: source "
                "'%s', modelRef '%s', %s",
                emd.pk,
                location,
                emd.source,
                emd.model_ref,
                resolution.status.value,
            )
        return resolution

    def _resolve(
        self,
        location: str,
        emd: ExternalModelDefinition,
        visited: frozenset[tuple[str, str]],
    ) -> ExternalModelResolution:
        """Resolve one definition, `visited` being the definitions of the chain."""
        key = (location, emd.pk)
        if key in visited:
            return ExternalModelResolution(status=ResolutionStatus.CIRCULAR)
        if SCHEME.match(emd.source):
            return ExternalModelResolution(status=ResolutionStatus.REMOTE_SOURCE)
        normalized = resolve_source(location, emd.source)
        entry = self.entries.get(normalized) if normalized is not None else None
        if entry is None:
            return ExternalModelResolution(status=ResolutionStatus.NOT_FOUND)

        md5_matches: bool | None = None
        if emd.md5 is not None and entry in self.checksums:
            md5_matches = emd.md5.strip().lower() == self.checksums[entry].lower()

        report = self.reports.get(entry)
        if report is None:
            return ExternalModelResolution(
                status=ResolutionStatus.NOT_SBML, entry=entry, md5_matches=md5_matches
            )

        model = self._named_model(report, emd.model_ref)
        if model is not None:
            self._models[key] = ExternalModel(location=entry, model=model)
            return ExternalModelResolution(
                status=ResolutionStatus.RESOLVED,
                entry=entry,
                model=model.pk,
                md5_matches=md5_matches,
            )

        # the modelRef may name an external model definition of the other
        # document, which names a model of a third one (comp §3.3.2)
        for hop in report.external_model_definitions:
            if emd.model_ref is not None and hop.id == emd.model_ref:
                end = self._resolve(entry, hop, visited | {key})
                target = self._models.get((entry, hop.pk))
                if target is not None:
                    self._models[key] = target
                return ExternalModelResolution(
                    status=end.status,
                    entry=end.entry or entry,
                    model=end.model,
                    md5_matches=md5_matches,
                )

        return ExternalModelResolution(
            status=ResolutionStatus.MODEL_NOT_FOUND,
            entry=entry,
            md5_matches=md5_matches,
        )

    @staticmethod
    def _named_model(report: Report, model_ref: str | None) -> Model | None:
        """The model of a report with the id, the main model where none is named."""
        for model in report.models:
            if model_ref is None and model.kind == "model":
                return model
            if model_ref is not None and model.id == model_ref:
                return model
        return None
