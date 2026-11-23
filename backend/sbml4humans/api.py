"""The http api of sbml4humans.

Served with `uvicorn sbml4humans.api:api`.

Error contract: the frontend expects every response with status 200. Failures
are reported in the body as `{"errors": [message], "warnings": [], "info":
{...}}`, with the query parameters of the request as `info`. The traceback of a
failure is logged and stays on the server, unless the request states
`TRACEBACK_STATE` in its state, which the local server of `sbml4humans.show`
does, whose client is the user of the machine: then the traceback is the second
element of `errors`.

The body of a request is read up to `limits.MAX_CONTENT_SIZE`
(`BodyLimitMiddleware`), so that the size of an upload does not depend on the
proxy in front of the api, and the url of `GET /api/url` is downloaded from
public addresses alone (`download.py`).

Compression: a response of at least `GZIP_MINIMUM_SIZE` bytes is gzipped for a
client which accepts it. The report of an example is built once and kept
gzipped (`example_report_gzip`), so that a request for it is answered without
building or compressing it again.

The report of a source of a request and the validation of libsbml of it both
run in a child process bounded in time and memory (`isolation.py`), waited for
in a thread of a limiter of their own (`report_limiter`, `validation_limiter`),
so that they never hold a thread of the other endpoints, and cancelled when
their client disconnects (`run_report`, `run_validation`): the child is killed
and the admission freed at once. Work beyond the admission of the server is
busy: a report says so as an error of the contract, since the report is the
answer of its request, a validation as a `ValidationResponse` without entries,
since it is one part of a page the frontend shows without it. The ODE file of a
source of a request (`/api/ode/...`) reads that source through sbmlode and
libsbml as well, so it is admitted, run and cancelled by `run_report` with the
budget of the reports; the file of an example is written in the process of the
server, as its report is.

A report endpoint answers the gzipped JSON of its `ReportResponse`, which was
written once where the report was built: by pydantic in the child of a request
(`report.report_gzip_for_bytes`) or in the server for an example
(`example_report_gzip`). The JSON applies the configuration of the model:
camelCase keys and an infinite value or a value which is not a number as the
strings `"Infinity"`, `"-Infinity"` and `"NaN"`. `report_response` sends those
bytes to a client which accepts gzip and the JSON to one which does not.

The validation of a source is answered by endpoints of its own below
`/api/validation/`, which take the sources of the report endpoints with their
limits and their trust and answer a `ValidationResponse`, so that a report is
shown before its validation has ended. The validation of an example is kept
(`example_validations`) unless a limit ended it.
"""

import asyncio
import contextlib
import gzip
import logging
import threading
import traceback
from collections import OrderedDict
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from datetime import datetime
from functools import lru_cache
from typing import Annotated, Any

from anyio import CapacityLimiter, create_task_group, to_thread
from anyio.lowlevel import RunVar
from fastapi import Depends, FastAPI, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from starlette.middleware.base import RequestResponseEndpoint
from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from sbml4humans import __version__, isolation, limits
from sbml4humans.annotations import (
    CHEBI_ID,
    MAX_RESOURCE_LENGTH,
    AnnotationResource,
    ChebiQuery,
    resource_cache,
)
from sbml4humans.download import download
from sbml4humans.examples import (
    ExampleMetaData,
    load_examples,
    ode_for_example,
    report_for_example,
    validation_for_example,
)
from sbml4humans.limits import ContentTooLargeError, format_size
from sbml4humans.model import ReportResponse, ValidationResponse
from sbml4humans.report import (
    REPORT_GZIP_LEVEL as GZIP_LEVEL,
)
from sbml4humans.report import (
    OdeFile,
    ReportInterruptedError,
    Work,
    ode_for_bytes,
    report_gzip_for_bytes,
    validation_for_bytes,
)
from sbml4humans.uploads import CLEANUP_INTERVAL, UploadStore, upload_store


logger = logging.getLogger(__name__)

# the key of the state of a request whose error response carries the traceback
TRACEBACK_STATE = "sbml4humans_traceback"

# responses below this size are sent as they are, in bytes
GZIP_MINIMUM_SIZE = 1000
# the number of example reports kept gzipped, the largest (Recon3D) is 5 MB
EXAMPLE_CACHE_SIZE = 32


class ExampleNotFoundError(KeyError):
    """Raised for an unknown example id."""

    def __init__(self, example_id: str) -> None:
        """Create the error for the unknown example id."""
        super().__init__(example_id)
        self.example_id = example_id

    def __str__(self) -> str:
        """Message for the frontend."""
        return f"example for id does not exist '{self.example_id}'"


async def remove_expired_uploads(store: UploadStore) -> None:
    """Delete the expired uploads now and every `CLEANUP_INTERVAL`.

    A failure of one cleanup is logged, the next one runs: the loop ends only with
    the api.
    """
    while True:
        try:
            await asyncio.to_thread(store.remove_expired)
        except Exception:
            logger.exception("The cleanup of the expired uploads failed")
        await asyncio.sleep(CLEANUP_INTERVAL)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    """Read the examples on startup, and delete the expired uploads while the api runs.

    The examples are read and the forkserver of the validations is started on
    startup, so that the first requests are fast.
    """
    load_examples()
    isolation.start_forkserver()
    cleanup = asyncio.create_task(remove_expired_uploads(upload_store()))
    try:
        yield
    finally:
        cleanup.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cleanup


api = FastAPI(
    title="sbml4humans",
    description="sbml4humans backend api",
    version=__version__,
    terms_of_service="https://github.com/matthiaskoenig/sbml4humans/blob/main/frontend/privacy_notice.md",
    contact={
        "name": "Matthias König",
        "url": "https://livermetabolism.com",
        "email": "konigmatt@googlemail.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/license/MIT",
    },
    openapi_tags=[
        {"name": "examples", "description": "Query examples."},
        {"name": "reports", "description": "Create report data."},
        {
            "name": "validation",
            "description": "Validate the source of a report with libsbml.",
        },
        {"name": "metadata", "description": "Query metadata."},
    ],
    lifespan=lifespan,
)


def error_response(request: Request, exc: Exception) -> JSONResponse:
    """Report an exception to the frontend in the body of a 200 response.

    The traceback is logged, and sent along only for a request which states
    `TRACEBACK_STATE`.
    """
    logger.error(
        "%s %s failed: %s",
        request.method,
        request.url.path,
        exc,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    errors = [str(exc)]
    if getattr(request.state, TRACEBACK_STATE, False):
        errors.append("".join(traceback.format_exception(exc)))
    return JSONResponse(
        status_code=200,
        content={
            "errors": errors,
            "warnings": [],
            "info": dict(request.query_params),
        },
    )


class BodyLimitMiddleware:
    """Refuse a request whose body is larger than `limits.MAX_CONTENT_SIZE`.

    A declared `Content-Length` beyond the limit is refused before the body is
    read. A body without length is counted while it is read, and the request
    fails at the first byte beyond the limit. FastAPI answers a failure while it
    parses a form with a 400 of its own, so the response of a request which
    went beyond the limit is replaced by the error response of the contract.
    """

    def __init__(self, app: ASGIApp) -> None:
        """Wrap the app."""
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Pass the request on with a receive which counts its body."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        limit = limits.MAX_CONTENT_SIZE
        too_large = ContentTooLargeError(
            f"The content is larger than the limit of {format_size(limit)}."
        )
        declared = request.headers.get("content-length", "")
        if declared.isdigit() and int(declared) > limit:
            await error_response(request, too_large)(scope, receive, send)
            return

        received = 0
        exceeded = False
        replaced = False

        async def counting_receive() -> Message:
            """Receive the body, up to the limit."""
            nonlocal received, exceeded
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    exceeded = True
                    raise too_large
            return message

        async def replacing_send(message: Message) -> None:
            """Send the response, the error response once the limit was exceeded."""
            nonlocal replaced
            if replaced:
                return
            if exceeded and message["type"] == "http.response.start":
                replaced = True
                await error_response(request, too_large)(scope, receive, send)
                return
            await send(message)

        await self.app(scope, counting_receive, replacing_send)


def add_error_contract(app: FastAPI) -> None:
    """Make every failure of the app an error response with status 200.

    Starlette's own exception handling runs in the outermost
    `ServerErrorMiddleware`, outside a `CORSMiddleware`, so its responses carry
    no CORS headers. The middleware of the contract has to be added before the
    `CORSMiddleware`, which makes it the innermost one (Starlette wraps
    middleware in the order they are added, most recent outermost), so the
    `CORSMiddleware` wraps it and adds its headers to the error response as it
    would to any other response.
    """

    @app.middleware("http")
    async def error_response_middleware(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Turn an exception of any endpoint into an error response."""
        try:
            return await call_next(request)
        except Exception as exc:
            return error_response(request, exc)

    # Safety net for exceptions raised outside the middleware stack above, for
    # example during request parsing before `error_response_middleware` runs.
    app.add_exception_handler(Exception, error_response)
    app.add_exception_handler(RequestValidationError, error_response)


def add_gzip(app: FastAPI) -> None:
    """Gzip the responses of the app for a client which accepts it.

    Added last, the middleware is the outermost one and compresses the error
    responses of the contract and the headers of CORS alike.
    """
    app.add_middleware(
        GZipMiddleware, minimum_size=GZIP_MINIMUM_SIZE, compresslevel=GZIP_LEVEL
    )


add_error_contract(api)
# inside the CORS middleware, so that its error responses carry the CORS headers
api.add_middleware(BodyLimitMiddleware)
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    # the frontend of another origin names a download of the ODE system after its file
    expose_headers=["Content-Disposition"],
    allow_headers=["*"],
)
add_gzip(api)


@api.get("/api/examples", tags=["examples"])
def examples() -> dict[str, list[dict[str, Any]]]:
    """List the metadata of all examples."""
    return {
        "examples": [
            example.model_dump(exclude={"file", "location"})
            for example in load_examples().values()
        ]
    }


async def report_response(request: Request, packed: bytes) -> Response:
    """The response of a report, whose JSON was written where it was built.

    The JSON of a report is gzipped where it was written, in the child of a
    request or in the cache of an example, which holds even the largest report
    in a few megabytes: a client which accepts gzip reads those bytes as they
    are, one which does not reads the JSON, which is expanded in a thread.

    Args:
        request: the request, whose `Accept-Encoding` decides the encoding.
        packed: the gzipped JSON of the `ReportResponse`.

    Returns:
        The response of the report.
    """
    if "gzip" in request.headers.get("accept-encoding", ""):
        return Response(
            packed,
            media_type="application/json",
            headers={"Content-Encoding": "gzip", "Vary": "Accept-Encoding"},
        )
    # the JSON of the largest report expands from a few megabytes to a hundred,
    # which the event loop may not do: it would stall every other request of
    # the worker, the watchers of the clients which left among them. The gzip
    # middleware names the header in `Vary` itself, and compresses a body of
    # that size in a thread of its own as well
    content = await run_in_threadpool(gzip.decompress, packed)
    return Response(content, media_type="application/json")


@api.get(
    "/api/examples/{example_id}",
    tags=["examples"],
    response_model=ReportResponse,
    response_model_by_alias=True,
)
async def example(example_id: str, request: Request) -> Response:
    """The report data of an example, built on the first request for it.

    The report of the first request for an example is built in a thread: it is
    read in the process of the server, since an example is trusted, and takes
    as long as the report of a request does.
    """
    packed = await run_in_threadpool(example_report_gzip, example_id)
    return await report_response(request, packed)


@lru_cache(maxsize=EXAMPLE_CACHE_SIZE)
def example_report_gzip(example_id: str) -> bytes:
    """The gzipped JSON of the report of an example.

    An example does not change while the server runs, so its report is built
    once. The JSON is the one a report endpoint writes, kept gzipped, which
    holds even the largest example in a few megabytes. The uid of the report is
    the one of its first request.

    Raises:
        ExampleNotFoundError: if there is no example of the id.
    """
    example: ExampleMetaData | None = load_examples().get(example_id)
    if example is None:
        raise ExampleNotFoundError(example_id)
    report = report_for_example(example)
    return gzip.compress(
        report.model_dump_json(by_alias=True).encode(), compresslevel=GZIP_LEVEL
    )


# the threads of the isolated work of a kind, one per admitted run, apart from
# the threadpool of the other endpoints, which a run waiting for its child
# would otherwise hold
_REPORT_LIMITER: RunVar[tuple[int, CapacityLimiter]] = RunVar("reports")
_VALIDATION_LIMITER: RunVar[tuple[int, CapacityLimiter]] = RunVar("validations")


def _limiter(
    run_var: RunVar[tuple[int, CapacityLimiter]], budget: isolation.Budget
) -> CapacityLimiter:
    """The limiter of the threads of a budget of this event loop.

    The limiter holds as many threads as the server admits runs of the budget,
    and is replaced when that number changed, which a test lowers.

    Args:
        run_var: where the limiter of this event loop is kept.
        budget: the budget whose runs wait in the threads.

    Returns:
        The limiter of the threads of the budget.
    """
    capacity = isolation.admission_capacity(budget)
    try:
        total, limiter = run_var.get()
    except LookupError:
        total, limiter = -1, None
    if limiter is None or total != capacity:
        limiter = CapacityLimiter(capacity)
        run_var.set((capacity, limiter))
    return limiter


def report_limiter() -> CapacityLimiter:
    """The limiter of the threads of the reports of this event loop."""
    return _limiter(_REPORT_LIMITER, isolation.REPORT_BUDGET)


def validation_limiter() -> CapacityLimiter:
    """The limiter of the threads of the validations of this event loop."""
    return _limiter(_VALIDATION_LIMITER, isolation.VALIDATION_BUDGET)


async def _run_admitted[R](
    request: Request,
    limiter: CapacityLimiter,
    function: Callable[..., R],
    *args: Any,
) -> R:
    """Run the admitted work of a request in a thread of its limiter.

    The work is cancelled when the client of the request disconnects: it stops
    waiting for a child or its child is killed, and the thread and the
    admission are free again.

    Args:
        request: the request whose client is watched.
        limiter: the limiter of the threads of its kind of work.
        function: the work, which runs in a thread of the limiter.
        args: the arguments of the function.

    Returns:
        What the function returned.

    Raises:
        isolation.IsolatedRunCancelledError: if the client disconnected.
        Exception: the exception the function raised.
    """
    cancel = threading.Event()
    done: list[R] = []
    failure: Exception | None = None
    async with create_task_group() as group:
        group.start_soon(_cancel_on_disconnect, request, cancel)
        try:
            done.append(
                await to_thread.run_sync(
                    isolation.run_cancellable, cancel, function, *args, limiter=limiter
                )
            )
        except Exception as exc:
            # raised outside of the task group, which would wrap it in an
            # exception group
            failure = exc
        finally:
            group.cancel_scope.cancel()
    if failure is not None:
        raise failure
    return done[0]


async def _cancel_on_disconnect(request: Request, cancel: threading.Event) -> None:
    """Set `cancel` when the client of the request disconnects.

    The body of the request has been read, so the next message of the
    connection is its end.
    """
    while (await request.receive())["type"] != "http.disconnect":
        pass
    cancel.set()


async def run_report[R](
    request: Request,
    function: Callable[..., R],
    *args: Any,
    work: Work = "report",
) -> R:
    """Build a report in a thread of the reports, if the server admits it.

    A report beyond the admission of `isolation.REPORT_BUDGET` is an error of
    the contract, which says that the server is busy: the report is the answer
    of its request, where a busy validation is one part of a page the frontend
    shows without it. A report whose client disconnects is busy as well, which
    nobody reads. The ODE file of a source is admitted as a report and shares
    the budget of the reports, its child reads the same content; it says `work`,
    so that its client reads of the file it asked for and not of a report.

    Args:
        request: the request of the report, whose client is watched.
        function: what builds the report, which runs in a thread.
        args: the arguments of the function.
        work: what the client asked for, of the error of a busy server.

    Returns:
        What the function built: the gzipped JSON of a `ReportResponse` or the
        `OdeFile` of its source.

    Raises:
        ReportInterruptedError: if the server is busy or the client left.
        Exception: the exception the function raised.
    """
    with isolation.admission(isolation.REPORT_BUDGET) as admitted:
        if not admitted:
            logger.warning("the %s of a request was refused, the server is busy", work)
            raise ReportInterruptedError("busy", work)
        try:
            return await _run_admitted(request, report_limiter(), function, *args)
        except isolation.IsolatedRunCancelledError as exc:
            logger.info("the %s of a request was cancelled, its client left", work)
            raise ReportInterruptedError("busy", work) from exc


async def run_validation(
    request: Request, function: Callable[..., ValidationResponse], *args: Any
) -> ValidationResponse:
    """Validate in a thread of the validations, if the server admits it.

    A validation beyond the admission of `isolation.VALIDATION_BUDGET` is
    answered at once as busy, without an entry, and never holds a thread of the
    other endpoints. A validation whose client disconnects answers busy as
    well, which nobody reads.

    Args:
        request: the request of the validation, whose client is watched.
        function: what validates the source, which runs in a thread.
        args: the arguments of the function.

    Returns:
        The validation, busy where the server had no room for it.

    Raises:
        Exception: the exception the function raised.
    """
    with isolation.admission(isolation.VALIDATION_BUDGET) as admitted:
        if not admitted:
            logger.warning("a validation was refused, the server is busy")
            return ValidationResponse(skipped="busy")
        try:
            return await _run_admitted(request, validation_limiter(), function, *args)
        except isolation.IsolatedRunCancelledError:
            logger.info("a validation was cancelled, its client disconnected")
            return ValidationResponse(skipped="busy")


@api.post(
    "/api/file",
    tags=["reports"],
    response_model=ReportResponse,
    response_model_by_alias=True,
)
async def report_from_file(source: UploadFile, request: Request) -> Response:
    """Create the report data of an uploaded SBML file or COMBINE archive."""
    content = await source.read()
    packed = await run_report(request, report_gzip_for_bytes, content)
    return await report_response(request, packed)


@api.get(
    "/api/url",
    tags=["reports"],
    response_model=ReportResponse,
    response_model_by_alias=True,
)
async def report_from_url(url: str, request: Request) -> Response:
    """Create the report data of an SBML file or COMBINE archive behind a url.

    The report is admitted before the download, a busy server downloads
    nothing.
    """
    packed = await run_report(request, report_of_download, url)
    return await report_response(request, packed)


def report_of_download(url: str) -> bytes:
    """Download the source behind a url and report it, in the thread of the report.

    The download is not cancelled when the client leaves, as the one of
    `validation_of_download` is not: the cancellation reaches the child of the
    report, which is started once the source is there.
    """
    return report_gzip_for_bytes(download(url))


@api.post(
    "/api/content",
    tags=["reports"],
    response_model=ReportResponse,
    response_model_by_alias=True,
)
async def report_from_content(request: Request) -> Response:
    """Create the report data of the SBML content in the request body."""
    content = await request.body()
    packed = await run_report(request, report_gzip_for_bytes, content)
    return await report_response(request, packed)


class UploadResponse(BaseModel):
    """The id of an upload, whose report is at `/report?upload=<id>`, and when it expires."""

    id: str
    expires: datetime


@api.post("/api/upload", tags=["reports"], response_model=UploadResponse)
async def upload(
    source: UploadFile,
    store: Annotated[UploadStore, Depends(upload_store)],
    request: Request,
) -> UploadResponse:
    """Keep an SBML file or COMBINE archive for 24 hours, for the report of its id.

    The upload is reported once in a child like every report of a request, so
    content which cannot be reported is an error and not kept; its report is
    built again for every request for it. Its size is limited by
    `BodyLimitMiddleware` like every body.
    """
    content = await source.read()
    await run_report(request, report_gzip_for_bytes, content)
    stored = await run_in_threadpool(store.put, content)
    return UploadResponse(id=stored.id, expires=stored.expires)


@api.get(
    "/api/upload/{upload_id}",
    tags=["reports"],
    response_model=ReportResponse,
    response_model_by_alias=True,
)
async def report_from_upload(
    upload_id: str,
    store: Annotated[UploadStore, Depends(upload_store)],
    request: Request,
) -> Response:
    """Create the report data of an upload."""
    content = await run_in_threadpool(store.get, upload_id)
    packed = await run_report(request, report_gzip_for_bytes, content)
    return await report_response(request, packed)


class ExampleValidations:
    """The validations of the examples, the most recent `EXAMPLE_CACHE_SIZE`.

    An example does not change while the server runs, so its validation is kept
    unless the timeout, the memory limit or a busy server ended it, which
    depends on the load of the server and is tried again on the next request.
    """

    def __init__(self, limit: int = EXAMPLE_CACHE_SIZE) -> None:
        """Create an empty store."""
        self.limit = limit
        self._lock = threading.Lock()
        self._validations: OrderedDict[str, ValidationResponse] = OrderedDict()

    def get(self, example_id: str) -> ValidationResponse | None:
        """The kept validation of an example, None without one."""
        with self._lock:
            validation = self._validations.get(example_id)
            if validation is not None:
                self._validations.move_to_end(example_id)
            return validation

    def put(self, example_id: str, validation: ValidationResponse) -> None:
        """Keep the validation of an example, unless a limit ended it."""
        if validation.skipped is not None:
            return
        with self._lock:
            self._validations[example_id] = validation
            while len(self._validations) > self.limit:
                self._validations.popitem(last=False)

    def clear(self) -> None:
        """Forget every validation."""
        with self._lock:
            self._validations.clear()


example_validations = ExampleValidations()


@api.get(
    "/api/validation/examples/{example_id}",
    tags=["validation"],
    response_model=ValidationResponse,
    response_model_by_alias=True,
)
async def validation_of_example(
    example_id: str, request: Request
) -> ValidationResponse:
    """The validation of an example, kept after the first request for it."""
    validation = example_validations.get(example_id)
    if validation is not None:
        return validation
    example: ExampleMetaData | None = load_examples().get(example_id)
    if example is None:
        raise ExampleNotFoundError(example_id)
    validation = await run_validation(request, validation_for_example, example)
    example_validations.put(example_id, validation)
    return validation


@api.post(
    "/api/validation/file",
    tags=["validation"],
    response_model=ValidationResponse,
    response_model_by_alias=True,
)
async def validation_of_file(
    source: UploadFile, request: Request
) -> ValidationResponse:
    """Validate an uploaded SBML file or COMBINE archive."""
    return await run_validation(request, validation_for_bytes, await source.read())


@api.get(
    "/api/validation/url",
    tags=["validation"],
    response_model=ValidationResponse,
    response_model_by_alias=True,
)
async def validation_of_url(url: str, request: Request) -> ValidationResponse:
    """Validate an SBML file or COMBINE archive behind a url.

    The validation is admitted before the download, a busy server downloads
    nothing.
    """
    return await run_validation(request, validation_of_download, url)


def validation_of_download(url: str) -> ValidationResponse:
    """Download the source behind a url and validate it."""
    return validation_for_bytes(download(url))


@api.post(
    "/api/validation/content",
    tags=["validation"],
    response_model=ValidationResponse,
    response_model_by_alias=True,
)
async def validation_of_content(request: Request) -> ValidationResponse:
    """Validate the SBML content in the request body."""
    return await run_validation(request, validation_for_bytes, await request.body())


@api.get(
    "/api/validation/upload/{upload_id}",
    tags=["validation"],
    response_model=ValidationResponse,
    response_model_by_alias=True,
)
async def validation_of_upload(
    upload_id: str,
    store: Annotated[UploadStore, Depends(upload_store)],
    request: Request,
) -> ValidationResponse:
    """Validate an upload."""
    content = await run_in_threadpool(store.get, upload_id)
    return await run_validation(request, validation_for_bytes, content)


def ode_response(ode: OdeFile) -> Response:
    """The ODE system of a model as a file to download."""
    return Response(
        content=ode.content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{ode.filename}"'},
    )


@api.get(
    "/api/ode/examples/{example_id}",
    tags=["ode"],
    response_class=PlainTextResponse,
)
def ode_of_example(example_id: str, format: str) -> Response:
    """The ODE system of an example in a format of sbmlode, as a file."""
    example: ExampleMetaData | None = load_examples().get(example_id)
    if example is None:
        raise ExampleNotFoundError(example_id)
    return ode_response(ode_for_example(example, format))


@api.post("/api/ode/file", tags=["ode"], response_class=PlainTextResponse)
async def ode_of_file(
    source: UploadFile,
    format: str,
    request: Request,
    location: str | None = None,
) -> Response:
    """The ODE system of an uploaded SBML file or COMBINE archive, as a file."""
    content = await source.read()
    ode = await run_report(
        request, ode_for_bytes, content, format, location, work="ode system"
    )
    return ode_response(ode)


@api.get("/api/ode/url", tags=["ode"], response_class=PlainTextResponse)
async def ode_of_url(
    url: str,
    format: str,
    request: Request,
    location: str | None = None,
) -> Response:
    """The ODE system of an SBML file or COMBINE archive behind a url, as a file.

    The file is admitted before the download, a busy server downloads nothing.
    """
    ode = await run_report(
        request, ode_of_download, url, format, location, work="ode system"
    )
    return ode_response(ode)


def ode_of_download(url: str, fmt: str, location: str | None) -> OdeFile:
    """Download the source behind a url and write its ODE system, in its own thread.

    The download is not cancelled when the client leaves, as the one of
    `report_of_download` is not: the cancellation reaches the child, which is
    started once the source is there.
    """
    return ode_for_bytes(download(url), fmt, location)


@api.post("/api/ode/content", tags=["ode"], response_class=PlainTextResponse)
async def ode_of_content(
    request: Request,
    format: str,
    location: str | None = None,
) -> Response:
    """The ODE system of the SBML content in the request body, as a file."""
    content = await request.body()
    ode = await run_report(
        request, ode_for_bytes, content, format, location, work="ode system"
    )
    return ode_response(ode)


@api.get("/api/ode/upload/{upload_id}", tags=["ode"], response_class=PlainTextResponse)
async def ode_of_upload(
    upload_id: str,
    store: Annotated[UploadStore, Depends(upload_store)],
    format: str,
    request: Request,
    location: str | None = None,
) -> Response:
    """The ODE system of an upload, as a file."""
    content = await run_in_threadpool(store.get, upload_id)
    ode = await run_report(
        request, ode_for_bytes, content, format, location, work="ode system"
    )
    return ode_response(ode)


@api.get(
    "/api/annotation_resource",
    tags=["metadata"],
    response_model=AnnotationResource,
)
def annotation_resource(resource: str, response: Response) -> AnnotationResource:
    """Resolve the information of an annotation resource (url or MIRIAM urn).

    A resolved resource may stay in the browser for a day, one with warnings (a
    term the web services do not know) ten minutes, like in `ResourceCache`; one
    whose web service failed may not, so that the next look at it asks again.
    """
    if len(resource) > MAX_RESOURCE_LENGTH:
        raise ValueError(
            f"The resource is longer than {MAX_RESOURCE_LENGTH} characters."
        )
    value = resource_cache().get(resource)
    if value.errors:
        response.headers["Cache-Control"] = "no-store"
    elif value.warnings:
        response.headers["Cache-Control"] = "public, max-age=600"
    else:
        response.headers["Cache-Control"] = "public, max-age=86400"
    return value


# the structure is an image: the frontend shows it in an `<img>`, the sandbox keeps
# a script of the svg from running where it is opened as a page of its own
STRUCTURE_HEADERS = {
    "Content-Security-Policy": "sandbox; default-src 'none'; style-src 'unsafe-inline'",
    "X-Content-Type-Options": "nosniff",
    "Cache-Control": "public, max-age=2592000",
}

# a 404 is not kept by the browser: the web service of ChEBI may be down only now
NOT_FOUND_HEADERS = {"Cache-Control": "no-store"}


@api.get(
    "/api/annotation_structure/{chebi}", tags=["metadata"], response_class=Response
)
def annotation_structure(chebi: str) -> Response:
    """The structure of a ChEBI compound as svg, 404 without one.

    The one answer of the api outside the error contract: it is an image and
    no JSON, and an image which is not there is a 404 the browser understands.
    """
    if not CHEBI_ID.fullmatch(chebi):
        return Response(status_code=404, headers=NOT_FOUND_HEADERS)
    svg = ChebiQuery.structure(chebi)
    if svg is None:
        return Response(status_code=404, headers=NOT_FOUND_HEADERS)
    return Response(content=svg, media_type="image/svg+xml", headers=STRUCTURE_HEADERS)
