# Native runtime

SBML4Humans has one SBML implementation: Rust. FastAPI handles HTTP, uploads, downloads, caching, cancellation and worker admission. Pydantic describes the public API. Annotation HTTP services continue to use pymetadata. There is no Python SBML parser, renderer, equation generator or validation fallback.

The shared [sbml4humans-core](https://github.com/matthiaskoenig/sbml4humans-core) reads SBML and COMBINE archives, resolves admitted companions, builds units, equations and reference graphs, and calls native libSBML for validation and validation-rule documentation. ODE code generation comes from the shared sbmlsim-core Rust crate. Browser workers use the same report implementation as import-free WASM.

## Installation

A platform wheel includes its native runtime privately as `_sbml4humans_runtime`. Installing a matching wheel needs neither a Rust compiler nor a separate `sbml4humans-core` Python package. The private package preserves its repaired shared-library paths and works with editable source mounts. Its ABI3 extension supports Python 3.12 and later.

Source and editable installations compile the exact revision in `backend/sbml4humans/native-source.json`. This file is generated from `parser-source.json`; do not edit it independently. A source build needs Git, Bash, Rust 1.100, CMake, Make, a C++ compiler and the development headers of Expat, zlib and bzip2. On Debian or Ubuntu:

```bash
sudo apt-get install g++ cmake make libexpat1-dev zlib1g-dev libbz2-dev
rustup toolchain install 1.100.0 --profile minimal
uv sync --project backend --locked
uv run --project backend --no-sync uvicorn sbml4humans.api:api --port 1444
```

Native builds default to two Cargo jobs and two CMake jobs. `CARGO_BUILD_JOBS` and `CMAKE_BUILD_PARALLEL_LEVEL` can allocate a different build budget. `SBML4HUMANS_BUILD_CACHE` selects the build cache, otherwise it is `~/.cache/sbml4humans-build`. A process lock prevents concurrent source builds from duplicating the same compilation. Native caches distinguish the host platform, architecture and libc version. libSBML prefixes are shared by build-script hash, so a report-only Rust change does not rebuild the C++ library. `LIBSBML_DIR` selects an existing compatible prefix.

CI builds the native runtime once and passes the same artifact to backend tests, documentation, browser tests and package builds. The production image is built separately and checked with its installed private runtime. Release builds do not restore the native build cache.

## Updating the pin

Merge and test the Rust change first, then update `parser-source.json`. Generate both installed provenance and browser assets with the supported builder:

```bash
python3 scripts/build_parser.py --source /path/to/clean/sbml4humans-core --wasm
python3 scripts/build_parser.py --check
```

The application checks the runtime's compiled source revision and required host contracts. A missing or mismatched runtime stops startup with an installation error. It never selects another parser or compiles code during a request.

For package builds, `SBML4HUMANS_NATIVE_WHEEL` can name a previously built runtime wheel or a directory containing one. The build hook verifies its revision, capabilities and ABI3 tag before bundling it. `SBML4HUMANS_CORE_SOURCE` can select a clean local checkout at the exact pin when building from source. These are build inputs, not runtime parser modes.

Remove obsolete `SBML4HUMANS_PARSER=python` and `SBML4HUMANS_PARSER=auto` settings. Rust is mandatory. No Python libSBML, lxml, NumPy, Pint or sbmlsim-core package is installed by the backend.

## Work and memory

Rust serializes reports directly into gzip. API responses and local report tokens retain those bytes, without constructing and serializing a second report in Python. Equation diagnostics travel separately from the report, so logging an equation failure does not decode a large JSON response.

Validation and ODE preparation share the canonical key builder and comp expansion analysis. Their lightweight projection skips rendered math, unit inference and copied XML. Example metadata reads the manifest and selected model without building a report or extracting an archive into Python temporary files. Selected example entries use the same confined companion-admission logic as local models.

Untrusted reports, ODE downloads and validation run in separate worker processes. Source limits, comp expansion limits, deadlines, memory bounds and cancellation remain active. Math ASTs deeper than 10,000 nodes are refused with a diagnostic, including flat sums represented internally as binary trees. Validation sends completed entries individually, so an interrupted worker preserves its earlier results. Rust allocation aborts retain the `memory` interruption status.

## Verification

The Rust workspace owns the parser, math, units, links, comp and code-generation tests. Backend tests cover the HTTP and process boundaries and compare every report field against independent fixtures captured before the Python implementation was removed. The fixture provenance records its source revision; do not regenerate expected results from the implementation being tested.

The installed-wheel and source-distribution checks must run outside the repository. They verify private runtime loading, provenance, licenses, CLI reports and the absence of the removed Python engines. Native libSBML license and copyright notices are included in the distribution; the application and Rust source remain available under their respective licenses.
