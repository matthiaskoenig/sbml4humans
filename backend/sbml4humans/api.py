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

A report endpoint returns its `ReportResponse` as it is. FastAPI takes an
instance of the response model without validating it again and writes its JSON
in one pass of pydantic, which applies the configuration of the model: camelCase
keys and an infinite value or a value which is not a number as the strings
`"Infinity"`, `"-Infinity"` and `"NaN"`.
"""

import gzip
import logging
import traceback
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint
from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from sbml4humans import __version__, limits
from sbml4humans.annotations import annotation_info
from sbml4humans.download import download
from sbml4humans.examples import ExampleMetaData, load_examples, report_for_example
from sbml4humans.limits import ContentTooLargeError, format_size
from sbml4humans.model import ReportResponse
from sbml4humans.report import report_for_bytes


logger = logging.getLogger(__name__)

# the key of the state of a request whose error response carries the traceback
TRACEBACK_STATE = "sbml4humans_traceback"

# responses below this size are sent as they are, in bytes
GZIP_MINIMUM_SIZE = 1000
# a moderate level: the reports compress about 20 fold already at this level,
# and a higher one costs time on every large report for a few percent
GZIP_LEVEL = 5
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


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Read the examples on startup, so that the first requests are fast."""
    load_examples()
    yield


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


@api.get(
    "/api/examples/{example_id}",
    tags=["examples"],
    response_model=ReportResponse,
    response_model_by_alias=True,
)
def example(example_id: str, request: Request) -> Response:
    """The report data of an example, built on the first request for it."""
    content = example_report_gzip(example_id)
    if "gzip" in request.headers.get("accept-encoding", ""):
        return Response(
            content,
            media_type="application/json",
            headers={"Content-Encoding": "gzip", "Vary": "Accept-Encoding"},
        )
    # the gzip middleware names the header in `Vary` itself
    return Response(gzip.decompress(content), media_type="application/json")


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


@api.post(
    "/api/file",
    tags=["reports"],
    response_model=ReportResponse,
    response_model_by_alias=True,
)
def report_from_file(source: UploadFile) -> ReportResponse:
    """Create the report data of an uploaded SBML file or COMBINE archive."""
    return report_for_bytes(source.file.read())


@api.get(
    "/api/url",
    tags=["reports"],
    response_model=ReportResponse,
    response_model_by_alias=True,
)
def report_from_url(url: str) -> ReportResponse:
    """Create the report data of an SBML file or COMBINE archive behind a url."""
    return report_for_bytes(download(url))


@api.post(
    "/api/content",
    tags=["reports"],
    response_model=ReportResponse,
    response_model_by_alias=True,
)
async def report_from_content(request: Request) -> ReportResponse:
    """Create the report data of the SBML content in the request body."""
    content = await request.body()
    return await run_in_threadpool(report_for_bytes, content)


@api.get("/api/annotation_resource", tags=["metadata"])
def annotation_resource(resource: str) -> dict[str, Any]:
    """Resolve the information of an annotation resource (url or MIRIAM urn)."""
    return annotation_info(resource)
