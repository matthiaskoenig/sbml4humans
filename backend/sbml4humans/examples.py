"""Example models served by the api.

The examples are the models shipped with sbmlutils and, if available, the
first curated biomodels. They are read once on first use.
"""

import logging
from functools import lru_cache
from pathlib import Path

import libsbml
from pydantic import BaseModel, Field, FilePath
from pymetadata.omex import ManifestEntry, Omex
from sbmlutils.io import read_sbml
from sbmlutils.resources import (
    API_EXAMPLES_MODEL,
    API_EXAMPLES_OMEX,
    BIOMODELS_CURATED_PATH,
)


logger = logging.getLogger(__name__)

# number of curated biomodels served as examples (BIOMD0000000001, ...)
BIOMODELS_COUNT = 49


class ExampleMetaData(BaseModel):
    """Metadata of an example model."""

    id: str
    file: FilePath
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
    doc: libsbml.SBMLDocument = read_sbml(sbml_path, validate=False)
    model: libsbml.Model | None = doc.getModel()
    if model is None:
        raise ValueError(f"Model could not be read for '{sbml_path}'")

    model_id = model.getId() if model.isSetId() else sbml_path.stem
    packages = [doc.getPlugin(k).getPrefix() for k in range(doc.getNumPlugins())]

    return ExampleMetaData(
        id=example_id or f"{model_id} ({sbml_path.name})",
        file=sbml_path,
        name=model.getName() if model.isSetName() else None,
        description=model.getNotesString() if model.isSetNotes() else None,
        packages=packages,
    )


def example_from_omex(omex_path: Path) -> ExampleMetaData:
    """Read the metadata of an example from its COMBINE archive."""
    omex = Omex.from_omex(omex_path)
    return ExampleMetaData(
        id=omex_path.stem,
        file=omex_path,
        name=omex_path.stem,
        description=str(omex.manifest),
        packages=["OMEX"],
    )


def biomodel_examples(
    biomodels_dir: Path = BIOMODELS_CURATED_PATH, count: int = BIOMODELS_COUNT
) -> list[ExampleMetaData]:
    """Read the metadata of the first curated biomodels.

    The curated biomodels are not part of the sbmlutils distribution, missing
    archives are skipped. The example of a biomodel is its main SBML model.
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

        omex = Omex.from_omex(omex_path)
        sbml_path = omex.get_path(main_sbml_entry(omex).location)
        examples.append(example_from_sbml(sbml_path, example_id=biomodel_id))

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
