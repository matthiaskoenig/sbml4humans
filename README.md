# SBML4Humans

[SBML4Humans](https://sbml4humans.de) renders [SBML](https://sbml.org) models as interactive, human readable reports: a Vue frontend on top of a FastAPI backend which creates the report of a model with [libsbml](https://sbml.org/software/libsbml/).

The report is self-contained: the backend reads the model with libsbml and renders the math, units and annotations itself.

## Repository layout

| path | content |
| --- | --- |
| `frontend/` | the Vue 3 application (Vite, TypeScript, Pinia, Vue Router, Tailwind CSS, Lucide icons) |
| `backend/` | the `sbml4humans` Python package: the report of a document (`sbmlinfo`, `mathml`, `units`) and the FastAPI api which serves it |
| `nginx/` | the proxy configuration of sbml4humans.de |
| `Dockerfile`, `docker-compose-*.yml` | the containers of the backend, the frontend and the proxy |
| `deploy.md`, `deploy.sh`, `docker-purge.sh` | deployment of the server |

## Development

```bash
git clone https://github.com/matthiaskoenig/sbml4humans.git
cd sbml4humans
```

### Frontend and backend with docker compose

```bash
sudo docker compose -f docker-compose-develop.yml build --no-cache
sudo docker compose -f docker-compose-develop.yml up
```

The frontend answers on <http://localhost:8083>, the api on <http://localhost:1444>.

### Backend

The backend is the `sbml4humans` Python package in `backend/`, it requires Python 3.14 and [uv](https://docs.astral.sh/uv/). The report is created with libsbml, lxml (the math), pint (the units) and pymetadata (COMBINE archives and annotations); the example models are part of the package (`backend/sbml4humans/resources/`).

```bash
cd backend
uv sync
uv run uvicorn sbml4humans.api:api --reload --port 1444
```

`uv sync` creates `backend/.venv` with the pinned dependencies of `uv.lock` and installs `sbml4humans` editable. The api answers on port 1444, e.g. <http://localhost:1444/api/examples>, the OpenAPI documentation on <http://localhost:1444/docs>. With `--reload` the server restarts on changes in `backend/`. A dependency change goes through `uv add`/`uv lock`, commit the updated `uv.lock` with it, the CI installs from the lock. The JSON schema of the api response is generated from the pydantic model into `frontend/src/schema/report.schema.json` with `uv run python -m sbml4humans.schema`.

Tests, linting and type checks run from the `backend` directory, the same checks run as GitHub Actions on every pull request (see [Branches and pull requests](#branches-and-pull-requests)):

```bash
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run ty check
```

### Frontend

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

## Branches and pull requests

- **`develop`** is the branch everything is integrated into.
- **`main`** tracks the latest release. It is fast-forwarded to the released commit by the `sync-main` job of `ci.yml` after the GitHub release was created, so `main` and the newest release always agree. Nothing is developed on `main` and nothing is merged into it by hand.

Work happens on short lived branches off `develop`, which GitHub deletes after the merge. `develop` does not accept a direct push, every change goes through a pull request against `develop`. This includes the maintainer, there is no bypass.

A pull request can only be merged once the required checks are green:

| check      | workflow   | content                                                                                    |
| ---------- | ---------- | ------------------------------------------------------------------------------------------ |
| `test`     | `ci.yml`   | `pytest` of the backend                                                                     |
| `schema`   | `ci.yml`   | the committed JSON schema of the report is current                                         |
| `frontend` | `ci.yml`   | the generated types are current, lint, type check, unit tests and the build of the frontend |
| `e2e`      | `ci.yml`   | the Playwright end to end tests against the backend                                        |
| `ruff`     | `ruff.yml` | `ruff check` and `ruff format --check` of the backend                                      |
| `ty`       | `ty.yml`   | `ty check` of the backend                                                                  |

Further rules of a pull request:

- conversations have to be resolved before the merge
- an approval is dismissed when new commits are pushed
- the history stays linear, i.e., a pull request is merged with squash or rebase; merge commits are disabled
- the maintainer is the code owner of the repository (`.github/CODEOWNERS`) and is requested for review on every pull request. A pull request is therefore reviewed and merged by the maintainer, who has the only write access. The rulesets themselves do not require an approval: on a personal repository a ruleset cannot ask for an approval only from somebody else, and requiring one would block the pull requests of the maintainer, who cannot approve their own. Once a second person has write access, a ruleset requiring an approving review of a code owner can be added

[Auto-merge](https://docs.github.com/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/automatically-merging-a-pull-request) is enabled, so a pull request can be queued and is merged as soon as the checks pass.

The protection is implemented with [repository rulesets](https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets), which are part of the repository in `.github/rulesets/`, so a change to a policy is reviewed like any other change:

| ruleset        | applies to | rules                                                                                                                                                                                                                                 |
| -------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `develop.json` | `develop`  | pull request required, the six checks above, resolved conversations, linear history, no force push, no deletion. **No bypass, for anybody.**                                                                                         |
| `main.json`    | `main`     | no force push, no deletion, no bypass. The fast-forward of the release workflow needs none, only a force push would be rejected. `main` follows `develop`, whose history carries merge commits from before merge commits were disabled, so `main` cannot require a linear history |
| `tags.json`    | all tags   | a tag cannot be deleted or moved, so a release tag keeps pointing at what was released                                                                                                                                               |

Changing a policy means changing the json and applying it:

```bash
.github/rulesets/apply.sh
```

The script is idempotent: it updates the rulesets which exist and creates the missing ones. It also sets the merge settings of the repository, i.e., auto-merge, delete branch on merge, and squash and rebase as the only merge methods. It needs the [github cli](https://cli.github.com) authenticated as a user with admin permission on the repository.

## Releases

The version of sbml4humans is the version of the backend package in `backend/sbml4humans/__init__.py`, the frontend `package.json` follows it. A release is made from `develop`. Since `develop` only accepts pull requests, the release is prepared on a branch and tagged once that pull request is merged:

1. branch off `develop`: `git switch -c release/x.y.z origin/develop`
2. write the release notes for the version in `release-notes/x.y.z.md`
3. bump the version from the `backend` directory: `uv run bump-my-version bump [major|minor|patch]`, which updates `backend/sbml4humans/__init__.py` and `frontend/package.json` and commits. It does not create the tag; a squash or rebase merge would rewrite the commit and leave the tag behind on a commit which is not part of `develop`
4. push the branch, open the pull request against `develop` and merge it once the checks are green
5. tag the merged commit on `develop` and push the tag:

    ```bash
    git switch develop
    git pull
    git tag x.y.z
    git push origin x.y.z
    ```

    This starts the `CI` workflow, which runs the checks, creates the [GitHub release](https://github.com/matthiaskoenig/sbml4humans/releases) from `release-notes/x.y.z.md` and fast-forwards `main` to the tagged commit. Check the version before pushing, a tag cannot be moved or deleted afterwards.

## Funding

SBML4Humans was funded as part of [Google Summer of Code 2021](https://summerofcode.withgoogle.com/).

## License

- Source Code: [MIT](https://opensource.org/license/MIT), the full text is in [LICENSE](LICENSE)
- Documentation: [CC BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/)

&copy; 2021-2026 Matthias König
