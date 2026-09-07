"""Shared fixtures of the backend tests."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from sbml4humans.api import api


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    """Test client of the api.

    Server exceptions are not raised, so that the error contract of the api
    (an error payload with status 200) can be tested.
    """
    with TestClient(api, raise_server_exceptions=False) as client:
        yield client
