"""Open the report of a local file in the browser.

`show(path)` is the python interface of sbml4humans. It talks to the local
server of this machine (`local.py`), which it finds through `localstate.py`, which it starts when none is running: a
detached process which outlives the caller, so that the page a script opened
keeps working after the script ended, and which ends itself when no report is
open any more. The file is read where it is and never leaves the machine.
"""

import contextlib
import logging
import os
import secrets
import socket
import subprocess
import sys
import time
import webbrowser
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx

from sbml4humans import __version__
from sbml4humans.localstate import (
    HOST,
    SECRET_HEADER,
    SECRET_VARIABLE,
    frontend_dir,
    read_state,
    state_file,
)


logger = logging.getLogger(__name__)

START_TIMEOUT = 30.0  # [s]
PING_TIMEOUT = 2.0  # [s]
# a genome scale model takes minutes to report
REPORT_TIMEOUT = 1800.0  # [s]


def show(path: Path | str, open_browser: bool = True) -> str:
    """Open the report of an SBML file or COMBINE archive in the browser.

    The report is created when the function is called, so the file may change
    or go afterwards. The files next to a model of the comp package which its
    external model definitions name are part of the report.

    Args:
        path: the SBML file, plain or gzipped, or the COMBINE archive.
        open_browser: open the report in the browser of the user.

    Returns:
        The url of the report, which works as long as the local server runs.

    Raises:
        FileNotFoundError: if the path is no file.
        ValueError: if no report could be created, with what the report said.
        FrontendMissingError: if the package holds no build of the frontend.
    """
    file = Path(path).expanduser().resolve()
    if not file.is_file():
        raise FileNotFoundError(f"The file does not exist: '{file}'")

    state = _server()
    response = httpx.post(
        f"http://{HOST}:{state['port']}/api/local/reports",
        json={"path": str(file)},
        headers={SECRET_HEADER: state["secret"]},
        timeout=REPORT_TIMEOUT,
    )
    response.raise_for_status()
    body = response.json()
    if body.get("errors"):
        raise ValueError(body["errors"][0])
    url: str = body["url"]
    if open_browser:
        webbrowser.open(url)
    return url


def stop() -> bool:
    """End the local server.

    Returns:
        Whether there was a server to end.
    """
    state = _running()
    if state is None:
        return False
    _shutdown(state)
    return True


# -------------------------------------------------------------------------------------
# the server
# -------------------------------------------------------------------------------------
def _ping(port: int) -> str | None:
    """The version of the sbml4humans server on the port, None if there is none."""
    try:
        response = httpx.get(
            f"http://{HOST}:{port}/api/local/ping", timeout=PING_TIMEOUT
        )
        version = response.json().get("version")
    except httpx.HTTPError, ValueError, AttributeError:
        return None
    return version if isinstance(version, str) else None


def _running() -> dict[str, Any] | None:
    """The state of the server which answers, None if none does.

    The state file of a server which was killed is still there, so the file
    alone says nothing: the server of the file has to answer.
    """
    state = read_state(state_file())
    if state is None or not isinstance(state.get("port"), int):
        return None
    if not isinstance(state.get("secret"), str) or _ping(state["port"]) is None:
        return None
    return state


def _server() -> dict[str, Any]:
    """The state of a running server of this version, started if there is none."""
    state = _running()
    if state is not None and _ping(state["port"]) != __version__:
        # the page of a report and the api which answers it belong to one version
        _shutdown(state)
        state = None
    return state if state is not None else _start()


def _shutdown(state: dict[str, Any]) -> None:
    """Ask the server to end and wait until it did."""
    port: int = state["port"]
    # a server which does not answer any more has ended, which is what is asked for
    with contextlib.suppress(httpx.HTTPError):
        httpx.post(
            f"http://{HOST}:{port}/api/local/shutdown",
            headers={SECRET_HEADER: state["secret"]},
            timeout=PING_TIMEOUT,
        )
    _wait_until(lambda: _ping(port) is None, "the local server to end")
    # a server which ends removes its file, one which was killed before did not
    current = read_state(state_file())
    if current is not None and current.get("pid") == state.get("pid"):
        state_file().unlink(missing_ok=True)


def _free_port() -> int:
    """A port of the loopback interface which is free right now."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, 0))
        port: int = s.getsockname()[1]
    return port


def _start() -> dict[str, Any]:
    """Start the server as a process of its own and wait until it answers.

    The process is detached from the caller: it is no member of its session,
    shares none of its streams and writes its log next to the state file.
    """
    frontend_dir()  # fail here, where the caller reads it, and not in the log
    port = _free_port()
    secret = secrets.token_hex(32)
    log = state_file().parent / "server.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    detached: dict[str, Any] = (
        {
            "creationflags": getattr(subprocess, "DETACHED_PROCESS", 0)
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        }
        if sys.platform == "win32"
        else {"start_new_session": True}
    )
    with log.open("ab") as output:
        process = subprocess.Popen(
            [sys.executable, "-m", "sbml4humans.local", "--port", str(port)],
            env={**os.environ, SECRET_VARIABLE: secret},
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=output,
            **detached,
        )

    def answers() -> bool:
        """Whether the server of this call is up, which fails if it ended."""
        if process.poll() is not None:
            raise RuntimeError(
                f"The local server of sbml4humans ended with code "
                f"{process.returncode}, see '{log}'."
            )
        state = read_state(state_file())
        return (
            state is not None
            and state.get("secret") == secret
            and _ping(port) is not None
        )

    _wait_until(answers, f"the local server to start, see '{log}'")
    logger.info("sbml4humans serves on http://%s:%s", HOST, port)
    return {"port": port, "secret": secret, "pid": process.pid}


def _wait_until(
    condition: Callable[[], bool], what: str, timeout: float = START_TIMEOUT
) -> None:
    """Wait until the condition holds.

    Raises:
        TimeoutError: if it does not hold after `timeout` seconds.
    """
    end = time.monotonic() + timeout
    while not condition():
        if time.monotonic() > end:
            raise TimeoutError(f"Waited {timeout} s for {what}.")
        time.sleep(0.05)
