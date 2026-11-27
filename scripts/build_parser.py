"""Build or verify the pinned Rust parser used by the application.

The browser package is committed so regular frontend and Python package builds need
no Rust toolchain. CI rebuilds it from pinned source and verifies every shipped byte.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "frontend/vendor/sbml4humans-core"
SDK = [
    "index.mjs",
    "wasm.mjs",
    "worker.mjs",
    "index.d.mts",
    "wasm.d.mts",
    "report.d.ts",
    "runtime/sbml4humans-core.wasm",
]


def digest(path: Path) -> str:
    """Return the SHA256 of a generated artifact."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(arguments: list[str], cwd: Path) -> None:
    """Run a build command without interpreting shell text."""
    subprocess.run(arguments, cwd=cwd, check=True)


@contextmanager
def checkout(pin: dict[str, str], local: Path | None) -> Iterator[Path]:
    """Use the exact reviewed revision, in a temporary checkout by default."""
    with tempfile.TemporaryDirectory(prefix="sbml-parser-") as temporary:
        source = Path(temporary) if local is None else local.resolve()
        if local is None:
            run(["git", "init", "--quiet"], source)
            run(["git", "remote", "add", "origin", pin["repository"]], source)
            run(
                ["git", "fetch", "--quiet", "--depth", "1", "origin", pin["revision"]],
                source,
            )
            run(["git", "checkout", "--quiet", "--detach", "FETCH_HEAD"], source)
        actual = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=source, text=True
        ).strip()
        if actual != pin["revision"]:
            raise SystemExit(f"Parser revision is {actual}, expected {pin['revision']}")
        dirty = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=normal"],
            cwd=source,
            text=True,
        )
        if dirty.strip():
            raise SystemExit(
                "The parser checkout must have no tracked or untracked changes"
            )
        yield source


def render(source: Path, destination: Path, pin: dict[str, str]) -> None:
    """Assemble the runtime package and its complete provenance."""
    schema = ROOT / "frontend/src/schema/report.schema.json"
    if (source / "js/report.schema.json").read_bytes() != schema.read_bytes():
        raise SystemExit("The parser report schema differs from the application schema")
    if (source / "js/report.d.ts").read_bytes() != (
        ROOT / "frontend/src/types/report.ts"
    ).read_bytes():
        raise SystemExit("The parser report types differ from the application types")
    if destination.is_symlink():
        raise SystemExit(
            "Refusing to replace a symlink as the generated parser package"
        )
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for name in SDK:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / "js" / name, target)
    shutil.copyfile(source / "LICENSE", destination / "LICENSE")
    upstream = json.loads((source / "js/package.json").read_text())
    package = {
        key: upstream[key]
        for key in ("name", "version", "type", "private", "exports", "types")
    }
    package.update(license="MIT", repository=pin["repository"])
    (destination / "package.json").write_text(json.dumps(package, indent=2) + "\n")
    files = [*SDK, "LICENSE", "package.json"]
    provenance = {
        **pin,
        "generator": "scripts/build_parser.py",
        "schemaSha256": digest(schema),
        "files": {name: digest(destination / name) for name in sorted(files)},
    }
    (destination / "SOURCE.json").write_text(json.dumps(provenance, indent=2) + "\n")


def verify(pin: dict[str, str]) -> None:
    """Check committed artifacts without a compiler, network or external checkout."""
    provenance = json.loads((VENDOR / "SOURCE.json").read_text())
    for key, value in pin.items():
        if provenance.get(key) != value:
            raise SystemExit(f"Parser provenance differs at {key}")
    if provenance["schemaSha256"] != digest(
        ROOT / "frontend/src/schema/report.schema.json"
    ):
        raise SystemExit("Parser schema hash differs from the application schema")
    if set(provenance["files"]) != {*SDK, "LICENSE", "package.json"}:
        raise SystemExit("The parser package has an unexpected artifact inventory")
    for name, expected in provenance["files"].items():
        if digest(VENDOR / name) != expected:
            raise SystemExit(
                f"Parser artifact differs: {name}; rebuild from pinned source"
            )
    print("Pinned parser package and schema verified.")


def main() -> None:
    """Build the pinned browser/native package or verify committed artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path, help="Existing clean checkout at the pinned revision"
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--wasm", action="store_true")
    parser.add_argument("--verify-build", action="store_true")
    parser.add_argument("--wheel-out", type=Path)
    args = parser.parse_args()
    pin = json.loads((ROOT / "parser-source.json").read_text())
    if args.check:
        verify(pin)
    if not (args.wasm or args.verify_build or args.wheel_out):
        if not args.check:
            parser.error("Choose --check, --wasm, --verify-build or --wheel-out")
        return
    with checkout(pin, args.source) as source:
        if args.wasm or args.verify_build:
            run(["node", "js/build.mjs"], source)
            if args.verify_build:
                with tempfile.TemporaryDirectory(
                    prefix="sbml-parser-verify-"
                ) as temporary:
                    rendered = Path(temporary)
                    render(source, rendered, pin)
                    if (rendered / "SOURCE.json").read_bytes() != (
                        VENDOR / "SOURCE.json"
                    ).read_bytes():
                        raise SystemExit(
                            "Rebuilt parser differs from committed artifacts"
                        )
                    print("Rebuilt parser matches all committed artifacts.")
            else:
                render(source, VENDOR, pin)
        if args.wheel_out:
            if not os.environ.get("LIBSBML_DIR"):
                run(["bash", "scripts/build-libsbml.sh"], source)
            output = args.wheel_out.resolve()
            output.mkdir(parents=True, exist_ok=True)
            run(
                [
                    "uv",
                    "tool",
                    "run",
                    "--from",
                    "maturin[patchelf]>=1.16,<2",
                    "maturin",
                    "build",
                    "--release",
                    "--locked",
                    "--features",
                    "validation",
                    "--out",
                    str(output),
                ],
                source,
            )


if __name__ == "__main__":
    main()
