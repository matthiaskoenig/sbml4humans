"""Tests of the store of the uploads."""

import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from sbml4humans.uploads import (
    UPLOAD_LIFETIME,
    UploadNotFoundError,
    UploadStore,
    UploadStoreFullError,
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


def test_put_refused_when_the_store_is_full(tmp_path: Path) -> None:
    """Uploads are refused while the store holds its maximum, so the disk does not fill."""
    store = UploadStore(tmp_path, max_bytes=10)
    store.put(b"x" * 8)
    with pytest.raises(UploadStoreFullError):
        store.put(b"y" * 3)
    assert (
        len([path for path in tmp_path.iterdir() if not path.name.startswith(".")]) == 1
    )


def test_put_after_the_directory_was_removed(tmp_path: Path) -> None:
    """A store whose directory was removed (e.g. a cleaned temporary directory) creates it again."""
    store = UploadStore(tmp_path / "uploads")
    (tmp_path / "uploads").rmdir()
    upload = store.put(b"a")
    assert store.get(upload.id) == b"a"
    assert store.remove_expired() == 0


def test_remove_expired_of_a_removed_directory(tmp_path: Path) -> None:
    """The cleanup of a removed directory removes nothing and does not fail."""
    store = UploadStore(tmp_path / "uploads")
    (tmp_path / "uploads").rmdir()
    assert store.remove_expired() == 0


def test_independent_writers_share_one_atomic_quota(tmp_path: Path) -> None:
    """Separate store objects cannot both reserve the same remaining bytes."""

    def write(_: int) -> bool:
        """Race independent SQLite connections against one shared directory."""
        try:
            UploadStore(tmp_path, max_bytes=100).put(b"x" * 80)
            return True
        except UploadStoreFullError:
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(write, range(8)))
    assert sum(results) == 1
    assert UploadStore(tmp_path)._size() == 80


def test_reports_are_revision_bound_counted_and_expire_with_the_source(
    tmp_path: Path,
) -> None:
    """A cached response never survives or exceeds the source's storage policy."""
    store = UploadStore(tmp_path, max_bytes=20, lifetime=60)
    saved = store.put(b"source", b"report", variant="native/a")
    assert store.get_report(saved.id, "native/a") == b"report"
    assert store.get_report(saved.id, "native/b") is None
    assert store._size() == 12
    expired = time.time() - 61
    os.utime(tmp_path / saved.id, (expired, expired))
    assert store.remove_expired() == 1
    assert store._size() == 0
    assert not list(tmp_path.glob("*.report.gz"))


def test_a_lease_survives_source_expiry_and_cleanup(tmp_path: Path) -> None:
    """An admitted worker cannot lose its source while waiting for capacity."""
    store = UploadStore(tmp_path, lifetime=60)
    saved = store.put(b"source")
    with store.lease(saved.id) as leased:
        expired = time.time() - 61
        os.utime(tmp_path / saved.id, (expired, expired))
        store.remove_expired()
        assert leased.read_bytes() == b"source"
    assert not leased.exists()


def test_failed_publication_releases_files_and_reserved_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A filesystem failure cannot leak quota or partial uploads."""
    store = UploadStore(tmp_path)

    def fail(*args):
        """Fail after quota reservation and writing the partial file."""
        raise OSError("failed publication")

    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(OSError, match="failed publication"):
        store.put(b"source", b"report")
    assert store._size() == 0
    assert not list(tmp_path.glob(".partial-*"))


def _process_upload(directory: str) -> bool:
    """Reserve bytes in a separate server process with an independent connection."""
    try:
        UploadStore(Path(directory), max_bytes=100).put(b"x" * 80)
        return True
    except UploadStoreFullError:
        return False


def test_server_processes_share_the_same_quota(tmp_path: Path) -> None:
    """The filesystem quota also holds across multiple API worker processes."""
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor

    with ProcessPoolExecutor(
        max_workers=2, mp_context=multiprocessing.get_context("spawn")
    ) as pool:
        results = list(pool.map(_process_upload, [str(tmp_path)] * 4))
    assert sum(results) == 1
    assert UploadStore(tmp_path)._size() == 80
