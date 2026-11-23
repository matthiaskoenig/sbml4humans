"""Shared fixtures of the backend tests."""

import os
import shutil
import socket
import tempfile
import threading
import time
from collections.abc import Callable, Iterator
from multiprocessing.util import Finalize
from typing import Any

import pytest
import uvicorn
from fastapi.testclient import TestClient

from sbml4humans import isolation, validation
from sbml4humans.api import api
from sbml4humans.model import Report
from sbml4humans.report import report_for_path
from sbml4humans.resources import BIOMODELS_CURATED_PATH


def pytest_configure(config: pytest.Config) -> None:
    """Give every worker of pytest-xdist a temporary directory of its own.

    Tests check that the archives they read leave no directory in the temporary
    directory of the system (`_leaves_nothing` of `test_validation.py`), which would
    otherwise count the archives the other workers read at the same time. The
    directory is set in `TMPDIR`, which the forkserver and the children of the
    validation inherit, and is removed at the end of the session.
    """
    worker = os.environ.get("PYTEST_XDIST_WORKER")
    if worker is None:
        return
    worker_tmpdir = tempfile.mkdtemp(prefix=f"sbml4humans_tests_{worker}_")
    os.environ["TMPDIR"] = worker_tmpdir
    # `gettempdir` caches the directory it found first
    tempfile.tempdir = None
    # multiprocessing removes its own directory at priority -100. Removing its
    # parent in pytest_unconfigure races with that finalizer at process exit.
    Finalize(
        None,
        shutil.rmtree,
        args=(worker_tmpdir,),
        kwargs={"ignore_errors": True},
        exitpriority=-200,
    )


@pytest.fixture(scope="session")
def level2_biomodel() -> Report:
    """The report of BIOMD0000000003, a curated Level 2 Version 4 model.

    The model has one parameter in most of its kinetic laws, which a Level 2
    document writes as `<parameter>` (core §4.11.5).
    """
    response = report_for_path(BIOMODELS_CURATED_PATH / "BIOMD0000000003.omex")
    return next(iter(response.reports.values())).report


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    """Test client of the api.

    Server exceptions are not raised, so that the error contract of the api
    (an error payload with status 200) can be tested.
    """
    with TestClient(api, raise_server_exceptions=False) as client:
        yield client


# -------------------------------------------------------------------------------------
# the child processes of the isolated work, which the validation and the report share
# -------------------------------------------------------------------------------------
def _wide(instances: int, species: int = 20) -> bytes:
    """A main model of `instances` submodels of a definition of unitless species.

    With 1,000 instances of 20 species the document has 52 KB, the check of its
    consistency takes more than 20 seconds and reports 41,043 issues, and its
    report takes more than a minute.
    """
    definition = (
        '<comp:modelDefinition id="d"><listOfCompartments>'
        '<compartment id="c" constant="true"/></listOfCompartments><listOfSpecies>'
        + "".join(
            f'<species id="x{k}" compartment="c" initialAmount="1" '
            'hasOnlySubstanceUnits="true" boundaryCondition="false" '
            'constant="false"/>'
            for k in range(species)
        )
        + "</listOfSpecies></comp:modelDefinition>"
    )
    submodels = "".join(
        f'<comp:submodel comp:id="s{i}" comp:modelRef="d"/>' for i in range(instances)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" '
        'xmlns:comp="http://www.sbml.org/sbml/level3/version1/comp/version1" '
        'level="3" version="1" comp:required="true">'
        f'<model id="m"><comp:listOfSubmodels>{submodels}'
        "</comp:listOfSubmodels></model><comp:listOfModelDefinitions>"
        f"{definition}</comp:listOfModelDefinitions></sbml>"
    ).encode()


@pytest.fixture
def wide_document() -> Callable[..., bytes]:
    """The document of `_wide`, by the number of instances it is asked for."""
    return _wide


def _fan_out(depth: int, n: int = 10) -> bytes:
    """A document whose main model expands to `n` submodels on `depth` levels.

    With five levels of ten the 3 KB document expands to 222,268 elements:
    more than the comp validator checks, and more than the flattening of its
    ODE system fits in the memory of a child (5.2 GiB of address space, where
    the report of its elements takes 1 GiB and a second). `fanOut` of
    `frontend/tests/e2e/helpers.ts` and of `frontend/scripts/fixtures.mjs` builds
    the same document byte for byte, so that every suite states the same number
    of elements.
    """

    def submodels(model_ref: str) -> str:
        """A list of `n` submodels of one model."""
        return (
            "<comp:listOfSubmodels>"
            + "".join(
                f'<comp:submodel comp:id="s{i}" comp:modelRef="{model_ref}"/>'
                for i in range(n)
            )
            + "</comp:listOfSubmodels>"
        )

    definitions = '<comp:modelDefinition id="d0"/>' + "".join(
        f'<comp:modelDefinition id="d{k}">{submodels(f"d{k - 1}")}'
        "</comp:modelDefinition>"
        for k in range(1, depth)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" '
        'xmlns:comp="http://www.sbml.org/sbml/level3/version1/comp/version1" '
        'level="3" version="1" comp:required="true">'
        f'<model id="m"><listOfParameters>'
        '<parameter id="p" value="1" constant="true"/></listOfParameters>'
        f"{submodels(f'd{depth - 1}')}</model>"
        f"<comp:listOfModelDefinitions>{definitions}"
        "</comp:listOfModelDefinitions></sbml>"
    ).encode()


@pytest.fixture
def fan_out_document() -> Callable[..., bytes]:
    """The document of `_fan_out`, by the levels and the width it is asked for."""
    return _fan_out


@pytest.fixture
def slow_content(monkeypatch: pytest.MonkeyPatch) -> bytes:
    """Content whose read outlasts a short timeout, validated and reported.

    The validation of the 1,000 instances takes more than 20 seconds once the
    budget of the expanded size no longer skips it, and their report more than
    a minute.
    """
    monkeypatch.setattr(validation, "MAX_EXPANDED_ELEMENTS", 10**9)
    return _wide(1000)


@pytest.fixture
def spy_children(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """Record the pid of every child process an isolated run starts."""
    pids: list[int] = []
    start = isolation._start

    def spy(*args: Any) -> Any:
        process = start(*args)
        assert process.pid is not None
        pids.append(process.pid)
        return process

    monkeypatch.setattr(isolation, "_start", spy)
    return pids


# -------------------------------------------------------------------------------------
# a server a client can leave, which the `TestClient` never does
# -------------------------------------------------------------------------------------
@pytest.fixture
def live_server() -> Iterator[int]:
    """The port of the api served by uvicorn on the loopback interface."""
    server = uvicorn.Server(
        uvicorn.Config(api, host="127.0.0.1", port=0, log_level="warning")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    started = time.monotonic() + 20
    while not server.started:
        assert time.monotonic() < started, "the server did not start"
        time.sleep(0.05)
    try:
        yield server.servers[0].sockets[0].getsockname()[1]
    finally:
        server.should_exit = True
        thread.join(10)


def _post_and_leave(
    port: int, path: str, content: bytes, until: Callable[[], bool]
) -> None:
    """Post the content to a path, close the connection once `until` holds."""
    with socket.create_connection(("127.0.0.1", port)) as connection:
        connection.sendall(
            f"POST {path} HTTP/1.1\r\nHost: 127.0.0.1\r\n".encode()
            + b"Content-Type: application/octet-stream\r\n"
            + f"Content-Length: {len(content)}\r\n\r\n".encode()
            + content
        )
        limit = time.monotonic() + 20
        while not until():
            assert time.monotonic() < limit, "the request did not start"
            time.sleep(0.05)


@pytest.fixture
def post_and_leave() -> Callable[..., None]:
    """Post content to an endpoint of a live server and leave while it works."""
    return _post_and_leave


def _eventually(condition: Callable[[], bool], seconds: float) -> bool:
    """Whether the condition holds within some seconds."""
    limit = time.monotonic() + seconds
    while not condition():
        if time.monotonic() > limit:
            return False
        time.sleep(0.05)
    return True


@pytest.fixture
def eventually() -> Callable[..., bool]:
    """Wait for a condition, and say whether it held within its seconds."""
    return _eventually
