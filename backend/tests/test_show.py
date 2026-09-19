"""Tests of `sbml4humans.show`, against a real server process."""

import os
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest

import sbml4humans
from sbml4humans import viewer
from sbml4humans.cli import main
from sbml4humans.localstate import (
    FRONTEND_VARIABLE,
    STATE_DIR_VARIABLE,
    FrontendMissingError,
    read_state,
    state_file,
)
from sbml4humans.resources import EXAMPLES_DIR, REPRESSILATOR_SBML
from sbml4humans.viewer import show, stop


@pytest.fixture
def environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A state directory and a frontend of the test, and no server left behind."""
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "index.html").write_text("<html>the page</html>")
    monkeypatch.setenv(STATE_DIR_VARIABLE, str(tmp_path / "state"))
    monkeypatch.setenv(FRONTEND_VARIABLE, str(frontend))
    opened: list[str] = []
    monkeypatch.setattr(viewer.webbrowser, "open", opened.append)
    monkeypatch.setattr(viewer, "_opened", opened, raising=False)
    try:
        yield tmp_path
    finally:
        stop()


def _opened() -> list[str]:
    """The urls the browser was asked to open."""
    return viewer._opened  # ty: ignore[unresolved-attribute]


def test_show_is_a_function_of_the_package() -> None:
    """`from sbml4humans import show` is the interface of the issue."""
    assert sbml4humans.show is show
    assert sbml4humans.stop is stop


def test_show_starts_a_server_and_opens_the_report(environment: Path) -> None:
    """The url serves the page, and its token the report of the file."""
    url = show(REPRESSILATOR_SBML)
    assert _opened() == [url]
    assert url.startswith("http://127.0.0.1:")
    assert httpx.get(url).text == "<html>the page</html>"

    token = url.split("local=")[1]
    base = url.split("/report")[0]
    body = httpx.get(f"{base}/api/local/reports/{token}").json()
    report = body["reports"]["./BIOMD0000000012_urn.xml"]["report"]
    assert report["models"][0]["id"] == "BIOMD0000000012"

    # the state file is the one of the server, for the user alone
    state = read_state(state_file())
    assert state is not None
    assert state["port"] == int(base.rsplit(":", 1)[1])
    assert state["version"] == sbml4humans.__version__
    if os.name == "posix":
        assert state_file().stat().st_mode & 0o777 == 0o600


def test_show_reuses_the_server_and_takes_a_relative_path(
    environment: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A second call is a second report of the same process."""
    first = show(REPRESSILATOR_SBML, open_browser=False)
    state = read_state(state_file())
    monkeypatch.chdir(EXAMPLES_DIR)
    second = show("comp_deletion.xml", open_browser=False)
    assert _opened() == []
    assert read_state(state_file()) == state
    assert first.split("?")[0] == second.split("?")[0]
    assert first != second
    # a path of the user is read with the files next to it
    token = second.split("local=")[1]
    body = httpx.get(f"{second.split('/report')[0]}/api/local/reports/{token}").json()
    assert list(body["reports"]) == ["./comp_deletion.xml", "./unit_definitions.xml"]


def test_show_raises_what_the_report_says(environment: Path) -> None:
    """A file which is missing, and a file which is no SBML."""
    with pytest.raises(FileNotFoundError, match=r"missing\.xml"):
        show(environment / "missing.xml")
    garbage = environment / "garbage.xml"
    garbage.write_text("no sbml")
    with pytest.raises(ValueError, match="No SBML model could be read"):
        show(garbage, open_browser=False)
    assert _opened() == []


def test_a_server_of_another_version_is_replaced(
    environment: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The page and the api of a report belong to one version."""
    show(REPRESSILATOR_SBML, open_browser=False)
    old = read_state(state_file())
    assert old is not None
    monkeypatch.setattr(viewer, "__version__", "0.0.0")
    show(REPRESSILATOR_SBML, open_browser=False)
    new = read_state(state_file())
    assert new is not None
    assert new["pid"] != old["pid"]
    with pytest.raises(httpx.TransportError):
        httpx.get(f"http://127.0.0.1:{old['port']}/api/local/ping")


def test_stop_ends_the_server(environment: Path) -> None:
    """The process ends, the state file goes, and there is nothing to stop twice."""
    url = show(REPRESSILATOR_SBML, open_browser=False)
    assert stop() is True
    assert not state_file().exists()
    with pytest.raises(httpx.TransportError):
        httpx.get(url)
    assert stop() is False


def test_a_stale_state_file_is_no_server(environment: Path) -> None:
    """A server which was killed leaves its file, which names nothing any more."""
    url = show(REPRESSILATOR_SBML, open_browser=False)
    state = read_state(state_file())
    assert state is not None
    os.kill(state["pid"], 9)
    viewer._wait_until(lambda: not viewer._ping(state["port"]), "the kill")
    assert state_file().exists()
    again = show(REPRESSILATOR_SBML, open_browser=False)
    assert again != url
    assert httpx.get(again).status_code == 200


def test_without_the_build_of_the_frontend_show_says_how_to_get_it(
    environment: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A checkout of the repository has no build until it is created."""
    monkeypatch.setenv(FRONTEND_VARIABLE, str(environment / "no-frontend"))
    with pytest.raises(FrontendMissingError, match="npm run build:package"):
        show(REPRESSILATOR_SBML, open_browser=False)


def test_the_command(environment: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """`sbml4humans PATH` prints the url, `--stop` ends the server."""
    assert main([str(REPRESSILATOR_SBML), "--no-browser"]) == 0
    url = capsys.readouterr().out.strip()
    assert httpx.get(url).status_code == 200
    assert _opened() == []
    assert main(["--stop"]) == 0
    assert "stopped" in capsys.readouterr().out
    assert main([str(environment / "missing.xml")]) == 1
    assert "missing.xml" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        main([])
