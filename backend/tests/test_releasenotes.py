"""Tests of the generated release notes page of the documentation."""

from pathlib import Path

import pytest

from sbml4humans import __version__, releasenotes
from sbml4humans.releasenotes import ReleaseNotesError


NOTES = """# Release notes for sbml4humans 1.2.0

The summary of the release.

## Fixes
- a fix, with `# no heading` in code

```bash
# a comment of a command, not a heading
uv run pytest
```

### A detail
More.

Your sbml4humans team
"""


def _repository(tmp_path: Path, notes: dict[str, str], version: str) -> Path:
    """A repository root with release notes and a package of a version."""
    (tmp_path / releasenotes.NOTES_DIR).mkdir()
    for name, text in notes.items():
        (tmp_path / releasenotes.NOTES_DIR / f"{name}.md").write_text(text, "utf-8")
    (tmp_path / releasenotes.VERSION_PATH).parent.mkdir(parents=True)
    (tmp_path / releasenotes.VERSION_PATH).write_text(
        f'"""The package."""\n\n__version__ = "{version}"\n', "utf-8"
    )
    (tmp_path / releasenotes.PAGE_PATH).parent.mkdir()
    return tmp_path


def test_a_section_is_headed_by_its_version() -> None:
    """The title gives way to the version, the headings move down, the greeting goes."""
    section = releasenotes.section("1.2.0", NOTES)
    lines = section.splitlines()
    assert lines[0] == "## 1.2.0"
    assert "# Release notes for sbml4humans 1.2.0" not in lines
    assert "The summary of the release." in lines
    assert "### Fixes" in lines
    assert "#### A detail" in lines
    assert "# a comment of a command, not a heading" in lines
    assert releasenotes.SIGN_OFF not in section
    assert not section.endswith("\n")


def test_the_versions_are_ordered_by_their_numbers(tmp_path: Path) -> None:
    """The newest version is first, and 0.10.0 is newer than 0.9.0."""
    root = _repository(
        tmp_path, {"0.9.0": NOTES, "0.10.0": NOTES, "1.0.0": NOTES}, "1.0.0"
    )
    assert releasenotes.versions(root) == ["1.0.0", "0.10.0", "0.9.0"]
    page = releasenotes.page(root)
    assert page.startswith("# Release notes\n\n")
    assert page.index("## 1.0.0") < page.index("## 0.10.0") < page.index("## 0.9.0")
    assert page.endswith("More.\n")


def test_a_file_which_is_not_a_version_is_refused(tmp_path: Path) -> None:
    """Every file of the directory is the notes of one release."""
    root = _repository(tmp_path, {"1.0.0": NOTES, "draft": NOTES}, "1.0.0")
    with pytest.raises(
        ReleaseNotesError, match=r"draft\.md is not named after a version"
    ):
        releasenotes.versions(root)


def test_check_finds_a_stale_page_and_a_version_without_notes(tmp_path: Path) -> None:
    """The page follows the notes, and the version of the package has notes."""
    root = _repository(tmp_path, {"1.0.0": NOTES}, "1.1.0")
    with pytest.raises(ReleaseNotesError) as error:
        releasenotes.check(root)
    assert "the version 1.1.0 of the package has no release notes" in str(error.value)
    assert "docs/release-notes.md is not current" in str(error.value)

    (root / releasenotes.NOTES_DIR / "1.1.0.md").write_text(NOTES, "utf-8")
    (root / releasenotes.PAGE_PATH).write_text(releasenotes.page(root), "utf-8")
    releasenotes.check(root)


def test_the_committed_page_is_current() -> None:
    """The page of the repository is the one its release notes generate."""
    releasenotes.check(releasenotes.REPO_ROOT)
    assert releasenotes.package_version(releasenotes.REPO_ROOT) == __version__


def test_main_checks_and_reports(capsys: pytest.CaptureFixture[str]) -> None:
    """`--check` of the command line answers with the exit code."""
    assert releasenotes.main(["releasenotes", "--check"]) == 0
    assert "the release notes page is current" in capsys.readouterr().out
