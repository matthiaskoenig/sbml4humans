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
import shutil
import sqlite3
import tempfile
import time
from collections.abc import Generator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from platformdirs import user_cache_path


logger = logging.getLogger(__name__)

UPLOAD_LIFETIME = 24 * 60 * 60.0  # [s]
# the uploads of all tools together, so a client which uploads in a loop cannot fill the disk
MAX_STORE_BYTES = 5 * 1024 * 1024 * 1024
MAX_STORE_ENTRIES = 10_000
INDEX_NAME = ".uploads.sqlite3"
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
        max_entries: int = MAX_STORE_ENTRIES,
    ) -> None:
        """Create the store of the directory, which is created if it does not exist."""
        self.directory = directory
        self.lifetime = lifetime
        self.max_bytes = max_bytes
        self.max_entries = max_entries
        self._directory()

    def _directory(self) -> None:
        """Keep opaque upload identifiers private from other local accounts."""
        self.directory.mkdir(parents=True, mode=0o700, exist_ok=True)
        self.directory.chmod(0o700)

    @contextlib.contextmanager
    def _database(self) -> Generator[sqlite3.Connection]:
        """Open the shared quota index, migrating legacy files once under its lock."""
        self._directory()
        index = self.directory / INDEX_NAME
        connection = sqlite3.connect(index, timeout=30, isolation_level=None)
        try:
            index.chmod(0o600)
            if connection.execute("PRAGMA user_version").fetchone()[0] == 1:
                yield connection
                return
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS uploads ("
                "id TEXT PRIMARY KEY, bytes INTEGER NOT NULL, created REAL NOT NULL, "
                "partial TEXT, report_partial TEXT, report_key TEXT, "
                "report_size INTEGER NOT NULL DEFAULT 0, cache_key TEXT)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS quota (id INTEGER PRIMARY KEY, "
                "bytes INTEGER NOT NULL, count INTEGER NOT NULL)"
            )
            for statement in (
                "CREATE TRIGGER IF NOT EXISTS upload_added AFTER INSERT ON uploads "
                "BEGIN UPDATE quota SET bytes=bytes+NEW.bytes,count=count+1 WHERE id=1; END",
                "CREATE TRIGGER IF NOT EXISTS upload_removed AFTER DELETE ON uploads "
                "BEGIN UPDATE quota SET bytes=bytes-OLD.bytes,count=count-1 WHERE id=1; END",
                "CREATE TRIGGER IF NOT EXISTS upload_resized AFTER UPDATE OF bytes ON uploads "
                "BEGIN UPDATE quota SET bytes=bytes+NEW.bytes-OLD.bytes WHERE id=1; END",
                "CREATE INDEX IF NOT EXISTS upload_cache_key ON uploads(cache_key)",
            ):
                connection.execute(statement)
            if connection.execute("SELECT 1 FROM quota WHERE id=1").fetchone() is None:
                connection.execute("INSERT INTO quota VALUES (1,0,0)")
                for path in self.directory.iterdir():
                    # New writers open the index before creating partial files.
                    # Anything left here predates this transactional store.
                    if path.name.startswith(PARTIAL_PREFIX):
                        path.unlink(missing_ok=True)
                        continue
                    if not ID_PATTERN.fullmatch(path.name) or path.is_symlink():
                        continue
                    try:
                        stat = path.stat()
                    except FileNotFoundError:
                        continue
                    report = self._report_path(path.name)
                    report_size = report.stat().st_size if report.is_file() else 0
                    connection.execute(
                        "INSERT OR IGNORE INTO uploads(id,bytes,created,report_size) VALUES (?,?,?,?)",
                        (
                            path.name,
                            stat.st_size + report_size,
                            stat.st_mtime,
                            report_size,
                        ),
                    )
            connection.execute("PRAGMA user_version=1")
            connection.commit()
            yield connection
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _report_path(self, upload_id: str) -> Path:
        """The immutable report sidecar, never an independently public identifier."""
        return self.directory / f"{upload_id}.report.gz"

    def put(
        self,
        content: bytes | Path,
        report: bytes | None = None,
        *,
        variant: str = "",
        cache_key: str | None = None,
    ) -> Upload:
        """Keep the content and return its upload.

        The file is written to a temporary file of the directory first and renamed,
        so a file of an id is always complete; `mkstemp` creates it with mode 0600.
        """
        size = len(content) if isinstance(content, bytes) else content.stat().st_size
        report_size = len(report) if report is not None else 0
        with self._database() as connection:
            upload_id = secrets.token_urlsafe(16)
            fd, partial = tempfile.mkstemp(dir=self.directory, prefix=PARTIAL_PREFIX)
            reserved = False
            try:
                connection.execute("BEGIN IMMEDIATE")
                used, count = connection.execute(
                    "SELECT bytes,count FROM quota WHERE id=1"
                ).fetchone()
                if (
                    used + size + report_size > self.max_bytes
                    or count >= self.max_entries
                ):
                    connection.rollback()
                    self.remove_expired()
                    connection.execute("BEGIN IMMEDIATE")
                    used, count = connection.execute(
                        "SELECT bytes,count FROM quota WHERE id=1"
                    ).fetchone()
                    if (
                        used + size + report_size > self.max_bytes
                        or count >= self.max_entries
                    ):
                        raise UploadStoreFullError
                connection.execute(
                    "INSERT INTO uploads(id,bytes,created,partial,report_key,report_size,cache_key) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (
                        upload_id,
                        size + report_size,
                        time.time(),
                        Path(partial).name,
                        variant if report is not None else None,
                        report_size,
                        cache_key,
                    ),
                )
                connection.commit()
                reserved = True
                with os.fdopen(fd, "wb") as target:
                    fd = -1
                    if isinstance(content, bytes):
                        target.write(content)
                    else:
                        with content.open("rb") as source:
                            remaining = size
                            while chunk := source.read(min(64 * 1024, remaining + 1)):
                                if len(chunk) > remaining:
                                    raise ValueError(
                                        "The source changed while it was stored."
                                    )
                                target.write(chunk)
                                remaining -= len(chunk)
                    if target.tell() != size:
                        raise ValueError("The source changed while it was stored.")
                if report is not None:
                    report_fd, report_partial = tempfile.mkstemp(
                        dir=self.directory, prefix=PARTIAL_PREFIX
                    )
                    try:
                        with os.fdopen(report_fd, "wb") as target:
                            connection.execute(
                                "UPDATE uploads SET report_partial=? WHERE id=?",
                                (Path(report_partial).name, upload_id),
                            )
                            target.write(report)
                        os.replace(report_partial, self._report_path(upload_id))
                    finally:
                        Path(report_partial).unlink(missing_ok=True)
                # The source is the publication marker: its report is complete first.
                os.replace(partial, self.directory / upload_id)
                connection.execute(
                    "UPDATE uploads SET partial=NULL,report_partial=NULL WHERE id=?",
                    (upload_id,),
                )
            except BaseException:
                connection.rollback()
                if fd >= 0:
                    os.close(fd)
                Path(partial).unlink(missing_ok=True)
                if reserved:
                    self._discard(connection, upload_id)
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
        with self.lease(upload_id) as path:
            return path.read_bytes()

    @contextlib.contextmanager
    def lease(self, upload_id: str) -> Generator[Path]:
        """Keep an admitted source alive across concurrent expiry and worker queuing."""
        if not ID_PATTERN.fullmatch(upload_id):
            raise UploadNotFoundError(upload_id)
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "model"
            with self._database() as connection:
                connection.execute("BEGIN IMMEDIATE")
                source = self.directory / upload_id
                row = connection.execute(
                    "SELECT 1 FROM uploads WHERE id=?", (upload_id,)
                ).fetchone()
                try:
                    written = source.stat().st_mtime
                    if (
                        row is None
                        or self._expired(written, time.time())
                        or source.is_symlink()
                    ):
                        raise FileNotFoundError
                    try:
                        os.link(source, target)
                    except OSError:
                        with (
                            source.open("rb") as incoming,
                            target.open("wb") as outgoing,
                        ):
                            shutil.copyfileobj(incoming, outgoing, 64 * 1024)
                except FileNotFoundError:
                    self._discard(connection, upload_id)
                    raise UploadNotFoundError(upload_id) from None
                connection.commit()
            yield target

    def get_report(self, upload_id: str, variant: str = "") -> bytes | None:
        """Reuse a report only for the same source and native runtime/options."""
        with self.lease(upload_id), self._database() as connection:
            row = connection.execute(
                "SELECT report_key FROM uploads WHERE id=?", (upload_id,)
            ).fetchone()
            if row is None or row[0] != variant:
                return None
            try:
                return self._report_path(upload_id).read_bytes()
            except FileNotFoundError:
                return None

    def matches(self, upload_id: str, cache_key: str) -> bool:
        """Bind an opaque snapshot to its original URL and report semantics."""
        if not ID_PATTERN.fullmatch(upload_id):
            return False
        with self._database() as connection:
            return (
                connection.execute(
                    "SELECT 1 FROM uploads WHERE id=? AND cache_key=?",
                    (upload_id, cache_key),
                ).fetchone()
                is not None
            )

    def evict_oldest(self) -> bool:
        """Make room in an explicitly ephemeral cache without affecting active leases."""
        with self._database() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT id FROM uploads WHERE partial IS NULL ORDER BY created LIMIT 1"
            ).fetchone()
            if row is None:
                connection.rollback()
                return False
            self._discard(connection, row[0])
            return True

    def save_report(self, upload_id: str, report: bytes, variant: str = "") -> bool:
        """Fill a missing report once, reserving sidecar bytes before writing."""
        with self.lease(upload_id), self._database() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT report_size FROM uploads WHERE id=?", (upload_id,)
            ).fetchone()
            used = connection.execute("SELECT bytes FROM quota WHERE id=1").fetchone()[
                0
            ]
            if row is None or row[0] or used + len(report) > self.max_bytes:
                connection.rollback()
                return False
            fd, temporary = tempfile.mkstemp(dir=self.directory, prefix=PARTIAL_PREFIX)
            reserved = False
            try:
                with os.fdopen(fd, "wb") as target:
                    connection.execute(
                        "UPDATE uploads SET bytes=bytes+?,report_size=?,report_partial=? WHERE id=?",
                        (len(report), len(report), Path(temporary).name, upload_id),
                    )
                    connection.commit()
                    reserved = True
                    target.write(report)
                connection.execute("BEGIN IMMEDIATE")
                if (
                    connection.execute(
                        "SELECT 1 FROM uploads WHERE id=?", (upload_id,)
                    ).fetchone()
                    is None
                ):
                    connection.rollback()
                    return False
                os.replace(temporary, self._report_path(upload_id))
                connection.execute(
                    "UPDATE uploads SET report_key=?,report_partial=NULL WHERE id=?",
                    (variant, upload_id),
                )
                connection.commit()
                return True
            except BaseException:
                connection.rollback()
                if reserved:
                    self._report_path(upload_id).unlink(missing_ok=True)
                    connection.execute(
                        "UPDATE uploads SET bytes=bytes-?,report_size=0,report_partial=NULL WHERE id=?",
                        (len(report), upload_id),
                    )
                raise
            finally:
                Path(temporary).unlink(missing_ok=True)

    def _discard(self, connection: sqlite3.Connection, upload_id: str) -> None:
        """Remove files before releasing their reservation, including interrupted writes."""
        if not connection.in_transaction:
            connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT partial,report_partial FROM uploads WHERE id=?", (upload_id,)
        ).fetchone()
        if row is not None:
            for name in (upload_id, f"{upload_id}.report.gz", *row):
                if name is not None:
                    (self.directory / name).unlink(missing_ok=True)
            connection.execute("DELETE FROM uploads WHERE id=?", (upload_id,))
        connection.commit()

    def remove_expired(self) -> int:
        """Delete the expired uploads, and partial files as old; returns how many."""
        if not self.directory.is_dir():
            return 0
        now, removed = time.time(), 0
        with self._database() as connection:
            connection.execute("BEGIN IMMEDIATE")
            for upload_id, created in connection.execute(
                "SELECT id,created FROM uploads"
            ).fetchall():
                path = self.directory / upload_id
                try:
                    written = path.stat().st_mtime
                except FileNotFoundError:
                    written = created
                if self._expired(written, now):
                    self._discard(connection, upload_id)
                    removed += 1
                    connection.execute("BEGIN IMMEDIATE")
            connection.commit()
        if removed:
            logger.info("Removed %s expired uploads", removed)
        return removed

    def _size(self) -> int:
        """The bytes of the files of the store."""
        with self._database() as connection:
            return connection.execute("SELECT bytes FROM quota WHERE id=1").fetchone()[
                0
            ]

    def _expired(self, written: float, now: float) -> bool:
        """Whether a file written at the time has expired at now."""
        return now >= written + self.lifetime


def default_directory() -> Path:
    """The directory of the uploads: `SBML4HUMANS_UPLOADS`, else a private user-cache directory."""
    configured = os.environ.get(UPLOADS_VARIABLE)
    if configured:
        return Path(configured)
    return user_cache_path("sbml4humans") / "sbml4humans-uploads"


@functools.cache
def upload_store() -> UploadStore:
    """The store of the uploads of the api, created at the first use."""
    return UploadStore(default_directory())
