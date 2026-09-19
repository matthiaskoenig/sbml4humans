"""The command `sbml4humans`: the report of a local file in the browser."""

import argparse
import sys
from collections.abc import Sequence

from sbml4humans import __version__
from sbml4humans.viewer import show, stop


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command and return its exit code."""
    parser = argparse.ArgumentParser(
        prog="sbml4humans",
        description=(
            "Open the report of an SBML file or COMBINE archive in the browser. The "
            "file is read by a local server and never leaves this machine."
        ),
    )
    parser.add_argument("path", nargs="?", help="SBML file or COMBINE archive")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="print the url of the report without opening it",
    )
    parser.add_argument("--stop", action="store_true", help="end the local server")
    parser.add_argument("--version", action="version", version=__version__)
    arguments = parser.parse_args(argv)

    if arguments.stop:
        stopped = stop()
        print("the local server stopped" if stopped else "no local server is running")
        return 0
    if arguments.path is None:
        parser.error("the path of an SBML file or COMBINE archive is required")
    try:
        url = show(arguments.path, open_browser=not arguments.no_browser)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"sbml4humans: {error}", file=sys.stderr)
        return 1
    print(url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
