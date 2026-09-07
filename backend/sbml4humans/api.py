"""The http api of sbml4humans.

Run with `uvicorn sbml4humans.api:api`.

Error contract: the frontend expects every response with status 200. Failures
are reported in the body as `{"errors": [message, traceback], "warnings": [],
"info": {...}}`, with the query parameters of the request as `info`.
"""

import logging
import traceback
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
import uvicorn
from fastapi import FastAPI, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from sbml4humans import __version__
from sbml4humans.annotations import annotation_info
from sbml4humans.examples import ExampleMetaData, load_examples
from sbml4humans.report import report_for_bytes, report_for_path


logger = logging.getLogger(__name__)

DOWNLOAD_TIMEOUT = 60.0  # [s]


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

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
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


api.add_exception_handler(Exception, error_response)
api.add_exception_handler(RequestValidationError, error_response)


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


@api.get("/api/examples/{example_id}", tags=["examples"])
def example(example_id: str) -> dict[str, Any]:
    """Create the report data of an example."""
    example: ExampleMetaData | None = load_examples().get(example_id)
    if example is None:
        raise ExampleNotFoundError(example_id)
    return report_for_path(example.file)


@api.post("/api/file", tags=["reports"])
def report_from_file(source: UploadFile) -> dict[str, Any]:
    """Create the report data of an uploaded SBML file or COMBINE archive."""
    return report_for_bytes(source.file.read())


@api.get("/api/url", tags=["reports"])
def report_from_url(url: str) -> dict[str, Any]:
    """Create the report data of an SBML file or COMBINE archive behind a url."""
    return report_for_bytes(download(url))


@api.post("/api/content", tags=["reports"])
async def report_from_content(request: Request) -> dict[str, Any]:
    """Create the report data of the SBML content in the request body."""
    content = await request.body()
    return await run_in_threadpool(report_for_bytes, content)


@api.get("/api/annotation_resource", tags=["metadata"])
def annotation_resource(resource: str) -> dict[str, Any]:
    """Resolve the information of an annotation resource (url or MIRIAM urn)."""
    return annotation_info(resource)


def main() -> None:
    """Serve the api for development with reload."""
    uvicorn.run("sbml4humans.api:api", host="localhost", port=1444, reload=True)


if __name__ == "__main__":
    main()
