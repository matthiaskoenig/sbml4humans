"""Example models served by the api.

The examples are the models of `sbml4humans.resources`: the example models and
the first curated biomodels. They are read once on first use. The example of a
biomodel is the main SBML entry of its archive, which is extracted for the
time its metadata or its report is read and removed afterwards.
"""

import logging
from functools import lru_cache
from pathlib import Path

import libsbml
from pydantic import BaseModel, Field, FilePath
from pymetadata.omex import ManifestEntry, Omex

from sbml4humans.model import ReportResponse
from sbml4humans.report import report_for_path
from sbml4humans.resources import (
    API_EXAMPLES_MODEL,
    API_EXAMPLES_OMEX,
    BIOMODELS_CURATED_PATH,
)
from sbml4humans.sbml import package_plugins, read_sbml


logger = logging.getLogger(__name__)

# number of curated biomodels served as examples (BIOMD0000000001, ...)
BIOMODELS_COUNT = 49
# length up to which the description of an archive names its SBML entries
# instead of counting them alone, in characters
DESCRIPTION_NAMES_LENGTH = 60


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
    """Read the metadata of an example from its SBML file.

    Args:
        sbml_path: path to the SBML file.
        example_id: id of the example, derived from the model id by default.

    Raises:
        ValueError: if the file contains no model.
    """
    doc: libsbml.SBMLDocument = read_sbml(sbml_path)
    model: libsbml.Model | None = doc.getModel()
    if model is None:
        raise ValueError(f"Model could not be read for '{sbml_path}'")

    model_id = model.getId() if model.isSetId() else sbml_path.stem
    packages = [plugin.getPrefix() for plugin in package_plugins(doc)]

    return ExampleMetaData(
        id=example_id or f"{model_id} ({sbml_path.name})",
        file=sbml_path,
        name=model.getName() if model.isSetName() else None,
        description=model.getNotesString() if model.isSetNotes() else None,
        packages=packages,
    )


def example_from_omex(omex_path: Path) -> ExampleMetaData:
    """Read the metadata of an example from its COMBINE archive."""
    with Omex.from_omex(omex_path) as omex:
        description = omex_description(omex)
    return ExampleMetaData(
        id=omex_path.stem,
        file=omex_path,
        name=omex_path.stem,
        description=description,
        packages=["OMEX"],
    )


def omex_description(omex: Omex) -> str:
    """Describe the content of an archive in one sentence.

    The number of SBML entries is what the description of an example says
    about an archive, because the report holds one report per SBML entry. The
    entries are named as well as long as their names stay short enough for the
    sentence to be read at a glance.
    """
    entries = omex.entries_by_format(format_key="sbml")
    if not entries:
        return "COMBINE archive without an SBML entry"

    count = f"{len(entries)} SBML {'entry' if len(entries) == 1 else 'entries'}"
    names = ", ".join(Path(entry.location).name for entry in entries)
    if len(names) > DESCRIPTION_NAMES_LENGTH:
        return f"COMBINE archive with {count}"
    return f"COMBINE archive with {count}: {names}"


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

        with Omex.from_omex(omex_path) as omex:
            location = main_sbml_entry(omex).location
            example = example_from_sbml(omex.get_path(location), example_id=biomodel_id)
        examples.append(
            example.model_copy(update={"file": omex_path, "location": location})
        )

    return examples


def main_sbml_entry(omex: Omex) -> ManifestEntry:
    """Get the main SBML entry of an archive.

    This is the master entry if one of the SBML entries is the master,
    otherwise the first SBML entry by location (the order of the entries in
    an archive is not guaranteed).

    Raises:
        ValueError: if the archive contains no SBML entry.
    """
    entries = omex.entries_by_format(format_key="sbml")
    if not entries:
        raise ValueError("The archive contains no SBML entry")
    return next(
        (entry for entry in entries if entry.master),
        min(entries, key=lambda entry: entry.location),
    )


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
    """Create the report of an example.

    The example is read trusted: its files were chosen by the operator, so the
    files next to it which its external model definitions name are read as
    well, for an entry of an archive the other entries of the archive.
    """
    if example.location is None:
        return report_for_path(example.file, trusted=True)
    with Omex.from_omex(example.file) as omex:
        return report_for_path(omex.get_path(example.location), trusted=True)
