"""Tests for the order of the entries of a COMBINE archive."""

import zipfile
from pathlib import Path

import pytest

from sbml4humans.archive import manifest_locations, read_omex
from sbml4humans.report import report_for_path
from sbml4humans.resources import API_EXAMPLES_OMEX, OMEX_ICGMODEL


MANIFEST = """<?xml version="1.0" encoding="UTF-8"?>
<omexManifest xmlns="http://identifiers.org/combine.specifications/omex-manifest">
  <content location="." format="http://identifiers.org/combine.specifications/omex"/>
  <content location="./manifest.xml" format="http://identifiers.org/combine.specifications/omex-manifest"/>
  {content}
</omexManifest>
"""
SBML_FORMAT = "http://identifiers.org/combine.specifications/sbml"


def _archive(path: Path, locations: list[str], files: list[str]) -> Path:
    """Write an archive whose manifest lists the locations and which holds the files."""
    content = "\n  ".join(
        f'<content location="{location}" format="{SBML_FORMAT}"/>'
        for location in locations
    )
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("manifest.xml", MANIFEST.format(content=content))
        for name in files:
            zf.writestr(name, "<sbml/>")
    return path


def test_manifest_locations() -> None:
    """The locations of an archive are read in the order of its manifest."""
    assert manifest_locations(OMEX_ICGMODEL) == [
        ".",
        "./manifest.xml",
        "./models/icg_liver.xml",
        "./models/icg_body.xml",
        "./models/icg_body_flat.xml",
    ]


def test_manifest_locations_are_normalised(tmp_path: Path) -> None:
    """A location without the leading `./` is the location pymetadata makes of it."""
    path = _archive(tmp_path / "a.omex", ["b.xml", "./a.xml"], ["a.xml", "b.xml"])
    assert manifest_locations(path)[2:] == ["./b.xml", "./a.xml"]


def test_manifest_locations_without_manifest(tmp_path: Path) -> None:
    """An archive without a manifest, or with one which is not XML, has no order."""
    path = tmp_path / "a.omex"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("a.xml", "<sbml/>")
    assert manifest_locations(path) == []
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("manifest.xml", "no xml")
    assert manifest_locations(path) == []


@pytest.mark.parametrize("omex_path", API_EXAMPLES_OMEX, ids=lambda path: path.stem)
def test_read_omex_keeps_the_order_of_the_manifest(omex_path: Path) -> None:
    """The entries of an archive are in the order of its manifest.

    pymetadata adds them in the order of `os.walk`, which is the order of the
    file system the archive is extracted to.
    """
    locations = [entry.location for entry in read_omex(omex_path).manifest.entries]
    assert locations == manifest_locations(omex_path)


def test_read_omex_appends_files_the_manifest_omits(tmp_path: Path) -> None:
    """A file which the manifest does not list follows the listed ones, by location."""
    path = _archive(
        tmp_path / "a.omex",
        ["./m.xml", "./b.xml"],
        ["z.xml", "b.xml", "c.xml", "m.xml"],
    )
    locations = [entry.location for entry in read_omex(path).manifest.entries]
    assert locations[2:] == ["./m.xml", "./b.xml", "./c.xml", "./z.xml"]


def test_report_keeps_the_order_of_the_manifest() -> None:
    """The manifest and the reports of a response are in the order of the manifest."""
    response = report_for_path(OMEX_ICGMODEL)
    assert [entry.location for entry in response.manifest.entries] == (
        manifest_locations(OMEX_ICGMODEL)
    )
    assert list(response.reports) == [
        "./models/icg_liver.xml",
        "./models/icg_body.xml",
        "./models/icg_body_flat.xml",
    ]
