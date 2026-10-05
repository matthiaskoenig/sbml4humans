"""Tests of the http api."""

import asyncio
import contextlib
import io
import json
import threading
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI, UploadFile
from fastapi.testclient import TestClient

from sbml4humans import __version__, annotations, api, limits
from sbml4humans.annotations import AnnotationResource, OntologyTerm
from sbml4humans.examples import load_examples, report_for_example
from sbml4humans.model import ReportResponse
from sbml4humans.resources import EXAMPLES_DIR, OMEX_ICGMODEL, REPRESSILATOR_SBML
from sbml4humans.uploads import UploadStore, upload_store


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


def _check_validation(data: dict[str, Any], entries: int = 1) -> None:
    """Check validation data returned by the api."""
    assert "errors" not in data
    assert set(data) == {"entries", "skipped"}
    assert data["skipped"] is None
    assert len(data["entries"]) == entries
    for entry in data["entries"].values():
        assert set(entry) == {"issues", "skipped"}
        for issue in entry["issues"]:
            assert set(issue) == {
                "rule",
                "severity",
                "category",
                "shortMessage",
                "message",
                "line",
                "column",
                "pk",
            }


def _rules(data: dict[str, Any], location: str = "./model.xml") -> set[int]:
    """The rules of the issues of an entry of validation data."""
    return {issue["rule"] for issue in data["entries"][location]["issues"]}


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
        ("/api/upload/{upload_id}", "get"),
    ]:
        content = schema["paths"][path][method]["responses"]["200"]["content"]
        assert content["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ReportResponse"
        }
    for path, method in [
        ("/api/validation/examples/{example_id}", "get"),
        ("/api/validation/file", "post"),
        ("/api/validation/url", "get"),
        ("/api/validation/content", "post"),
        ("/api/validation/upload/{upload_id}", "get"),
    ]:
        content = schema["paths"][path][method]["responses"]["200"]["content"]
        assert content["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ValidationResponse"
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


def test_annotation_resource_is_typed(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The resource is answered in camelCase and may be cached by the browser for a day."""
    value = AnnotationResource(
        resource="GO:0006096",
        identifier="GO:0006096",
        pattern_match=True,
        ontology=OntologyTerm(label="glycolytic process", ols_url="https://ols/x"),
    )
    monkeypatch.setattr(annotations.resource_cache(), "get", lambda resource: value)
    response = client.get("/api/annotation_resource", params={"resource": "GO:0006096"})
    assert response.status_code == 200
    body = response.json()
    assert body["patternMatch"] is True
    assert body["ontology"]["olsUrl"] == "https://ols/x"
    assert response.headers["cache-control"] == "public, max-age=86400"


def test_annotation_resource_with_errors_is_not_cached(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A resource whose web service failed must not stay in the browser."""
    value = AnnotationResource(resource="GO:1", errors=["OLS down"])
    monkeypatch.setattr(annotations.resource_cache(), "get", lambda resource: value)
    response = client.get("/api/annotation_resource", params={"resource": "GO:1"})
    assert response.headers["cache-control"] == "no-store"


def test_annotation_resource_with_warnings_is_cached_ten_minutes(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A resource the web services do not know stays in the browser ten minutes."""
    value = AnnotationResource(
        resource="CHEBI:999999999", warnings=["Term 'CHEBI:999999999' is not on ChEBI."]
    )
    monkeypatch.setattr(annotations.resource_cache(), "get", lambda resource: value)
    response = client.get(
        "/api/annotation_resource", params={"resource": "CHEBI:999999999"}
    )
    assert response.headers["cache-control"] == "public, max-age=600"


def test_annotation_resource_too_long(client: TestClient) -> None:
    """A resource longer than 2,000 characters is refused by the error contract."""
    response = client.get("/api/annotation_resource", params={"resource": "x" * 2001})
    assert response.status_code == 200
    assert "2000" in response.json()["errors"][0]


def test_annotation_resource_unknown_collection(client: TestClient) -> None:
    """An unknown collection is answered by the error contract."""
    response = client.get(
        "/api/annotation_resource",
        params={"resource": "https://identifiers.org/notacollection:1"},
    )
    assert response.status_code == 200
    assert response.json()["errors"]


def test_annotation_structure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The structure is an svg which cannot run a script."""
    monkeypatch.setattr(
        annotations.ChebiQuery, "structure", staticmethod(lambda chebi: b"<svg/>")
    )
    response = client.get("/api/annotation_structure/CHEBI:15377")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    assert response.headers["content-security-policy"].startswith("sandbox")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.content == b"<svg/>"


@pytest.mark.parametrize(
    "chebi", ["CHEBI:abc", "15377", "CHEBI:1%2F..", "CHEBI:1234567890", "CHEBI:1%0A"]
)
def test_annotation_structure_invalid(client: TestClient, chebi: str) -> None:
    """An id which is not `CHEBI:<number>` has no structure."""
    response = client.get(f"/api/annotation_structure/{chebi}")
    assert response.status_code == 404
    if "%2F" not in chebi:  # a slash is no route at all, the router answers
        assert response.headers["cache-control"] == "no-store"


def test_annotation_structure_missing(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A compound without a structure answers 404."""
    monkeypatch.setattr(
        annotations.ChebiQuery, "structure", staticmethod(lambda chebi: None)
    )
    response = client.get("/api/annotation_structure/CHEBI:1")
    assert response.status_code == 404
    assert response.headers["cache-control"] == "no-store"


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


@pytest.fixture
def uploads(tmp_path: Path) -> Iterator[UploadStore]:
    """A store of uploads in a temporary directory for the api."""
    store = UploadStore(tmp_path / "uploads")
    api.api.dependency_overrides[upload_store] = lambda: store
    yield store
    api.api.dependency_overrides.pop(upload_store)


def test_upload(client: TestClient, uploads: UploadStore) -> None:
    """An upload is stored, and its report is read by its id."""
    with OMEX_ICGMODEL.open("rb") as f:
        response = client.post("/api/upload", files={"source": ("model.omex", f)})
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"id", "expires"}
    assert uploads.get(data["id"]) == OMEX_ICGMODEL.read_bytes()

    report = client.get(f"/api/upload/{data['id']}")
    assert report.status_code == 200
    _check_report(report.json())
    assert len(report.json()["reports"]) == 3


def test_upload_invalid(client: TestClient, uploads: UploadStore) -> None:
    """An upload which cannot be reported is an error and not stored."""
    response = client.post("/api/upload", files={"source": ("model.xml", b"garbage")})
    _check_error(response.json(), info={})
    assert list(uploads.directory.iterdir()) == []


def test_upload_too_large(
    client: TestClient, uploads: UploadStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An upload above the limit of the content is an error and not stored."""
    monkeypatch.setattr(limits, "MAX_CONTENT_SIZE", 1024)
    response = client.post("/api/upload", files={"source": ("model.xml", b"x" * 2048)})
    data = response.json()
    _check_error(data, info={})
    assert "larger than" in data["errors"][0]
    assert list(uploads.directory.iterdir()) == []


def test_upload_unknown(client: TestClient, uploads: UploadStore) -> None:
    """An unknown id is an error which says how long uploads are kept."""
    response = client.get("/api/upload/unknown_id_of_22_chars")
    data = response.json()
    _check_error(data, info={})
    assert "kept for 24 hours" in data["errors"][0]


def test_cleanup_continues_after_a_failure(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """A failure of one cleanup is logged and the next cleanup runs."""
    monkeypatch.setattr(api, "CLEANUP_INTERVAL", 0.01)
    calls: list[int] = []

    class FailingOnce:
        """A store whose first cleanup fails."""

        def remove_expired(self) -> int:
            """Fail at the first call."""
            calls.append(1)
            if len(calls) == 1:
                raise PermissionError("not allowed")
            return 0

    async def run() -> None:
        task = asyncio.create_task(api.remove_expired_uploads(FailingOnce()))  # ty: ignore[invalid-argument-type]
        await asyncio.sleep(0.2)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    asyncio.run(run())
    assert len(calls) > 1
    assert "not allowed" in caplog.text


# -------------------------------------------------------------------------------------
# validation
# -------------------------------------------------------------------------------------
VALIDATION_EXAMPLE = "validation (validation.xml)"
COMP_DELETION = EXAMPLES_DIR / "comp_deletion.xml"


def test_validation_of_an_example(client: TestClient) -> None:
    """The issues of an example are answered per entry, on the pks of its report."""
    response = client.get(f"/api/validation/examples/{VALIDATION_EXAMPLE}")
    assert response.status_code == 200
    data = response.json()
    _check_validation(data)
    report = client.get(f"/api/examples/{VALIDATION_EXAMPLE}").json()
    assert list(data["entries"]) == list(report["reports"])
    entry = next(iter(data["entries"].values()))
    assert entry["skipped"] is None
    pks = {(issue["rule"], issue["pk"]) for issue in entry["issues"]}
    assert (10601, "validation/Model:validation") in pks
    assert (10712, "validation/Compartment:cell") in pks
    assert (10703, "validation/Parameter:k1") in pks


def test_validation_of_an_example_is_kept(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An example is validated once, its validation does not change."""
    calls: list[str] = []
    validation_for_example = api.validation_for_example

    def spy(example: Any) -> Any:
        calls.append(example.id)
        return validation_for_example(example)

    monkeypatch.setattr(api, "validation_for_example", spy)
    api.example_validations.clear()
    for _ in range(2):
        response = client.get("/api/validation/examples/species (species.xml)")
        _check_validation(response.json())
    assert calls == ["species (species.xml)"]


def test_validation_of_an_example_with_a_timeout_is_not_kept(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A validation which was ended by its limits is tried again next time."""
    from sbml4humans import isolation

    monkeypatch.setattr(isolation, "MAX_CONCURRENT_VALIDATIONS", 1)
    monkeypatch.setattr(isolation, "VALIDATION_TIMEOUT", 0.2)
    api.example_validations.clear()
    # another validation holds the one child
    semaphore = isolation._semaphore()
    with semaphore:
        data = client.get("/api/validation/examples/species (species.xml)").json()
    assert data["skipped"] == "busy"
    monkeypatch.undo()
    data = client.get("/api/validation/examples/species (species.xml)").json()
    assert next(iter(data["entries"].values()))["skipped"] is None


def test_validation_of_an_example_is_trusted(client: TestClient) -> None:
    """An example reads the files next to it, like its report."""
    data = client.get("/api/validation/examples/comp_deletion (comp_deletion.xml)")
    data = data.json()
    _check_validation(data, entries=2)
    assert 1090101 not in _rules(data, "./comp_deletion.xml")


def test_validation_of_a_missing_example(client: TestClient) -> None:
    """An unknown example results in an error payload."""
    response = client.get("/api/validation/examples/does_not_exist")
    data = response.json()
    _check_error(data, info={})
    assert "does_not_exist" in data["errors"][0]


def test_validation_of_a_file(client: TestClient) -> None:
    """An uploaded file is validated untrusted: nothing next to it is read."""
    with COMP_DELETION.open("rb") as f:
        response = client.post(
            "/api/validation/file", files={"source": ("comp_deletion.xml", f)}
        )
    data = response.json()
    _check_validation(data)
    assert 1090101 in _rules(data)


def test_validation_of_an_archive(client: TestClient) -> None:
    """Every SBML entry of an archive is validated, keyed like its report."""
    with OMEX_ICGMODEL.open("rb") as f:
        response = client.post("/api/validation/file", files={"source": ("m.omex", f)})
    data = response.json()
    _check_validation(data, entries=3)
    with OMEX_ICGMODEL.open("rb") as f:
        report = client.post("/api/file", files={"source": ("m.omex", f)}).json()
    assert list(data["entries"]) == list(report["reports"])


def test_validation_of_content(client: TestClient) -> None:
    """Pasted content is validated untrusted."""
    response = client.post(
        "/api/validation/content", content=COMP_DELETION.read_bytes()
    )
    data = response.json()
    _check_validation(data)
    assert 1090101 in _rules(data)


def test_validation_of_content_without_a_model(client: TestClient) -> None:
    """A document without a model is an error, as for its report."""
    content = (
        b'<?xml version="1.0" encoding="UTF-8"?><sbml xmlns="http://www.sbml.org/'
        b'sbml/level3/version1/core" level="3" version="1"></sbml>'
    )
    data = client.post("/api/validation/content", content=content).json()
    _check_error(data, info={})
    assert "No SBML model" in data["errors"][0]


def test_validation_of_invalid_content(client: TestClient) -> None:
    """Content which is no SBML is an error."""
    data = client.post("/api/validation/content", content=b"garbage").json()
    _check_error(data, info={})


def test_validation_of_content_beyond_the_limit(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The body of a validation is limited like the body of a report."""
    monkeypatch.setattr(limits, "MAX_CONTENT_SIZE", 1024)
    data = client.post("/api/validation/content", content=b"x" * 2048).json()
    _check_error(data, info={})
    assert "larger than" in data["errors"][0]


def test_validation_of_a_url(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A model behind a url is downloaded and validated untrusted."""
    urls: list[str] = []

    def download(url: str) -> bytes:
        urls.append(url)
        return COMP_DELETION.read_bytes()

    monkeypatch.setattr(api, "download", download)
    url = "https://example.org/comp_deletion.xml"
    data = client.get("/api/validation/url", params={"url": url}).json()
    assert urls == [url]
    _check_validation(data)
    assert 1090101 in _rules(data)


def test_validation_of_a_url_of_the_internal_network(client: TestClient) -> None:
    """The download of a validation is the one of a report, public addresses only."""
    url = "http://127.0.0.1:1/model.xml"
    data = client.get("/api/validation/url", params={"url": url}).json()
    _check_error(data, info={"url": url})


def test_validation_of_an_upload(client: TestClient, uploads: UploadStore) -> None:
    """An upload is validated untrusted by its id."""
    with COMP_DELETION.open("rb") as f:
        response = client.post("/api/upload", files={"source": ("model.xml", f)})
    upload_id = response.json()["id"]
    data = client.get(f"/api/validation/upload/{upload_id}").json()
    _check_validation(data)
    assert 1090101 in _rules(data)


def test_validation_of_an_unknown_upload(
    client: TestClient, uploads: UploadStore
) -> None:
    """An unknown id is an error which says how long uploads are kept."""
    data = client.get("/api/validation/upload/unknown_id_of_22_chars").json()
    _check_error(data, info={})
    assert "kept for 24 hours" in data["errors"][0]


def test_a_skipped_validation_is_answered(client: TestClient) -> None:
    """A document beyond the budget is answered with its reason."""
    submodels = "".join(
        f'<comp:submodel comp:id="s{i}" comp:modelRef="d"/>' for i in range(1000)
    )
    species = "".join(
        f'<species id="x{k}" compartment="c" initialAmount="1" '
        'hasOnlySubstanceUnits="true" boundaryCondition="false" constant="false"/>'
        for k in range(20)
    )
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" '
        'xmlns:comp="http://www.sbml.org/sbml/level3/version1/comp/version1" '
        'level="3" version="1" comp:required="true">'
        f'<model id="m"><comp:listOfSubmodels>{submodels}</comp:listOfSubmodels>'
        '</model><comp:listOfModelDefinitions><comp:modelDefinition id="d">'
        '<listOfCompartments><compartment id="c" constant="true"/>'
        f"</listOfCompartments><listOfSpecies>{species}</listOfSpecies>"
        "</comp:modelDefinition></comp:listOfModelDefinitions></sbml>"
    )
    data = client.post("/api/validation/content", content=content.encode()).json()
    _check_validation(data)
    assert data["entries"]["./model.xml"]["skipped"] == "expandedSize"


def test_a_validation_beyond_the_admission_is_busy_at_once(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A server full of validations answers a further one at once as busy."""
    from sbml4humans import isolation

    monkeypatch.setattr(isolation, "MAX_CONCURRENT_VALIDATIONS", 1)
    monkeypatch.setattr(isolation, "MAX_WAITING_VALIDATIONS", 0)
    with isolation.admission() as admitted:
        assert admitted
        start = time.perf_counter()
        response = client.post(
            "/api/validation/content", content=REPRESSILATOR_SBML.read_bytes()
        )
        elapsed = time.perf_counter() - start
    assert response.json() == {"entries": {}, "skipped": "busy"}
    assert elapsed < 2.0


def test_reports_are_answered_while_validations_are_saturated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Validations never hold a thread of the other endpoints.

    The threadpool of the other endpoints is one thread here, the one child is
    held by the test: two validations waiting for it leave the thread free for
    a report, and a third validation is busy at once. The two waiting ones get
    no child before their timeout and are busy as well.
    """
    from anyio import to_thread

    from sbml4humans import isolation

    monkeypatch.setattr(isolation, "MAX_CONCURRENT_VALIDATIONS", 1)
    monkeypatch.setattr(isolation, "MAX_WAITING_VALIDATIONS", 1)
    monkeypatch.setattr(isolation, "VALIDATION_TIMEOUT", 3.0)
    content = REPRESSILATOR_SBML.read_bytes()

    async def one_thread() -> None:
        to_thread.current_default_thread_limiter().total_tokens = 1

    semaphore = isolation._semaphore()
    with (
        semaphore,
        TestClient(api.api, raise_server_exceptions=False) as local_client,
    ):
        assert local_client.portal is not None
        local_client.portal.call(one_thread)
        answers: list[dict[str, Any]] = []

        def validate() -> None:
            response = local_client.post("/api/validation/content", content=content)
            answers.append(response.json())

        threads = [threading.Thread(target=validate) for _ in range(2)]
        for thread in threads:
            thread.start()
        waited = time.perf_counter()
        while isolation._admitted < 2 and time.perf_counter() - waited < 10:
            time.sleep(0.01)
        assert isolation._admitted == 2

        start = time.perf_counter()
        report = local_client.post("/api/content", content=content)
        busy = local_client.post("/api/validation/content", content=content)
        elapsed = time.perf_counter() - start
        _check_report(report.json())
        assert busy.json() == {"entries": {}, "skipped": "busy"}
        assert elapsed < 2.5
        for thread in threads:
            thread.join()
    assert answers == [{"entries": {}, "skipped": "busy"}] * 2
