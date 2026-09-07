"""Resolution of annotation resources.

Used by the frontend to display information (label, description, cross
references) for the identifiers in the annotations of a model.
"""

from typing import Any

from pymetadata.core.annotation import RDFAnnotation, RDFAnnotationData
from pymetadata.core.miriam import BQB


def annotation_info(resource: str) -> dict[str, Any]:
    """Resolve the information of an annotation resource.

    Args:
        resource: identifier of the resource (url or MIRIAM urn).
    """
    annotation = RDFAnnotation(qualifier=BQB.IS, resource=resource)
    data = RDFAnnotationData(annotation=annotation)
    return data.to_dict()
