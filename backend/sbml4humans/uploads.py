"""Uploads kept for a limited time, so that other tools can link their report.

A tool such as cy3sbml uploads a model with `POST /api/upload` and opens the
report at `/report?upload=<id>`. The bytes of an upload are kept in a file of a
directory, named by the id, for `UPLOAD_LIFETIME` after the upload; whoever has
the id reads the report, so it is 128 random bits. The age of an upload is the
modification time of its file, so the uploads survive a restart of the server.
"""

import contextlib
import functools
import logging
import os
import re
import secrets
import tempfile
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


logger = logging.getLogger(__name__)

UPLOAD_LIFETIME = 24 * 60 * 60.0  # [s]
# the uploads of all tools together, so a client which uploads in a loop cannot fill the disk
MAX_STORE_BYTES = 5 * 1024 * 1024 * 1024
CLEANUP_INTERVAL = 60 * 60.0  # [s]
UPLOADS_VARIABLE = "SBML4HUMANS_UPLOADS"
# the form of `secrets.token_urlsafe(16)`, anything else is no id and never a path
ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{22}")
# the temporary files of uploads which are being written
PARTIAL_PREFIX = ".partial-"


@dataclass(frozen=True)
class Upload:
    """An upload: its id and the time it expires."""

    id: str
    expires: datetime


class UploadNotFoundError(KeyError):
    """Raised for an id without upload, or with an expired one."""

    def __init__(self, upload_id: str) -> None:
        """Create the error for the id."""
        super().__init__(upload_id)
        self.upload_id = upload_id

    def __str__(self) -> str:
        """Message for the frontend."""
        return f"The upload '{self.upload_id}' is not available: uploads are kept for 24 hours."


class UploadStoreFullError(RuntimeError):
    """Raised for an upload while the store holds `MAX_STORE_BYTES`."""

    def __str__(self) -> str:
        """Message for the frontend."""
        return "sbml4humans keeps too many uploads at the moment, try again later."


class UploadStore:
    """The uploads in a directory, one file per upload named by its id."""

    def __init__(
        self,
        directory: Path,
        lifetime: float = UPLOAD_LIFETIME,
        max_bytes: int = MAX_STORE_BYTES,
    ) -> None:
        """Create the store of the directory, which is created if it does not exist."""
        self.directory = directory
        self.lifetime = lifetime
        self.max_bytes = max_bytes
        directory.mkdir(parents=True, exist_ok=True)

    def put(self, content: bytes) -> Upload:
        """Keep the content and return its upload.

        The file is written to a temporary file of the directory first and renamed,
        so a file of an id is always complete; `mkstemp` creates it with mode 0600.
        """
        # the directory is created again if it was removed, e.g. a cleaned temporary directory
        self.directory.mkdir(parents=True, exist_ok=True)
        if self._size() + len(content) > self.max_bytes:
            self.remove_expired()
            if self._size() + len(content) > self.max_bytes:
                raise UploadStoreFullError
        upload_id = secrets.token_urlsafe(16)
        fd, partial = tempfile.mkstemp(dir=self.directory, prefix=PARTIAL_PREFIX)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(content)
            os.replace(partial, self.directory / upload_id)
        except BaseException:
            Path(partial).unlink(missing_ok=True)
            raise
        written = (self.directory / upload_id).stat().st_mtime
        return Upload(
            id=upload_id, expires=datetime.fromtimestamp(written + self.lifetime, UTC)
        )

    def get(self, upload_id: str) -> bytes:
        """The content of the upload; an expired upload is deleted.

        Raises:
            UploadNotFoundError: if there is no upload of the id (any more).
        """
        if not ID_PATTERN.fullmatch(upload_id):
            raise UploadNotFoundError(upload_id)
        path = self.directory / upload_id
        try:
            written = path.stat().st_mtime
        except FileNotFoundError:
            raise UploadNotFoundError(upload_id) from None
        if self._expired(written, time.time()):
            path.unlink(missing_ok=True)
            raise UploadNotFoundError(upload_id)
        return path.read_bytes()

    def remove_expired(self) -> int:
        """Delete the expired uploads, and partial files as old; returns how many."""
        now = time.time()
        removed = 0
        if not self.directory.is_dir():
            return 0
        for path in self.directory.iterdir():
            try:
                if path.is_file() and self._expired(path.stat().st_mtime, now):
                    path.unlink()
                    removed += 1
            except FileNotFoundError:
                continue
        if removed:
            logger.info("Removed %s expired uploads", removed)
        return removed

    def _size(self) -> int:
        """The bytes of the files of the store."""
        size = 0
        for path in self.directory.iterdir():
            with contextlib.suppress(FileNotFoundError):
                size += path.stat().st_size
        return size

    def _expired(self, written: float, now: float) -> bool:
        """Whether a file written at the time has expired at now."""
        return now >= written + self.lifetime


def default_directory() -> Path:
    """The directory of the uploads: `SBML4HUMANS_UPLOADS`, else one in the temporary directory."""
    configured = os.environ.get(UPLOADS_VARIABLE)
    if configured:
        return Path(configured)
    return Path(tempfile.gettempdir()) / "sbml4humans-uploads"


@functools.cache
def upload_store() -> UploadStore:
    """The store of the uploads of the api, created at the first use."""
    return UploadStore(default_directory())
