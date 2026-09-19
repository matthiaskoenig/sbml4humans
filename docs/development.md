# Development

Everything below starts from a clone of the repository:

```bash
git clone https://github.com/matthiaskoenig/sbml4humans.git
cd sbml4humans
```

## Repository layout

| path | content |
| --- | --- |
| `frontend/` | the Vue 3 application (Vite, TypeScript, Pinia, Vue Router, Tailwind CSS, Lucide icons) |
| `backend/` | the `sbml4humans` Python package: the report of a document (`sbmlinfo`, `mathml`, `units`) and the FastAPI api which serves it |
| `glossary/` | the glossary the reference pages of the documentation and the explanations of the application are generated from |
| `docs/`, `zensical.toml` | the pages and the configuration of the documentation site |
| `release-notes/` | one file per version, the body of its GitHub release and a section of the generated [release notes](release-notes.md) page |
| `nginx/` | the proxy configuration of sbml4humans.de |
| `Dockerfile`, `docker-compose-*.yml` | the containers of the backend, the frontend and the proxy |
| `deploy.sh`, `docker-purge.sh`, `deploy.md` | the deployment of sbml4humans.de on its server |
| `CITATION.cff` | how to cite SBML4Humans, the same citation as the README |
| `LICENSE`, `backend/LICENSE` | the MIT license, and the copy of it which the wheel and the sdist of the package ship; a test keeps the two identical |

## Frontend and backend with docker compose

```bash
sudo docker compose -f docker-compose-develop.yml build --no-cache
sudo docker compose -f docker-compose-develop.yml up
```

The frontend answers on <http://localhost:8083>, the api on <http://localhost:1444>.

## Backend

The backend is the `sbml4humans` Python package in `backend/`, it requires Python 3.14 and [uv](https://docs.astral.sh/uv/). The report is created with libsbml, lxml (the math), pint (the units) and pymetadata (COMBINE archives and annotations); the example models are part of the package (`backend/sbml4humans/resources/`).

```bash
cd backend
uv sync
uv run uvicorn sbml4humans.api:api --reload --port 1444
```

`uv sync` creates `backend/.venv` with the pinned dependencies of `uv.lock` and installs `sbml4humans` editable. The api answers on port 1444, e.g. <http://localhost:1444/api/examples>, the OpenAPI documentation on <http://localhost:1444/docs>. With `--reload` the server restarts on changes in `backend/`. A dependency change goes through `uv add`/`uv lock`, commit the updated `uv.lock` with it, the CI installs from the lock. The JSON schema of the api response is generated from the pydantic model into `frontend/src/schema/report.schema.json` with `uv run python -m sbml4humans.schema`.

`sbml4humans.show` and the command `sbml4humans` ([Reports from python](python.md)) serve the built frontend from inside the package, `backend/sbml4humans/resources/frontend/`, which is git ignored and created by `npm run build:package` in `frontend/`: a production build with the api at the relative address `/api` and without analytics (`frontend/.env.package`). Without it `show` fails with that command. The environment variable `SBML4HUMANS_FRONTEND` serves another build instead, and `SBML4HUMANS_STATE_DIR` moves the state file and the log of the local server out of the cache directory of the user, which is what the tests do.

Tests, linting and type checks run from the `backend` directory, the same checks run as GitHub Actions on every pull request (see [Branches and pull requests](#branches-and-pull-requests)):

```bash
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run ty check
```

## Frontend

The frontend needs node 24 (`frontend/.nvmrc`), e.g. with [nvm](https://github.com/nvm-sh/nvm):

```bash
cd frontend
nvm install    # reads .nvmrc, once
nvm use
npm ci
npm run dev
```

The development server runs on <http://localhost:3456> and talks to the backend api on port 1444 (`frontend/.env.development`).

Linting, type checks, unit and end to end tests run from the `frontend` directory, the same checks run as GitHub Actions on every pull request:

```bash
npm run lint
npm run typecheck
npm run test:unit
npm run test:e2e
```

## Documentation

The documentation is this Zensical site, built from the sources in `docs/` with the configuration in `zensical.toml`, from the repository root:

```bash
uv run --project backend zensical serve   # live preview
uv run --project backend zensical build --clean --strict   # build into site/
```

`--strict` aborts the build on a warning, i.e. on a link or an anchor of a page which does not resolve; the `documentation` workflow builds the site the same way, so a broken link fails the check instead of reaching the published page.

`site/` is git ignored, it is built by the `documentation` workflow and published to <https://matthiaskoenig.github.io/sbml4humans/>. Three files are generated, not written by hand, from the glossary in `glossary/`: the reference pages under `docs/reference/`, the tooltips of the application (`frontend/src/data/glossary.json`) and the explanations of its help dialog (`frontend/src/data/glossary-details.json`). All three are committed.

```bash
cd backend
uv run python -m sbml4humans.glossary           # regenerate all three, commit the result
uv run python -m sbml4humans.glossary --check   # the check of the documentation workflow
```

The glossary names what it explains: the `label` of a type is the name of its class in the specification, the `label` of an attribute which cites a specification is its name there (`initialConcentration`, and `fbc:charge` for an attribute a package adds to a type of the core), the `label` of a link kind is its key, and only what the report adds is labelled in plain words (`derived units`). The application takes the headers of its columns, the labels of the rows of its inspector and the names of its link groups from these labels and states none of its own, so a name is changed in the glossary and nowhere else.

An attribute states its low level next to its prose, which the reference page and the dialog both show. The header comment of `glossary/core.toml` holds the conventions in full, these are the keys:

- `required`, whether the specification demands the attribute. Every attribute which cites a `spec` states it, an attribute the report adds never does, because no specification asks anything of it.
- `default`, one clause in plain words which says what holds when the attribute is absent, only next to `required = false` and only where the absence teaches the reader something. Level 3 defines no default values, so this says what holds instead, no stronger than the specification says.
- `rules`, the numbers of the validation rules of libsbml which concern the entry, on an attribute and on a type. Their text is never written in the glossary: the generator reads the message, the severity and the section of the specification from libsbml, the library which judges the file of a reader. A rule is cited at the attribute its message is about and at the type when it concerns the element as a whole; rules about MathML, about units consistency or about modelling practice in general are left out, as is a rule whose sentence is not true for the reader of the page.
- `values`, the literals of an enumeration, in the order and the spelling of the specification.
- `[datatypes.*]`, one entry per `type` an attribute names which is no type of the glossary. An entry which cites a `spec` is a data type of that specification (`SIdRef`, `double`, `FbcType`), one without a `spec` a kind of value the report adds (`latex`, `Math`). Every `type` has to resolve to such an entry or to a type of the glossary, and a data type nothing uses is an error.

The number of a rule is found with `resolve_rule`, which answers exactly what the generator would write, so a candidate is read before it is cited. With `uv run python` from `backend/`:

```python
from sbml4humans.glossaryrules import resolve_rule

for code in range(20608, 20612):
    rule = resolve_rule(code)
    print(code, rule.severity, rule.message)
```

`--check` regenerates into a temporary directory and fails when a committed file is not current, when a type or a field of the report model has no entry, when a label of the specification is not such a name, when a type or an attribute entry explains something the report does not have, when an attribute of a specification does not state whether it is required, when an attribute the report adds states `required` or when a `default` stands next to `required = true`, when a rule number is unknown to libsbml, is cited twice in one entry or belongs to another package than the entry, when a `type` resolves to neither a data type nor a type of the glossary or a data type is unused, when a link of a description does not resolve to a page or to an anchor of one, when a page references a missing image, or when the navigation in `zensical.toml` does not list a generated page.

The [release notes](release-notes.md) page is generated as well, from the files of `release-notes/`, the versions newest first:

```bash
cd backend
uv run python -m sbml4humans.releasenotes           # regenerate docs/release-notes.md, commit the result
uv run python -m sbml4humans.releasenotes --check   # the check of the documentation workflow
```

`--check` fails when the committed page is not current, when the version of the package has no file in `release-notes/` and when a file there is not named after a version. The version bump of a release runs the generator, so a release which follows the steps below needs no extra step.

The screenshots of `docs/images/` are taken by `frontend/scripts/screenshots.mjs` against a running backend and a running dev server:

```bash
cd backend && uv run uvicorn sbml4humans.api:api --port 1444 &
cd frontend && npx vite --port 3456 &
cd frontend && npm run screenshots
```

The images are committed like any other source file. Nothing compares them with the application: the check of the documentation only verifies that an image a page references exists, so a screenshot which shows an interface that no longer exists passes every check. Rerun the script and commit the result after a change of the user interface that a screenshot shows, so the documentation keeps matching what the application looks like.

## Branches and pull requests

- **`develop`** is the branch everything is integrated into.
- **`main`** tracks the latest release. It is fast-forwarded to the released commit by the `sync-main` job of `ci-cd.yml` after the GitHub release was created, so `main` and the newest release always agree. Nothing is developed on `main` and nothing is merged into it by hand.

Work happens on short lived branches off `develop`, which GitHub deletes after the merge. `develop` does not accept a direct push, every change goes through a pull request against `develop`. This includes the maintainer, there is no bypass.

A pull request can only be merged once the required checks are green:

| check      | workflow    | content                                                                                     |
| ---------- | ----------- | ------------------------------------------------------------------------------------------- |
| `test`     | `ci-cd.yml` | `pytest` of the backend                                                                     |
| `schema`   | `ci-cd.yml` | the committed JSON schema of the report is current                                          |
| `frontend` | `ci-cd.yml` | the generated types are current, lint, type check, unit tests and the build of the frontend |
| `e2e`      | `ci-cd.yml` | the Playwright end to end tests against the backend                                         |
| `ruff`     | `ruff.yml`  | `ruff check` and `ruff format --check` of the backend                                       |
| `ty`       | `ty.yml`    | `ty check` of the backend                                                                   |
| `docs`     | `docs.yml`  | the documentation site builds                                                               |

Further rules of a pull request:

- conversations have to be resolved before the merge
- an approval is dismissed when new commits are pushed
- the history stays linear, i.e., a pull request is merged with squash or rebase; merge commits are disabled
- the maintainer is the code owner of the repository (`.github/CODEOWNERS`) and is requested for review on every pull request. A pull request is therefore reviewed and merged by the maintainer, who has the only write access. The rulesets themselves do not require an approval: on a personal repository a ruleset cannot ask for an approval only from somebody else, and requiring one would block the pull requests of the maintainer, who cannot approve their own. Once a second person has write access, a ruleset requiring an approving review of a code owner can be added

[Auto-merge](https://docs.github.com/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/automatically-merging-a-pull-request) is enabled, so a pull request can be queued and is merged as soon as the checks pass.

The protection is implemented with [repository rulesets](https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets), which are part of the repository in `.github/rulesets/`, so a change to a policy is reviewed like any other change:

| ruleset        | applies to | rules                                                                                                                                                                                                                                 |
| -------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `develop.json` | `develop`  | pull request required, the checks above, resolved conversations, linear history, no force push, no deletion. **No bypass, for anybody.**                                                                                         |
| `main.json`    | `main`     | no force push, no deletion, no bypass. The fast-forward of the release workflow needs none, only a force push would be rejected. `main` follows `develop`, whose history carries merge commits from before merge commits were disabled, so `main` cannot require a linear history |
| `tags.json`    | all tags   | a tag cannot be deleted or moved, so a release tag keeps pointing at what was released                                                                                                                                               |

Changing a policy means changing the json and applying it:

```bash
.github/rulesets/apply.sh
```

The script is idempotent: it updates the rulesets which exist and creates the missing ones. It also sets the merge settings of the repository, i.e., auto-merge, delete branch on merge, and squash and rebase as the only merge methods. It needs the [github cli](https://cli.github.com) authenticated as a user with admin permission on the repository.

## Releases

The version of SBML4Humans is the version of the backend package in `backend/sbml4humans/__init__.py`, the frontend `package.json` follows it. A release is made from `develop`. Since `develop` only accepts pull requests, the release is prepared on a branch and tagged once that pull request is merged:

1. branch off `develop`: `git switch -c release/x.y.z origin/develop`
2. write the release notes for the version in `release-notes/x.y.z.md` and commit them, the bump needs a clean working tree
3. bump the version from the `backend` directory: `uv run bump-my-version bump [major|minor|patch]`, which updates `backend/pyproject.toml`, `backend/sbml4humans/__init__.py`, `frontend/package.json` and the version of the package in `frontend/package-lock.json`, writes the [release notes](release-notes.md) page of the documentation from `release-notes/` and commits. It does not create the tag; a squash or rebase merge would rewrite the commit and leave the tag behind on a commit which is not part of `develop`
4. push the branch, open the pull request against `develop` and merge it once the checks are green
5. tag the merged commit on `develop` and push the tag:

    ```bash
    git switch develop
    git pull
    git tag x.y.z
    git push origin x.y.z
    ```

    This starts the `CI/CD` workflow, which runs the checks, creates the [GitHub release](https://github.com/matthiaskoenig/sbml4humans/releases) from `release-notes/x.y.z.md`, fast-forwards `main` to the tagged commit and publishes the package to [PyPI](https://pypi.org/project/sbml4humans/). Check the version before pushing, a tag cannot be moved or deleted afterwards.

The package on PyPI is the wheel and the sdist which the `package` job builds on every pull request, with the frontend built into them, and which it installs into a fresh environment to open a report with. The `publish` job uploads them by [trusted publishing](https://docs.pypi.org/trusted-publishers/), which needs no token and is set up once: the project `sbml4humans` on PyPI names the repository `matthiaskoenig/sbml4humans`, the workflow `ci-cd.yml` and the environment `pypi` as its publisher (for the first release as a [pending publisher](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)), and the repository has an environment `pypi`. The job runs next to the GitHub release, so a failed upload leaves the release and `main` as they are and can be run again.

The release is archived on [Zenodo](https://zenodo.org/), which mints a DOI for it. Update the citation afterwards: the version and the DOI of the release in the "How to cite" section of `README.md` and of `docs/index.md` and in `CITATION.cff`. The badge and the "archived software" link carry the concept DOI `10.5281/zenodo.22827237`, which always resolves to the newest version and does not change; the citation itself names the DOI of the version.
