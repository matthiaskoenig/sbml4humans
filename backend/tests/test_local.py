"""Tests of the local server behind `sbml4humans.show`."""

import asyncio
import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sbml4humans import __version__
from sbml4humans import local as local_module
from sbml4humans.local import MAX_REPORTS, LocalApp, ReportStore
from sbml4humans.localstate import SECRET_HEADER, read_state
from sbml4humans.model import ReportResponse
from sbml4humans.report import report_for_path
from sbml4humans.resources import EXAMPLES_DIR, REPRESSILATOR_SBML


PORT = 1777
SECRET = "the-secret-of-the-test"
ORIGIN = f"http://127.0.0.1:{PORT}"


@pytest.fixture
def frontend(tmp_path: Path) -> Path:
    """A directory which looks like the build of the frontend."""
    directory = tmp_path / "frontend"
    (directory / "assets").mkdir(parents=True)
    (directory / "index.html").write_text("<html>the page</html>")
    (directory / "assets" / "index.js").write_text("console.log('the script')")
    (directory / "assets" / "glossary-details.json").write_text('{"entries": {}}')
    (tmp_path / "secret.txt").write_text("outside of the build")
    return directory


@pytest.fixture
def app(frontend: Path) -> LocalApp:
    """The local app on the port and with the secret of the test."""
    return LocalApp(port=PORT, secret=SECRET, frontend=frontend)


@pytest.fixture
def local(app: LocalApp) -> TestClient:
    """A client which talks to the app the way the browser of the user does.

    A browser states the site a request comes from, for a request of the page
    of the server `same-origin`.
    """
    return TestClient(
        app,
        base_url=ORIGIN,
        raise_server_exceptions=False,
        headers={"Sec-Fetch-Site": "same-origin"},
    )


@pytest.fixture
def python_client(app: LocalApp) -> TestClient:
    """A client which talks to the app the way `sbml4humans.show` does."""
    return TestClient(app, base_url=ORIGIN, raise_server_exceptions=False)


def _post_report(local: TestClient, path: Path | str) -> dict[str, str]:
    """Ask for the report of a path, with the secret."""
    response = local.post(
        "/api/local/reports", json={"path": str(path)}, headers={SECRET_HEADER: SECRET}
    )
    assert response.status_code == 200
    return response.json()


# -------------------------------------------------------------------------------------
# the store of the reports
# -------------------------------------------------------------------------------------
def test_store_keeps_the_last_reports() -> None:
    """A token names a report until too many newer ones were added."""
    report = report_for_path(REPRESSILATOR_SBML)
    store = ReportStore()
    first = store.add(report)
    tokens = [store.add(report) for _ in range(MAX_REPORTS - 1)]
    assert store.get(first) is report
    # the first one was read last, so the next report pushes out the second one
    store.add(report)
    assert store.get(first) is report
    with pytest.raises(KeyError):
        store.get(tokens[0])
    assert len({first, *tokens}) == MAX_REPORTS
    assert all(len(token) >= 32 for token in tokens)


# -------------------------------------------------------------------------------------
# routing
# -------------------------------------------------------------------------------------
def test_ping_answers_with_the_version(local: TestClient) -> None:
    """The ping is how `show` finds a server it can use."""
    assert local.get("/api/local/ping").json() == {"version": __version__}


def test_the_public_api_is_served(local: TestClient) -> None:
    """The endpoints of the api are the ones of the public service."""
    examples = local.get("/api/examples").json()["examples"]
    assert any(example["id"] == "BIOMD0000000012" for example in examples)
    assert local.get("/openapi.json").json()["info"]["title"] == "sbml4humans"


def test_the_frontend_is_served(local: TestClient) -> None:
    """The page, its files, and the page again for every route of the frontend."""
    assert local.get("/").text == "<html>the page</html>"
    assert "the script" in local.get("/assets/index.js").text
    # the explanations of the report are a file of the build which the page fetches, so a
    # reader of a local report has them without a network
    details = local.get("/assets/glossary-details.json")
    assert details.json() == {"entries": {}}
    assert details.headers["content-type"].startswith("application/json")
    for route in (
        "/report?local=token",
        "/examples",
        "/examples/icg_body%20(icg_body.xml)",
    ):
        response = local.get(route)
        assert response.status_code == 200
        assert response.text == "<html>the page</html>"
        assert response.headers["content-type"].startswith("text/html")


def test_a_missing_file_of_the_build_is_not_the_page(local: TestClient) -> None:
    """A script which is not there is a 404 and not html which fails to parse."""
    assert local.get("/assets/missing.js").status_code == 404


def test_nothing_outside_of_the_build_is_served(local: TestClient) -> None:
    """A path does not leave the directory of the frontend."""
    for path in ("/../secret.txt", "/%2e%2e/secret.txt", "/assets/../../secret.txt"):
        assert "outside of the build" not in local.get(path).text


# -------------------------------------------------------------------------------------
# reports
# -------------------------------------------------------------------------------------
def test_a_report_is_built_and_read_by_its_token(local: TestClient) -> None:
    """The answer names the token and the url of the page which shows the report."""
    answer = _post_report(local, REPRESSILATOR_SBML)
    assert answer["url"] == f"{ORIGIN}/report?local={answer['token']}"
    body = local.get(f"/api/local/reports/{answer['token']}").json()
    report = ReportResponse.model_validate(body)
    assert list(report.reports) == ["./BIOMD0000000012_urn.xml"]
    assert "linkGraph" in body["reports"]["./BIOMD0000000012_urn.xml"]["report"]


def test_the_responses_are_gzipped(local: TestClient, frontend: Path) -> None:
    """The reports, the public api and the files of the build are gzipped."""
    (frontend / "assets" / "large.js").write_text("console.log('x');\n" * 1000)
    token = _post_report(local, REPRESSILATOR_SBML)["token"]
    gzip = {"Accept-Encoding": "gzip"}
    for path in (f"/api/local/reports/{token}", "/api/examples", "/assets/large.js"):
        response = local.get(path, headers=gzip)
        assert response.status_code == 200, path
        assert response.headers["content-encoding"] == "gzip", path
        assert response.num_bytes_downloaded < len(response.content), path


def test_the_files_next_to_a_model_are_read(local: TestClient) -> None:
    """A path of the user is a trusted path (#36)."""
    answer = _post_report(local, EXAMPLES_DIR / "comp_deletion.xml")
    body = local.get(f"/api/local/reports/{answer['token']}").json()
    assert list(body["reports"]) == ["./comp_deletion.xml", "./unit_definitions.xml"]


def test_errors_follow_the_contract_of_the_api(
    local: TestClient, tmp_path: Path
) -> None:
    """Status 200 with the message, for a bad file, a missing one and a bad token."""
    garbage = tmp_path / "garbage.xml"
    garbage.write_text("no sbml")
    assert "No SBML model could be read" in _post_report(local, garbage)["errors"][0]
    missing = _post_report(local, tmp_path / "missing.xml")
    assert "does not exist" in missing["errors"][0]
    relative = _post_report(local, "model.xml")
    assert "absolute" in relative["errors"][0]
    unknown = local.get("/api/local/reports/unknown")
    assert unknown.status_code == 200
    assert "no report for the token" in unknown.json()["errors"][0]
    invalid = local.post("/api/local/reports", json={}, headers={SECRET_HEADER: SECRET})
    assert invalid.status_code == 200
    assert invalid.json()["errors"]


def test_errors_carry_the_traceback_on_the_machine_of_the_user(
    local: TestClient, tmp_path: Path
) -> None:
    """The client of the local server is the user, who may read the traceback."""
    garbage = tmp_path / "garbage.xml"
    garbage.write_text("no sbml")
    errors = _post_report(local, garbage)["errors"]
    assert len(errors) == 2
    assert "Traceback" in errors[1]
    # the routed public api as well
    errors = local.post("/api/content", content=b"garbage").json()["errors"]
    assert len(errors) == 2
    assert "Traceback" in errors[1]


# -------------------------------------------------------------------------------------
# who may talk to the server
# -------------------------------------------------------------------------------------
@pytest.mark.parametrize("headers", [{}, {SECRET_HEADER: "wrong"}])
def test_a_report_of_a_path_needs_the_secret(
    local: TestClient, headers: dict[str, str]
) -> None:
    """Without the secret of the state file no path is read and nothing is shut down."""
    response = local.post(
        "/api/local/reports", json={"path": str(REPRESSILATOR_SBML)}, headers=headers
    )
    assert response.status_code == 403
    assert local.post("/api/local/shutdown", headers=headers).status_code == 403


@pytest.mark.parametrize(
    "host", ["evil.example", f"evil.example:{PORT}", "127.0.0.1:1", "127.0.0.1"]
)
def test_another_host_is_refused(app: LocalApp, host: str) -> None:
    """A name which resolves to 127.0.0.1 is not the server (DNS rebinding)."""
    client = TestClient(app, base_url=f"http://{host}")
    for path in ("/", "/api/examples", "/api/local/ping"):
        assert client.get(path).status_code == 403


def test_localhost_is_the_server_as_well(app: LocalApp) -> None:
    """The two names of the loopback interface."""
    client = TestClient(app, base_url=f"http://localhost:{PORT}")
    assert client.get("/api/local/ping").status_code == 200


@pytest.mark.parametrize(
    "origin", ["https://evil.example", "http://127.0.0.1:1", "null"]
)
def test_another_origin_is_refused(local: TestClient, origin: str) -> None:
    """A page of another site does not reach the api, which allows every origin."""
    for path in ("/api/examples", "/api/local/ping", "/api/url?url=http://intranet/"):
        assert local.get(path, headers={"Origin": origin}).status_code == 403
    # the page of the server itself states its own origin on a post
    assert local.get("/api/examples", headers={"Origin": ORIGIN}).status_code == 200


@pytest.mark.parametrize("site", ["cross-site", "same-site"])
def test_a_request_of_another_site_is_refused(app: LocalApp, site: str) -> None:
    """A page of another site does not reach the api by a request without origin.

    An image or a link of another page is a GET without `Origin`, which the
    browser states as a request of another site.
    """
    client = TestClient(app, base_url=ORIGIN, headers={"Sec-Fetch-Site": site})
    for path in (
        "/api/examples",
        "/api/local/ping",
        "/api/url?url=http://intranet/",
        "/api/local/reports/unknown",
    ):
        assert client.get(path).status_code == 403, path
    # the page itself may be opened from another site
    assert client.get("/report").status_code == 200


def test_a_request_the_user_makes_is_answered(app: LocalApp) -> None:
    """The address typed into the browser, which states no site."""
    client = TestClient(app, base_url=ORIGIN, headers={"Sec-Fetch-Site": "none"})
    assert client.get("/api/examples").status_code == 200


def test_the_python_client_reaches_the_local_endpoints_alone(
    python_client: TestClient,
) -> None:
    """A request without `Origin` and `Sec-Fetch-Site` is no request of a browser.

    It is the client of `sbml4humans.show`, which needs the local endpoints, or
    the request of an old browser, which might be one of another site, so the
    public api is not answered.
    """
    assert python_client.get("/api/local/ping").status_code == 200
    assert python_client.get("/api/examples").status_code == 403
    assert python_client.get("/api/url?url=http://intranet/").status_code == 403
    assert python_client.post("/api/content", content=b"<sbml/>").status_code == 403
    token = _post_report(python_client, REPRESSILATOR_SBML)["token"]
    assert python_client.get(f"/api/local/reports/{token}").status_code == 200


# -------------------------------------------------------------------------------------
# life and end
# -------------------------------------------------------------------------------------
def test_requests_are_signs_of_life_and_shutdown_is_asked_for(
    app: LocalApp, local: TestClient
) -> None:
    """The watcher of the server reads both from the app."""
    assert app.idle_seconds() >= 0
    before = app.last_request
    local.get("/api/local/ping")
    assert app.last_request > before
    assert app.shutdown_requested is False
    response = local.post("/api/local/shutdown", headers={SECRET_HEADER: SECRET})
    assert response.json() == {"shutdown": True}
    assert app.shutdown_requested is True


class _Server:
    """What the watcher reads and writes of a uvicorn server."""

    started = True
    should_exit = False


def test_the_watcher_says_where_the_server_is_and_ends_an_idle_one(
    app: LocalApp, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The state file is written once the server is up, and idleness ends it."""
    monkeypatch.setattr(local_module, "WATCH_INTERVAL", 0.01)
    server = _Server()
    state = tmp_path / "state" / "server.json"
    # the idle time counts from the last request, not from the start of the watcher
    app.last_request = time.monotonic()
    asyncio.run(local_module._watch(server, app, 0.2, state))  # ty: ignore[invalid-argument-type]
    assert app.idle_seconds() >= 0.2
    assert server.should_exit is True
    written = read_state(state)
    assert written is not None
    assert written["port"] == PORT
    assert written["secret"] == SECRET
    assert written["pid"] == os.getpid()


def test_the_watcher_ends_a_server_which_is_asked_to(
    app: LocalApp, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A shutdown does not wait for the idle timeout."""
    monkeypatch.setattr(local_module, "WATCH_INTERVAL", 0.01)
    server = _Server()
    app.shutdown_requested = True
    asyncio.run(local_module._watch(server, app, 3600, tmp_path / "server.json"))  # ty: ignore[invalid-argument-type]
    assert server.should_exit is True
