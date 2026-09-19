"""Where the local server of this machine is, for the server and for `show`.

The running server writes a state file with its port, its process id, its
secret and its version into the cache directory of the user, readable by that
user alone. `viewer.show` finds the server through it. The module imports
nothing of the report, so that `import sbml4humans` stays cheap.
"""

import json
import os
from pathlib import Path
from typing import Any

from platformdirs import user_cache_path

from sbml4humans.resources import FRONTEND_DIR


HOST = "127.0.0.1"
SECRET_HEADER = "X-SBML4Humans-Secret"
# the environment of the server process: the secret `show` hands over, and for
# tests and development another state directory and another build of the frontend
SECRET_VARIABLE = "SBML4HUMANS_SECRET"
STATE_DIR_VARIABLE = "SBML4HUMANS_STATE_DIR"
FRONTEND_VARIABLE = "SBML4HUMANS_FRONTEND"


class FrontendMissingError(RuntimeError):
    """Raised when the package holds no build of the frontend."""

    def __init__(self, directory: Path) -> None:
        """Create the error with the command which creates the build."""
        super().__init__(
            f"sbml4humans has no build of its frontend in '{directory}'. A release "
            "from PyPI ships it; in a checkout of the repository create it with "
            "`npm ci && npm run build:package` in `frontend/`."
        )


def frontend_dir() -> Path:
    """The directory of the built frontend.

    Raises:
        FrontendMissingError: if there is no build.
    """
    directory = Path(os.environ.get(FRONTEND_VARIABLE) or FRONTEND_DIR)
    if not (directory / "index.html").is_file():
        raise FrontendMissingError(directory)
    return directory


def state_file() -> Path:
    """The file in which the running server says where it is.

    It holds the port, the process id, the secret and the version as JSON, in
    the cache directory of the user, readable by that user alone.
    """
    directory = os.environ.get(STATE_DIR_VARIABLE)
    base = Path(directory) if directory else user_cache_path("sbml4humans")
    return base / "server.json"


def write_state(path: Path, state: dict[str, Any]) -> None:
    """Write the state file, readable by the user alone from the start."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f".{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as f:
        json.dump(state, f)
    temporary.replace(path)


def read_state(path: Path) -> dict[str, Any] | None:
    """The state of the file, None without a file which can be read."""
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except OSError, ValueError:
        return None
    return state if isinstance(state, dict) else None
