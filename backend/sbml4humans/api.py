"""The http api of sbml4humans.

Served with `uvicorn sbml4humans.api:api`.

Error contract: the frontend expects every response with status 200. Failures
are reported in the body as `{"errors": [message, traceback], "warnings": [],
"info": {...}}`, with the query parameters of the request as `info`.

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

import httpx
from fastapi import FastAPI, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint
from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import Response

from sbml4humans import __version__
from sbml4humans.annotations import annotation_info
from sbml4humans.examples import ExampleMetaData, load_examples
from sbml4humans.model import ReportResponse
from sbml4humans.report import report_for_bytes, report_for_path


logger = logging.getLogger(__name__)

DOWNLOAD_TIMEOUT = 60.0  # [s]

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
    """Report an exception to the frontend in the body of a 200 response."""
    logger.error("%s %s failed: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=200,
        content={
            "errors": [
                str(exc),
                "".join(traceback.format_exception(exc)),
            ],
            "warnings": [],
            "info": dict(request.query_params),
        },
    )


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
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
add_gzip(api)


def download(url: str) -> bytes:
    """Download the content behind url."""
    response = httpx.get(url, follow_redirects=True, timeout=DOWNLOAD_TIMEOUT)
    response.raise_for_status()
    return response.content


@api.get("/api/examples", tags=["examples"])
def examples() -> dict[str, list[dict[str, Any]]]:
    """List the metadata of all examples."""
    return {
        "examples": [
            example.model_dump(exclude={"file"}) for example in load_examples().values()
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
    report = report_for_path(example.file, trusted=True)
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
