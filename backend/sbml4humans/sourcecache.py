"""Opaque, bounded URL snapshots shared by report, validation and code export."""

import functools
import hashlib
import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from platformdirs import user_cache_path

from sbml4humans.uploads import UploadNotFoundError, UploadStore


SOURCE_HEADER = "X-SBML4Humans-Source"


class SourceSnapshotExpiredError(ValueError):
    """The immutable source shown by a report is no longer retained."""

    def __str__(self) -> str:
        """Ask for a fresh report instead of validating different source bytes."""
        return "The source of this report has expired. Reload the report before validating or exporting it."


def source_key(url: str, variant: str) -> str:
    """Keep URL credentials out of cache filenames and bind report semantics."""
    return hashlib.sha256(f"{variant}\0{url}".encode()).hexdigest()


@functools.cache
def snapshot_store() -> UploadStore:
    """A private disk cache with both byte and entry limits."""
    directory = Path(
        os.environ.get("SBML4HUMANS_SNAPSHOTS")
        or user_cache_path("sbml4humans") / "sources"
    )
    return UploadStore(
        directory, lifetime=15 * 60, max_bytes=512 * 1024**2, max_entries=1024
    )


@contextmanager
def snapshot_path(url: str, snapshot: str, variant: str) -> Generator[Path]:
    """Lease the exact source used by a report; never silently fetch a replacement."""
    store = snapshot_store()
    if not store.matches(snapshot, source_key(url, variant)):
        raise SourceSnapshotExpiredError
    try:
        with store.lease(snapshot) as path:
            yield path
    except UploadNotFoundError as error:
        raise SourceSnapshotExpiredError from error
