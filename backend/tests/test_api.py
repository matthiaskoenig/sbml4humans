"""Tests of the http api."""

import io
import json
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import FastAPI, UploadFile
from fastapi.testclient import TestClient

from sbml4humans import __version__, api, limits
from sbml4humans.examples import load_examples, report_for_example
from sbml4humans.model import ReportResponse
from sbml4humans.resources import OMEX_ICGMODEL, REPRESSILATOR_SBML


def _strict_json(content: bytes) -> Any:
    """The JSON of a response body, refusing the tokens JSON does not define.

    Python writes an infinite float as the bare token `Infinity`, which
    `json.loads` accepts and `JSON.parse` of a browser does not.
    """

    def refuse(token: str) -> None:
        raise ValueError(f"the body carries the token {token}, which is no JSON")

    return json.loads(content, parse_constant=refuse)


def _check_error(data: dict[str, Any], info: dict[str, str] | None = None) -> None:
    """Check the error payload of the api."""
    assert set(data) == {"errors", "warnings", "info"}
    # the message alone, the traceback is logged by the server
    assert len(data["errors"]) == 1
    assert "Traceback" not in data["errors"][0]
    assert data["warnings"] == []
    if info is not None:
        assert data["info"] == info


def _check_report(data: dict[str, Any]) -> None:
    """Check report data returned by the api."""
    assert "errors" not in data
    assert set(data) == {"uid", "manifest", "reports"}
    assert set(data["manifest"]) == {"entries"}
    for entry in data["manifest"]["entries"]:
        assert set(entry) == {"location", "format", "master"}
    for entry in data["reports"].values():
        assert set(entry) == {"report", "debug"}
        assert set(entry["report"]) == {
            "document",
            "models",
            "externalModelDefinitions",
            "linkGraph",
        }


def test_openapi(client: TestClient) -> None:
    """The api describes itself."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    info = schema["info"]
    assert info["title"] == "sbml4humans"
    assert info["version"] == __version__
    for path, method in [
        ("/api/examples/{example_id}", "get"),
        ("/api/file", "post"),
        ("/api/url", "get"),
        ("/api/content", "post"),
    ]:
        content = schema["paths"][path][method]["responses"]["200"]["content"]
        assert content["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ReportResponse"
        }


def test_cors(client: TestClient) -> None:
    """Browsers from any origin may call the api."""
    response = client.get("/api/examples", headers={"Origin": "https://example.org"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"


def test_cors_error_response(client: TestClient) -> None:
    """An error payload also carries the CORS headers of the request origin."""
    response = client.get(
        "/api/examples/nope", headers={"Origin": "https://example.org"}
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    _check_error(response.json(), info={})


def test_cors_validation_error_response(client: TestClient) -> None:
    """A validation error payload also carries the CORS headers of the request origin."""
    response = client.get("/api/url", headers={"Origin": "https://example.org"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    _check_error(response.json(), info={})


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


def test_an_infinite_value_reaches_the_frontend(client: TestClient) -> None:
    """The api sends an infinite value as the constant the report reads.

    The decision belongs to the whole report: an unbounded flux is the common
    case of a constraint based model, and `null` is what an attribute the file
    does not set at all sends.
    """
    response = client.get("/api/examples/fbc_bounds_v1 (fbc_bounds_v1.xml)")
    assert response.status_code == 200
    report = next(iter(_strict_json(response.content)["reports"].values()))["report"]
    bounds = {b["id"]: b["value"] for b in report["models"][0]["listOfFluxBounds"]}
    assert bounds["v1_ub"] == "Infinity"
    assert bounds["v1_lb"] == 0.0

    response = client.get("/api/examples/fbc_example (fbc_example.xml)")
    parameters = {
        p["id"]: p["value"]
        for p in next(iter(_strict_json(response.content)["reports"].values()))[
            "report"
        ]["models"][0]["listOfParameters"]
    }
    assert parameters["ub_inf"] == "Infinity"
    assert parameters["lb_inf"] == "-Infinity"


def test_a_report_endpoint_returns_the_response_for_fastapi_to_write() -> None:
    """A report endpoint hands its response to FastAPI, which writes it once.

    The endpoints dumped the response to a dictionary through its JSON, which
    FastAPI validated into the response model again and wrote a second time:
    three passes over a report of 100 MB. FastAPI takes the model as it is
    and writes its JSON in one pass, with the constants of a double which JSON
    has no literal for as the strings of the model configuration.
    """
    upload = UploadFile(file=io.BytesIO(REPRESSILATOR_SBML.read_bytes()))
    response = api.report_from_file(upload)
    assert isinstance(response, ReportResponse)


def _without_request(data: dict[str, Any]) -> dict[str, Any]:
    """The report data without what differs between two requests."""
    data = {**data, "uid": None}
    data["reports"] = {
        location: {**entry, "debug": None}
        for location, entry in data["reports"].items()
    }
    return data


def test_example_is_the_json_fastapi_writes(client: TestClient) -> None:
    """The kept JSON of an example is the JSON FastAPI writes for its report."""
    example = "fbc_bounds_v1 (fbc_bounds_v1.xml)"
    metadata = load_examples()[example]
    app = FastAPI()

    @app.get("/report", response_model=ReportResponse, response_model_by_alias=True)
    def report() -> ReportResponse:
        """The report of the example as a report endpoint returns it."""
        return report_for_example(metadata)

    kept = client.get(f"/api/examples/{example}")
    written = TestClient(app).get("/report")
    assert _without_request(_strict_json(kept.content)) == _without_request(
        _strict_json(written.content)
    )


def test_example_is_built_once(client: TestClient) -> None:
    """The report of an example is built on the first request for it alone."""
    api.example_report_gzip.cache_clear()
    example = "BIOMD0000000012 (BIOMD0000000012_urn.xml)"
    first = client.get(f"/api/examples/{example}").json()
    second = client.get(f"/api/examples/{example}").json()
    assert first == second
    assert api.example_report_gzip.cache_info().hits == 1


def test_example_without_gzip(client: TestClient) -> None:
    """A client which does not accept gzip receives the plain JSON of an example."""
    response = client.get(
        "/api/examples/icg_model", headers={"Accept-Encoding": "identity"}
    )
    assert "content-encoding" not in response.headers
    assert "Accept-Encoding" in response.headers["vary"].split(", ")
    gzipped = client.get("/api/examples/icg_model", headers={"Accept-Encoding": "gzip"})
    assert "Accept-Encoding" in gzipped.headers["vary"].split(", ")
    _check_report(_strict_json(response.content))


@pytest.mark.parametrize(
    ("method", "path", "kwargs"),
    [
        ("get", "/api/examples/icg_model", {}),
        ("get", "/api/examples", {}),
        ("post", "/api/content", {"content": REPRESSILATOR_SBML.read_bytes()}),
    ],
)
def test_gzip(
    client: TestClient, method: str, path: str, kwargs: dict[str, Any]
) -> None:
    """A large response is gzipped for a client which accepts it."""
    response = client.request(
        method, path, headers={"Accept-Encoding": "gzip"}, **kwargs
    )
    assert response.headers["content-encoding"] == "gzip"
    assert response.num_bytes_downloaded < len(response.content)
    assert "errors" not in response.json()


def test_gzip_error_response(client: TestClient) -> None:
    """An error response is gzipped like any other and keeps its CORS headers."""
    response = client.get(
        "/api/examples/" + "x" * 2000,
        headers={"Accept-Encoding": "gzip", "Origin": "https://example.org"},
    )
    assert response.headers["content-encoding"] == "gzip"
    assert response.headers["access-control-allow-origin"] == "*"
    _check_error(response.json())


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
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A failing resolution results in an error payload with the resource."""

    def annotation_info(resource: str) -> dict[str, Any]:
        raise ValueError("unknown namespace")

    monkeypatch.setattr(api, "annotation_info", annotation_info)
    response = client.get("/api/annotation_resource", params={"resource": "x/y"})
    assert response.status_code == 200
    data = response.json()
    _check_error(data, info={"resource": "x/y"})
    assert data["errors"] == ["unknown namespace"]
    # the traceback stays on the server
    assert "Traceback" in caplog.text
    assert "unknown namespace" in caplog.text


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:1/model.xml",
        "http://localhost:1/model.xml",
        "http://169.254.169.254/latest/meta-data/",
        "file:///etc/passwd",
    ],
)
def test_url_of_the_internal_network_is_refused(client: TestClient, url: str) -> None:
    """The server downloads from public addresses alone, nothing of its network."""
    response = client.get("/api/url", params={"url": url})
    assert response.status_code == 200
    data = response.json()
    _check_error(data, info={"url": url})
    assert "not downloaded" in data["errors"][0]


def _chunks(content: bytes) -> Iterator[bytes]:
    """The content in chunks, which is sent without a content length."""
    for k in range(0, len(content), 256):
        yield content[k : k + 256]


@pytest.mark.parametrize("chunked", [False, True])
def test_the_size_of_a_body_is_limited(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, chunked: bool
) -> None:
    """Pasted content and an upload beyond `MAX_CONTENT_SIZE` are refused."""
    monkeypatch.setattr(limits, "MAX_CONTENT_SIZE", 1024)
    content = REPRESSILATOR_SBML.read_bytes()
    assert len(content) > 1024
    response = client.post(
        "/api/content", content=_chunks(content) if chunked else content
    )
    assert response.status_code == 200
    data = response.json()
    _check_error(data, info={})
    assert "limit of 1024 bytes" in data["errors"][0]
    # the response of an error carries the CORS headers like any other
    response = client.post(
        "/api/file",
        files={"source": ("model.xml", content)},
        headers={"Origin": "https://example.org"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    data = response.json()
    _check_error(data, info={})
    assert "limit of 1024 bytes" in data["errors"][0]
    # an upload without content length is refused while it is read
    boundary = "sbml4humans-test"
    body = (
        (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="source"; filename="model.xml"\r\n'
            "Content-Type: application/xml\r\n\r\n"
        ).encode()
        + content
        + f"\r\n--{boundary}--\r\n".encode()
    )
    response = client.post(
        "/api/file",
        content=_chunks(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    assert response.status_code == 200
    data = response.json()
    _check_error(data, info={})
    assert "limit of 1024 bytes" in data["errors"][0]


def test_a_body_within_the_limit_is_reported(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The limit counts the body, a chunked one as well."""
    content = REPRESSILATOR_SBML.read_bytes()
    monkeypatch.setattr(limits, "MAX_CONTENT_SIZE", len(content))
    _check_report(client.post("/api/content", content=_chunks(content)).json())
