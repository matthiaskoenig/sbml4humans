"""Example models served by the api.

The examples are the models of `sbml4humans.resources`: the example models and
the first curated biomodels. They are read once on first use. The example of a
biomodel is the main SBML entry of its archive, selected and read in Rust.
"""

import json
import logging
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, FilePath

from sbml4humans import native
from sbml4humans.model import ReportResponse, ValidationResponse
from sbml4humans.report import (
    OdeFile,
    ode_for_path,
    report_for_path,
    validation_for_path,
)
from sbml4humans.resources import (
    API_EXAMPLES_MODEL,
    API_EXAMPLES_OMEX,
    BIOMODELS_CURATED_PATH,
)


logger = logging.getLogger(__name__)

# number of curated biomodels served as examples (BIOMD0000000001, ...)
BIOMODELS_COUNT = 49


class ExampleMetaData(BaseModel):
    """Metadata of an example model.

    The `file` is the SBML file or the COMBINE archive of the example, and
    `location` the entry of the archive which is the example, if the example is
    one entry of it rather than the whole archive.
    """

    id: str
    file: FilePath
    location: str | None = None
    name: str | None = None
    description: str | None = None
    packages: list[str] = Field(default_factory=list)


def example_from_sbml(
    sbml_path: Path, example_id: str | None = None
) -> ExampleMetaData:
    """Read lightweight model metadata through the mandatory Rust runtime."""
    try:
        data = json.loads(
            native._reader().example_json(str(sbml_path), "sbml", example_id)
        )
    except ValueError as error:
        raise ValueError(
            f"Model could not be read for '{sbml_path}': {error}"
        ) from error
    return ExampleMetaData(file=sbml_path, **data)


def example_from_omex(omex_path: Path) -> ExampleMetaData:
    """Describe an archive through the shared Rust manifest reader."""
    data = json.loads(native._reader().example_json(str(omex_path), "archive", None))
    return ExampleMetaData(file=omex_path, **data)


def biomodel_examples(
    biomodels_dir: Path = BIOMODELS_CURATED_PATH, count: int = BIOMODELS_COUNT
) -> list[ExampleMetaData]:
    """Read the metadata of the first curated biomodels.

    Missing archives are skipped. The example of a biomodel is its main SBML
    model.
    """
    if not biomodels_dir.is_dir():
        logger.warning("No curated biomodels found in '%s'", biomodels_dir)
        return []

    examples: list[ExampleMetaData] = []
    for k in range(1, count + 1):
        biomodel_id = f"BIOMD{k:010d}"
        omex_path = biomodels_dir / f"{biomodel_id}.omex"
        if not omex_path.is_file():
            continue

        data = json.loads(
            native._reader().example_json(str(omex_path), "biomodel", biomodel_id)
        )
        examples.append(ExampleMetaData(file=omex_path, **data))

    return examples


@lru_cache(maxsize=1)
def load_examples() -> dict[str, ExampleMetaData]:
    """Read the metadata of all examples, keyed by example id.

    The first example wins for duplicate ids.
    """
    examples: dict[str, ExampleMetaData] = {}
    for example in (
        [example_from_omex(p) for p in API_EXAMPLES_OMEX]
        + [example_from_sbml(p) for p in API_EXAMPLES_MODEL]
        + biomodel_examples()
    ):
        if example.id in examples:
            logger.warning("Duplicate example id '%s': %s", example.id, example.file)
            continue
        examples[example.id] = example

    logger.info("%s examples loaded", len(examples))
    return examples


def report_for_example(example: ExampleMetaData) -> ReportResponse:
    """Report the Rust-selected example without Python archive extraction."""
    return report_for_path(example.file, trusted=True, source_entry=example.location)


def ode_for_example(example: ExampleMetaData, fmt: str) -> OdeFile:
    """Export the example through the shared Rust source and ODE pipeline."""
    return ode_for_path(example.file, fmt, trusted=True, source_entry=example.location)


def validation_for_example(example: ExampleMetaData) -> ValidationResponse:
    """Validate the selected source entirely inside a bounded Rust worker."""
    return validation_for_path(
        example.file, trusted=True, source_entry=example.location
    )
