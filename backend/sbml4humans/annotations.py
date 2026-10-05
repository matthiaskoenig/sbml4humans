"""Resolution of annotation resources.

Used by the frontend to display information (label, description, cross
references) for the identifiers in the annotations of a model.
"""

import os
from pathlib import Path
from typing import Any

import pymetadata
from pydantic import Field
from pymetadata.core.annotation import RDFAnnotation, RDFAnnotationData
from pymetadata.core.miriam import BQB
from pymetadata.webservices.chebi import ChebiQuery
from pymetadata.webservices.uniprot import UniprotQuery

from sbml4humans.model import ReportModel


CACHE_VARIABLE = "SBML4HUMANS_CACHE"


def configure_cache() -> None:
    """Point the disk cache of pymetadata to `SBML4HUMANS_CACHE` where it is set.

    The deployment keeps the answers of OLS, ChEBI, UniProt and the registry on
    a volume, so that they survive a restart of the container (a deploy removes
    the volume and starts empty); elsewhere pymetadata keeps its default,
    `~/.cache/pymetadata`.
    """
    path = os.environ.get(CACHE_VARIABLE)
    if path:
        pymetadata.CACHE_PATH = Path(path)


configure_cache()


def _text(value: Any) -> str | None:
    """Convert a field to text; a field which carries no text has no value."""
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _messages(value: Any) -> list[str]:
    """Convert a field to a list of messages."""
    if not isinstance(value, list):
        return []
    return [str(message) for message in value]


class Collection(ReportModel):
    """The collection of the identifiers.org registry a resource belongs to."""

    prefix: str
    name: str | None = None
    homepage: str | None = None


class Provider(ReportModel):
    """A provider which resolves the identifier of a resource."""

    name: str
    url: str
    official: bool


class CrossReference(ReportModel):
    """A cross reference of an ontology term, a link where OLS gives an url."""

    label: str
    url: str | None = None


class OntologyTerm(ReportModel):
    """The term of a resource in the Ontology Lookup Service."""

    ontology: str | None = None
    label: str | None = None
    iri: str | None = None
    ols_url: str | None = None
    description: str | None = None
    synonyms: list[str] = Field(default_factory=list)
    xrefs: list[CrossReference] = Field(default_factory=list)


class ChebiInfo(ReportModel):
    """The chemical information of a ChEBI compound."""

    formula: str | None = None
    charge: int | None = None
    mass: str | None = None
    structure: bool = False


class UniprotInfo(ReportModel):
    """The information of a UniProt protein."""

    entry: str | None = None
    name: str | None = None
    organism: str | None = None
    genes: list[str] = Field(default_factory=list)
    length: int | None = None
    function: str | None = None


class AnnotationResource(ReportModel):
    """Everything the report shows of one resource of an annotation."""

    resource: str
    collection: Collection | None = None
    identifier: str | None = None
    url: str | None = None
    pattern_match: bool | None = None
    providers: list[Provider] = Field(default_factory=list)
    ontology: OntologyTerm | None = None
    chebi: ChebiInfo | None = None
    uniprot: UniprotInfo | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


def _synonyms(values: Any) -> list[str]:
    """The names of the synonyms of OLS, each once, in order."""
    names: list[str] = []
    for value in values if isinstance(values, list) else []:
        name = _text(value.get("name") if isinstance(value, dict) else value)
        if name and name not in names:
            names.append(name)
    return names


def _xrefs(values: Any) -> list[CrossReference]:
    """The cross references of OLS, labelled `database:id`."""
    xrefs: list[CrossReference] = []
    for value in values if isinstance(values, list) else []:
        if not isinstance(value, dict):
            continue
        identifier = _text(value.get("id"))
        if not identifier:
            continue
        database = _text(value.get("database"))
        label = f"{database}:{identifier}" if database else identifier
        xrefs.append(CrossReference(label=label, url=_text(value.get("url"))))
    return xrefs


def _chebi(term: str, warnings: list[str]) -> ChebiInfo | None:
    """The chemical information of a ChEBI compound, a warning if ChEBI does not know it."""
    info = ChebiQuery.query(term)
    if not info:
        warnings.append(f"Term '{term}' is not on ChEBI.")
        return None
    charge = info.get("charge")
    mass = info.get("mass")
    return ChebiInfo(
        formula=_text(info.get("formula")),
        charge=charge if isinstance(charge, int) else None,
        mass=str(mass) if mass is not None else None,
        structure=bool(info.get("inchikey")),
    )


def _uniprot(accession: str, warnings: list[str]) -> UniprotInfo | None:
    """The information of a UniProt protein, a warning if UniProt does not know it."""
    info = UniprotQuery.query(accession)
    if not info:
        warnings.append(f"Term '{accession}' is not on UniProt.")
        return None
    length = info.get("length")
    return UniprotInfo(
        entry=_text(info.get("entry")),
        name=_text(info.get("name")),
        organism=_text(info.get("organism")),
        genes=[gene for gene in info.get("genes") or [] if isinstance(gene, str)],
        length=length if isinstance(length, int) else None,
        function=_text(info.get("function")),
    )


def resolve_resource(resource: str) -> AnnotationResource:
    """Resolve everything the report shows of an annotation resource.

    Args:
        resource: identifier of the resource (url or MIRIAM urn).

    Returns:
        The typed information of the resource.

    Raises:
        ValueError: if the resource cannot be parsed or its collection is unknown.
    """
    data = RDFAnnotationData(
        annotation=RDFAnnotation(qualifier=BQB.IS, resource=resource)
    )
    warnings = _messages(data.warnings)
    term = _text(data.term)
    label = _text(data.label)
    iri = _text(data.iri)
    ontology = None
    if label or iri:
        ontology = OntologyTerm(
            ontology=_text(data.ontology),
            label=label,
            iri=iri,
            ols_url=_text(data.ols_url),
            description=_text(data.description),
            synonyms=_synonyms(data.synonyms),
            xrefs=_xrefs(data.xrefs),
        )
    collection = _text(data.collection)
    return AnnotationResource(
        resource=resource,
        collection=Collection(
            prefix=collection,
            name=_text(data.collection_name),
            homepage=_text(data.collection_homepage),
        )
        if collection
        else None,
        identifier=term,
        url=_text(data.url),
        pattern_match=data.pattern_match,
        providers=[
            Provider(name=p.name, url=p.url, official=p.official)
            for p in data.providers
        ],
        ontology=ontology,
        chebi=_chebi(term, warnings) if collection == "chebi" and term else None,
        uniprot=_uniprot(term, warnings) if collection == "uniprot" and term else None,
        warnings=warnings,
        errors=_messages(data.errors),
    )


def annotation_info(resource: str) -> dict[str, Any]:
    """Resolve the information of an annotation resource as JSON.

    Args:
        resource: identifier of the resource (url or MIRIAM urn).

    Returns:
        The camelCase JSON form of `resolve_resource`.
    """
    return resolve_resource(resource).model_dump(by_alias=True)
