"""URL validation and exports use the precise source shown by a report."""

import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sbml4humans import api
from sbml4humans.model import ValidationResponse
from sbml4humans.report import OdeFile
from sbml4humans.resources import REPRESSILATOR_SBML
from sbml4humans.sourcecache import SOURCE_HEADER, snapshot_store


@pytest.fixture(autouse=True)
def snapshots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Keep snapshots isolated from other tests and the user's cache."""
    monkeypatch.setenv("SBML4HUMANS_SNAPSHOTS", str(tmp_path / "sources"))
    snapshot_store.cache_clear()
    api.url_reports.cache_clear()
    yield
    snapshot_store.cache_clear()
    api.url_reports.cache_clear()


def test_validation_and_export_do_not_download_the_url_again(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Even a changed upstream URL cannot change the source under an open report."""
    content = REPRESSILATOR_SBML.read_bytes()
    monkeypatch.setattr(api, "download", lambda _: content)
    url = "https://example.org/model.xml"
    response = client.get("/api/url", params={"url": url})
    snapshot = response.headers[SOURCE_HEADER]
    reads: list[bytes] = []

    def no_download(_: str) -> bytes:
        """A second download would break both source identity and efficiency."""
        raise AssertionError("downloaded again")

    def validate(path: Path) -> ValidationResponse:
        """Observe the admitted bytes without running consistency checks here."""
        reads.append(path.read_bytes())
        return ValidationResponse()

    def export(path: Path, fmt: str, location: str | None) -> OdeFile:
        """Observe the same source for a later code generation request."""
        reads.append(path.read_bytes())
        return OdeFile("same.py", "same source")

    monkeypatch.setattr(api, "download", no_download)
    monkeypatch.setattr(api, "validation_for_bytes", validate)
    monkeypatch.setattr(api, "ode_for_bytes", export)
    validated = client.get(
        "/api/validation/url", params={"url": url, "snapshot": snapshot}
    )
    exported = client.get(
        "/api/ode/url", params={"url": url, "snapshot": snapshot, "format": "python"}
    )
    assert validated.json()["skipped"] is None
    assert exported.text == "same source"
    assert reads == [content, content]


def test_expired_or_foreign_snapshots_never_silently_download_a_new_source(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unavailable source asks for reload instead of judging another model."""
    monkeypatch.setattr(api, "download", lambda _: REPRESSILATOR_SBML.read_bytes())
    url = "https://example.org/model.xml"
    snapshot = client.get("/api/url", params={"url": url}).headers[SOURCE_HEADER]
    foreign = client.get(
        "/api/validation/url",
        params={"url": url + "?different=1", "snapshot": snapshot},
    )
    assert "Reload" in foreign.json()["errors"][0]
    expired = time.time() - 1000
    os.utime(snapshot_store().directory / snapshot, (expired, expired))
    result = client.get(
        "/api/validation/url", params={"url": url, "snapshot": snapshot}
    )
    assert "Reload" in result.json()["errors"][0]
