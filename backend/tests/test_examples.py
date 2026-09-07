"""Tests of the example models."""

import shutil
from pathlib import Path

import pytest
from sbmlutils.resources import (
    BIOMODELS_CURATED_PATH,
    OMEX_ICGMODEL,
    REPRESSILATOR_SBML,
)

from sbml4humans.examples import (
    ExampleMetaData,
    biomodel_examples,
    example_from_omex,
    example_from_sbml,
    load_examples,
)


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
    assert "icg_body.xml" in (example.description or "")


def test_biomodel_examples_without_directory(tmp_path: Path) -> None:
    """Missing curated biomodels are skipped, not fatal."""
    assert biomodel_examples(tmp_path / "missing") == []


def test_biomodel_examples_skips_missing_files(tmp_path: Path) -> None:
    """Only existing biomodel archives become examples, named by biomodel id."""
    shutil.copy(OMEX_ICGMODEL, tmp_path / "BIOMD0000000002.omex")
    examples = biomodel_examples(tmp_path, count=3)
    assert [e.id for e in examples] == ["BIOMD0000000002"]
    assert examples[0].file.is_file()
    assert examples[0].file.name == "icg_body.xml"
    assert examples[0].packages == ["comp"]


def test_biomodel_examples_available() -> None:
    """The curated biomodels of sbmlutils are served if available."""
    if not BIOMODELS_CURATED_PATH.is_dir():
        pytest.skip("curated biomodels are not available")
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
