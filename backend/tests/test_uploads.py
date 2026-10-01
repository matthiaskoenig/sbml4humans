"""Tests of the store of the uploads."""

import os
import time
from pathlib import Path

import pytest

from sbml4humans.uploads import (
    UPLOAD_LIFETIME,
    UploadNotFoundError,
    UploadStore,
    default_directory,
)


def test_put_and_get(tmp_path: Path) -> None:
    """The bytes of an upload are read back by its id, which expires in 24 hours."""
    store = UploadStore(tmp_path)
    before = time.time()
    upload = store.put(b"<sbml/>")
    assert len(upload.id) == 22
    assert store.get(upload.id) == b"<sbml/>"
    assert (
        before + UPLOAD_LIFETIME - 5
        <= upload.expires.timestamp()
        <= time.time() + UPLOAD_LIFETIME + 5
    )
    assert (tmp_path / upload.id).stat().st_mode & 0o777 == 0o600


def test_ids_differ(tmp_path: Path) -> None:
    """Every upload has its own id."""
    store = UploadStore(tmp_path)
    assert store.put(b"a").id != store.put(b"a").id


@pytest.mark.parametrize(
    "upload_id", ["unknown_id_of_22_chars", "../../etc/passwd", "a/b", "", "x" * 23]
)
def test_get_unknown(tmp_path: Path, upload_id: str) -> None:
    """An unknown id, and one which is no id, are not found; neither reaches a path."""
    store = UploadStore(tmp_path)
    with pytest.raises(UploadNotFoundError) as error:
        store.get(upload_id)
    assert "kept for 24 hours" in str(error.value)


def test_get_expired(tmp_path: Path) -> None:
    """An expired upload is not found and deleted, also before the cleanup ran."""
    store = UploadStore(tmp_path, lifetime=60)
    upload = store.put(b"a")
    old = time.time() - 61
    os.utime(tmp_path / upload.id, (old, old))
    with pytest.raises(UploadNotFoundError):
        store.get(upload.id)
    assert not (tmp_path / upload.id).exists()


def test_remove_expired(tmp_path: Path) -> None:
    """The cleanup deletes the expired uploads and keeps the others."""
    store = UploadStore(tmp_path, lifetime=60)
    expired = store.put(b"a")
    kept = store.put(b"b")
    old = time.time() - 61
    os.utime(tmp_path / expired.id, (old, old))
    assert store.remove_expired() == 1
    assert store.get(kept.id) == b"b"


def test_default_directory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The directory comes from SBML4HUMANS_UPLOADS, else the temporary directory."""
    monkeypatch.setenv("SBML4HUMANS_UPLOADS", str(tmp_path / "uploads"))
    assert default_directory() == tmp_path / "uploads"
    monkeypatch.delenv("SBML4HUMANS_UPLOADS")
    assert default_directory().name == "sbml4humans-uploads"
