"""The downloads of the ODE system of a model, `/api/ode/...`."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from sbml4humans import api
from sbml4humans.resources import EXAMPLES_DIR, OMEX_ICGMODEL, REPRESSILATOR_SBML


EXAMPLE = "BIOMD0000000012"


def _check_download(response: Any, filename: str, contains: str) -> None:
    """The response is a file of the system, an attachment."""
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert (
        response.headers["content-disposition"] == f'attachment; filename="{filename}"'
    )
    assert contains in response.text


def _check_error(response: Any, message: str) -> None:
    """The response is an error of the error contract."""
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"errors", "warnings", "info"}
    assert message in data["errors"][0]


@pytest.mark.parametrize(
    ("fmt", "filename", "contains"),
    [
        ("python", "BIOMD0000000012.py", "def f_dxdt("),
        ("julia", "BIOMD0000000012.jl", "function"),
        ("r", "BIOMD0000000012.R", "function("),
        ("latex", "BIOMD0000000012.tex", r"\begin{document}"),
        ("typst", "BIOMD0000000012.typ", "#set"),
        ("markdown", "BIOMD0000000012.md", "$$"),
    ],
)
def test_ode_of_example(
    client: TestClient, fmt: str, filename: str, contains: str
) -> None:
    """Every format of the system of an example."""
    response = client.get(f"/api/ode/examples/{EXAMPLE}", params={"format": fmt})
    _check_download(response, filename, contains)


def test_ode_of_file(client: TestClient) -> None:
    """An uploaded file."""
    response = client.post(
        "/api/ode/file",
        params={"format": "python"},
        files={"source": ("model.xml", REPRESSILATOR_SBML.read_bytes())},
    )
    _check_download(response, "BIOMD0000000012.py", "def f_dxdt(")


def test_ode_of_content(client: TestClient) -> None:
    """Pasted content."""
    response = client.post(
        "/api/ode/content",
        params={"format": "markdown"},
        content=REPRESSILATOR_SBML.read_bytes(),
    )
    _check_download(response, "BIOMD0000000012.md", "$$")


def test_ode_of_url(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """A model behind a url, downloaded as for its report."""
    urls: list[str] = []

    def download(url: str) -> bytes:
        urls.append(url)
        return REPRESSILATOR_SBML.read_bytes()

    monkeypatch.setattr(api, "download", download)
    url = "https://example.org/model.xml"
    response = client.get("/api/ode/url", params={"url": url, "format": "r"})
    assert urls == [url]
    _check_download(response, "BIOMD0000000012.R", "function(")


def test_ode_of_upload(client: TestClient) -> None:
    """An upload of another tool."""
    upload = client.post(
        "/api/upload", files={"source": ("model.xml", REPRESSILATOR_SBML.read_bytes())}
    ).json()
    response = client.get(f"/api/ode/upload/{upload['id']}", params={"format": "julia"})
    _check_download(response, "BIOMD0000000012.jl", "function")


def test_ode_of_archive_entry(client: TestClient) -> None:
    """The entry of an archive is chosen by its location."""
    response = client.post(
        "/api/ode/file",
        params={"format": "python", "location": "./models/icg_body_flat.xml"},
        files={"source": ("model.omex", OMEX_ICGMODEL.read_bytes())},
    )
    assert response.status_code == 200
    assert response.headers["content-disposition"].endswith('.py"')


def test_ode_of_unknown_location(client: TestClient) -> None:
    """A location which is no SBML entry is an error."""
    response = client.post(
        "/api/ode/file",
        params={"format": "python", "location": "./missing.xml"},
        files={"source": ("model.omex", OMEX_ICGMODEL.read_bytes())},
    )
    _check_error(response, "./missing.xml")


def test_ode_of_unknown_format(client: TestClient) -> None:
    """A format sbmlode does not write is an error."""
    response = client.get(f"/api/ode/examples/{EXAMPLE}", params={"format": "pdf"})
    _check_error(response, "pdf")


def test_ode_of_unsupported_model(client: TestClient) -> None:
    """Code of a model with an algebraic rule is refused by sbmlode, an error."""
    response = client.post(
        "/api/ode/content",
        params={"format": "python"},
        content=(EXAMPLES_DIR / "algebraic_rule.xml").read_bytes(),
    )
    _check_error(response, "algebraic rule")


def test_ode_routes_are_documented(client: TestClient) -> None:
    """The routes of the downloads are part of the schema of the api."""
    paths = client.get("/openapi.json").json()["paths"]
    for path in [
        "/api/ode/examples/{example_id}",
        "/api/ode/file",
        "/api/ode/url",
        "/api/ode/content",
        "/api/ode/upload/{upload_id}",
    ]:
        assert path in paths


def test_ode_filename_is_readable_across_origins(client: TestClient) -> None:
    """A page of another origin reads the name of the file, CORS exposes it."""
    response = client.get(
        f"/api/ode/examples/{EXAMPLE}",
        params={"format": "python"},
        headers={"Origin": "https://example.org"},
    )
    assert "content-disposition" in response.headers[
        "access-control-expose-headers"
    ].lower()
