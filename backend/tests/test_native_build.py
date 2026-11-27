"""Check failures at the native artifact boundary without compiling a runtime."""

import importlib.util
import sys
import zipfile
from pathlib import Path
from types import ModuleType

import pytest


@pytest.fixture(autouse=True)
def _cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep all build cache writes inside the test directory."""
    monkeypatch.setenv("SBML4HUMANS_BUILD_CACHE", str(tmp_path / "cache"))


def _builder() -> ModuleType:
    """Load the same standalone helper used by isolated build hooks."""
    spec = importlib.util.spec_from_file_location(
        "native_build_test", Path(__file__).parents[1] / "build_native.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_an_incompatible_native_wheel_is_rejected_before_import(tmp_path: Path) -> None:
    """An artifact for another OS cannot enter the application bundle."""
    platform = "win_amd64" if sys.platform != "win32" else "manylinux_2_38_x86_64"
    wheel = tmp_path / f"sbml4humans_core-0.1.0-cp312-abi3-{platform}.whl"
    with pytest.raises(RuntimeError, match="incompatible with this host"):
        _builder().payload(wheel, {"revision": "expected"})


def test_the_runtime_requires_abi3(tmp_path: Path) -> None:
    """A pure Python artifact cannot impersonate the required native runtime."""
    wheel = tmp_path / "sbml4humans_core-0.1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w"):
        pass
    with pytest.raises(RuntimeError, match="ABI3 wheel"):
        _builder().payload(wheel, {"revision": "expected"})


def test_native_archive_paths_cannot_escape_the_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject parent traversal before writing any files outside staging."""
    monkeypatch.setenv("SBML4HUMANS_BUILD_CACHE", str(tmp_path / "cache"))
    from packaging.tags import sys_tags

    platform = next(tag.platform for tag in sys_tags() if tag.abi == "abi3")
    wheel = tmp_path / f"sbml4humans_core-0.1.0-cp312-abi3-{platform}.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("../escaped", "bad")
    with pytest.raises(RuntimeError, match="Invalid path"):
        _builder().payload(wheel, {"revision": "expected"})
    assert not (tmp_path / "escaped").exists()


def test_broken_native_import_reports_its_cause(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Missing libraries produce an installation error with the native cause."""
    monkeypatch.setenv("SBML4HUMANS_BUILD_CACHE", str(tmp_path / "cache"))
    from packaging.tags import sys_tags

    platform = next(tag.platform for tag in sys_tags() if tag.abi == "abi3")
    wheel = tmp_path / f"sbml4humans_core-0.1.0-cp312-abi3-{platform}.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(
            "sbml4humans_core/__init__.py",
            "raise ImportError('missing native library')",
        )
    with pytest.raises(RuntimeError, match="missing native library"):
        _builder().payload(wheel, {"revision": "expected"})
