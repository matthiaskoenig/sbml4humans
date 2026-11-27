"""The mandatory, privately bundled Rust runtime used by every source operation."""

import importlib
import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Protocol, cast

from sbml4humans.limits import ContentLimits, ContentTooLargeError


logger = logging.getLogger(__name__)


class NativeValidation(Protocol):
    """An owned native source, kept inside its isolated worker."""

    locations: list[str]

    def entry_json(self, location: str) -> bytes:
        """Validate one entry and preserve completed worker results."""
        ...


class NativeCore(Protocol):
    """The versioned private host interface, without per-element Python objects."""

    SOURCE_REVISION: str
    HOST_CONTRACT: str
    VALIDATION_SOURCE_CONTRACT: str
    ODE_SOURCE_CONTRACT: str

    def report_path(
        self,
        path: str,
        *,
        trusted: bool,
        max_expanded_elements: int,
        limits: dict[str, int],
        gzip: bool,
        source_entry: str | None,
    ) -> tuple[bytes, list[str]]:
        """Construct and serialize a report directly into JSON or gzip."""
        ...

    def validation_source(
        self,
        path: str,
        *,
        trusted: bool,
        max_expanded_elements: int,
        limits: dict[str, int],
        source_entry: str | None,
    ) -> NativeValidation:
        """Prepare canonical positions, budgets and native documents in Rust."""
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
        source_entry: str | None,
    ) -> bytes:
        """Select an admitted model and call the shared ODE generator."""
        ...

    def example_json(self, path: str, mode: str, example_id: str | None) -> bytes:
        """Read example metadata without constructing its report."""
        ...

    def rule_json(self, code: int) -> bytes:
        """Resolve rule documentation from the native validator tables."""
        ...

    def rule_package(self, code: int) -> str:
        """Identify the specification a rule belongs to."""
        ...


@lru_cache(maxsize=1)
def _reader() -> NativeCore:
    """Load the exact bundled runtime, failing clearly before serving any model."""
    if os.environ.get("SBML4HUMANS_PARSER", "rust").strip().lower() != "rust":
        raise RuntimeError(
            "Rust is the only backend. Remove the obsolete SBML4HUMANS_PARSER setting."
        )
    try:
        core = cast(NativeCore, importlib.import_module("_sbml4humans_runtime"))
    except ImportError as error:
        raise RuntimeError(
            "The bundled Rust runtime is missing or cannot load. Reinstall sbml4humans, or run uv sync for a source checkout."
        ) from error
    pin = json.loads(Path(__file__).with_name("native-source.json").read_text())
    expected = {
        "SOURCE_REVISION": pin["revision"],
        "HOST_CONTRACT": "host/1",
        "VALIDATION_SOURCE_CONTRACT": "validation-source/1",
        "ODE_SOURCE_CONTRACT": "ode-source/1",
    }
    if any(getattr(core, key, None) != value for key, value in expected.items()):
        raise RuntimeError(
            "The bundled Rust runtime does not match this application. Reinstall or rebuild sbml4humans."
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
    *,
    trusted: bool = False,
    source_entry: str | None = None,
) -> NativeValidation:
    """Prepare validation through Rust under the worker's captured source limits."""
    try:
        return _reader().validation_source(
            str(path),
            trusted=trusted,
            max_expanded_elements=budget,
            limits=_source_limits(limits),
            source_entry=source_entry,
        )
    except ValueError as error:
        if getattr(error, "kind", None) == "refused":
            raise ContentTooLargeError(str(error)) from error
        raise


def report_json(
    path: Path,
    limits: ContentLimits,
    budget: int,
    *,
    trusted: bool = False,
    gzip: bool = False,
    source_entry: str | None = None,
) -> bytes:
    """Receive serialized Rust output and small diagnostics without decoding the report."""
    try:
        content, diagnostics = _reader().report_path(
            str(path),
            trusted=trusted,
            max_expanded_elements=budget,
            limits=_source_limits(limits),
            source_entry=source_entry,
            gzip=gzip,
        )
    except ValueError as error:
        if getattr(error, "kind", None) == "refused":
            raise ContentTooLargeError(str(error)) from error
        raise
    for message in diagnostics:
        logger.warning("The ODE system of the model could not be built: %s", message)
    return content


def ode_json(
    path: Path,
    format: str,
    location: str | None,
    limits: ContentLimits,
    budget: int,
    *,
    trusted: bool = False,
    simulator: bool = False,
    source_entry: str | None = None,
) -> bytes:
    """Generate one ODE download without Python SBML objects or format tables."""
    try:
        return _reader().ode_path_json(
            str(path),
            format,
            location=location,
            trusted=trusted,
            simulator=simulator,
            max_expanded_elements=budget,
            limits=_source_limits(limits),
            source_entry=source_entry,
        )
    except ValueError as error:
        if getattr(error, "kind", None) == "refused":
            raise ContentTooLargeError(str(error)) from error
        raise
