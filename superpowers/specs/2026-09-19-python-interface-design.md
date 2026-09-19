# A report from python

**Issue:** [#33](https://github.com/matthiaskoenig/sbml4humans/issues/33) - "Python interface to create report": a simple way to create a report from python, `sbml4humans(path)`, to inspect generated models, in the long run the replacement of cy3sbml in the browser.

**Goal:** one call, `sbml4humans.show(path)`, or one command, `sbml4humans model.xml`, opens the report of a local SBML file or COMBINE archive in the browser. The model never leaves the machine, the report works offline, and the files next to a comp model are followed ([#36](https://github.com/matthiaskoenig/sbml4humans/issues/36)).

## Decisions

1. **A local server, not an upload.** The wheel of `sbml4humans` ships the built frontend, and the call starts the api and the frontend on a port of `127.0.0.1`. An upload to sbml4humans.de would send unpublished models to a server and would make that server keep reports; it is not built.
2. **The server outlives the call.** A script which calls `show()` and ends must leave a working page, and the page needs the api for as long as it is open (the annotation resources are resolved on demand). So `show()` starts the server as a detached process, later calls reuse it, and it ends itself when no page is open any more.
3. **The report is built when `show()` is called**, from the path, as a trusted path: a temporary file may be gone a moment later, and the external model definitions of a comp model are resolved against the files next to it.
4. **`show` is a function of the package**, `from sbml4humans import show`, not a callable module.

## The pieces

**`sbml4humans/local.py`, the local server.** `LocalApp` is a small ASGI application which routes by path: `/api/local/...` to the local endpoints, every other `/api/...` and the OpenAPI pages to the public `api` unchanged, and everything else to the built frontend, with `index.html` for every path which is no file, because the router of the frontend uses the history mode. The local endpoints follow the error contract of the api:

| endpoint | what it does |
| --- | --- |
| `GET /api/local/ping` | answers with the version, and counts as a sign of life |
| `POST /api/local/reports` `{"path": ...}` | builds the report of the path (`report_for_path(path, trusted=True)`), keeps it under a new token and answers `{"token", "url"}`; needs the secret |
| `GET /api/local/reports/{token}` | the `ReportResponse` of the token |
| `POST /api/local/shutdown` | ends the server; needs the secret |

The reports are kept in memory, the last 16 of them. `serve(port, secret, idle_timeout)` runs the app with uvicorn on `127.0.0.1`, writes the state file when it is up, removes it when it ends, and ends when no request arrived for `idle_timeout` (15 minutes). An open report page pings every minute, so the server lives as long as a page is open.

**Who may talk to the server.** The public api allows every origin, which is right for a public service and wrong on localhost, where any web page of the browser could otherwise ask the server to read a path or to download a url from inside the network. `LocalApp` therefore answers 403 to a request whose `Host` is not `127.0.0.1:<port>` or `localhost:<port>` (DNS rebinding) or whose `Origin` is another origin (cross site requests). The two endpoints which act on the machine, building a report of a path and the shutdown, additionally need the secret of the state file in the header `X-SBML4Humans-Secret`, which only a process of the same user can read (file mode 0600). A token is 128 random bits, so a report is only read by who was given its url.

**`sbml4humans/show.py`, the client.** `show(path, open_browser=True) -> str` checks the path, finds the running server through the state file (`<user cache dir>/sbml4humans/server.json` with port, pid, secret and version, located with `platformdirs`) and a ping, starts one if there is none (`python -m sbml4humans.local` as a detached process on a free port, the secret handed over in the environment, the log next to the state file) or if it is one of another version (which is shut down first), posts the path, opens `http://127.0.0.1:<port>/report?local=<token>` with `webbrowser` and returns the url. An error of the report, a file which is no SBML, is raised as `ValueError` with the message of the api. `stop()` shuts the server down.

**`sbml4humans/cli.py`, the command.** `sbml4humans PATH [--no-browser]`, `sbml4humans --stop`, `sbml4humans --version`, registered as the console script `sbml4humans`.

**The frontend.** `/report?local=<token>` is a fourth source of the report store (`loadLocal`, `GET /local/reports/<token>`), kept in the route like `url`. While a report of that source is shown, the page pings the server every minute. The build for the package is a vite mode of its own, `npm run build:package` (`.env.package`: the api at the relative `/api`, analytics off), which writes into the git ignored `backend/sbml4humans/resources/frontend/`. `VITE_ANALYTICS=off` keeps vue-gtag out of that build: a local tool does not report to Google Analytics.

**Packaging and release.** `[tool.hatch.build] artifacts` takes the git ignored frontend build into the wheel and the sdist. `show()` in a checkout without the build fails with the command which creates it. The `package` job of `ci.yml` builds the frontend and the wheel on every pull request, installs the wheel into a fresh environment and checks there that `sbml4humans --no-browser` answers with a url which serves the page and the report. On a tag, the `publish` job uploads the same artifacts to PyPI by trusted publishing; it runs next to the GitHub release and does not block `sync-main`. The PyPI project and its trusted publisher are configured once by the maintainer, `docs/development.md` says how.

## Tests

- `tests/test_local.py`: the routing (api, local, static, the fallback to `index.html`, no path traversal out of the frontend directory), the host and origin checks, the secret, the token store and its limit, the error contract for a path which is no SBML, the idle watcher.
- `tests/test_show.py`: `show()` against a real server process on a free port with a state directory of the test: it starts one, reuses it, returns a url which serves the report, raises for a missing file and for a file which is no SBML, replaces a server of another version, and `stop()` ends it and removes the state file.
- Frontend unit tests of the client, the store and the page (the `local` source, the ping), an end to end test of `/report?local=` with the api answered by the test.
- The `package` job is the end to end test of the real thing: the wheel, the server, the page.

## Out of scope

An upload endpoint on sbml4humans.de, a Jupyter widget, and support for python below 3.14, which is the requirement of the package.
