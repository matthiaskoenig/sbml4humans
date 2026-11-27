"""Build and privately bundle the exact Rust runtime pinned by the application.

Wheels carry their native runtime. Source/editable builds reuse a verified local
wheel or compile the pin with bounded jobs and a shared libSBML build cache.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import sysconfig
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parent
PIN_PATH = ROOT / "sbml4humans/native-source.json"


def run(arguments: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    """Run a build tool without shell interpretation."""
    subprocess.run(arguments, cwd=cwd, env=env, check=True)


def cache_root() -> Path:
    """Use the operator-selected build cache or the user's cache directory."""
    selected = os.environ.get("SBML4HUMANS_BUILD_CACHE")
    base = (
        Path(selected)
        if selected
        else Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        / "sbml4humans-build"
    )
    base.mkdir(parents=True, exist_ok=True)
    return base


def build_core(source: Path, output: Path, pin: dict[str, str]) -> Path:
    """Build the pinned validation-enabled ABI3 wheel with shared native dependencies."""
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=source, text=True
    ).strip()
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=normal"],
        cwd=source,
        text=True,
    )
    if revision != pin["revision"] or dirty.strip():
        raise RuntimeError(
            "The Rust checkout must be clean and match native-source.json."
        )
    env = os.environ.copy()
    env.setdefault("CARGO_BUILD_JOBS", "2")
    env.setdefault("CMAKE_BUILD_PARALLEL_LEVEL", "2")
    env["SBML4HUMANS_CORE_REVISION"] = revision
    env["PYO3_PYTHON"] = sys.executable
    if not env.get("LIBSBML_DIR"):
        script = source / "scripts/build-libsbml.sh"
        fingerprint = hashlib.sha256(script.read_bytes()).hexdigest()
        dependencies = cache_root() / "libsbml" / fingerprint
        prefix = dependencies / "prefix"
        if not (
            (prefix / "include/sbml/SBMLTypes.h").is_file()
            and (prefix / "lib/libsbml-static.a").is_file()
        ):
            env["LIBSBML_BUILD_ROOT"] = str(dependencies)
            run(["bash", str(script)], source, env)
        env["LIBSBML_DIR"] = str(prefix)
    env.setdefault("CARGO_TARGET_DIR", str(cache_root() / "target"))
    output.mkdir(parents=True, exist_ok=True)
    maturin = (
        [sys.executable, "-m", "maturin"]
        if importlib.util.find_spec("maturin")
        else ["uv", "tool", "run", "--from", "maturin[patchelf]>=1.16,<2", "maturin"]
    )
    run(
        [
            *maturin,
            "build",
            "--release",
            "--locked",
            "--features",
            "validation",
            "--out",
            str(output),
        ],
        source,
        env,
    )
    wheels = list(output.glob("sbml4humans_core-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError("The native build must produce exactly one runtime wheel.")
    return wheels[0]


def payload(wheel: Path, pin: dict[str, str]) -> tuple[Path, str]:
    """Verify the private runtime, its source identity and its native wheel tag."""
    from packaging.tags import sys_tags
    from packaging.utils import parse_wheel_filename

    _, _, _, supported = parse_wheel_filename(wheel.name)
    if not supported.intersection(sys_tags()):
        raise RuntimeError(
            f"The Rust runtime wheel is incompatible with this host: {wheel.name}"
        )
    fingerprint = hashlib.sha256(wheel.read_bytes()).hexdigest()
    directory = cache_root() / "unpacked-v2" / fingerprint
    with zipfile.ZipFile(wheel) as archive:
        tags = "-".join(wheel.stem.rsplit("-", 3)[-3:])
        if not tags.startswith("cp312-abi3-"):
            raise RuntimeError(
                "The Rust runtime must be an ABI3 wheel for Python 3.12 and later."
            )
        if not directory.exists():
            directory.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(dir=directory.parent) as temporary:
                stage = Path(temporary) / "payload"
                (stage / "_sbml4humans_runtime").mkdir(parents=True)
                (stage / "_sbml4humans_runtime/__init__.py").write_text(
                    "from .sbml4humans_core import *\n"
                )
                for name in archive.namelist():
                    if name.endswith("/"):
                        continue
                    parts = PurePosixPath(name)
                    if parts.is_absolute() or ".." in parts.parts:
                        raise RuntimeError("Invalid path in the native runtime wheel.")
                    if name.startswith("sbml4humans_core/"):
                        relative = "_sbml4humans_runtime/" + name
                    elif name.startswith("sbml4humans_core.libs/"):
                        # Preserve the wheel repair tool's relative shared-library paths.
                        relative = "_sbml4humans_runtime/" + name
                    else:
                        continue
                    target = stage / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(name))
                stage.rename(directory)
    code = "import json,sys; sys.path.insert(0,sys.argv[1]); import _sbml4humans_runtime as r; print(json.dumps({k:getattr(r,k,None) for k in ['SOURCE_REVISION','HOST_CONTRACT','VALIDATION_SOURCE_CONTRACT','ODE_SOURCE_CONTRACT']}))"
    checked = subprocess.run(
        [sys.executable, "-B", "-I", "-c", code, str(directory)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if checked.returncode:
        raise RuntimeError(
            "The bundled Rust runtime cannot load on this host:\n"
            + checked.stderr.strip()
        )
    actual = json.loads(checked.stdout)
    expected = {
        "SOURCE_REVISION": pin["revision"],
        "HOST_CONTRACT": "host/1",
        "VALIDATION_SOURCE_CONTRACT": "validation-source/1",
        "ODE_SOURCE_CONTRACT": "ode-source/1",
    }
    if actual != expected:
        raise RuntimeError(
            f"The bundled Rust runtime does not match the application pin: {actual}"
        )
    return directory / "_sbml4humans_runtime", tags


def runtime() -> tuple[Path, str]:
    """Reuse a verified native artifact or compile the pinned source once."""
    from filelock import FileLock

    pin = json.loads(PIN_PATH.read_text())
    with FileLock(str(cache_root() / "build.lock"), timeout=3600):
        selected = os.environ.get("SBML4HUMANS_NATIVE_WHEEL")
        if selected:
            path = Path(selected).resolve()
            wheels = (
                list(path.glob("sbml4humans_core-*.whl")) if path.is_dir() else [path]
            )
            if len(wheels) != 1:
                raise RuntimeError(
                    "SBML4HUMANS_NATIVE_WHEEL must select exactly one runtime wheel."
                )
            return payload(wheels[0], pin)
        wheels_dir = (
            cache_root() / "wheels" / sysconfig.get_platform() / pin["revision"]
        )
        wheels = list(wheels_dir.glob("*.whl"))
        if len(wheels) == 1:
            return payload(wheels[0], pin)
        local = os.environ.get("SBML4HUMANS_CORE_SOURCE")
        source = (
            Path(local).resolve()
            if local
            else cache_root() / "sources" / pin["revision"]
        )
        if not source.exists():
            if local:
                raise RuntimeError(f"SBML4HUMANS_CORE_SOURCE does not exist: {source}")
            source.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(dir=source.parent) as temporary:
                stage = Path(temporary) / "source"
                stage.mkdir()
                run(["git", "init", "--quiet"], stage)
                run(["git", "remote", "add", "origin", pin["repository"]], stage)
                run(
                    [
                        "git",
                        "fetch",
                        "--quiet",
                        "--depth",
                        "1",
                        "origin",
                        pin["revision"],
                    ],
                    stage,
                )
                run(["git", "checkout", "--quiet", "--detach", "FETCH_HEAD"], stage)
                stage.rename(source)
        return payload(build_core(source, wheels_dir, pin), pin)
