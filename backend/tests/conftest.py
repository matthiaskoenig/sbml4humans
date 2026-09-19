"""Shared fixtures of the backend tests."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from sbml4humans.api import api
from sbml4humans.model import Report
from sbml4humans.report import report_for_path
from sbml4humans.resources import BIOMODELS_CURATED_PATH


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
