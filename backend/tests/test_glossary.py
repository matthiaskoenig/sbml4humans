"""Tests of the glossary generator."""

from pathlib import Path

import pytest

from sbml4humans.glossary import Glossary, GlossaryError, render_json, render_type_page


FIXTURE = Path(__file__).parent / "data" / "glossary"


def test_reads_the_entries() -> None:
    """Every section of a glossary file becomes an entry."""
    glossary = Glossary.from_directory(FIXTURE)
    assert glossary.types["Species"].label == "Species"
    assert glossary.types["Species"].attributes["initialAmount"].summary
    assert glossary.links["compartment"].label == "compartment"
    assert glossary.concepts["derivedUnits"].label == "derived units"


def test_renders_the_page_of_a_type() -> None:
    """The page of a type has its attributes, its related types and its source."""
    glossary = Glossary.from_directory(FIXTURE)
    page = render_type_page(glossary, glossary.types["Species"])
    assert page.startswith("# Species\n")
    assert "| initial amount |" in page
    assert "[Compartment](compartment.md)" in page
    assert "SBML Level 3 Version 2 Core" in page


def test_renders_the_json_without_the_descriptions() -> None:
    """The application reads the labels and the summaries, not the prose."""
    glossary = Glossary.from_directory(FIXTURE)
    data = render_json(glossary)
    assert data["types"]["Species"]["summary"]
    assert "description" not in data["types"]["Species"]
    assert (
        data["types"]["Species"]["attributes"]["initialAmount"]["label"]
        == "initial amount"
    )
    assert data["links"]["compartment"]["summary"]
    assert data["concepts"]["derivedUnits"]["summary"]


def test_a_missing_summary_is_an_error(tmp_path: Path) -> None:
    """An entry without a summary has no tooltip, which is an error."""
    (tmp_path / "core.toml").write_text('[types.Species]\nlabel = "Species"\n')
    with pytest.raises(GlossaryError, match="summary"):
        Glossary.from_directory(tmp_path)


def test_a_broken_page_link_is_an_error(tmp_path: Path) -> None:
    """A description which links a page that is not generated is an error."""
    (tmp_path / "core.toml").write_text(
        '[types.Species]\nlabel = "Species"\nsummary = "a species"\n'
        'description = "see [Nothing](nothing.md)"\n'
    )
    glossary = Glossary.from_directory(tmp_path)
    with pytest.raises(GlossaryError, match=r"nothing\.md"):
        glossary.validate_links()
