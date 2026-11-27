"""The downloads of the ODE system of a model, `/api/ode/...`."""

import gzip
import logging
import os
import time
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from sbml4humans import api, isolation, limits, report
from sbml4humans.limits import ContentTooLargeError
from sbml4humans.report import (
    OdeFile,
    ReportInterruptedError,
    ode_for_bytes,
    ode_for_path,
)
from sbml4humans.resources import EXAMPLES_DIR, OMEX_ICGMODEL, REPRESSILATOR_SBML


EXAMPLE = "BIOMD0000000012"
# the latex document of that model, which the example and the repressilator of
# the endpoints of a request are both written as
LATEX_FILE = f"{EXAMPLE}.tex"
LATEX_CONTENT = r"\begin{document}"


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
        ("diffrax", "BIOMD0000000012.py", "import jax"),
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
    """A format sbmlsim-core does not write is an error."""
    response = client.get(f"/api/ode/examples/{EXAMPLE}", params={"format": "pdf"})
    _check_error(response, "pdf")


def test_ode_of_unsupported_model(client: TestClient) -> None:
    """Code of a model with an algebraic rule is refused by sbmlsim-core, an error."""
    response = client.post(
        "/api/ode/content",
        params={"format": "python"},
        content=(EXAMPLES_DIR / "algebraic_rule.xml").read_bytes(),
    )
    _check_error(response, "algebraic rule")


def test_ode_of_a_model_beyond_the_expanded_size(
    client: TestClient, fan_out_document: Callable[..., bytes]
) -> None:
    """A document whose comp submodels expand beyond the budget is an error.

    The download flattens the model as the report does, so it is gated like
    the report: the client reads why the equations were not built instead of
    the sentence of a child which ran out of memory.
    """
    response = client.post(
        "/api/ode/content",
        params={"format": "python"},
        content=fan_out_document(5),
    )
    _check_error(response, "expands by its comp submodels to 222,268 elements")


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
    assert (
        "content-disposition"
        in response.headers["access-control-expose-headers"].lower()
    )


# -------------------------------------------------------------------------------------
# the ODE file of an untrusted source, which a child process writes
# -------------------------------------------------------------------------------------
def _crashing_child(job: report.OdeJob) -> Iterator[tuple[str, OdeFile]]:
    """End the child process before it writes the file, as a document of libsbml can.

    `multiprocessing` pickles the function of a child by its name, so the child
    imports this module and runs this replacement of `report.ode_source`.
    """
    os._exit(1)


def test_the_ode_file_of_untrusted_content_runs_in_a_child(
    spy_children: list[int],
) -> None:
    """Nothing of an untrusted source is read in the process of the server."""
    ode = ode_for_bytes(REPRESSILATOR_SBML.read_bytes(), "latex")
    assert LATEX_CONTENT in ode.content
    assert ode.filename == LATEX_FILE
    assert len(spy_children) == 1


def test_every_ode_download_runs_in_a_child(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, spy_children: list[int]
) -> None:
    """Content, file, url and upload each write their file in a child process."""
    content = REPRESSILATOR_SBML.read_bytes()

    def download(url: str) -> bytes:
        return content

    monkeypatch.setattr(api, "download", download)
    upload_id = client.post(
        "/api/upload", files={"source": ("model.xml", content)}
    ).json()["id"]
    # the upload was reported by a child of its own before the store kept it
    vetted = len(spy_children)
    responses = [
        client.post("/api/ode/content", params={"format": "latex"}, content=content),
        client.post(
            "/api/ode/file",
            params={"format": "latex"},
            files={"source": ("model.xml", content)},
        ),
        client.get(
            "/api/ode/url",
            params={"url": "https://example.org/model.xml", "format": "latex"},
        ),
        client.get(f"/api/ode/upload/{upload_id}", params={"format": "latex"}),
    ]
    for response in responses:
        _check_download(response, LATEX_FILE, LATEX_CONTENT)
    assert len(spy_children) == vetted + len(responses)


def test_the_ode_file_of_an_example_forks_no_child(
    client: TestClient, spy_children: list[int]
) -> None:
    """A trusted source pays nothing for the isolation of a request."""
    response = client.get(f"/api/ode/examples/{EXAMPLE}", params={"format": "latex"})
    _check_download(response, LATEX_FILE, LATEX_CONTENT)
    assert spy_children == []


def test_an_ode_file_whose_child_crashes_is_an_error_body(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A document which ends the process which reads it is an error of its request.

    The sentence names the file the client asked for and no report.
    """
    monkeypatch.setattr(report, "ode_source", _crashing_child)
    response = client.post(
        "/api/ode/content",
        params={"format": "latex"},
        content=REPRESSILATOR_SBML.read_bytes(),
    )
    _check_error(
        response,
        "The document could not be written as an ODE system: the process which "
        "read it ended unexpectedly.",
    )


def _delayed_ode(job: report.OdeJob) -> Iterator[tuple[str, OdeFile]]:
    """Keep an actual isolated export busy independently of generator speed."""
    time.sleep(20)
    yield from report.ode_source(job)


def test_an_ode_file_which_times_out_is_an_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A file beyond the timeout of the report budget is an error the client reads."""
    monkeypatch.setattr(isolation, "MIN_CHILD_TIME", 0.1)
    monkeypatch.setattr(isolation.REPORT_BUDGET, "timeout", 1.0)
    monkeypatch.setattr(report, "ode_source", _delayed_ode)
    with pytest.raises(
        ReportInterruptedError,
        match="The ODE system took longer than the 1 seconds an ODE system may take",
    ) as raised:
        ode_for_bytes(REPRESSILATOR_SBML.read_bytes(), "latex")
    assert raised.value.interruption == "timeout"
    assert raised.value.work == "ode system"


def test_an_ode_file_beyond_the_admission_is_busy(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A download shares the admission of the reports, and is busy with them.

    The sentence of a busy server names no report either: the server is busy
    with the work of other requests, reports and downloads alike.
    """
    monkeypatch.setattr(isolation.REPORT_BUDGET, "concurrency", 1)
    monkeypatch.setattr(isolation.REPORT_BUDGET, "waiting", 0)
    with isolation.admission(isolation.REPORT_BUDGET) as admitted:
        assert admitted
        response = client.post(
            "/api/ode/content",
            params={"format": "latex"},
            content=REPRESSILATOR_SBML.read_bytes(),
        )
    _check_error(
        response, "The server is busy with other requests, try again in a moment."
    )


def test_an_ode_file_which_fails_logs_its_time(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The time of a file is logged also when it raised, which a reader wants most."""
    content = b'<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core"/>'
    with (
        caplog.at_level(logging.INFO, logger="sbml4humans.report"),
        pytest.raises(ValueError, match="No SBML model"),
    ):
        ode_for_bytes(content, "latex")
    assert f"ode system (latex) of {len(content)} bytes in " in caplog.text


def test_the_limits_of_the_server_reach_the_child_of_an_ode_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A child writes the file within the limits of its server, which it is given."""
    monkeypatch.setattr(limits, "MAX_CONTENT_SIZE", 1024)
    with pytest.raises(ContentTooLargeError, match="1024 bytes"):
        ode_for_bytes(gzip.compress(b" " * 4096), "latex")


def test_code_is_the_ode_system_without_simulator() -> None:
    """The code of a download holds the ODE system, `simulator` adds the integrator."""
    plain = ode_for_path(REPRESSILATOR_SBML, "python")
    assert "def f_dxdt(" in plain.content
    assert "def simulate(" not in plain.content
    full = ode_for_path(REPRESSILATOR_SBML, "python", simulator=True)
    assert "def simulate(" in full.content
    document = ode_for_path(REPRESSILATOR_SBML, "latex")
    assert r"\begin{document}" in document.content


def test_export_preserves_the_original_double_precision(client: TestClient) -> None:
    """An export must not round source values through a libSBML XML serialization."""
    source = b"""<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" version="2"><model id="precise"><listOfParameters><parameter id="p" constant="false" value="1.2345678901234567"/></listOfParameters><listOfRules><rateRule variable="p"><math xmlns="http://www.w3.org/1998/Math/MathML"><cn type="real">1.2345678901234567</cn></math></rateRule></listOfRules></model></sbml>"""
    response = client.post(
        "/api/ode/content?format=python",
        content=source,
        headers={"Content-Type": "application/xml"},
    )
    assert response.status_code == 200
    assert "1.2345678901234567" in response.text
    assert "1.23456789012346" not in response.text
