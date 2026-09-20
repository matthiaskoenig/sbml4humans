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
from sbml4humans.links import _names_an_element, _nested, _with_extensions
from sbml4humans.model import (
    Deletion,
    EdgeKind,
    Port,
    ReplacedBy,
    ReplacedElement,
    Report,
    ResolutionStatus,
    SBaseRefFields,
)
from sbml4humans.report import report_for_path
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


def test_list_of_example_is_served() -> None:
    """The example of the lists which carry something of their own is served."""
    example = load_examples()["list_of (list_of.xml)"]
    assert example.file.name == "list_of.xml"
    assert example.name == "ListOf containers with attributes of their own"
    assert example.description is not None
    assert example.packages == ["comp"]


def test_qual_example_is_served() -> None:
    """The example of a qualitative model is served with its package."""
    example = load_examples()["qual_example (qual_example.xml)"]
    assert example.name == "Qualitative example model"
    assert example.description is not None
    assert example.packages == ["qual"]


@pytest.mark.parametrize(
    ("example_id", "name", "count"),
    [
        ("Faure2006 (Faure2006.sbml)", "Mammalian Cell Cycle 2006", 10),
        (
            "ThieffryThomas1995_multivalue (ThieffryThomas1995_multivalue.sbml)",
            "A multi-valued model on lysis vs lysogeny decision in the phage lambda",
            4,
        ),
    ],
)
def test_published_qual_models_are_served(
    example_id: str, name: str, count: int
) -> None:
    """The published logical models are served, a transition per qualitative species."""
    example = load_examples()[example_id]
    assert example.name == name
    assert example.description is not None
    assert example.packages == ["qual"]
    response = report_for_path(example.file, trusted=True)
    (entry,) = response.reports.values()
    (model,) = entry.report.models
    assert len(model.list_of_qualitative_species) == count
    assert len(model.list_of_transitions) == count


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


# -------------------------------------------------------------------------------------
# the comp references of the examples end at the element they name
# -------------------------------------------------------------------------------------
REFERENCE_KINDS = {
    ReplacedBy: EdgeKind.REPLACED_BY,
    ReplacedElement: EdgeKind.REPLACED_ELEMENT,
    Deletion: EdgeKind.DELETION,
    Port: EdgeKind.PORT,
}


def _comp_references(report: Report) -> tuple[int, int]:
    """How many comp references of a report name an element, and how many reach it.

    A replacement has an edge of its kind to its submodel as well, which is as
    far as a reference goes which is not resolved, so that edge does not count.
    """
    nodes = report.link_graph.nodes
    reached = {
        (edge.source, edge.kind)
        for edge in report.link_graph.edges
        if edge.target_entry is not None
        or nodes[edge.target].sbml_type != "Submodel"
        or nodes[edge.source].sbml_type == "Port"
    }
    named = resolved = 0
    for model in report.models:
        for element in [model, *_nested(model)]:
            for carrier in _with_extensions(element):
                if not isinstance(carrier, SBaseRefFields):
                    continue
                kind = REFERENCE_KINDS.get(type(carrier))
                if kind is None or not _names_an_element(carrier):
                    continue
                named += 1
                resolved += (carrier.pk, kind) in reached
    return named, resolved


def test_comp_references_reach_elements() -> None:
    """Every replacement, deletion and port of the examples ends at its element.

    Every submodel of the comp models which ship with the backend instantiates
    an external model definition, whose document is another entry of the archive
    or a file next to the example, so every reference can be followed (#36).
    """
    named = resolved = across = 0
    for example in load_examples().values():
        response = report_for_path(example.file, trusted=True)
        for entry in response.reports.values():
            for emd in entry.report.external_model_definitions:
                assert emd.resolution.status == ResolutionStatus.RESOLVED, example.id
            counts = _comp_references(entry.report)
            assert counts[0] == counts[1], example.id
            named += counts[0]
            resolved += counts[1]
            across += sum(
                edge.target_entry is not None for edge in entry.report.link_graph.edges
            )
    assert named == resolved > 300
    assert across > 100


def test_comp_references_of_an_upload_end_at_the_submodel() -> None:
    """Without the other documents the references stop where they did before."""
    report = next(
        iter(report_for_path(EXAMPLES_DIR / "minimal_model_comp.xml").reports.values())
    ).report
    assert _comp_references(report) == (10, 0)
