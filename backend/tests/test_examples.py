"""Tests of the example models."""

import shutil
from pathlib import Path

import libsbml
import pytest
from pymetadata.omex import Omex

from sbml4humans.examples import (
    ExampleMetaData,
    biomodel_examples,
    example_from_omex,
    example_from_sbml,
    load_examples,
    main_sbml_entry,
    omex_description,
)
from sbml4humans.resources import (
    BIOMODELS_CURATED_PATH,
    EXAMPLES_DIR,
    OMEX_ICGMODEL,
    REPRESSILATOR_SBML,
)
from sbml4humans.sbml import read_sbml


def test_example_from_sbml() -> None:
    """Metadata is read from the SBML model."""
    example = example_from_sbml(REPRESSILATOR_SBML)
    assert example.id == "BIOMD0000000012 (BIOMD0000000012_urn.xml)"
    assert example.file == REPRESSILATOR_SBML
    assert example.name
    assert example.description
    assert example.packages == ["layout", "render"]


def test_example_from_sbml_with_id() -> None:
    """The id of an example can be overwritten."""
    example = example_from_sbml(REPRESSILATOR_SBML, example_id="repressilator")
    assert example.id == "repressilator"


def test_example_from_sbml_without_model(tmp_path: Path) -> None:
    """A file without model is rejected."""
    path = tmp_path / "empty.xml"
    path.write_text("<sbml/>", encoding="utf-8")
    with pytest.raises(ValueError, match="could not be read"):
        example_from_sbml(path)


def test_example_from_omex() -> None:
    """Metadata of an archive is derived from its file name and manifest."""
    example = example_from_omex(OMEX_ICGMODEL)
    assert example.id == "icg_model"
    assert example.name == "icg_model"
    assert example.file == OMEX_ICGMODEL
    assert example.packages == ["OMEX"]
    # a sentence about the content of the archive, not the repr of its manifest
    assert example.description == (
        "COMBINE archive with 3 SBML entries: "
        "icg_liver.xml, icg_body.xml, icg_body_flat.xml"
    )


def test_omex_description_counts_entries_without_naming_them() -> None:
    """Entries whose names are too long for the sentence are only counted."""
    omex = Omex.from_omex(OMEX_ICGMODEL)
    for k, entry in enumerate(omex.entries_by_format(format_key="sbml")):
        entry.location = f"./models/a_model_with_a_very_long_name_{k}.xml"
    assert omex_description(omex) == "COMBINE archive with 3 SBML entries"


def test_omex_description_without_sbml() -> None:
    """An archive without an SBML entry says so."""
    assert omex_description(Omex()) == "COMBINE archive without an SBML entry"


def test_biomodel_examples_without_directory(tmp_path: Path) -> None:
    """Missing curated biomodels are skipped, not fatal."""
    assert biomodel_examples(tmp_path / "missing") == []


def test_biomodel_examples_skips_missing_files(tmp_path: Path) -> None:
    """Only existing biomodel archives become examples, named by biomodel id."""
    shutil.copy(OMEX_ICGMODEL, tmp_path / "BIOMD0000000002.omex")
    examples = biomodel_examples(tmp_path, count=3)
    assert [e.id for e in examples] == ["BIOMD0000000002"]
    assert examples[0].file.is_file()
    # the master model of the archive
    assert examples[0].file.name == "icg_body_flat.xml"


def test_main_sbml_entry_master() -> None:
    """The master SBML entry of an archive is the main entry."""
    entry = main_sbml_entry(Omex.from_omex(OMEX_ICGMODEL))
    assert entry.location == "./models/icg_body_flat.xml"
    assert entry.master


def test_main_sbml_entry_without_master() -> None:
    """Without master the first SBML entry by location is the main entry."""
    omex = Omex.from_omex(OMEX_ICGMODEL)
    for entry in omex.manifest.entries:
        entry.master = False
    assert main_sbml_entry(omex).location == "./models/icg_body.xml"


def test_main_sbml_entry_without_sbml() -> None:
    """An archive without SBML entry is rejected."""
    with pytest.raises(ValueError, match="no SBML entry"):
        main_sbml_entry(Omex())


def test_biomodel_examples_available() -> None:
    """The curated biomodels are served."""
    assert BIOMODELS_CURATED_PATH.is_dir()
    examples = biomodel_examples(count=2)
    assert [e.id for e in examples] == ["BIOMD0000000001", "BIOMD0000000002"]


def test_load_examples() -> None:
    """All examples load with unique ids and existing files."""
    examples = load_examples()
    assert len(examples) >= 40
    assert all(isinstance(e, ExampleMetaData) for e in examples.values())
    assert all(example_id == e.id for example_id, e in examples.items())
    assert all(e.file.is_file() for e in examples.values())
    assert "icg_model" in examples
    assert "BIOMD0000000012 (BIOMD0000000012_urn.xml)" in examples


def test_load_examples_is_cached() -> None:
    """Examples are only read once."""
    assert load_examples() is load_examples()


def test_constraint_event_example_is_served() -> None:
    """The example of the constraint, the event and the local parameters is served."""
    example = load_examples()["constraint_event (constraint_event.xml)"]
    assert example.file.name == "constraint_event.xml"
    assert example.name == "model with a constraint, an event and local parameters"
    assert example.description is not None
    # a Level 3 Version 2 document of core alone uses no package
    assert example.packages == []


def test_comp_deletion_example_is_served() -> None:
    """The example of the deletions and the replacements of comp is served."""
    example = load_examples()["comp_deletion (comp_deletion.xml)"]
    assert example.file.name == "comp_deletion.xml"
    assert example.name == "Two cells and a tissue in one medium"
    assert example.description is not None
    assert example.packages == ["comp"]


@pytest.mark.parametrize(
    "example_id, name, packages",
    [
        (
            "fbc_bounds_v1 (fbc_bounds_v1.xml)",
            "Flux bounds of fbc Version 1",
            ["fbc"],
        ),
        (
            "fbc_constraints_v3 (fbc_constraints_v3.xml)",
            "Constraints of fbc Version 3",
            ["fbc"],
        ),
    ],
)
def test_fbc_version_examples_are_served(
    example_id: str, name: str, packages: list[str]
) -> None:
    """The examples of the first and of the third version of fbc are served."""
    example = load_examples()[example_id]
    assert example.name == name
    assert example.description is not None
    assert example.packages == packages


def test_qual_example_is_served() -> None:
    """The example of a qualitative model is served with its package."""
    example = load_examples()["qual_example (qual_example.xml)"]
    assert example.name == "Qualitative example model"
    assert example.description is not None
    assert example.packages == ["qual"]


def test_distrib_spans_example_is_served() -> None:
    """The example of the spans and distributions of distrib is served."""
    example = load_examples()["distrib_spans (distrib_spans.xml)"]
    assert example.name == "Uncertainty spans and distributions"
    assert example.description is not None
    assert example.packages == ["distrib"]


# the examples written for the complete data model, one per part of it which no
# published model of the resources contains
WRITTEN_EXAMPLES = [
    "constraint_event.xml",
    "comp_deletion.xml",
    "fbc_bounds_v1.xml",
    "fbc_constraints_v3.xml",
    "qual_example.xml",
    "distrib_spans.xml",
]


@pytest.mark.parametrize("name", WRITTEN_EXAMPLES)
def test_written_examples_are_valid_sbml(name: str) -> None:
    """An example written to teach is a valid SBML document, without a warning."""
    doc: libsbml.SBMLDocument = read_sbml(EXAMPLES_DIR / name)
    doc.checkConsistency()
    messages = [doc.getError(k).getMessage().strip() for k in range(doc.getNumErrors())]
    assert messages == []
