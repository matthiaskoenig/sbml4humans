# Annotation Details Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The inspector shows one cy3sbml-like card per annotation resource, with collection, identifier, OLS term (label, IRI, synonyms, description, cross references), providers, and ChEBI or UniProt details, resolved through pymetadata and cached (#92).

**Architecture:** pymetadata (`~/git/pymetadata`) gains a UniProt query, a ChEBI structure query, providers and OLS term metadata on `RDFAnnotationData`, and is released as 0.8.0. The sbml4humans backend answers a typed `AnnotationResource` at `GET /api/annotation_resource` through an in-process single-flight cache, and serves ChEBI structures at `GET /api/annotation_structure/{chebi}`. The Vue frontend renders `AnnotationCard.vue` per resource, with every label taken from glossary concepts.

**Tech Stack:** Python 3.14, FastAPI, pydantic, pymetadata, pytest, ruff, ty (sbml4humans); Python >=3.11, requests, pytest, tox (pymetadata); Vue 3, TypeScript ~6.0.3, Tailwind 4, vitest, Playwright.

**Spec:** `specs/2026-10-05-annotation-details-design.md`

## Global Constraints

- Never use the em dash character anywhere; use a plain dash "-".
- No agent attribution anywhere: no Co-Authored-By lines, no "Generated with" lines in commits, PRs, code, docs.
- Never edit `CHANGELOG.md`, `docs/release-notes.md` or any generated file by hand (`frontend/src/types/*.ts`, `frontend/src/schema/*.json`, `frontend/src/data/glossary*.json`, `docs/reference/*.md` are generated).
- Markdown has no hard line wraps: one paragraph, list item or table row per line.
- sbml4humans: every module, class and function is annotated and has a google style docstring; `uv run ruff check . && uv run ruff format --check . && uv run ty check` stay clean (ty warnings are errors, suppress only with `# ty: ignore[rule]`).
- sbml4humans: logging through `logging.getLogger(__name__)` with lazy `%s` arguments, never configure logging.
- sbml4humans: every failure of a JSON endpoint is answered by `error_response` with status 200 (`{"errors": [...], "warnings": [], "info": {...}}`). The only exception is the image endpoint `/api/annotation_structure/{chebi}`, which answers 404 without a structure.
- sbml4humans: the frontend states no names of its own; every label of the card is a concept of `glossary/report.toml`, read with `conceptEntry(key)`.
- sbml4humans: no new frontend dependency; every element an e2e test uses carries a `data-testid`; text is rendered as Vue text, never `v-html`.
- pymetadata requires python >= 3.11; runtime dependencies stay `rich`, `requests`, `pydantic`.
- `develop` of both repositories only takes pull requests; `uv.lock` and `package-lock.json` are committed with every dependency change.
- Push with `git -c credential.helper= -c credential.helper='!gh auth git-credential' push -u origin <branch>`; use `npx -y gh-axi` for GitHub, never `gh`.
- Node 22 is on the PATH (no nvm); never run `npm install` for unrelated packages.
- Version of pymetadata to release: **0.8.0** (0.7.0 is already tagged; the spec said 0.7.0 before this was known).
- Cache lifetimes: in-process 24 h for a resolved resource, 10 min for a resource with warnings (not found), never for a resource with errors; at most 5,000 entries. Resource length limit 2,000 characters. Synonyms shown before "show all": 5.

## Review Focus

1. An OLS outage while a reader looks at a model: the card shows its head and the error as a warning line, nothing is cached in-process, the browser is told `Cache-Control: no-store`, and the next request retries (tests in Task 9 and Task 10).
2. A ChEBI compound without a structure, or a structure request that fails: no broken image icon, the formula table stays (test in Task 13: the `<img>` is removed on `error`).
3. OLS text with markup (`<sub>2</sub>`, `<script>`) in label, synonym or description: shown literally as text (test in Task 13).
4. An element with more than 100 resources: resources beyond the automatic limit show their head without a loading line forever, and resolve after "resolve all" (test in Task 13).
5. A resource which is not identifiers.org (`https://en.wikipedia.org/wiki/Cytosol`) or of an unknown collection: the request answers the error contract, the card shows the resource as a link and the failure as a warning line (tests in Task 10 and Task 13).

---

## Part 1: pymetadata 0.8.0 (repository `~/git/pymetadata`)

Work on a branch `annotation-details` of `~/git/pymetadata` from `develop`. Commands run from `~/git/pymetadata`. Tests: `uv run pytest -q -x <file>`; lint: `uv run ruff check && uv run ruff format --check`; types: `uvx ty check`.

### Task 1: 404 means "not found", and a collection which is not on OLS warns nothing

**Files:**
- Modify: `src/pymetadata/webservices/webservice.py` (class `WebserviceError`, function `get_json`)
- Modify: `src/pymetadata/webservices/ols.py` (`OLSQuery.query_ols`)
- Test: `tests/test_webservice.py`, `tests/test_ols.py`

**Interfaces:**
- Produces: `class WebserviceNotFoundError(WebserviceError)` in `pymetadata.webservices.webservice`, raised by `get_json` for status 404. `OLSQuery.query_ols` returns `{"errors": [], "warnings": [f"Term '{term}' is not on OLS."]}` for a 404 and `{"errors": [], "warnings": []}` for an ontology which is not on OLS.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_webservice.py`:

```python
def test_get_json_raises_not_found_for_404(monkeypatch: pytest.MonkeyPatch) -> None:
    """A 404 is the dedicated not found error, a subclass of the webservice error."""
    from pymetadata.webservices import webservice

    class Response:
        status_code = 404

    class Session:
        def get(self, url: str, params: object = None) -> Response:
            return Response()

    monkeypatch.setattr(webservice, "get_session", lambda: Session())
    with pytest.raises(webservice.WebserviceNotFoundError):
        webservice.get_json("https://example.org/missing")
    assert issubclass(webservice.WebserviceNotFoundError, webservice.WebserviceError)
```

Append to `tests/test_ols.py`:

```python
def test_unknown_term_is_a_warning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A term OLS does not know is a warning and no error, nothing is cached."""
    from pymetadata.webservices.ols import ONTOLOGIES, OLSQuery
    from pymetadata.webservices.webservice import WebserviceNotFoundError

    def missing(url: str, params: object = None) -> dict:
        raise WebserviceNotFoundError(f"'404' response for: '{url}'")

    monkeypatch.setattr("pymetadata.webservices.ols.get_json", missing)
    query = OLSQuery(ontologies=ONTOLOGIES, cache_path=tmp_path, cache=True)
    data = query.query_ols(ontology="go", term="GO:9999999")
    assert data == {"errors": [], "warnings": ["Term 'GO:9999999' is not on OLS."]}
    assert not any(tmp_path.rglob("*.json"))


def test_collection_not_on_ols_warns_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    """A collection without an ontology on OLS is no problem of the annotation."""
    from pymetadata.webservices.ols import ONTOLOGIES, OLSQuery

    class Registry:
        ns_dict: dict = {}

    monkeypatch.setattr("pymetadata.webservices.ols.get_registry", lambda: Registry())
    query = OLSQuery(ontologies=ONTOLOGIES, cache=False)
    assert query.query_ols(ontology="pubmed", term="10659856") == {"errors": [], "warnings": []}
```

(Add `from pathlib import Path` and `import pytest` at the top of the files where missing.)

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest -q tests/test_webservice.py tests/test_ols.py -k "not_found or unknown_term or not_on_ols"`
Expected: FAIL (`AttributeError: ... WebserviceNotFoundError`, and the old warning `'pubmed' is not on OLS.`).

- [ ] **Step 3: Implement**

In `webservice.py`, after `class WebserviceError`:

```python
class WebserviceNotFoundError(WebserviceError):
    """Raised when a web service answers that the queried entry does not exist (404).

    A caller tells a missing entry apart from a service which cannot answer:
    the entry is reported as unknown, and no cached content is used.
    """
```

In `get_json`, before the generic status check:

```python
    if response.status_code == 404:
        raise WebserviceNotFoundError(f"'404' response for: '{url}'")
```

In `ols.py` import `WebserviceNotFoundError` next to `WebserviceError`, replace the "not on OLS" return with `return {"errors": [], "warnings": []}`, and catch the not found error first:

```python
            try:
                data = get_json(url)
            except WebserviceNotFoundError:
                return {"errors": [], "warnings": [f"Term '{term}' is not on OLS."]}
            except WebserviceError as err:
                ...  # unchanged
```

Update the docstring of `query_ols` ("Returns: ... a term OLS does not know is a warning, an ontology which is not on OLS returns no information and no message").

- [ ] **Step 4: Run the whole suite**

Run: `uv run pytest -q -x`
Expected: PASS. A test which asserted the old `'... is not on OLS.'` warning is updated to the new behaviour.

- [ ] **Step 5: Commit**

```bash
git add src/pymetadata/webservices/webservice.py src/pymetadata/webservices/ols.py tests/
git commit -m "Tell a term OLS does not know apart from a failing service"
```

### Task 2: OLS ontology, IRI and term page on the annotation

**Files:**
- Modify: `src/pymetadata/webservices/ols.py` (`process_response`, new `ols_term_url`)
- Modify: `src/pymetadata/core/annotation.py` (`RDFAnnotationData.__init__`, `query_ols`, `to_dict`)
- Test: `tests/test_ols.py`, `tests/core/test_annotation.py` (create if missing)

**Interfaces:**
- Produces: `ols_term_url(ontology: str | None, iri: str | None) -> str | None`; `process_response` additionally returns `ontology`, `iri`, `ols_url`; `RDFAnnotationData` has `ontology: str | None`, `iri: str | None`, `ols_url: str | None`, all in `to_dict()`.

- [ ] **Step 1: Write the failing tests**

In `tests/test_ols.py`:

```python
def test_process_response_reports_the_term_page() -> None:
    """The ontology, the IRI and the OLS page of the term are part of the response."""
    from pymetadata.webservices.ols import ONTOLOGIES, OLSQuery

    info = OLSQuery(ontologies=ONTOLOGIES, cache=False).process_response(
        {
            "errors": [],
            "warnings": [],
            "label": "glycolytic process",
            "ontology_name": "go",
            "iri": "http://purl.obolibrary.org/obo/GO_0006096",
        }
    )
    assert info["ontology"] == "go"
    assert info["iri"] == "http://purl.obolibrary.org/obo/GO_0006096"
    assert info["ols_url"] == (
        "https://www.ebi.ac.uk/ols4/ontologies/go/classes?iri="
        "http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FGO_0006096"
    )


def test_term_page_needs_ontology_and_iri() -> None:
    """Without an ontology or an IRI there is no term page."""
    from pymetadata.webservices.ols import ols_term_url

    assert ols_term_url(None, "http://purl.obolibrary.org/obo/GO_0006096") is None
    assert ols_term_url("go", None) is None
```

In `tests/core/test_annotation.py`:

```python
"""Tests of the resolved annotation data."""

from typing import Any

import pytest

from pymetadata.core.annotation import RDFAnnotation, RDFAnnotationData
from pymetadata.core.miriam import BQB


def test_annotation_data_carries_the_ols_term(monkeypatch: pytest.MonkeyPatch) -> None:
    """The ontology, the IRI and the OLS page of the term end up in `to_dict`."""

    class Query:
        def query_ols(self, ontology: Any, term: Any) -> dict:
            return {"errors": [], "warnings": []}

        def process_response(self, term: dict) -> dict:
            return {
                "errors": [],
                "warnings": [],
                "label": "glycolytic process",
                "description": None,
                "synonyms": [],
                "xrefs": [],
                "ontology": "go",
                "iri": "http://purl.obolibrary.org/obo/GO_0006096",
                "ols_url": "https://www.ebi.ac.uk/ols4/ontologies/go/classes?iri=x",
            }

    monkeypatch.setattr("pymetadata.core.annotation.get_ols_query", lambda: Query())
    data = RDFAnnotationData(RDFAnnotation(qualifier=BQB.IS, resource="GO:0006096")).to_dict()
    assert data["ontology"] == "go"
    assert data["iri"] == "http://purl.obolibrary.org/obo/GO_0006096"
    assert data["ols_url"] == "https://www.ebi.ac.uk/ols4/ontologies/go/classes?iri=x"
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest -q tests/test_ols.py tests/core/test_annotation.py -k "term_page or ols_term"`
Expected: FAIL (`KeyError: 'ontology'`, `ImportError: ols_term_url`).

- [ ] **Step 3: Implement**

In `ols.py`:

```python
OLS_TERM_PAGE = "https://www.ebi.ac.uk/ols4/ontologies/{}/classes?iri={}"


def ols_term_url(ontology: str | None, iri: str | None) -> str | None:
    """Get the page of a term in the Ontology Lookup Service.

    Args:
        ontology: ontology id of OLS, e.g., `go`
        iri: IRI of the term

    Returns:
        The url of the page, or None without an ontology or an IRI.
    """
    if not ontology or not iri:
        return None
    return OLS_TERM_PAGE.format(ontology, urllib.parse.quote(iri, safe=""))
```

In `process_response`, add to the returned dict:

```python
        ontology = term.get("ontology_name")
        iri = term.get("iri")
        return {
            **data,
            "label": label,
            "description": description,
            "synonyms": synonyms,
            "xrefs": xrefs,
            "ontology": ontology,
            "iri": iri,
            "ols_url": ols_term_url(ontology, iri),
        }
```

In `RDFAnnotationData.__init__` add `self.ontology: str | None = None`, `self.iri: str | None = None`, `self.ols_url: str | None = None` next to `self.label`; in `query_ols` set `self.ontology = info.get("ontology")`, `self.iri = info.get("iri")`, `self.ols_url = info.get("ols_url")`; in `to_dict` add `"ontology"`, `"iri"`, `"ols_url"`. Document the three attributes in the class docstring.

- [ ] **Step 4: Run the whole suite**

Run: `uv run pytest -q -x`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/pymetadata tests
git commit -m "Report the ontology, the IRI and the OLS page of an annotation term"
```

### Task 3: Providers, primary provider, collection name and pattern

**Files:**
- Modify: `src/pymetadata/core/annotation.py` (new dataclass `Provider`, `RDFAnnotationData.__init__`, `to_dict`)
- Test: `tests/core/test_annotation.py`

**Interfaces:**
- Produces: `@dataclass class Provider: name: str; url: str; official: bool` in `pymetadata.core.annotation`. `RDFAnnotationData` gains `providers: list[Provider]` (non deprecated providers, primary first), `collection_name: str | None`, `collection_homepage: str | None`, `pattern_match: bool | None`; `url` is the url of the primary provider. `to_dict()` carries `providers` as a list of dicts (`dataclasses.asdict`), `collection_name`, `collection_homepage`, `pattern_match`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/core/test_annotation.py`:

```python
from pymetadata.webservices.registry import Namespace, Resource


def _resource(name: str, url: str, official: bool, deprecated: bool = False) -> Resource:
    """A provider of the registry."""
    return Resource.from_dict(
        {
            "id": None, "providerCode": name.lower(), "name": name, "urlPattern": url,
            "mirId": None, "description": name, "official": official, "sampleId": None,
            "resourceHomeUrl": f"https://{name.lower()}.example.org", "institution": {},
            "location": {}, "deprecated": deprecated, "deprecationDate": "",
        }
    )


@pytest.fixture
def uniprot_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    """A registry with the collection uniprot and three providers, OLS answers nothing."""
    namespace = Namespace.from_dict(
        {
            "id": None, "prefix": "uniprot", "name": "UniProt Knowledgebase",
            "pattern": r"^([A-N,R-Z][0-9]([A-Z][A-Z, 0-9][A-Z, 0-9][0-9]){1,2})|([O,P,Q][0-9][A-Z, 0-9][A-Z, 0-9][A-Z, 0-9][0-9])(\.\d+)?$",
            "namespaceEmbeddedInLui": False, "description": "UniProt",
            "resources": [
                _resource("NCBI", "https://www.ncbi.nlm.nih.gov/protein/{$id}", False),
                _resource("Old", "https://old.example.org/{$id}", True, deprecated=True),
                _resource("UniProt", "https://www.uniprot.org/uniprotkb/{$id}", True),
            ],
        }
    )

    class Registry:
        ns_dict = {"uniprot": namespace}

    class Query:
        def query_ols(self, ontology: Any, term: Any) -> dict:
            return {"errors": [], "warnings": []}

        def process_response(self, term: dict) -> dict:
            return {"errors": [], "warnings": [], "label": None, "description": None,
                    "synonyms": [], "xrefs": [], "ontology": None, "iri": None, "ols_url": None}

    monkeypatch.setattr("pymetadata.core.annotation.get_registry", lambda: Registry())
    monkeypatch.setattr("pymetadata.core.annotation.get_ols_query", lambda: Query())


def test_primary_provider_is_the_official_one(uniprot_registry: None) -> None:
    """The official non deprecated provider is the url, deprecated providers are left out."""
    data = RDFAnnotationData(
        RDFAnnotation(qualifier=BQB.IS, resource="https://identifiers.org/uniprot:P69905")
    )
    assert data.url == "https://www.uniprot.org/uniprotkb/P69905"
    assert [p.name for p in data.providers] == ["UniProt", "NCBI"]
    assert data.collection_name == "UniProt Knowledgebase"
    assert data.collection_homepage == "https://uniprot.example.org"
    assert data.pattern_match is True
    assert data.to_dict()["providers"][0] == {
        "name": "UniProt", "url": "https://www.uniprot.org/uniprotkb/P69905", "official": True
    }


def test_pattern_mismatch(uniprot_registry: None) -> None:
    """An identifier which does not match the pattern of its collection is reported."""
    data = RDFAnnotationData(
        RDFAnnotation(qualifier=BQB.IS, resource="https://identifiers.org/uniprot:not-an-id", validate=False)
    )
    assert data.pattern_match is False
```

If `RDFAnnotation` reads the registry through another module than `pymetadata.core.annotation`, patch `get_registry` there as well (search `get_registry` in `src/pymetadata/core`).

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest -q tests/core/test_annotation.py -k "provider or pattern"`
Expected: FAIL (`AttributeError: 'RDFAnnotationData' object has no attribute 'providers'`).

- [ ] **Step 3: Implement**

At module level of `annotation.py` (with `import re` and `from dataclasses import asdict, dataclass`):

```python
@dataclass
class Provider:
    """A provider which resolves the term of an annotation.

    Attributes:
        name: name of the provider, e.g., `UniProt`
        url: url of the term at the provider
        official: whether the registry names it the official provider
    """

    name: str
    url: str
    official: bool


def primary_resource(resources: list[Resource]) -> Resource | None:
    """Get the provider a term links to: the official non deprecated one.

    Falls back to the first non deprecated provider, and to the first provider
    when all are deprecated.
    """
    active = [resource for resource in resources if not resource.deprecated]
    for resource in active:
        if resource.official:
            return resource
    if active:
        return active[0]
    return resources[0] if resources else None


def pattern_matches(pattern: str | None, term: str | None) -> bool | None:
    """Check a term against the pattern of its collection, None if it cannot be checked."""
    if not pattern or not term:
        return None
    try:
        return re.match(pattern, term) is not None
    except re.error:
        return None
```

(Import `Resource` from `pymetadata.webservices.registry` next to `Namespace`.)

In `RDFAnnotationData.__init__`, initialise `self.providers: list[Provider] = []`, `self.collection_name: str | None = None`, `self.collection_homepage: str | None = None`, `self.pattern_match: bool | None = None`. Inside the identifiers.org branch, after the namespace lookup, replace the "set url to first resource url" logic: build the url of every resource in the existing loop into a dict `urls: dict[int, str]` keyed by `id(ns_resource)`, keep appending the `CrossReference`s as today, and after the loop:

```python
            primary = primary_resource(namespace.resources)
            self.collection_name = namespace.name
            self.pattern_match = pattern_matches(namespace.pattern, self.term)
            if primary is not None:
                self.collection_homepage = primary.resourceHomeUrl
                self.url = urls.get(id(primary))
            active = [r for r in namespace.resources if not r.deprecated and id(r) in urls]
            active.sort(key=lambda r: r is not primary)
            self.providers = [
                Provider(name=r.name, url=urls[id(r)], official=bool(r.official))
                for r in active
            ]
```

In `to_dict` add `"providers": [asdict(p) for p in self.providers]`, `"collection_name"`, `"collection_homepage"`, `"pattern_match"`. Document the new attributes in the class docstring (`url: url of the primary provider of the collection`).

- [ ] **Step 4: Run the whole suite**

Run: `uv run pytest -q -x`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/pymetadata/core/annotation.py tests/core/test_annotation.py
git commit -m "Providers, primary provider, collection name and pattern of an annotation"
```

### Task 4: UniProt query

**Files:**
- Create: `src/pymetadata/webservices/uniprot.py`
- Test: `tests/test_uniprot.py`

**Interfaces:**
- Produces: `UniprotQuery.query(accession: str, cache: bool | None = None, cache_path: Path | None = None) -> dict` returning `{"accession", "entry", "name", "organism", "genes": list[str], "length": int | None, "function": str | None}` or `{}` for an invalid, unknown or inactive accession, or a failing service without cache.

- [ ] **Step 1: Write the failing tests**

```python
"""Test UniProt."""

from pathlib import Path
from typing import Any

import pytest

from pymetadata.webservices.uniprot import UniprotQuery
from pymetadata.webservices.webservice import WebserviceError, WebserviceNotFoundError

HBA = {
    "entryType": "UniProtKB reviewed (Swiss-Prot)",
    "primaryAccession": "P69905",
    "uniProtkbId": "HBA_HUMAN",
    "proteinDescription": {"recommendedName": {"fullName": {"value": "Hemoglobin subunit alpha"}}},
    "organism": {"scientificName": "Homo sapiens"},
    "genes": [{"geneName": {"value": "HBA1"}}, {"geneName": {"value": "HBA2"}}],
    "comments": [
        {"commentType": "FUNCTION", "texts": [{"value": "Involved in oxygen transport."}]}
    ],
    "sequence": {"length": 142},
}


@pytest.fixture
def fake_uniprot(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Answer P69905, every other accession is unknown."""
    queries: list[str] = []

    def get_json(url: str, params: Any = None) -> dict:
        queries.append(url)
        if url.endswith("/P69905.json"):
            return HBA
        raise WebserviceNotFoundError(f"'404' response for: '{url}'")

    monkeypatch.setattr("pymetadata.webservices.uniprot.get_json", get_json)
    return queries


def test_query(tmp_path: Path, fake_uniprot: list[str]) -> None:
    """The entry is reduced to name, organism, genes, length and function, and cached."""
    data = UniprotQuery.query("P69905", cache=True, cache_path=tmp_path)
    assert data == {
        "accession": "P69905", "entry": "HBA_HUMAN", "name": "Hemoglobin subunit alpha",
        "organism": "Homo sapiens", "genes": ["HBA1", "HBA2"], "length": 142,
        "function": "Involved in oxygen transport.",
    }
    assert (tmp_path / "uniprot" / "P69905.json").exists()
    assert UniprotQuery.query("P69905", cache=True, cache_path=tmp_path) == data
    assert len(fake_uniprot) == 1


@pytest.mark.parametrize("accession", ["Q00000", "../../x", "P69905&x=1", ""])
def test_unknown_or_invalid(tmp_path: Path, fake_uniprot: list[str], accession: str) -> None:
    """An unknown or invalid accession answers no information."""
    assert UniprotQuery.query(accession, cache=True, cache_path=tmp_path) == {}


def test_outdated_cache_when_offline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An outdated cache is used when UniProt cannot be reached."""
    monkeypatch.setattr("pymetadata.webservices.uniprot.get_json", lambda url, params=None: HBA)
    UniprotQuery.query("P69905", cache=True, cache_path=tmp_path)
    path = tmp_path / "uniprot" / "P69905.json"
    import os
    os.utime(path, (0, 0))

    def offline(url: str, params: Any = None) -> dict:
        raise WebserviceError("Service is not reachable")

    monkeypatch.setattr("pymetadata.webservices.uniprot.get_json", offline)
    assert UniprotQuery.query("P69905", cache=True, cache_path=tmp_path)["entry"] == "HBA_HUMAN"


def test_inactive_entry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A merged or deleted entry answers no information."""
    monkeypatch.setattr(
        "pymetadata.webservices.uniprot.get_json",
        lambda url, params=None: {"entryType": "Inactive", "primaryAccession": "P00000"},
    )
    assert UniprotQuery.query("P00000", cache=False, cache_path=tmp_path) == {}
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest -q tests/test_uniprot.py`
Expected: FAIL (`ModuleNotFoundError: pymetadata.webservices.uniprot`).

- [ ] **Step 3: Implement `src/pymetadata/webservices/uniprot.py`**

```python
"""Protein information from UniProt.

```python
from pymetadata.webservices.uniprot import UniprotQuery

info = UniprotQuery.query("P69905")
```

See <https://www.uniprot.org/>.
"""

import contextlib
import logging
import re
from pathlib import Path
from typing import Any

import pymetadata
from pymetadata.cache import (
    CACHE_DURATION_ONTOLOGY,
    cache_file,
    read_json_cache,
    read_json_cache_fallback,
    write_json_cache,
)
from pymetadata.webservices.webservice import (
    WebserviceError,
    WebserviceNotFoundError,
    get_json,
)

logger = logging.getLogger(__name__)

UNIPROT_URL = "https://rest.uniprot.org/uniprotkb/{}.json"

# the accession format of UniProt, with an optional isoform
UNIPROT_PATTERN = re.compile(
    r"^(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})(?:-\d+)?$"
)


def _entry_info(entry: dict[str, Any]) -> dict[str, Any]:
    """Reduce an entry of UniProt to the information shown for an annotation."""
    description = entry.get("proteinDescription") or {}
    names = description.get("recommendedName") or next(
        iter(description.get("submissionNames") or []), {}
    )
    function = next(
        (
            comment["texts"][0].get("value")
            for comment in entry.get("comments") or []
            if comment.get("commentType") == "FUNCTION" and comment.get("texts")
        ),
        None,
    )
    return {
        "accession": entry.get("primaryAccession"),
        "entry": entry.get("uniProtkbId"),
        "name": (names.get("fullName") or {}).get("value"),
        "organism": (entry.get("organism") or {}).get("scientificName"),
        "genes": [
            gene["geneName"]["value"]
            for gene in entry.get("genes") or []
            if "geneName" in gene
        ],
        "length": (entry.get("sequence") or {}).get("length"),
        "function": function,
    }


class UniprotQuery:
    """Queries against the UniProt web service.

    Responses are cached on disk for `CACHE_DURATION_ONTOLOGY` hours, see
    `pymetadata.CACHE_USE`. If UniProt cannot be reached, cached content is used
    however old it is.
    """

    @staticmethod
    def query(
        accession: str, cache: bool | None = None, cache_path: Path | None = None
    ) -> dict[str, Any]:
        """Query the information of a protein.

        Args:
            accession: accession of UniProt, e.g., `P69905`
            cache: cache the response, defaults to `pymetadata.CACHE_USE`
            cache_path: directory for cached responses, defaults to
                `pymetadata.CACHE_PATH`

        Returns:
            The protein information, empty if the accession is invalid, unknown
            or inactive, or if UniProt cannot be reached and nothing is cached.
        """
        accession = accession.strip().upper() if accession else ""
        if not UNIPROT_PATTERN.match(accession):
            logger.error("Invalid UniProt accession: '%s'", accession)
            return {}
        if cache is None:
            cache = pymetadata.CACHE_USE
        if cache_path is None:
            cache_path = pymetadata.CACHE_PATH

        path = cache_file(Path(cache_path) / "uniprot", accession)
        if cache:
            with contextlib.suppress(OSError):
                data = read_json_cache(cache_path=path, max_age=CACHE_DURATION_ONTOLOGY)
                if data:
                    return data

        try:
            entry = get_json(UNIPROT_URL.format(accession))
        except WebserviceNotFoundError:
            logger.error("UniProt accession is unknown: '%s'", accession)
            return {}
        except WebserviceError as err:
            if cache:
                fallback = read_json_cache_fallback(path, reason=str(err))
                if fallback is not None:
                    return fallback
            logger.error("UniProt information could not be retrieved for '%s': %s", accession, err)
            return {}

        if not isinstance(entry, dict) or entry.get("entryType") == "Inactive":
            logger.error("UniProt entry is inactive: '%s'", accession)
            return {}

        data = _entry_info(entry)
        if cache:
            path.parent.mkdir(parents=True, exist_ok=True)
            write_json_cache(data=data, cache_path=path)
        return data
```

Check the exact signature of `read_json_cache` (it may raise when the file is missing or outdated; `contextlib.suppress(OSError)` follows `chebi.py`), and of `write_json_cache` (whether it creates the directory). Keep it consistent with `chebi.py`.

- [ ] **Step 4: Run tests, lint, types**

Run: `uv run pytest -q tests/test_uniprot.py && uv run ruff check && uv run ruff format --check && uvx ty check`
Expected: PASS, no diagnostics.

- [ ] **Step 5: Commit**

```bash
git add src/pymetadata/webservices/uniprot.py tests/test_uniprot.py
git commit -m "Protein information from UniProt"
```

### Task 5: ChEBI structure

**Files:**
- Modify: `src/pymetadata/webservices/webservice.py` (new `get_bytes`)
- Modify: `src/pymetadata/webservices/chebi.py` (new `ChebiQuery.structure`)
- Test: `tests/test_chebi.py`

**Interfaces:**
- Produces: `get_bytes(url: str, params: dict[str, str] | None = None) -> bytes` (same errors as `get_json`, raises `WebserviceError` unless the content type is `image/svg+xml`); `ChebiQuery.structure(chebi: str, cache: bool | None = None, cache_path: Path | None = None) -> bytes | None`, cached as `CACHE_PATH/chebi/CHEBI%3A<n>.svg`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_chebi.py`:

```python
SVG = b"<?xml version='1.0'?><svg xmlns='http://www.w3.org/2000/svg'></svg>"


def test_structure_is_cached(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The structure is fetched once and cached as an svg file."""
    urls: list[str] = []

    def get_bytes(url: str, params: Any = None) -> bytes:
        urls.append(url)
        return SVG

    monkeypatch.setattr("pymetadata.webservices.chebi.get_bytes", get_bytes)
    assert ChebiQuery.structure("CHEBI:15377", cache=True, cache_path=tmp_path) == SVG
    assert ChebiQuery.structure("chebi:15377", cache=True, cache_path=tmp_path) == SVG
    assert urls == ["https://www.ebi.ac.uk/chebi/backend/api/public/compound/15377/structure/"]
    assert (tmp_path / "chebi" / "CHEBI%3A15377.svg").read_bytes() == SVG


@pytest.mark.parametrize("chebi", ["../../evil", "CHEBI:abc", ""])
def test_structure_rejects_invalid_id(tmp_path: Path, chebi: str) -> None:
    """An invalid id has no structure and queries nothing."""
    assert ChebiQuery.structure(chebi, cache=True, cache_path=tmp_path) is None


def test_structure_unknown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A compound without a structure answers None."""
    from pymetadata.webservices.webservice import WebserviceNotFoundError

    def missing(url: str, params: Any = None) -> bytes:
        raise WebserviceNotFoundError("404")

    monkeypatch.setattr("pymetadata.webservices.chebi.get_bytes", missing)
    assert ChebiQuery.structure("CHEBI:1", cache=True, cache_path=tmp_path) is None
```

Append to `tests/test_webservice.py` a test that `get_bytes` raises `WebserviceError` for a 200 response whose `headers["Content-Type"]` is `text/html` and returns `response.content` for `image/svg+xml` (same fake session pattern as Task 1, the fake response has `status_code`, `headers` and `content`).

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest -q tests/test_chebi.py tests/test_webservice.py -k "structure or bytes"`
Expected: FAIL (`AttributeError: ... get_bytes` / `structure`).

- [ ] **Step 3: Implement**

`webservice.py`:

```python
def get_bytes(url: str, params: dict[str, str] | None = None) -> bytes:
    """Query a url for an svg image and return its content.

    Args:
        url: url to query
        params: query parameters, encoded and appended to the url

    Returns:
        The content of the response.

    Raises:
        WebserviceNotFoundError: if the service answers 404
        WebserviceError: if the service cannot be reached, answers with another
            status than 200, or does not answer with an svg image
    """
    logger.debug("Query: %s %s", url, params or "")
    try:
        response = get_session().get(url, params=params)
    except requests.RequestException as err:
        raise WebserviceError(f"Service is not reachable for '{url}': {err}") from err
    if response.status_code == 404:
        raise WebserviceNotFoundError(f"'404' response for: '{url}'")
    if response.status_code != 200:
        raise WebserviceError(f"'{response.status_code}' response for: '{url}'")
    content_type = response.headers.get("Content-Type", "")
    if not content_type.startswith("image/svg+xml"):
        raise WebserviceError(f"Response for '{url}' is no svg image: '{content_type}'")
    return response.content
```

`chebi.py`:

```python
CHEBI_STRUCTURE_URL = "https://www.ebi.ac.uk/chebi/backend/api/public/compound/{}/structure/"

    @staticmethod
    def structure(
        chebi: str, cache: bool | None = None, cache_path: Path | None = None
    ) -> bytes | None:
        """Get the structure of a ChEBI compound as an svg image.

        Args:
            chebi: ChEBI term, e.g., `CHEBI:33699`
            cache: cache the image, defaults to `pymetadata.CACHE_USE`
            cache_path: directory for cached responses, defaults to
                `pymetadata.CACHE_PATH`

        Returns:
            The svg image, None if the id is invalid, the compound has no
            structure, or ChEBI cannot be reached and nothing is cached.
        """
        match = CHEBI_PATTERN.match(chebi.strip()) if chebi else None
        if not match:
            logger.error("Invalid ChEBI id: '%s'", chebi)
            return None
        number = match.group(1)
        if cache is None:
            cache = pymetadata.CACHE_USE
        if cache_path is None:
            cache_path = pymetadata.CACHE_PATH
        path = Path(cache_path) / "chebi" / f"CHEBI%3A{number}.svg"
        age = cache_age(path) if cache else None
        if age is not None and age <= CACHE_DURATION_ONTOLOGY:
            return path.read_bytes()
        try:
            svg = get_bytes(CHEBI_STRUCTURE_URL.format(number))
        except WebserviceNotFoundError:
            return None
        except WebserviceError as err:
            if age is not None:
                logger.warning("Using outdated structure of 'CHEBI:%s': %s", number, err)
                return path.read_bytes()
            logger.error("ChEBI structure could not be retrieved for 'CHEBI:%s': %s", number, err)
            return None
        if cache:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(svg)
        return svg
```

(Import `cache_age`, `get_bytes`, `WebserviceNotFoundError`.)

- [ ] **Step 4: Run tests, lint, types**

Run: `uv run pytest -q -x && uv run ruff check && uv run ruff format --check && uvx ty check`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/pymetadata/webservices tests
git commit -m "Structure of a ChEBI compound as svg"
```

### Task 6: Release pymetadata 0.8.0

**Files:**
- Create: `release-notes/0.8.0.md`
- Create: `docs/api/uniprot.md` (content `::: pymetadata.webservices.uniprot`), and its entry in the nav of `zensical.toml` next to the ChEBI page
- Modify: `CLAUDE.md` of pymetadata (architecture: `webservices/uniprot.py`, `WebserviceNotFoundError`, `get_bytes`, providers on `RDFAnnotationData`)

- [ ] **Step 1: Write the release notes** `release-notes/0.8.0.md`, in the format of `release-notes/0.7.0.md`: New (UniProt query, ChEBI structure, providers and primary provider, collection name and homepage, pattern check, OLS ontology, IRI and term page), Changed (a collection which is not on OLS warns nothing; a term OLS does not know is a warning, not an error; the url of an annotation is the url of the official provider, UniProt links UniProt instead of NCBI Protein).
- [ ] **Step 2: Build the docs** `uv run zensical build --clean` - Expected: no warnings.
- [ ] **Step 3: Full checks** `uv run pytest -q && uv run ruff check && uv run ruff format --check && uvx ty check`
- [ ] **Step 4: Commit, push, PR**

```bash
git add -A && git commit -m "Release notes and documentation of 0.8.0"
git -c credential.helper= -c credential.helper='!gh auth git-credential' push -u origin annotation-details
npx -y gh-axi pr create --base develop --head annotation-details --title "UniProt, ChEBI structure, providers and OLS term pages for annotations" --body-file <body>
```

- [ ] **Step 5:** Wait for the checks (`npx -y gh-axi pr checks <n>`), fix failures, squash merge with `--delete-branch`.
- [ ] **Step 6: Bump** on a branch `release-0.8.0` from the updated `develop`: `uvx bump-my-version bump minor` (0.7.0 to 0.8.0), push, PR, checks, squash merge.
- [ ] **Step 7: Tag** on the updated `develop`: confirm the version with the user first (a tag cannot be moved), then `git tag 0.8.0 && git push origin 0.8.0` (with the credential helper). Wait for the release workflow and check `https://pypi.org/pypi/pymetadata/0.8.0/json` answers 200.

---

## Part 2: sbml4humans (repository root, branch `annotation-details`)

Backend commands from `backend/`: `uv run pytest -q -x`, `uv run ruff check . && uv run ruff format --check .`, `uv run ty check`. Frontend commands from `frontend/`: `npx vitest run`, `npm run lint`, `npx vue-tsc --build --force`, e2e `npx playwright test` with the backend on port 1444 (`SBML4HUMANS_ALLOW_PRIVATE_URLS=1 uv run uvicorn sbml4humans.api:api --port 1444` from `backend/`).

### Task 7: pymetadata 0.8.0 and the cache directory

**Files:**
- Modify: `backend/pyproject.toml` (`"pymetadata>=0.8.0"`), `backend/uv.lock`
- Modify: `backend/sbml4humans/annotations.py` (cache configuration)
- Modify: `Dockerfile`, `docker-compose-production.yml`, `docs/development.md`, `deploy.md`
- Test: `backend/tests/test_annotations.py`

**Interfaces:**
- Produces: `CACHE_VARIABLE = "SBML4HUMANS_CACHE"` and `configure_cache() -> None` in `sbml4humans.annotations`, called once at import: when the variable is set, `pymetadata.CACHE_PATH = Path(value)`.

- [ ] **Step 1: Update the dependency** - in `backend/pyproject.toml` set `"pymetadata>=0.8.0"`, run `uv lock --upgrade-package pymetadata && uv sync`. Expected: `uv run python -c "import pymetadata; print(pymetadata.__version__)"` prints `0.8.0`.
- [ ] **Step 2: Write the failing test**

```python
def test_cache_directory_from_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`SBML4HUMANS_CACHE` is where pymetadata caches the web services."""
    import pymetadata

    from sbml4humans import annotations

    monkeypatch.setattr(pymetadata, "CACHE_PATH", pymetadata.CACHE_PATH)
    monkeypatch.setenv(annotations.CACHE_VARIABLE, str(tmp_path))
    annotations.configure_cache()
    assert tmp_path == pymetadata.CACHE_PATH
```

- [ ] **Step 3: Run it** `uv run pytest -q tests/test_annotations.py -k cache_directory` - Expected: FAIL (`AttributeError: CACHE_VARIABLE`).
- [ ] **Step 4: Implement** in `annotations.py`:

```python
CACHE_VARIABLE = "SBML4HUMANS_CACHE"


def configure_cache() -> None:
    """Point the disk cache of pymetadata to `SBML4HUMANS_CACHE` where it is set.

    The deployment keeps the answers of OLS, ChEBI, UniProt and the registry on
    a volume, so that they survive a new container; elsewhere pymetadata keeps
    its default, `~/.cache/pymetadata`.
    """
    path = os.environ.get(CACHE_VARIABLE)
    if path:
        pymetadata.CACHE_PATH = Path(path)


configure_cache()
```

- [ ] **Step 5: Deployment** - in `docker-compose-production.yml` add the named volume `cache` next to `uploads`, mount `cache:/cache` in the backend service and set `SBML4HUMANS_CACHE: /cache`; in `Dockerfile` create `/cache` owned by the unprivileged user exactly as `/uploads` is created (read how `/uploads` is prepared there and mirror it, and update the comment which names `~/.cache/pymetadata`); document the variable in `docs/development.md` and the volume in `deploy.md`, one line each, next to `SBML4HUMANS_UPLOADS`.
- [ ] **Step 6: Run** `uv run pytest -q -x && uv run ruff check . && uv run ruff format --check . && uv run ty check` - Expected: PASS. Existing tests that assert the `'... is not on OLS.'` warning or the NCBI url are updated to the 0.8.0 behaviour.
- [ ] **Step 7: Commit** `git add -A backend Dockerfile docker-compose-production.yml docs/development.md deploy.md && git commit -m "pymetadata 0.8.0, the cache of the web services on a volume"`

### Task 8: The typed annotation resource

**Files:**
- Modify: `backend/sbml4humans/annotations.py` (models and `resolve_resource`, replacing `annotation_info`)
- Test: `backend/tests/test_annotations.py` (replace the tests of `annotation_info`)

**Interfaces:**
- Consumes: `RDFAnnotationData` of pymetadata 0.8.0 (attributes `collection`, `term`, `url`, `label`, `description`, `synonyms` (OLS dicts with `name`), `xrefs` (OLS dicts with `database`, `id`, `url`), `ontology`, `iri`, `ols_url`, `providers`, `collection_name`, `collection_homepage`, `pattern_match`, `warnings`, `errors`), `ChebiQuery.query`, `UniprotQuery.query`.
- Produces (all `ReportModel` subclasses, camelCase JSON):
  - `Collection(prefix: str, name: str | None, homepage: str | None)`
  - `Provider(name: str, url: str, official: bool)`
  - `CrossReference(label: str, url: str | None)`
  - `OntologyTerm(ontology: str | None, label: str | None, iri: str | None, ols_url: str | None, description: str | None, synonyms: list[str], xrefs: list[CrossReference])`
  - `ChebiInfo(formula: str | None, charge: int | None, mass: str | None, structure: bool)`
  - `UniprotInfo(entry: str | None, name: str | None, organism: str | None, genes: list[str], length: int | None, function: str | None)`
  - `AnnotationResource(resource: str, collection: Collection | None, identifier: str | None, url: str | None, pattern_match: bool | None, providers: list[Provider], ontology: OntologyTerm | None, chebi: ChebiInfo | None, uniprot: UniprotInfo | None, warnings: list[str], errors: list[str])`
  - `resolve_resource(resource: str) -> AnnotationResource` (raises `ValueError` for an unknown collection or an unparsable resource, from pymetadata)

- [ ] **Step 1: Write the failing tests** (replace the old tests of `annotation_info`; keep the `_ols` helper pattern which patches `RDFAnnotationData.query_ols`):

```python
"""Tests of the resolution of annotation resources."""

from typing import Any

import pytest
from pymetadata.core.annotation import RDFAnnotationData

from sbml4humans import annotations
from sbml4humans.annotations import resolve_resource


def _ols(**fields: Any) -> Any:
    """A replacement of the OLS query which sets the given fields."""

    def query_ols(self: RDFAnnotationData) -> dict[str, Any]:
        for key, value in fields.items():
            setattr(self, key, value)
        return {}

    return query_ols


GO = {
    "label": "glycolytic process",
    "description": "The chemical reactions and pathways resulting in the breakdown of a carbohydrate.",
    "synonyms": [{"name": "glycolysis"}, {"name": "glycolysis"}, {"name": "  "}],
    "xrefs": [
        {"database": "MetaCyc", "id": "GLYCOLYSIS-VARIANTS", "url": "https://biocyc.org/x"},
        {"database": None, "id": "Wikipedia:Glycolysis", "url": None},
    ],
    "ontology": "go",
    "iri": "http://purl.obolibrary.org/obo/GO_0006096",
    "ols_url": "https://www.ebi.ac.uk/ols4/ontologies/go/classes?iri=x",
}


def test_ontology_term(monkeypatch: pytest.MonkeyPatch) -> None:
    """A GO term carries its collection, its providers and its OLS term."""
    monkeypatch.setattr(RDFAnnotationData, "query_ols", _ols(**GO))
    info = resolve_resource("https://identifiers.org/GO:0006096")
    assert info.identifier == "GO:0006096"
    assert info.collection is not None and info.collection.prefix == "go"
    assert info.collection.name
    assert info.providers and info.url == info.providers[0].url
    assert info.pattern_match is True
    assert info.ontology is not None
    assert info.ontology.label == "glycolytic process"
    assert info.ontology.synonyms == ["glycolysis"]
    assert [x.label for x in info.ontology.xrefs] == [
        "MetaCyc:GLYCOLYSIS-VARIANTS",
        "Wikipedia:Glycolysis",
    ]
    assert info.ontology.xrefs[1].url is None
    assert info.chebi is None and info.uniprot is None
    assert info.warnings == [] and info.errors == []


def test_empty_ols_fields_are_no_term(monkeypatch: pytest.MonkeyPatch) -> None:
    """OLS reports a missing definition as an empty list; no label and no IRI is no term."""
    monkeypatch.setattr(
        RDFAnnotationData, "query_ols", _ols(label=" ", description=[], iri=None)
    )
    assert resolve_resource("https://identifiers.org/pubmed/10659856").ontology is None


def test_chebi(monkeypatch: pytest.MonkeyPatch) -> None:
    """A ChEBI compound carries formula, charge, mass and whether it has a structure."""
    monkeypatch.setattr(RDFAnnotationData, "query_ols", _ols(label="indocyanine green"))
    monkeypatch.setattr(
        annotations.ChebiQuery,
        "query",
        staticmethod(
            lambda chebi: {"formula": "C43H47N2O6S2.Na", "charge": 0, "mass": "774.981", "inchikey": "MOFV"}
        ),
    )
    info = resolve_resource("https://identifiers.org/CHEBI:31696")
    assert info.chebi is not None
    assert (info.chebi.formula, info.chebi.charge, info.chebi.mass, info.chebi.structure) == (
        "C43H47N2O6S2.Na", 0, "774.981", True,
    )


def test_unknown_chebi_is_a_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    """A compound ChEBI does not know is a warning."""
    monkeypatch.setattr(RDFAnnotationData, "query_ols", _ols())
    monkeypatch.setattr(annotations.ChebiQuery, "query", staticmethod(lambda chebi: {}))
    info = resolve_resource("https://identifiers.org/CHEBI:999999999")
    assert info.chebi is None
    assert info.warnings == ["Term 'CHEBI:999999999' is not on ChEBI."]


def test_uniprot(monkeypatch: pytest.MonkeyPatch) -> None:
    """A protein carries the information of UniProt."""
    monkeypatch.setattr(RDFAnnotationData, "query_ols", _ols())
    monkeypatch.setattr(
        annotations.UniprotQuery,
        "query",
        staticmethod(
            lambda accession: {
                "accession": "P69905", "entry": "HBA_HUMAN", "name": "Hemoglobin subunit alpha",
                "organism": "Homo sapiens", "genes": ["HBA1", "HBA2"], "length": 142,
                "function": "Involved in oxygen transport.",
            }
        ),
    )
    info = resolve_resource("https://identifiers.org/uniprot/P69905")
    assert info.uniprot is not None and info.uniprot.entry == "HBA_HUMAN"
    assert info.uniprot.genes == ["HBA1", "HBA2"]
    assert info.url is not None and "uniprot.org" in info.url


def test_errors_and_warnings_are_text(monkeypatch: pytest.MonkeyPatch) -> None:
    """A failing request of OLS is reported as the text of the error."""
    monkeypatch.setattr(
        RDFAnnotationData, "query_ols", _ols(errors=[OSError("OLS down")], warnings=[1])
    )
    info = resolve_resource("https://identifiers.org/GO:0006096")
    assert info.errors == ["OLS down"]
    assert info.warnings == ["1"]


def test_unknown_collection() -> None:
    """A collection which is not in the registry raises."""
    with pytest.raises(ValueError):
        resolve_resource("https://identifiers.org/notacollection:123")
```

- [ ] **Step 2: Run** `uv run pytest -q tests/test_annotations.py` - Expected: FAIL (`ImportError: resolve_resource`).
- [ ] **Step 3: Implement** in `annotations.py` (keep `_text` and `_messages`; remove `annotation_info`, `TEXT_FIELDS`, `MESSAGE_FIELDS` once `api.py` no longer imports them in Task 10; until then keep `annotation_info` as a thin wrapper `return resolve_resource(resource).model_dump(by_alias=True)` so the api keeps working):

```python
from pymetadata.webservices.chebi import ChebiQuery
from pymetadata.webservices.uniprot import UniprotQuery

from sbml4humans.model import ReportModel


class Collection(ReportModel):
    """The collection of the identifiers.org registry a resource belongs to."""

    prefix: str
    name: str | None = None
    homepage: str | None = None


class Provider(ReportModel):
    """A provider which resolves the identifier of a resource."""

    name: str
    url: str
    official: bool


class CrossReference(ReportModel):
    """A cross reference of an ontology term, a link where OLS gives an url."""

    label: str
    url: str | None = None


class OntologyTerm(ReportModel):
    """The term of a resource in the Ontology Lookup Service."""

    ontology: str | None = None
    label: str | None = None
    iri: str | None = None
    ols_url: str | None = None
    description: str | None = None
    synonyms: list[str] = Field(default_factory=list)
    xrefs: list[CrossReference] = Field(default_factory=list)


class ChebiInfo(ReportModel):
    """The chemical information of a ChEBI compound."""

    formula: str | None = None
    charge: int | None = None
    mass: str | None = None
    structure: bool = False


class UniprotInfo(ReportModel):
    """The information of a UniProt protein."""

    entry: str | None = None
    name: str | None = None
    organism: str | None = None
    genes: list[str] = Field(default_factory=list)
    length: int | None = None
    function: str | None = None


class AnnotationResource(ReportModel):
    """Everything the report shows of one resource of an annotation."""

    resource: str
    collection: Collection | None = None
    identifier: str | None = None
    url: str | None = None
    pattern_match: bool | None = None
    providers: list[Provider] = Field(default_factory=list)
    ontology: OntologyTerm | None = None
    chebi: ChebiInfo | None = None
    uniprot: UniprotInfo | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


def _synonyms(values: Any) -> list[str]:
    """The names of the synonyms of OLS, each once, in order."""
    names: list[str] = []
    for value in values if isinstance(values, list) else []:
        name = _text(value.get("name") if isinstance(value, dict) else value)
        if name and name not in names:
            names.append(name)
    return names


def _xrefs(values: Any) -> list[CrossReference]:
    """The cross references of OLS, labelled `database:id`."""
    xrefs: list[CrossReference] = []
    for value in values if isinstance(values, list) else []:
        if not isinstance(value, dict):
            continue
        identifier = _text(value.get("id"))
        if not identifier:
            continue
        database = _text(value.get("database"))
        label = f"{database}:{identifier}" if database else identifier
        xrefs.append(CrossReference(label=label, url=_text(value.get("url"))))
    return xrefs


def _chebi(term: str, warnings: list[str]) -> ChebiInfo | None:
    """The chemical information of a ChEBI compound, a warning if ChEBI does not know it."""
    info = ChebiQuery.query(term)
    if not info:
        warnings.append(f"Term '{term}' is not on ChEBI.")
        return None
    charge = info.get("charge")
    mass = info.get("mass")
    return ChebiInfo(
        formula=_text(info.get("formula")),
        charge=charge if isinstance(charge, int) else None,
        mass=str(mass) if mass is not None else None,
        structure=bool(info.get("inchikey")),
    )


def _uniprot(accession: str, warnings: list[str]) -> UniprotInfo | None:
    """The information of a UniProt protein, a warning if UniProt does not know it."""
    info = UniprotQuery.query(accession)
    if not info:
        warnings.append(f"Term '{accession}' is not on UniProt.")
        return None
    return UniprotInfo(
        entry=_text(info.get("entry")),
        name=_text(info.get("name")),
        organism=_text(info.get("organism")),
        genes=[gene for gene in info.get("genes") or [] if isinstance(gene, str)],
        length=info.get("length") if isinstance(info.get("length"), int) else None,
        function=_text(info.get("function")),
    )


def resolve_resource(resource: str) -> AnnotationResource:
    """Resolve everything the report shows of an annotation resource.

    Args:
        resource: identifier of the resource (url or MIRIAM urn).

    Raises:
        ValueError: if the resource cannot be parsed or its collection is unknown.
    """
    data = RDFAnnotationData(annotation=RDFAnnotation(qualifier=BQB.IS, resource=resource))
    warnings = _messages(data.warnings)
    term = _text(data.term)
    label = _text(data.label)
    iri = _text(getattr(data, "iri", None))
    ontology = None
    if label or iri:
        ontology = OntologyTerm(
            ontology=_text(getattr(data, "ontology", None)),
            label=label,
            iri=iri,
            ols_url=_text(getattr(data, "ols_url", None)),
            description=_text(data.description),
            synonyms=_synonyms(data.synonyms),
            xrefs=_xrefs(data.xrefs),
        )
    collection = _text(data.collection)
    return AnnotationResource(
        resource=resource,
        collection=Collection(
            prefix=collection,
            name=_text(data.collection_name),
            homepage=_text(data.collection_homepage),
        )
        if collection
        else None,
        identifier=term,
        url=_text(data.url),
        pattern_match=data.pattern_match,
        providers=[
            Provider(name=p.name, url=p.url, official=p.official) for p in data.providers
        ],
        ontology=ontology,
        chebi=_chebi(term, warnings) if collection == "chebi" and term else None,
        uniprot=_uniprot(term, warnings) if collection == "uniprot" and term else None,
        warnings=warnings,
        errors=_messages(data.errors),
    )
```

(`Field` from pydantic; `getattr` with a default only where the attribute is set by `query_ols`, which the tests replace; if `ty` objects, set the attributes on `RDFAnnotationData` directly. Check that `ReportModel` applies the camelCase alias; `pattern_match` becomes `patternMatch`, `ols_url` becomes `olsUrl`.)

- [ ] **Step 4: Run** `uv run pytest -q tests/test_annotations.py && uv run ruff check . && uv run ruff format --check . && uv run ty check` - Expected: PASS.
- [ ] **Step 5: Commit** `git add backend && git commit -m "The typed information of an annotation resource"`

### Task 9: The in-process cache

**Files:**
- Modify: `backend/sbml4humans/annotations.py` (class `ResourceCache`, function `resource_cache`)
- Test: `backend/tests/test_annotations.py`

**Interfaces:**
- Produces: `class ResourceCache` with `__init__(self, resolve: Callable[[str], AnnotationResource], max_entries: int = 5000, found_seconds: float = 86400, missing_seconds: float = 600, clock: Callable[[], float] = time.monotonic)` and `get(self, resource: str) -> AnnotationResource`; `resource_cache() -> ResourceCache` (one per process, `functools.cache`, resolving with `resolve_resource`).

- [ ] **Step 1: Write the failing tests**

```python
import threading
import time

from sbml4humans.annotations import AnnotationResource, ResourceCache


class Resolver:
    """Counts the resolves and answers what it was told."""

    def __init__(self, **fields: Any) -> None:
        self.calls = 0
        self.fields = fields

    def __call__(self, resource: str) -> AnnotationResource:
        self.calls += 1
        return AnnotationResource(resource=resource, **self.fields)


def test_cache_hit() -> None:
    """A resolved resource is resolved once within its lifetime."""
    resolver = Resolver()
    cache = ResourceCache(resolver)
    assert cache.get("a") == cache.get("a")
    assert resolver.calls == 1


def test_resolved_lives_a_day_and_not_found_ten_minutes() -> None:
    """A resource with warnings is resolved again after ten minutes, else after a day."""
    now = [0.0]
    found, missing = Resolver(), Resolver(warnings=["Term 'x' is not on OLS."])
    found_cache = ResourceCache(found, clock=lambda: now[0])
    missing_cache = ResourceCache(missing, clock=lambda: now[0])
    found_cache.get("a")
    missing_cache.get("a")
    now[0] = 601.0
    found_cache.get("a")
    missing_cache.get("a")
    assert (found.calls, missing.calls) == (1, 2)
    now[0] = 86402.0
    found_cache.get("a")
    assert found.calls == 2


def test_errors_are_not_cached() -> None:
    """A resource whose web service failed is resolved again on the next request."""
    resolver = Resolver(errors=["OLS down"])
    cache = ResourceCache(resolver)
    cache.get("a")
    cache.get("a")
    assert resolver.calls == 2


def test_exceptions_are_not_cached() -> None:
    """A resource which raises raises again and is not cached."""
    calls = []

    def resolve(resource: str) -> AnnotationResource:
        calls.append(resource)
        raise ValueError("unknown collection")

    cache = ResourceCache(resolve)
    for _ in range(2):
        with pytest.raises(ValueError):
            cache.get("a")
    assert len(calls) == 2


def test_oldest_entry_is_evicted() -> None:
    """The cache holds at most `max_entries`, the least recently used goes first."""
    resolver = Resolver()
    cache = ResourceCache(resolver, max_entries=2)
    cache.get("a")
    cache.get("b")
    cache.get("a")
    cache.get("c")
    cache.get("a")
    cache.get("b")
    assert resolver.calls == 4


def test_concurrent_requests_share_one_lookup() -> None:
    """Requests of one resource while it resolves wait for that one lookup."""
    started = threading.Event()
    release = threading.Event()
    calls = []

    def resolve(resource: str) -> AnnotationResource:
        calls.append(resource)
        started.set()
        release.wait(5)
        return AnnotationResource(resource=resource)

    cache = ResourceCache(resolve)
    results: list[AnnotationResource] = []
    threads = [threading.Thread(target=lambda: results.append(cache.get("a"))) for _ in range(4)]
    threads[0].start()
    started.wait(5)
    for thread in threads[1:]:
        thread.start()
    time.sleep(0.05)
    release.set()
    for thread in threads:
        thread.join(5)
    assert len(calls) == 1
    assert len(results) == 4
```

- [ ] **Step 2: Run** `uv run pytest -q tests/test_annotations.py -k cache` - Expected: FAIL (`ImportError: ResourceCache`).
- [ ] **Step 3: Implement**

```python
class ResourceCache:
    """The resolved resources of this process, in front of the disk cache of pymetadata.

    A resource with a term lives `found_seconds`, a resource with warnings (a
    term the web services do not know) `missing_seconds`, and a resource whose
    web service failed is not kept, so that the next request asks again. Each
    resource is looked up by one request at a time; the requests of a resource
    which is being resolved wait for that lookup. At most `max_entries`
    resources are kept, the least recently used is dropped first.
    """

    def __init__(
        self,
        resolve: Callable[[str], AnnotationResource],
        max_entries: int = 5000,
        found_seconds: float = 24 * 3600,
        missing_seconds: float = 600,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Keep the resources `resolve` answers."""
        self._resolve = resolve
        self._max_entries = max_entries
        self._found_seconds = found_seconds
        self._missing_seconds = missing_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._entries: OrderedDict[str, tuple[float, AnnotationResource]] = OrderedDict()
        self._pending: dict[str, Future[AnnotationResource]] = {}

    def _lifetime(self, value: AnnotationResource) -> float | None:
        """How long a resource is kept, None when it is not kept at all."""
        if value.errors:
            return None
        return self._missing_seconds if value.warnings else self._found_seconds

    def get(self, resource: str) -> AnnotationResource:
        """The resolved resource, from the cache while it lives."""
        with self._lock:
            entry = self._entries.get(resource)
            if entry is not None and entry[0] > self._clock():
                self._entries.move_to_end(resource)
                return entry[1]
            future = self._pending.get(resource)
            owner = future is None
            if future is None:
                future = Future()
                self._pending[resource] = future
        if not owner:
            return future.result()
        try:
            value = self._resolve(resource)
        except BaseException as err:
            future.set_exception(err)
            raise
        finally:
            with self._lock:
                self._pending.pop(resource, None)
        lifetime = self._lifetime(value)
        if lifetime is not None:
            with self._lock:
                self._entries[resource] = (self._clock() + lifetime, value)
                self._entries.move_to_end(resource)
                while len(self._entries) > self._max_entries:
                    self._entries.popitem(last=False)
        future.set_result(value)
        return value


@functools.cache
def resource_cache() -> ResourceCache:
    """The cache of the resolved resources of this process."""
    return ResourceCache(resolve_resource)
```

(Imports: `functools`, `threading`, `time`, `from collections import OrderedDict`, `from collections.abc import Callable`, `from concurrent.futures import Future`.) Note: `future.set_result` must run before another waiter can read it; the `finally` removes the pending entry first, so a request which arrives between the removal and `set_result` starts a lookup of its own, which is harmless. A waiter whose owner raised gets the same exception. Avoid "Future exception was never retrieved" warnings: only owners create futures and waiters read them.

- [ ] **Step 4: Run** `uv run pytest -q tests/test_annotations.py && uv run ruff check . && uv run ty check` - Expected: PASS.
- [ ] **Step 5: Commit** `git add backend && git commit -m "Cache the resolved annotation resources of the process"`

### Task 10: The endpoints

**Files:**
- Modify: `backend/sbml4humans/api.py` (`annotation_resource`, new `annotation_structure`)
- Modify: `backend/sbml4humans/annotations.py` (remove `annotation_info`, `TEXT_FIELDS`, `MESSAGE_FIELDS`; add `MAX_RESOURCE_LENGTH = 2000`, `CHEBI_ID = re.compile(r"^CHEBI:\d{1,9}$")`)
- Modify: `CLAUDE.md` (Error contract: the image endpoint is the one exception)
- Test: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: `resource_cache().get`, `AnnotationResource`, `ChebiQuery.structure`.
- Produces: `GET /api/annotation_resource?resource=` (JSON `AnnotationResource`, camelCase; `Cache-Control: public, max-age=86400` without errors, `no-store` with errors); `GET /api/annotation_structure/{chebi}` (`image/svg+xml`, 404 without structure).

- [ ] **Step 1: Write the failing tests** in `test_api.py` (use the module's existing `client` fixture or `TestClient(api, raise_server_exceptions=False)` as the file does):

```python
from sbml4humans import annotations
from sbml4humans.annotations import AnnotationResource, OntologyTerm


def test_annotation_resource_is_typed(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """The resource is answered in camelCase and may be cached by the browser for a day."""
    value = AnnotationResource(
        resource="GO:0006096", identifier="GO:0006096", pattern_match=True,
        ontology=OntologyTerm(label="glycolytic process", ols_url="https://ols/x"),
    )
    monkeypatch.setattr(annotations.resource_cache(), "get", lambda resource: value)
    response = client.get("/api/annotation_resource", params={"resource": "GO:0006096"})
    assert response.status_code == 200
    body = response.json()
    assert body["patternMatch"] is True
    assert body["ontology"]["olsUrl"] == "https://ols/x"
    assert response.headers["cache-control"] == "public, max-age=86400"


def test_annotation_resource_with_errors_is_not_cached(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A resource whose web service failed must not stay in the browser."""
    value = AnnotationResource(resource="GO:1", errors=["OLS down"])
    monkeypatch.setattr(annotations.resource_cache(), "get", lambda resource: value)
    response = client.get("/api/annotation_resource", params={"resource": "GO:1"})
    assert response.headers["cache-control"] == "no-store"


def test_annotation_resource_too_long(client: TestClient) -> None:
    """A resource longer than 2,000 characters is refused by the error contract."""
    response = client.get("/api/annotation_resource", params={"resource": "x" * 2001})
    assert response.status_code == 200
    assert "2000" in response.json()["errors"][0]


def test_annotation_resource_unknown_collection(client: TestClient) -> None:
    """An unknown collection is answered by the error contract."""
    response = client.get(
        "/api/annotation_resource", params={"resource": "https://identifiers.org/notacollection:1"}
    )
    assert response.status_code == 200
    assert response.json()["errors"]


def test_annotation_structure(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """The structure is an svg which cannot run a script."""
    monkeypatch.setattr(
        annotations.ChebiQuery, "structure", staticmethod(lambda chebi: b"<svg/>")
    )
    response = client.get("/api/annotation_structure/CHEBI:15377")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    assert response.headers["content-security-policy"].startswith("sandbox")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.content == b"<svg/>"


@pytest.mark.parametrize("chebi", ["CHEBI:abc", "15377", "CHEBI:1%2F..", "CHEBI:1234567890"])
def test_annotation_structure_invalid(client: TestClient, chebi: str) -> None:
    """An id which is not `CHEBI:<number>` has no structure."""
    assert client.get(f"/api/annotation_structure/{chebi}").status_code == 404


def test_annotation_structure_missing(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """A compound without a structure answers 404."""
    monkeypatch.setattr(annotations.ChebiQuery, "structure", staticmethod(lambda chebi: None))
    assert client.get("/api/annotation_structure/CHEBI:1").status_code == 404
```

Remove or update the existing test of `/api/annotation_resource` which asserted the old dict.

- [ ] **Step 2: Run** `uv run pytest -q tests/test_api.py -k annotation` - Expected: FAIL.
- [ ] **Step 3: Implement** in `api.py`:

```python
@api.get(
    "/api/annotation_resource",
    tags=["metadata"],
    response_model=AnnotationResource,
)
def annotation_resource(resource: str, response: Response) -> AnnotationResource:
    """Resolve the information of an annotation resource (url or MIRIAM urn).

    A resolved resource may stay in the browser for a day; one whose web
    service failed may not, so that the next look at it asks again.
    """
    if len(resource) > MAX_RESOURCE_LENGTH:
        raise ValueError(f"The resource is longer than {MAX_RESOURCE_LENGTH} characters.")
    value = resource_cache().get(resource)
    response.headers["Cache-Control"] = (
        "no-store" if value.errors else "public, max-age=86400"
    )
    return value


# the structure is an image: the frontend shows it in an `<img>`, the sandbox keeps
# a script of the svg from running where it is opened as a page of its own
STRUCTURE_HEADERS = {
    "Content-Security-Policy": "sandbox; default-src 'none'; style-src 'unsafe-inline'",
    "X-Content-Type-Options": "nosniff",
    "Cache-Control": "public, max-age=2592000",
}


@api.get("/api/annotation_structure/{chebi}", tags=["metadata"], response_class=Response)
def annotation_structure(chebi: str) -> Response:
    """The structure of a ChEBI compound as svg, 404 without one.

    The one answer of the api outside the error contract: it is an image and
    no JSON, and an image which is not there is a 404 the browser understands.
    """
    if not CHEBI_ID.match(chebi):
        return Response(status_code=404)
    svg = ChebiQuery.structure(chebi)
    if svg is None:
        return Response(status_code=404)
    return Response(content=svg, media_type="image/svg+xml", headers=STRUCTURE_HEADERS)
```

Check that the error contract middleware leaves a 404 `Response` alone (it converts exceptions only); if it rewrites status codes, exempt this path there and say why in a comment. Check that the gzip middleware compresses `image/svg+xml` (fine either way). Update the Error contract paragraph of `CLAUDE.md`: "... `GET /api/annotation_structure/{chebi}` is the one exception: an image, answered 404 without a structure."

- [ ] **Step 4: Run** `uv run pytest -q -x && uv run ruff check . && uv run ruff format --check . && uv run ty check` - Expected: PASS.
- [ ] **Step 5: Commit** `git add backend CLAUDE.md && git commit -m "Typed annotation resource and ChEBI structure endpoints"`

### Task 11: Schema and TypeScript types of the annotation resource

**Files:**
- Modify: `backend/sbml4humans/schema.py` (write `annotation.schema.json` next to `report.schema.json`)
- Modify: `backend/tests/test_schema.py`, `.github/workflows/ci-cd.yml` (schema job), `frontend/package.json` (`types` script)
- Create (generated): `frontend/src/schema/annotation.schema.json`, `frontend/src/types/annotation.ts`

**Interfaces:**
- Produces: `annotation_schema_json() -> str`; `main(argv)` writes both schemas into the directory `argv[1]` when given, else into `frontend/src/schema/`; TypeScript `AnnotationResource`, `OntologyTerm`, `ChebiInfo`, `UniprotInfo`, `Provider`, `CrossReference`, `Collection` exported from `frontend/src/types/annotation.ts`.

- [ ] **Step 1: Failing test** in `test_schema.py`:

```python
def test_annotation_schema_is_current() -> None:
    """The committed schema of the annotation resource is the one the model generates."""
    from sbml4humans.schema import ANNOTATION_SCHEMA_PATH, annotation_schema_json

    assert ANNOTATION_SCHEMA_PATH.read_text(encoding="utf-8") == annotation_schema_json()
```

Adjust the existing test of `main` to the directory argument.

- [ ] **Step 2: Run** `uv run pytest -q tests/test_schema.py` - Expected: FAIL.
- [ ] **Step 3: Implement** in `schema.py`: `SCHEMA_DIR = Path(...)/"frontend"/"src"/"schema"`, `SCHEMA_PATH = SCHEMA_DIR / "report.schema.json"`, `ANNOTATION_SCHEMA_PATH = SCHEMA_DIR / "annotation.schema.json"`, a helper `_schema_json(model: type[BaseModel]) -> str` used by `schema_json()` (ReportResponse) and `annotation_schema_json()` (AnnotationResource), and

```python
def main(argv: list[str]) -> None:
    """Write both schemas into the given directory or into `SCHEMA_DIR`."""
    directory = Path(argv[1]) if len(argv) > 1 else SCHEMA_DIR
    directory.mkdir(parents=True, exist_ok=True)
    for name, text in (
        (SCHEMA_PATH.name, schema_json()),
        (ANNOTATION_SCHEMA_PATH.name, annotation_schema_json()),
    ):
        (directory / name).write_text(text, encoding="utf-8")
        print(f"schema written to {directory / name}")
```

Update the module docstring. Run `uv run python -m sbml4humans.schema`.

In `ci-cd.yml` replace the schema check with:

```yaml
          uv run python -m sbml4humans.schema /tmp/schema
          diff -r /tmp/schema ../frontend/src/schema
```

In `frontend/package.json` extend `types` with a second `json2ts` for `src/schema/annotation.schema.json` into `src/types/annotation.ts` (same flags and banner naming its own schema), and `prettier --write` both outputs. Run `npm run types` from `frontend/`. Find where the CI diffs `src/types/report.ts` and add `src/types/annotation.ts` there.

- [ ] **Step 4: Run** backend tests and `cd frontend && npx vue-tsc --build --force` - Expected: PASS.
- [ ] **Step 5: Commit** `git add -A backend .github frontend/package.json frontend/src/schema frontend/src/types && git commit -m "Schema and types of the annotation resource"`

### Task 12: Glossary concepts of the card

**Files:**
- Modify: `glossary/report.toml` (new `[concepts.*]` entries)
- Generated: `frontend/src/data/glossary.json`, `frontend/src/data/glossary-details.json`, `docs/reference/*.md`

**Interfaces:**
- Produces: concept keys `annotationQualifier`, `annotationCollection`, `annotationIdentifier`, `annotationOntology`, `annotationSynonyms`, `annotationXrefs`, `annotationProviders`, `chebiFormula`, `chebiCharge`, `chebiMass`, `uniprotName`, `uniprotOrganism`, `uniprotGenes`, `uniprotLength`, `uniprotFunction`, read in the frontend with `conceptEntry(key)` and opened with the help key `concepts/<key>`.

- [ ] **Step 1: Add the entries** after `[concepts.equation]` in the format of the existing concepts (`label`, `summary`, `description`). Labels and summaries:

| key | label | summary |
|---|---|---|
| annotationQualifier | qualifier | the relation between the element and the resource, from MIRIAM |
| annotationCollection | collection | the database of identifiers.org the resource belongs to |
| annotationIdentifier | identifier | the identifier of the resource in its collection, linked to its primary provider |
| annotationOntology | ontology | the ontology of the Ontology Lookup Service which defines the term |
| annotationSynonyms | synonyms | other names of the term in its ontology |
| annotationXrefs | cross references | entries of other databases which the ontology names for the term |
| annotationProviders | providers | the web sites which show the entry of the resource |
| chebiFormula | formula | the molecular formula of the compound in ChEBI |
| chebiCharge | charge | the net charge of the compound in ChEBI |
| chebiMass | mass | the average mass of the compound in ChEBI, in Dalton |
| uniprotName | name | the recommended name of the protein in UniProt |
| uniprotOrganism | organism | the organism the protein is from |
| uniprotGenes | genes | the genes which encode the protein |
| uniprotLength | length | the number of amino acids of the canonical sequence |
| uniprotFunction | function | what the protein does, as UniProt describes it |

Descriptions (one paragraph each, no hard wraps, no em dash) say where the value comes from and where the card shows it. The description of `annotationQualifier` lists the qualifiers as a markdown table with their meaning, the biology qualifiers `BQB_IS`, `BQB_HAS_PART`, `BQB_IS_PART_OF`, `BQB_IS_VERSION_OF`, `BQB_HAS_VERSION`, `BQB_IS_HOMOLOG_TO`, `BQB_IS_DESCRIBED_BY`, `BQB_IS_ENCODED_BY`, `BQB_ENCODES`, `BQB_OCCURS_IN`, `BQB_HAS_PROPERTY`, `BQB_IS_PROPERTY_OF`, `BQB_HAS_TAXON` and the model qualifiers `BQM_IS`, `BQM_IS_DESCRIBED_BY`, `BQM_IS_DERIVED_FROM`, `BQM_IS_INSTANCE_OF`, `BQM_HAS_INSTANCE`, with the definitions of the MIRIAM qualifiers (http://co.mbine.org/standards/qualifiers). The description of `annotationOntology` names OLS (https://www.ebi.ac.uk/ols4) and says that the label, the IRI, the synonyms, the description and the cross references come from it and are cached for 30 days. The descriptions of `chebi*` and `uniprot*` name ChEBI (https://www.ebi.ac.uk/chebi/) and UniProt (https://www.uniprot.org/). Also update the last paragraph of `[types.SBase.attributes.cvterms]` in `glossary/core.toml`: "The report groups the annotations of an element by qualifier and shows every resource as a card: its collection, its identifier, the term of its ontology with synonyms, description and cross references, the providers which show it, and for a ChEBI compound or a UniProt protein the information of that database."

- [ ] **Step 2: Generate and check** from `backend/`: `uv run python -m sbml4humans.glossary && uv run python -m sbml4humans.glossary --check` - Expected: no errors. From the root: `uv run --project backend zensical build --clean --strict` - Expected: no warnings.
- [ ] **Step 3: Commit** `git add glossary frontend/src/data docs/reference && git commit -m "Glossary of the annotation card"`

### Task 13: The annotation card

**Files:**
- Create: `frontend/src/components/misc/AnnotationCard.vue`
- Modify: `frontend/src/api/client.ts` (`getAnnotationResource` returns `AnnotationResource`, new `annotationStructureUrl`), `frontend/src/api/annotations.ts` (types), `frontend/src/api/types.ts` (remove `AnnotationInfo`), `frontend/src/components/misc/CvTermResourceList.vue`, `CvTermList.vue`, `CvTermNestedList.vue` (pass `qualifier`)
- Test: `frontend/tests/unit/annotationCard.test.ts` (new), existing `annotations.test.ts`, `misc.test.ts`, `inspector.test.ts` updated where they assert the old markup

**Interfaces:**
- Consumes: `AnnotationResource` from `@/types/annotation`, `conceptEntry` from `@/report/glossary`, `HelpLabel`, `ShowAllButton`.
- Produces: `annotationStructureUrl(chebi: string): string` (`${API_URL}/annotation_structure/${encodeURIComponent(chebi)}`); `AnnotationCard` props `{ resource: string; qualifier: string; info?: AnnotationResource | null; state: "idle" | "loading" | "resolved" | "failed" }`; test ids `annotation-card`, `annotation-qualifier`, `annotation-collection`, `annotation-identifier`, `annotation-pattern-warning`, `annotation-ontology`, `annotation-label`, `annotation-iri`, `annotation-synonyms`, `annotation-description`, `annotation-chebi`, `annotation-structure`, `annotation-uniprot`, `annotation-xrefs`, `annotation-providers`, `annotation-warning`, `annotation-loading`.

- [ ] **Step 1: Write the failing unit tests** `frontend/tests/unit/annotationCard.test.ts`:

```ts
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import AnnotationCard from "@/components/misc/AnnotationCard.vue";
import type { AnnotationResource } from "@/types/annotation";

const GO: AnnotationResource = {
  resource: "https://identifiers.org/GO:0006096",
  collection: { prefix: "go", name: "Gene Ontology", homepage: "http://geneontology.org/" },
  identifier: "GO:0006096",
  url: "https://www.ebi.ac.uk/QuickGO/GTerm?id=GO:0006096",
  patternMatch: true,
  providers: [
    { name: "QuickGO", url: "https://www.ebi.ac.uk/QuickGO/GTerm?id=GO:0006096", official: true },
    { name: "AmiGO 2", url: "https://amigo.geneontology.org/amigo/term/GO:0006096", official: false },
  ],
  ontology: {
    ontology: "go",
    label: "glycolytic process",
    iri: "http://purl.obolibrary.org/obo/GO_0006096",
    olsUrl: "https://www.ebi.ac.uk/ols4/ontologies/go/classes?iri=x",
    description: "The breakdown of a carbohydrate into pyruvate.",
    synonyms: ["glycolysis", "a", "b", "c", "d", "e", "f"],
    xrefs: [
      { label: "MetaCyc:P341-PWY", url: "https://biocyc.org/x" },
      { label: "Wikipedia:Glycolysis", url: null },
    ],
  },
  chebi: null,
  uniprot: null,
  warnings: [],
  errors: [],
};

function card(info: AnnotationResource | null, state = "resolved") {
  return mount(AnnotationCard, {
    props: { resource: info?.resource ?? "https://identifiers.org/GO:0006096", qualifier: "BQB_IS", info, state },
  });
}

describe("AnnotationCard", () => {
  it("shows the head, the term and the providers of an ontology resource", () => {
    const wrapper = card(GO);
    expect(wrapper.get("[data-testid=annotation-qualifier]").text()).toBe("BQB_IS");
    const collection = wrapper.get("[data-testid=annotation-collection]");
    expect(collection.text()).toBe("Gene Ontology");
    expect(collection.attributes("href")).toBe("http://geneontology.org/");
    const identifier = wrapper.get("[data-testid=annotation-identifier]");
    expect(identifier.text()).toBe("GO:0006096");
    expect(identifier.attributes("href")).toBe(GO.url);
    expect(wrapper.get("[data-testid=annotation-ontology]").text()).toBe("GO");
    expect(wrapper.get("[data-testid=annotation-ontology]").attributes("href")).toBe(GO.ontology!.olsUrl);
    expect(wrapper.get("[data-testid=annotation-label]").text()).toBe("glycolytic process");
    expect(wrapper.get("[data-testid=annotation-iri]").attributes("href")).toBe(GO.ontology!.iri);
    expect(wrapper.get("[data-testid=annotation-description]").text()).toBe(GO.ontology!.description);
    expect(wrapper.findAll("[data-testid=annotation-providers] a").map((a) => a.text())).toEqual(["QuickGO", "AmiGO 2"]);
    const xrefs = wrapper.get("[data-testid=annotation-xrefs]");
    expect(xrefs.findAll("a").map((a) => a.text())).toEqual(["MetaCyc:P341-PWY"]);
    expect(xrefs.text()).toContain("Wikipedia:Glycolysis");
    expect(wrapper.find("[data-testid=annotation-pattern-warning]").exists()).toBe(false);
  });

  it("shows five synonyms before a show all", async () => {
    const wrapper = card(GO);
    const synonyms = wrapper.get("[data-testid=annotation-synonyms]");
    expect(synonyms.findAll("[data-testid=annotation-synonym]")).toHaveLength(5);
    await synonyms.get("[data-testid=show-all]").trigger("click");
    expect(wrapper.findAll("[data-testid=annotation-synonym]")).toHaveLength(7);
  });

  it("shows markup of the ontology as text", () => {
    const wrapper = card({
      ...GO,
      ontology: { ...GO.ontology!, label: "H<sub>2</sub>O", synonyms: ["<script>x</script>"], description: "<b>bold</b>" },
    });
    expect(wrapper.get("[data-testid=annotation-label]").text()).toBe("H<sub>2</sub>O");
    expect(wrapper.find("sub").exists()).toBe(false);
    expect(wrapper.find("script").exists()).toBe(false);
    expect(wrapper.get("[data-testid=annotation-description]").text()).toBe("<b>bold</b>");
  });

  it("shows the chemistry of a ChEBI compound and drops a structure which fails to load", async () => {
    const wrapper = card({
      ...GO,
      collection: { prefix: "chebi", name: "ChEBI", homepage: null },
      identifier: "CHEBI:31696",
      chebi: { formula: "C43H47N2O6S2.Na", charge: 0, mass: "774.981", structure: true },
    });
    const chebi = wrapper.get("[data-testid=annotation-chebi]");
    expect(chebi.text()).toContain("C43H47N2O6S2.Na");
    expect(chebi.text()).toContain("774.981");
    const image = wrapper.get("[data-testid=annotation-structure]");
    expect(image.attributes("src")).toContain("/annotation_structure/CHEBI%3A31696");
    await image.trigger("error");
    expect(wrapper.find("[data-testid=annotation-structure]").exists()).toBe(false);
    expect(wrapper.get("[data-testid=annotation-chebi]").text()).toContain("C43H47N2O6S2.Na");
  });

  it("shows the protein of a UniProt resource", () => {
    const wrapper = card({
      ...GO,
      ontology: null,
      collection: { prefix: "uniprot", name: "UniProt Knowledgebase", homepage: null },
      identifier: "P69905",
      uniprot: { entry: "HBA_HUMAN", name: "Hemoglobin subunit alpha", organism: "Homo sapiens", genes: ["HBA1", "HBA2"], length: 142, function: "Oxygen transport." },
    });
    const uniprot = wrapper.get("[data-testid=annotation-uniprot]");
    for (const text of ["Hemoglobin subunit alpha", "HBA_HUMAN", "Homo sapiens", "HBA1, HBA2", "142", "Oxygen transport."]) {
      expect(uniprot.text()).toContain(text);
    }
  });

  it("warns of a pattern mismatch and of the warnings and errors of the resource", () => {
    const wrapper = card({ ...GO, patternMatch: false, warnings: ["Term 'x' is not on OLS."], errors: ["OLS down"] });
    expect(wrapper.find("[data-testid=annotation-pattern-warning]").exists()).toBe(true);
    expect(wrapper.findAll("[data-testid=annotation-warning]").map((w) => w.text())).toEqual([
      "Term 'x' is not on OLS.",
      "OLS down",
    ]);
  });

  it("shows the resource as a link while it loads, before it is requested and after it failed", () => {
    const resource = "https://identifiers.org/GO:0006096";
    const loading = card(null, "loading");
    expect(loading.find("[data-testid=annotation-loading]").exists()).toBe(true);
    const idle = card(null, "idle");
    expect(idle.find("[data-testid=annotation-loading]").exists()).toBe(false);
    expect(idle.get("[data-testid=annotation-identifier]").attributes("href")).toBe(resource);
    const failed = card(null, "failed");
    expect(failed.find("[data-testid=annotation-loading]").exists()).toBe(false);
    expect(failed.findAll("[data-testid=annotation-warning]")).toHaveLength(1);
  });
});
```

- [ ] **Step 2: Run** `npx vitest run tests/unit/annotationCard.test.ts` - Expected: FAIL (component missing).
- [ ] **Step 3: Implement** `client.ts`:

```ts
import type { AnnotationResource } from "@/types/annotation";

export function getAnnotationResource(resource: string): Promise<AnnotationResource> {
  return request<AnnotationResource>(`/annotation_resource?resource=${encodeURIComponent(resource)}`, {
    signal: AbortSignal.timeout(15_000),
  });
}

/** The url of the structure of a ChEBI compound, the source of an `<img>`. */
export function annotationStructureUrl(chebi: string): string {
  return `${API_URL}/annotation_structure/${encodeURIComponent(chebi)}`;
}
```

Replace `AnnotationInfo` by `AnnotationResource` in `api/annotations.ts` and remove `AnnotationInfo` from `api/types.ts`.

`AnnotationCard.vue`:

```vue
<script setup lang="ts">
import { computed, ref } from "vue";

import { annotationStructureUrl } from "@/api/client";
import HelpLabel from "@/components/help/HelpLabel.vue";
import ShowAllButton from "@/components/misc/ShowAllButton.vue";
import { conceptEntry } from "@/report/glossary";
import { isHttpUrl } from "@/report/text";
import type { AnnotationResource } from "@/types/annotation";

/** One resource of an annotation, shown the way cy3sbml shows it: the qualifier, the collection
 * and the identifier as badges, the term of the ontology with its synonyms, its description and
 * its cross references, the chemistry of a ChEBI compound or the protein of UniProt, and the
 * providers which show the entry. Before the resource is resolved, and when it cannot be, the card
 * keeps its head, so that the identifier is always a link. */
const props = defineProps<{
  resource: string;
  qualifier: string;
  info?: AnnotationResource | null;
  state: "idle" | "loading" | "resolved" | "failed";
}>();

/** The synonyms shown before a "show all": a ChEBI compound has dozens of them. */
const SYNONYM_LIMIT = 5;

const allSynonyms = ref(false);
const structureFailed = ref(false);

const synonyms = computed(() => props.info?.ontology?.synonyms ?? []);
const shownSynonyms = computed(() =>
  allSynonyms.value ? synonyms.value : synonyms.value.slice(0, SYNONYM_LIMIT),
);
const fallbackHref = computed(() =>
  isHttpUrl(props.resource)
    ? props.resource
    : `https://identifiers.org/${props.resource.replace(/^urn:miriam:/, "")}`,
);
const identifierHref = computed(() => props.info?.url ?? fallbackHref.value);
const messages = computed(() => [
  ...(props.info?.warnings ?? []),
  ...(props.info?.errors ?? []),
  ...(props.state === "failed" ? [failedText.value] : []),
]);

function label(key: string): string {
  return conceptEntry(key)?.label ?? key;
}
function summary(key: string): string | undefined {
  return conceptEntry(key)?.summary;
}
const failedText = computed(() => "The resource could not be resolved.");
</script>
```

The words "The resource could not be resolved." are chrome of the component (allowed: "the only words the frontend owns are ... in the components themselves").

Template (Tailwind; badges `inline-block rounded-sm px-1.5 align-[1px] text-[11px] leading-[17px] whitespace-nowrap text-white`; colours: qualifier `bg-[#13721c]`, collection `bg-gray-900`, identifier `bg-amber-600 font-mono`, ontology `bg-cyan-700`; section labels `text-xs font-semibold tracking-wide text-gray-500 uppercase`):

```vue
<template>
  <div class="rounded-xl bg-gray-50 p-2.5 text-sm break-words" data-testid="annotation-card">
    <div class="flex flex-wrap items-baseline gap-1">
      <HelpLabel help-key="concepts/annotationQualifier" :tooltip="summary('annotationQualifier')">
        <span class="badge bg-[#13721c]" data-testid="annotation-qualifier">{{ qualifier }}</span>
      </HelpLabel>
      <a v-if="info?.collection" :href="info.collection.homepage ?? undefined" target="_blank" rel="noopener"
        v-tooltip.bottom="summary('annotationCollection')"
        class="badge bg-gray-900" data-testid="annotation-collection">{{ info.collection.name ?? info.collection.prefix }}</a>
      <a :href="identifierHref" target="_blank" rel="noopener" v-tooltip.bottom="summary('annotationIdentifier')"
        class="badge bg-amber-600 font-mono" data-testid="annotation-identifier">{{ info?.identifier ?? resource }}</a>
    </div>
    <p v-if="info?.patternMatch === false" class="mt-1 text-amber-700" data-testid="annotation-pattern-warning">
      {{ info.identifier }} does not match the pattern of {{ info.collection?.name ?? info.collection?.prefix }}.
    </p>
    <p v-for="message in messages" :key="message" class="mt-1 text-amber-700" data-testid="annotation-warning">{{ message }}</p>
    <p v-if="state === 'loading'" class="mt-1 text-xs text-gray-400" data-testid="annotation-loading">resolving</p>

    <template v-if="info?.ontology">
      <div class="mt-1">
        <a v-if="info.ontology.ontology" :href="info.ontology.olsUrl ?? undefined" target="_blank" rel="noopener"
          v-tooltip.bottom="summary('annotationOntology')"
          class="badge bg-cyan-700" data-testid="annotation-ontology">{{ info.ontology.ontology.toUpperCase() }}</a>
        <b class="ml-1" data-testid="annotation-label">{{ info.ontology.label }}</b>
        <a v-if="info.ontology.iri" :href="info.ontology.iri" target="_blank" rel="noopener"
          class="ml-1 text-xs break-all text-gray-500 hover:underline" data-testid="annotation-iri">{{ info.ontology.iri }}</a>
      </div>
      <div v-if="synonyms.length" class="mt-1" data-testid="annotation-synonyms">
        <HelpLabel help-key="concepts/annotationSynonyms" :tooltip="summary('annotationSynonyms')">
          <span class="section-label">{{ label("annotationSynonyms") }}</span></HelpLabel>
        <template v-for="(synonym, i) in shownSynonyms" :key="i">
          <span v-if="i > 0">; </span><span data-testid="annotation-synonym">{{ synonym }}</span>
        </template>
        <ShowAllButton v-if="!allSynonyms && synonyms.length > SYNONYM_LIMIT"
          :count="synonyms.length - SYNONYM_LIMIT" class="ml-1" @click="allSynonyms = true" />
      </div>
      <p v-if="info.ontology.description" class="mt-1 text-gray-800" data-testid="annotation-description">{{ info.ontology.description }}</p>
    </template>

    <div v-if="info?.chebi" class="mt-2 flex flex-wrap items-start gap-3" data-testid="annotation-chebi">
      <a v-if="info.chebi.structure && !structureFailed && info.identifier" :href="identifierHref" target="_blank" rel="noopener">
        <img :src="annotationStructureUrl(info.identifier)" :alt="info.ontology?.label ?? info.identifier"
          class="max-w-full rounded border border-gray-200 bg-white" width="180" height="180" loading="lazy"
          data-testid="annotation-structure" @error="structureFailed = true" />
      </a>
      <table><tbody>
        <tr v-for="row in chebiRows" :key="row.key">
          <td class="pr-3 text-gray-500"><HelpLabel :help-key="`concepts/${row.key}`" :tooltip="summary(row.key)">{{ label(row.key) }}</HelpLabel></td>
          <td class="font-mono">{{ row.value }}</td>
        </tr>
      </tbody></table>
    </div>

    <table v-if="info?.uniprot" class="mt-1" data-testid="annotation-uniprot"><tbody>
      <tr v-for="row in uniprotRows" :key="row.key">
        <td class="pr-3 align-top text-gray-500"><HelpLabel :help-key="`concepts/${row.key}`" :tooltip="summary(row.key)">{{ label(row.key) }}</HelpLabel></td>
        <td>{{ row.value }}</td>
      </tr>
    </tbody></table>

    <div v-if="info?.ontology?.xrefs.length" class="mt-1" data-testid="annotation-xrefs">
      <HelpLabel help-key="concepts/annotationXrefs" :tooltip="summary('annotationXrefs')">
        <span class="section-label">{{ label("annotationXrefs") }}</span></HelpLabel>
      <template v-for="xref in info.ontology.xrefs" :key="xref.label">
        <a v-if="xref.url" :href="xref.url" target="_blank" rel="noopener" class="ml-1 font-mono text-xs text-link hover:underline">{{ xref.label }}</a>
        <span v-else class="ml-1 font-mono text-xs">{{ xref.label }}</span>
      </template>
    </div>

    <div v-if="info?.providers.length" class="mt-1 text-xs" data-testid="annotation-providers">
      <HelpLabel help-key="concepts/annotationProviders" :tooltip="summary('annotationProviders')">
        <span class="section-label">{{ label("annotationProviders") }}</span></HelpLabel>
      <template v-for="(provider, i) in info.providers" :key="provider.url">
        <span v-if="i > 0"> · </span>
        <a :href="provider.url" target="_blank" rel="noopener" class="text-link hover:underline">{{ provider.name }}</a>
      </template>
    </div>
  </div>
</template>
```

Add to the script:

```ts
const chebiRows = computed(() => {
  const chebi = props.info?.chebi;
  if (!chebi) return [];
  return [
    { key: "chebiFormula", value: chebi.formula },
    { key: "chebiCharge", value: chebi.charge },
    { key: "chebiMass", value: chebi.mass },
  ].filter((row) => row.value !== null && row.value !== undefined);
});
const uniprotRows = computed(() => {
  const protein = props.info?.uniprot;
  if (!protein) return [];
  return [
    { key: "uniprotName", value: [protein.name, protein.entry].filter(Boolean).join(" ") },
    { key: "uniprotOrganism", value: protein.organism },
    { key: "uniprotGenes", value: protein.genes.join(", ") },
    { key: "uniprotLength", value: protein.length },
    { key: "uniprotFunction", value: protein.function },
  ].filter((row) => row.value !== null && row.value !== undefined && row.value !== "");
});
```

and a `<style scoped>` block with plain CSS for `.badge` and `.section-label` (the `@apply` of Tailwind utilities is allowed in this project; follow how other components style repeated classes, else inline the classes). The em dash character must not appear anywhere.

`CvTermResourceList.vue`: add the prop `qualifier: string`, keep the resolve bookkeeping, track the state per resource (`loading` when requested, `resolved` on success, `failed` on a rejected resolve that was not aborted, `idle` when not requested), and render:

```vue
<ul class="flex flex-col gap-2">
  <li v-for="resource in shown" :key="resource" data-testid="cvterm-resource">
    <AnnotationCard :resource="resource" :qualifier="qualifier" :info="resolved.get(resource)" :state="stateOf(resource)" />
  </li>
</ul>
```

with `const failed = reactive(new Set<string>())` filled in `.catch((error) => { if (current() && !controller.signal.aborted) failed.add(resource); })`, cleared in `cancelPending`, and

```ts
function stateOf(resource: string): "idle" | "loading" | "resolved" | "failed" {
  if (resolved.has(resource)) return "resolved";
  if (failed.has(resource)) return "failed";
  return controllers.has(resource) ? "loading" : "idle";
}
```

(`controllers` must become reactive, `reactive(new Map())`, for `stateOf` to update.) `CvTermList.vue` stops rendering the qualifier line (the card carries it) and passes `:qualifier="term.qualifier"`; `CvTermNestedList.vue` passes `:qualifier="term.qualifier"` too.

- [ ] **Step 4: Run** `npx vitest run && npm run lint && npx vue-tsc --build --force` - Expected: PASS. Fix the existing unit tests which assert the old markup of a resource (the label as link text, the qualifier line) to the card's test ids.
- [ ] **Step 5: Commit** `git add frontend && git commit -m "Annotation cards in the inspector"`

### Task 14: End to end test of the cards

**Files:**
- Create: `frontend/tests/e2e/annotations.spec.ts`
- Modify: e2e specs which assert the old markup of a resource (`listOf.spec.ts`, `constraintEvent.spec.ts`; `rg -l "cvterm" frontend/tests/e2e`)

- [ ] **Step 1: Write the test** - a pasted model whose species `S1` is annotated with `https://identifiers.org/CHEBI:31696`, `https://identifiers.org/GO:0006096`, `https://identifiers.org/uniprot/P69905` under `bqbiol:is`; `page.route("**/api/annotation_resource?**", ...)` answers fixtures keyed by the `resource` query parameter (the GO, ChEBI and UniProt objects of Task 13's unit test, the UniProt one with `ontology: null`), `page.route("**/api/annotation_structure/**", ...)` answers `<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>` with `contentType: "image/svg+xml"`. Paste it the way `layout.spec.ts` does (`home-tab-paste`, `paste-input`, `paste-submit`), select `S1` in the Species table, then assert in `page.getByTestId("inspector")`: three `annotation-card`s; the GO card's `annotation-label` is "glycolytic process" and its `annotation-ontology` links the OLS url; the ChEBI card's `annotation-structure` is visible and has a natural width above 0 (`evaluate((img: HTMLImageElement) => img.naturalWidth)`); the UniProt card's `annotation-uniprot` contains "HBA_HUMAN"; clicking the `show-all` button in `annotation-synonyms` of the GO card shows all 7 synonyms; clicking `annotation-identifier` is a link with `target="_blank"` and the provider's url.

The model (L3V2 with `metaid`s and an RDF annotation):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" version="2">
  <model id="annotated">
    <listOfCompartments>
      <compartment id="c" spatialDimensions="3" size="1" constant="true"/>
    </listOfCompartments>
    <listOfSpecies>
      <species metaid="meta_S1" id="S1" compartment="c" initialConcentration="1" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false">
        <annotation>
          <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:bqbiol="http://biomodels.net/biology-qualifiers/">
            <rdf:Description rdf:about="#meta_S1">
              <bqbiol:is>
                <rdf:Bag>
                  <rdf:li rdf:resource="https://identifiers.org/CHEBI:31696"/>
                  <rdf:li rdf:resource="https://identifiers.org/GO:0006096"/>
                  <rdf:li rdf:resource="https://identifiers.org/uniprot/P69905"/>
                </rdf:Bag>
              </bqbiol:is>
            </rdf:Description>
          </rdf:RDF>
        </annotation>
      </species>
    </listOfSpecies>
  </model>
</sbml>
```

- [ ] **Step 2: Run** with the backend on 1444: `npx playwright test tests/e2e/annotations.spec.ts` - Expected: PASS (the test passes against the finished Task 13; run it once with the card import broken to see it fail if desired).
- [ ] **Step 3: Fix the other e2e specs** that asserted the old markup, then run the full suite `npx playwright test` - Expected: all pass.
- [ ] **Step 4: Commit** `git add frontend/tests && git commit -m "End to end test of the annotation cards"`

### Task 15: Documentation, screenshots, verification, pull request

**Files:**
- Modify: `docs/report.md` (the Annotations part of the inspector), `frontend/CLAUDE.md` (`AnnotationCard`, `annotationStructureUrl`, the states of a resource), `backend/CLAUDE.md` (the annotation resource, its cache, the structure endpoint; read it first and follow its style)
- Regenerate: `docs/images/inspector-annotations.png` with `npm run screenshots` (backend and dev server running; check that `scripts/screenshots.mjs` still finds the annotations section, adjust its selector if it used the old markup)

- [ ] **Step 1:** Update the docs (one paragraph per idea, no hard wraps, no em dash): what a card shows, where the information comes from (identifiers.org registry, OLS, ChEBI, UniProt), that it is cached for a day by the server and 30 days on disk, that warnings say when a term is unknown.
- [ ] **Step 2:** `npm run screenshots`, look at `docs/images/inspector-annotations.png` (Read the image) and at the inspector in the dev server at 1600 px and at a phone width with chrome-devtools-axi: cards aligned, badges on one line where they fit, no overflow of a long IRI or IUPAC synonym, the structure inside the card. Fix what looks off.
- [ ] **Step 3: Full verification** - backend `uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run ty check && uv run python -m sbml4humans.glossary --check`; root `uv run --project backend zensical build --clean --strict`; frontend `npx vitest run && npm run lint && npx vue-tsc --build --force && npm run build && npx playwright test`. Expected: all green.
- [ ] **Step 4: Commit, push, PR**

```bash
git add -A && git commit -m "Documentation and screenshots of the annotation cards"
git -c credential.helper= -c credential.helper='!gh auth git-credential' push -u origin annotation-details
npx -y gh-axi pr create --base develop --head annotation-details --title "Annotation details resolved via OLS, ChEBI and UniProt (#92)" --body-file <body>
```

The body starts with `Closes #92`, summarises the change per part (pymetadata 0.8.0, backend, frontend, deployment volume `cache`) and the verification, without attribution lines. Wait for the checks and report to the user; merge only when the user asks.
