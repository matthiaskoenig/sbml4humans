"""Tests of the http api."""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from sbmlutils.resources import OMEX_ICGMODEL, REPRESSILATOR_SBML

from sbml4humans import __version__, api


def _check_error(data: dict[str, Any], info: dict[str, str] | None = None) -> None:
    """Check the error payload of the api."""
    assert set(data) == {"errors", "warnings", "info"}
    assert len(data["errors"]) == 2
    assert data["warnings"] == []
    if info is not None:
        assert data["info"] == info


def _check_report(data: dict[str, Any]) -> None:
    """Check report data returned by the api."""
    assert "errors" not in data
    assert set(data) == {"uid", "manifest", "reports"}
    assert data["reports"]


def test_openapi(client: TestClient) -> None:
    """The api describes itself."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    info = response.json()["info"]
    assert info["title"] == "sbml4humans"
    assert info["version"] == __version__


def test_cors(client: TestClient) -> None:
    """Browsers from any origin may call the api."""
    response = client.get("/api/examples", headers={"Origin": "https://example.org"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"


def test_examples(client: TestClient) -> None:
    """The example list contains the metadata without server paths."""
    response = client.get("/api/examples")
    assert response.status_code == 200
    examples = response.json()["examples"]
    assert len(examples) >= 40
    example = next(e for e in examples if e["id"] == "icg_model")
    assert set(example) == {"id", "name", "description", "packages"}
    assert example["packages"] == ["OMEX"]


def test_example(client: TestClient) -> None:
    """The report of an example is created."""
    response = client.get("/api/examples/icg_model")
    assert response.status_code == 200
    data = response.json()
    _check_report(data)
    assert len(data["reports"]) == 3


def test_example_with_special_characters(client: TestClient) -> None:
    """Example ids with spaces and parentheses are resolved."""
    response = client.get("/api/examples/BIOMD0000000012 (BIOMD0000000012_urn.xml)")
    assert response.status_code == 200
    _check_report(response.json())


def test_example_missing(client: TestClient) -> None:
    """An unknown example results in an error payload."""
    response = client.get("/api/examples/does_not_exist")
    assert response.status_code == 200
    data = response.json()
    _check_error(data, info={})
    assert "does_not_exist" in data["errors"][0]


def test_file_sbml(client: TestClient) -> None:
    """An uploaded SBML file is reported."""
    with REPRESSILATOR_SBML.open("rb") as f:
        response = client.post("/api/file", files={"source": ("model.xml", f)})
    assert response.status_code == 200
    _check_report(response.json())


def test_file_omex(client: TestClient) -> None:
    """An uploaded (binary) archive is reported."""
    with OMEX_ICGMODEL.open("rb") as f:
        response = client.post("/api/file", files={"source": ("model.omex", f)})
    assert response.status_code == 200
    data = response.json()
    _check_report(data)
    assert len(data["reports"]) == 3


def test_file_invalid(client: TestClient) -> None:
    """Invalid content results in an error payload."""
    response = client.post("/api/file", files={"source": ("model.xml", b"garbage")})
    assert response.status_code == 200
    _check_error(response.json(), info={})


def test_file_missing(client: TestClient) -> None:
    """A request without file results in an error payload."""
    response = client.post("/api/file", files={"other": ("model.xml", b"<sbml/>")})
    assert response.status_code == 200
    data = response.json()
    _check_error(data, info={})
    assert "source" in data["errors"][0]


def test_content(client: TestClient) -> None:
    """Pasted SBML content is reported."""
    response = client.post("/api/content", content=REPRESSILATOR_SBML.read_bytes())
    assert response.status_code == 200
    _check_report(response.json())


def test_content_invalid(client: TestClient) -> None:
    """Invalid content results in an error payload."""
    response = client.post("/api/content", content=b"garbage")
    assert response.status_code == 200
    _check_error(response.json(), info={})


def test_url(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """A model behind a url is downloaded and reported."""
    urls: list[str] = []

    def download(url: str) -> bytes:
        urls.append(url)
        return bytes(OMEX_ICGMODEL.read_bytes())

    monkeypatch.setattr(api, "download", download)
    response = client.get("/api/url", params={"url": "https://example.org/model.omex"})
    assert response.status_code == 200
    assert urls == ["https://example.org/model.omex"]
    _check_report(response.json())


def test_url_failing(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """A failing download results in an error payload with the url."""

    def download(url: str) -> bytes:
        raise ConnectionError(f"could not download {url}")

    monkeypatch.setattr(api, "download", download)
    response = client.get("/api/url", params={"url": "https://example.org/missing"})
    assert response.status_code == 200
    data = response.json()
    _check_error(data, info={"url": "https://example.org/missing"})
    assert "could not download" in data["errors"][0]


def test_url_missing_parameter(client: TestClient) -> None:
    """The url parameter is required."""
    response = client.get("/api/url")
    assert response.status_code == 200
    _check_error(response.json(), info={})


def test_annotation_resource(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Annotation resources are resolved."""

    def annotation_info(resource: str) -> dict[str, Any]:
        return {"resource": resource, "label": "glucose"}

    monkeypatch.setattr(api, "annotation_info", annotation_info)
    response = client.get(
        "/api/annotation_resource", params={"resource": "chebi/CHEBI:17234"}
    )
    assert response.status_code == 200
    assert response.json() == {"resource": "chebi/CHEBI:17234", "label": "glucose"}


def test_annotation_resource_failing(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failing resolution results in an error payload with the resource."""

    def annotation_info(resource: str) -> dict[str, Any]:
        raise ValueError("unknown namespace")

    monkeypatch.setattr(api, "annotation_info", annotation_info)
    response = client.get("/api/annotation_resource", params={"resource": "x/y"})
    assert response.status_code == 200
    data = response.json()
    _check_error(data, info={"resource": "x/y"})
    assert data["errors"][0] == "unknown namespace"
    assert "Traceback" in data["errors"][1]
