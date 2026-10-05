"""Resolution of annotation resources.

Used by the frontend to display information (label, description, cross
references) for the identifiers in the annotations of a model.
"""

import os
from pathlib import Path
from typing import Any

import pymetadata
from pymetadata.core.annotation import RDFAnnotation, RDFAnnotationData
from pymetadata.core.miriam import BQB


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

# fields the report shows as text; the Ontology Lookup Service reports a missing
# definition as an empty list, which ends up in the description of the term
TEXT_FIELDS = (
    "resource_normalized",
    "collection",
    "term",
    "label",
    "description",
    "url",
)

# fields the report shows as messages; a failing request is collected as the error itself
MESSAGE_FIELDS = ("errors", "warnings")


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


def annotation_info(resource: str) -> dict[str, Any]:
    """Resolve the information of an annotation resource.

    Args:
        resource: identifier of the resource (url or MIRIAM urn).
    """
    annotation = RDFAnnotation(qualifier=BQB.IS, resource=resource)
    data = RDFAnnotationData(annotation=annotation).to_dict()
    for field in TEXT_FIELDS:
        data[field] = _text(data.get(field))
    for field in MESSAGE_FIELDS:
        data[field] = _messages(data.get(field))
    return data
