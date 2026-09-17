"""Tests of the resolution of annotation resources."""

from typing import Any

import pytest
from pymetadata.core.annotation import RDFAnnotationData

from sbml4humans.annotations import annotation_info


def _ols(label: Any, description: Any) -> Any:
    """A replacement of the OLS query which fills in label and description."""

    def query_ols(self: RDFAnnotationData) -> dict[str, Any]:
        self.label = label
        self.description = description
        return {}

    return query_ols


def test_resolved_information(monkeypatch: pytest.MonkeyPatch) -> None:
    """Label and description of a resolved resource are reported as text."""
    monkeypatch.setattr(
        RDFAnnotationData, "query_ols", _ols("glucose", "An aldohexose.")
    )
    info = annotation_info("chebi/CHEBI:17234")
    assert info["term"] == "CHEBI:17234"
    assert info["label"] == "glucose"
    assert info["description"] == "An aldohexose."


def test_empty_description(monkeypatch: pytest.MonkeyPatch) -> None:
    """A term without a definition has no description.

    The Ontology Lookup Service reports the missing definition of CHEBI:31696
    (indocyanine green) as an empty list, which the report showed verbatim.
    """
    monkeypatch.setattr(RDFAnnotationData, "query_ols", _ols("indocyanine green", []))
    info = annotation_info("chebi/CHEBI:31696")
    assert info["label"] == "indocyanine green"
    assert info["description"] is None


def test_blank_label(monkeypatch: pytest.MonkeyPatch) -> None:
    """A label of whitespace only is no label."""
    monkeypatch.setattr(RDFAnnotationData, "query_ols", _ols("  ", "  "))
    info = annotation_info("chebi/CHEBI:17234")
    assert info["label"] is None
    assert info["description"] is None


def test_messages_are_text(monkeypatch: pytest.MonkeyPatch) -> None:
    """Errors and warnings are reported as text.

    A failing OLS request collects the request error itself, which is not
    part of the JSON of the response.
    """

    def query_ols(self: RDFAnnotationData) -> dict[str, Any]:
        self.errors.append(ValueError("404 Client Error"))
        return {}

    monkeypatch.setattr(RDFAnnotationData, "query_ols", query_ols)
    info = annotation_info("chebi/CHEBI:17234")
    assert info["errors"] == ["404 Client Error"]
    assert info["warnings"] == []
