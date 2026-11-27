# Backend architecture

The backend is a FastAPI transport around one required Rust implementation. Commands and the error contract are in the repository `CLAUDE.md`. Read `glossary/CLAUDE.md` before changing glossary generators, report DTOs or UI labels.

## Native runtime

`native.py` loads `_sbml4humans_runtime`, checks its compiled revision against the generated `native-source.json`, and checks the host, validation and ODE contracts. Missing or mismatched binaries stop startup. There is no optional parser, Python engine or runtime compilation. Obsolete `SBML4HUMANS_PARSER=python` and `auto` settings fail explicitly.

`parser-source.json` is the single source pin. `scripts/build_parser.py --wasm` generates the installed manifest, license copies and browser SDK. `--check` verifies them; `--verify-build` rebuilds WASM and checks every artifact. `backend/build_native.py` builds or validates the exact ABI3 runtime; `hatch_build.py` bundles it privately in platform wheels and editable installs. The private package contains the original native package and its repaired libraries beneath one owner, preserving relative library paths and avoiding collisions with a standalone core distribution. Wheels require no compiler; source builds need the documented Rust/C++ toolchain. Build cache, artifact and local-source overrides are build inputs only. See `docs/native-runtime.md`.

## Reports and workers

`report.py` passes paths, source limits, trust, optional selected example entries and expansion budgets to Rust. Rust reads SBML/gzip/OMEX, admits confined companions, builds canonical identities, units, math, graphs, equations and ODE exports, and serializes directly into gzip. Diagnostic strings are returned separately; Python never decodes report JSON to log equation failures. The Pydantic `model.py` classes are API DTOs and OpenAPI/schema inputs, not a report builder.

Untrusted reports and ODE files run under `isolation.REPORT_BUDGET`; validation uses `VALIDATION_BUDGET`. A job captures limits and `limits.MAX_EXPANDED_ELEMENTS` before entering the forkserver. Independent admission and concurrency limits prevent reports from starving validation. Each child has a deadline, address-space/CPU bounds and a temporary directory; cancellation kills it and frees admission. Validation sends locations and completed entry results separately, preserving results when a worker ends early. Rust allocator aborts and native `bad_alloc` failures retain the memory status. The forkserver maps the required native library and preloads the thin report adapter before child memory limits apply, without Python numerical/SBML stacks.

The process is a resource boundary, not a filesystem or network sandbox. Rust confines trusted standalone companions to their selected directory after canonical/symlink resolution; uploads and archives never discover disk neighbors. Native validation resolves only admitted documents. A selected example entry uses the same companion admission logic inside its archive directory, without Python extraction.

## HTTP and caches

`api.py` keeps the existing report, validation, ODE, example, upload and annotation endpoints. Report endpoints return final serialized bytes and retain `response_model` for OpenAPI. `report_response` sends gzip directly when accepted and decompresses in the threadpool otherwise. The middleware, traceback policy and image exception follow the repository error contract. Startup validates the native runtime, loads lightweight Rust example metadata and starts the forkserver.

`examples.py` creates lightweight example DTOs from native metadata. The API keeps immutable example reports as compressed bytes. `local.py` also keeps local report tokens as compressed bytes, with paths for later validation/export; neither cache stores a second Python object graph.

`download.py` enforces deadlines, redirect limits and public addresses, connects only to checked addresses, and prevents DNS rebinding. `limits.py` owns source/body limits and the comp budget. `SBML4HUMANS_ALLOW_PRIVATE_URLS=1` is for local tests only. `uploads.py` owns upload lifetime and cleanup.

`annotations.py` is the HTTP-service adapter around pymetadata, with typed results and bounded, coalesced caching. Known results live 24 hours, warnings 10 minutes, errors are not cached; at most 5,000 entries are retained. The disk cache uses `SBML4HUMANS_CACHE`. URLs shown by the report are HTTP(S) only. ChEBI structures use the existing sandboxed SVG response and 404 behavior. These HTTP services remain Python server code and do not import any removed SBML engine.

## Local interface and verification

`viewer.py`, `localstate.py` and `cli.py` implement `sbml4humans.show`, local server discovery, secret-protected file access, browser opening and shutdown. `localstate.py` stays cheap to import. The local app refuses foreign hosts/origins and routes public API traffic through the normal security rules. Do not add a `show.py` module which shadows the exported function.

The Rust workspace owns parser, units, math, linking, comp and generation tests. Backend tests own transport, isolation, source admission and independent wire snapshots in `tests/fixtures/rust-contract.json`. Those snapshots were captured from the previous implementation; do not regenerate expected results from the Rust code under test. Keep HTTP tests with `raise_server_exceptions=False`. Package smoke checks run outside the checkout and exercise the bundled runtime, source provenance, licenses and CLI.
