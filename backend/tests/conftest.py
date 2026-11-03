"""Shared fixtures of the backend tests."""

import os
import shutil
import tempfile
from collections.abc import Iterator
from multiprocessing.util import Finalize

import pytest
from fastapi.testclient import TestClient

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
