"""The optional native source reader, within the application's existing worker budgets.

The browser ships its own WASM build. Servers can install the matching native wheel
without making a Rust compiler a requirement of the pure Python application package.
"""

import importlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Literal, Protocol, cast

from sbml4humans.limits import ContentLimits, ContentTooLargeError, format_size


logger = logging.getLogger(__name__)
_ODE_ERROR = re.compile(rb'"odeError":(?!null)')


def _warn_ode_errors(content: bytes) -> None:
    """Log ordinary equation diagnostics without decoding successful large reports."""
    if _ODE_ERROR.search(content) is None:
        return
    response = json.loads(content)
    for entry in response.get("reports", {}).values():
        message = entry["report"].get("odeError")
        if message:
            logger.warning(
                "The ODE system of the model could not be built: %s",
                " ".join(message.split()),
            )


class NativeCore(Protocol):
    """The small, versioned interface needed from the native extension."""

    REPORT_CONTRACT: str
    SOURCE_CONTRACT: str

    def source_json(
        self, source: bytes, *, max_expanded_elements: int, limits: dict[str, int]
    ) -> bytes:
        """Build the complete response without constructing Python objects per element."""
        ...


Parser = Literal["auto", "rust", "python"]


def preference() -> Parser:
    """Capture the parser setting in the server, before an isolated job is sent."""
    value = os.environ.get("SBML4HUMANS_PARSER", "auto").strip().lower()
    if value not in {"auto", "rust", "python"}:
        raise ValueError("SBML4HUMANS_PARSER must be auto, rust or python.")
    return value


def _reader(parser: Parser | None = None) -> NativeCore | None:
    """Select the installed native reader, or the explicit Python compatibility path."""
    selected = preference() if parser is None else parser
    if selected == "python":
        return None
    try:
        core = cast(NativeCore, importlib.import_module("sbml4humans_core"))
    except ModuleNotFoundError as error:
        if error.name != "sbml4humans_core":
            raise
        if selected == "rust":
            raise RuntimeError(
                "The Rust parser was requested but sbml4humans-core is not installed."
            ) from error
        return None
    if (
        getattr(core, "REPORT_CONTRACT", None) != "report/1"
        or getattr(core, "SOURCE_CONTRACT", None) != "source/1"
    ):
        if selected == "auto":
            return None
        raise RuntimeError(
            "The installed Rust parser does not support the complete source/1 contract."
        )
    return core


def report_json(
    path: Path, limits: ContentLimits, budget: int, parser: Parser | None = None
) -> bytes | None:
    """Read an untrusted source through the optional Rust backend.

    Returns None only when the native backend was not selected. A native parse
    failure is returned to the caller, never retried through another parser.
    """
    core = _reader(parser)
    if core is None:
        return None
    with path.open("rb") as stream:
        source = stream.read(limits.max_content_size + 1)
    if len(source) > limits.max_content_size:
        raise ContentTooLargeError(
            f"The source is larger than the limit of {format_size(limits.max_content_size)}."
        )
    try:
        content = core.source_json(
            source,
            max_expanded_elements=budget,
            limits={
                "maxContentSize": limits.max_content_size,
                "maxArchiveEntries": limits.max_archive_entries,
                "maxCompressionRatio": limits.max_compression_ratio,
                "compressionRatioMinSize": limits.compression_ratio_min_size,
            },
        )
    except ValueError as error:
        if getattr(error, "kind", None) == "refused":
            raise ContentTooLargeError(str(error)) from error
        raise

    _warn_ode_errors(content)
    return content
