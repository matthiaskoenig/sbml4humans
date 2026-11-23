"""Shared fixtures of the backend tests."""

import os
import shutil
import tempfile
from collections.abc import Callable, Iterator
from multiprocessing.util import Finalize
from typing import Any

import pytest
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
