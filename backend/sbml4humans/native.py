"""Optional native reports and validation within the application's worker budgets.

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

from sbml4humans.limits import ContentLimits, ContentTooLargeError


logger = logging.getLogger(__name__)
_ODE_ERROR = re.compile(rb'"odeError":(?!null)')


class NativeValidation(Protocol):
    """A prepared source owned by Rust inside a bounded worker."""

    locations: list[str]

    def entry_json(self, location: str) -> bytes:
        """Check one entry, applying the native comp expansion gate."""
        ...


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
    ODE_SOURCE_CONTRACT: str
    SOURCE_PATH_CONTRACT: str
    VALIDATION_SOURCE_CONTRACT: str

    def source_path_json(
        self,
        path: str,
        *,
        trusted: bool,
        max_expanded_elements: int,
        limits: dict[str, int],
    ) -> bytes:
        """Read a source and construct serialized reports entirely in Rust."""
        ...

    def validation_source(
        self,
        path: str,
        *,
        trusted: bool,
        max_expanded_elements: int,
        limits: dict[str, int],
    ) -> NativeValidation:
        """Admit sources, derive keys and own native validation entirely in Rust."""
        ...

    def ode_path_json(
        self,
        path: str,
        format: str,
        *,
        location: str | None,
        trusted: bool,
        simulator: bool,
        max_expanded_elements: int,
        limits: dict[str, int],
    ) -> bytes:
        """Select and export one admitted model with the shared Rust generator."""
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
        or getattr(core, "SOURCE_PATH_CONTRACT", None) != "source-path/1"
    ):
        if selected == "auto":
            return None
        raise RuntimeError(
            "The installed Rust parser does not support the complete source-path/1 contract."
        )
    return core


def _source_limits(limits: ContentLimits) -> dict[str, int]:
    return {
        "maxContentSize": limits.max_content_size,
        "maxArchiveEntries": limits.max_archive_entries,
        "maxCompressionRatio": limits.max_compression_ratio,
        "compressionRatioMinSize": limits.compression_ratio_min_size,
    }


def validation_source(
    path: Path,
    limits: ContentLimits,
    budget: int,
    parser: Parser | None = None,
    *,
    trusted: bool = False,
) -> NativeValidation | None:
    """Prepare and validate through Rust, retaining optional compatibility mode."""
    selected = preference() if parser is None else parser
    core = _reader(selected)
    if core is None:
        return None
    if getattr(core, "VALIDATION_SOURCE_CONTRACT", None) != "validation-source/1":
        if selected == "auto":
            return None
        raise RuntimeError(
            "The installed Rust parser has no native source validator; "
            "install sbml4humans-core built with the validation feature."
        )
    try:
        return core.validation_source(
            str(path),
            trusted=trusted,
            max_expanded_elements=budget,
            limits=_source_limits(limits),
        )
    except ValueError as error:
        if getattr(error, "kind", None) == "refused":
            raise ContentTooLargeError(str(error)) from error
        raise


def report_json(
    path: Path,
    limits: ContentLimits,
    budget: int,
    parser: Parser | None = None,
    *,
    trusted: bool = False,
) -> bytes | None:
    """Read and report a path through Rust without per-element Python objects.

    Native failures reach the API error contract and never retry through Python.
    Trusted paths may admit companions only inside the selected directory.
    """
    core = _reader(parser)
    if core is None:
        return None
    try:
        content = core.source_path_json(
            str(path),
            trusted=trusted,
            max_expanded_elements=budget,
            limits=_source_limits(limits),
        )
    except ValueError as error:
        if getattr(error, "kind", None) == "refused":
            raise ContentTooLargeError(str(error)) from error
        raise
    _warn_ode_errors(content)
    return content


def ode_json(
    path: Path,
    format: str,
    location: str | None,
    limits: ContentLimits,
    budget: int,
    parser: Parser | None = None,
    *,
    trusted: bool = False,
    simulator: bool = False,
) -> bytes | None:
    """Read source entries and generate one ODE download without Python SBML objects."""
    selected = preference() if parser is None else parser
    core = _reader(selected)
    if core is None:
        return None
    if getattr(core, "ODE_SOURCE_CONTRACT", None) != "ode-source/1":
        if selected == "auto":
            return None
        raise RuntimeError("The installed Rust parser does not support ode-source/1.")
    try:
        return core.ode_path_json(
            str(path),
            format,
            location=location,
            trusted=trusted,
            simulator=simulator,
            max_expanded_elements=budget,
            limits=_source_limits(limits),
        )
    except ValueError as error:
        if getattr(error, "kind", None) == "refused":
            raise ContentTooLargeError(str(error)) from error
        raise
