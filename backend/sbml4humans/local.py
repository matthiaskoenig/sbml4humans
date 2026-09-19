"""The local server behind `sbml4humans.show`.

`python -m sbml4humans.local` serves the api and the built frontend on a port
of 127.0.0.1, so that the report of a file of this machine opens in the browser
without the file leaving the machine. `LocalApp` routes a request by its path:
`/api/local/...` to the endpoints of this module, every other `/api/...` to the
public api as it is, everything else to the frontend.

Who may talk to the server: the public api allows every origin, which is wrong
on localhost, where any page of the browser could ask the server to read a path
or to download a url from inside the network. A request whose `Host` is not the
server (DNS rebinding) or whose `Origin` is another one (a cross site request)
is refused, and the two endpoints which act on the machine, the report of a
path and the shutdown, need the secret of the state file, which only a process
of the same user can read.

The server ends itself when it was idle for `IDLE_TIMEOUT`. A report page pings
it while it is open, so it lives as long as somebody looks at a report.
"""

import argparse
import asyncio
import logging
import os
import secrets
import time
from collections import OrderedDict
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Header, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import PlainTextResponse, Response
from starlette.staticfiles import StaticFiles
from starlette.types import Receive, Scope, Send

from sbml4humans import __version__
from sbml4humans.api import add_error_contract, api
from sbml4humans.localstate import (
    HOST,
    SECRET_HEADER,
    SECRET_VARIABLE,
    frontend_dir,
    read_state,
    state_file,
    write_state,
)
from sbml4humans.model import ReportResponse
from sbml4humans.report import report_for_path


logger = logging.getLogger(__name__)

MAX_REPORTS = 16
IDLE_TIMEOUT = 15 * 60.0  # [s]
WATCH_INTERVAL = 1.0  # [s]

# the paths of the public api next to `/api/`, its OpenAPI pages
API_PAGES = ("/docs", "/redoc", "/openapi.json")


class ReportStore:
    """The reports of the server by their token, the most recent `MAX_REPORTS`.

    A token is the address of a report: whoever has it reads the report, so it
    is 128 random bits.
    """

    def __init__(self, limit: int = MAX_REPORTS) -> None:
        """Create an empty store."""
        self.limit = limit
        self._reports: OrderedDict[str, ReportResponse] = OrderedDict()

    def add(self, report: ReportResponse) -> str:
        """Keep the report and return its token."""
        token = secrets.token_hex(16)
        self._reports[token] = report
        while len(self._reports) > self.limit:
            self._reports.popitem(last=False)
        return token

    def get(self, token: str) -> ReportResponse:
        """The report of the token, which counts as a use of it.

        Raises:
            KeyError: if there is no report of the token (any more).
        """
        report = self._reports[token]
        self._reports.move_to_end(token)
        return report


class ReportNotFoundError(KeyError):
    """Raised for a token without report."""

    def __str__(self) -> str:
        """Message for the frontend."""
        return (
            "There is no report for the token of this address (any more). Create "
            "it again with `sbml4humans.show(path)`."
        )


class ReportRequest(BaseModel):
    """The body of the request for the report of a path."""

    path: str


class FrontendFiles(StaticFiles):
    """The built frontend, with its page for every path which is no file.

    The router of the frontend uses the history mode, so `/report` and
    `/examples/<id>` are addresses of the page and no files. Below `assets/`
    every path is a file, and a missing one stays a 404: the page in the place
    of a script is an error which says nothing.
    """

    async def get_response(self, path: str, scope: Scope) -> Response:
        """The file at the path, else the page."""
        try:
            response = await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code != 404 or path.startswith("assets"):
                raise
            return await super().get_response("index.html", scope)
        return response


class LocalApp:
    """The ASGI application of the local server."""

    def __init__(self, port: int, secret: str, frontend: Path) -> None:
        """Create the application.

        Args:
            port: the port the server listens on, which is part of its origin.
            secret: what a request which acts on the machine has to know.
            frontend: the directory of the built frontend.
        """
        self.port = port
        self.secret = secret
        self.hosts = {f"{HOST}:{port}", f"localhost:{port}"}
        self.reports = ReportStore()
        self.last_request = time.monotonic()
        self.shutdown_requested = False
        self.local = self._local_api()
        self.frontend = FrontendFiles(directory=frontend, html=True)

    def idle_seconds(self) -> float:
        """The time since the last request."""
        return time.monotonic() - self.last_request

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Route a request to the local endpoints, the api or the frontend."""
        if scope["type"] == "lifespan":
            await self.local(scope, receive, send)
            return
        if scope["type"] != "http":
            return
        self.last_request = time.monotonic()
        if not self._allowed(scope):
            response = PlainTextResponse(
                "sbml4humans answers its own page only", status_code=403
            )
            await response(scope, receive, send)
            return

        path: str = scope["path"]
        if path.startswith("/api/local/"):
            await self.local(scope, receive, send)
        elif path.startswith("/api/") or path in API_PAGES:
            await api(scope, receive, send)
        else:
            try:
                await self.frontend(scope, receive, send)
            except StarletteHTTPException as exc:
                response = PlainTextResponse(exc.detail, status_code=exc.status_code)
                await response(scope, receive, send)

    def _allowed(self, scope: Scope) -> bool:
        """Whether the request names this server as its host and as its origin."""
        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope["headers"]
        }
        if headers.get("host") not in self.hosts:
            return False
        origin = headers.get("origin")
        return origin is None or origin in {f"http://{host}" for host in self.hosts}

    def _check_secret(self, secret: str | None) -> None:
        """Refuse a request which does not know the secret."""
        if secret is None or not secrets.compare_digest(secret, self.secret):
            raise HTTPException(status_code=403, detail="the secret is missing")

    def _local_api(self) -> FastAPI:
        """The endpoints below `/api/local/`, with the error contract of the api."""
        local = FastAPI(title="sbml4humans local", version=__version__)
        add_error_contract(local)

        @local.get("/api/local/ping")
        def ping() -> dict[str, str]:
            """Say which version is running, which is also a sign of life."""
            return {"version": __version__}

        @local.post("/api/local/reports")
        async def create_report(
            request: ReportRequest,
            secret: str | None = Header(default=None, alias=SECRET_HEADER),
        ) -> dict[str, str]:
            """Build the report of a path of this machine and keep it."""
            self._check_secret(secret)
            path = Path(request.path)
            if not path.is_absolute():
                raise ValueError(f"The path has to be absolute: '{path}'")
            if not path.is_file():
                raise FileNotFoundError(f"The file does not exist: '{path}'")
            # the path was chosen by the user of this machine, so the files next
            # to it which its external model definitions name are read as well
            report = await run_in_threadpool(report_for_path, path, trusted=True)
            token = self.reports.add(report)
            return {
                "token": token,
                "url": f"http://{HOST}:{self.port}/report?local={token}",
            }

        @local.get(
            "/api/local/reports/{token}",
            response_model=ReportResponse,
            response_model_by_alias=True,
        )
        def read_report(token: str) -> ReportResponse:
            """The report of a token."""
            try:
                return self.reports.get(token)
            except KeyError:
                raise ReportNotFoundError(token) from None

        @local.post("/api/local/shutdown")
        def shutdown(
            secret: str | None = Header(default=None, alias=SECRET_HEADER),
        ) -> dict[str, bool]:
            """End the server, which its watcher does within a second."""
            self._check_secret(secret)
            self.shutdown_requested = True
            return {"shutdown": True}

        return local


# -------------------------------------------------------------------------------------
# the server process
# -------------------------------------------------------------------------------------
async def _watch(
    server: uvicorn.Server, app: LocalApp, idle_timeout: float, state: Path
) -> None:
    """Say where the server is once it is up, and end it when nobody needs it."""
    while not server.started:
        await asyncio.sleep(0.05)
    write_state(
        state,
        {
            "port": app.port,
            "pid": os.getpid(),
            "secret": app.secret,
            "version": __version__,
        },
    )
    logger.info("sbml4humans serves on http://%s:%s", HOST, app.port)
    while not app.shutdown_requested and app.idle_seconds() < idle_timeout:
        await asyncio.sleep(WATCH_INTERVAL)
    logger.info(
        "sbml4humans ends: %s",
        "asked to" if app.shutdown_requested else f"idle for {idle_timeout} s",
    )
    server.should_exit = True


def serve(port: int, secret: str, idle_timeout: float = IDLE_TIMEOUT) -> None:
    """Run the local server until it is shut down or idle for `idle_timeout`.

    Raises:
        FrontendMissingError: if the package holds no build of the frontend.
    """
    app = LocalApp(port=port, secret=secret, frontend=frontend_dir())
    server = uvicorn.Server(uvicorn.Config(app, host=HOST, port=port))
    state = state_file()

    async def run() -> None:
        """Serve with the watcher next to the server."""
        watcher = asyncio.create_task(_watch(server, app, idle_timeout, state))
        try:
            await server.serve()
        finally:
            watcher.cancel()

    try:
        asyncio.run(run())
    finally:
        # only the file of this server: a newer one may have replaced it
        current = read_state(state)
        if current is not None and current.get("pid") == os.getpid():
            state.unlink(missing_ok=True)


def main() -> None:
    """Run the server process `show` starts."""
    parser = argparse.ArgumentParser(
        prog="python -m sbml4humans.local",
        description="The local server of sbml4humans, which `sbml4humans.show` starts.",
    )
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--idle-timeout", type=float, default=IDLE_TIMEOUT)
    arguments = parser.parse_args()
    secret = os.environ.get(SECRET_VARIABLE)
    if not secret:
        parser.error(f"the secret is expected in the environment as {SECRET_VARIABLE}")
    serve(arguments.port, secret, arguments.idle_timeout)


if __name__ == "__main__":
    main()
