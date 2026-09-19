"""Tests of the files the python package ships."""

from pathlib import Path


BACKEND_PATH = Path(__file__).parent.parent


def test_the_license_of_the_package_is_the_license_of_the_repository() -> None:
    """The package ships a copy of the license, which must not drift.

    A build of the package only sees `backend/`, so the wheel and the sdist
    carry `backend/LICENSE`, a copy of the `LICENSE` of the repository.
    """
    package_license = BACKEND_PATH / "LICENSE"
    repository_license = BACKEND_PATH.parent / "LICENSE"
    assert package_license.read_text() == repository_license.read_text()
