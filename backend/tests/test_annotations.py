"""Tests of the resolution of annotation resources."""

import logging
import threading
from concurrent.futures import Future
from pathlib import Path
from typing import Any

import pytest
from pymetadata.core.annotation import Provider, RDFAnnotationData

from sbml4humans import annotations
from sbml4humans.annotations import AnnotationResource, ResourceCache, resolve_resource


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
        {
            "database": "MetaCyc",
            "id": "GLYCOLYSIS-VARIANTS",
            "url": "https://biocyc.org/x",
        },
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


def test_html_of_ols_is_plain_text(monkeypatch: pytest.MonkeyPatch) -> None:
    """The html tags of a term of OLS are dropped, a lone `<` is kept."""
    monkeypatch.setattr(
        RDFAnnotationData,
        "query_ols",
        _ols(
            label="alpha-<small>D</small>-galactose",
            description="<small>D</small>-Galactopyranose with a < b.",
            synonyms=[{"name": "<i>alpha</i>-D-Gal"}, {"name": "<br/>"}],
            iri="http://purl.obolibrary.org/obo/CHEBI_28061",
        ),
    )
    term = resolve_resource("https://identifiers.org/GO:0005829").ontology
    assert term is not None
    assert term.label == "alpha-D-galactose"
    assert term.description == "D-Galactopyranose with a < b."
    assert term.synonyms == ["alpha-D-Gal"]


def test_chebi(monkeypatch: pytest.MonkeyPatch) -> None:
    """A ChEBI compound carries formula, charge, mass and whether it has a structure."""
    monkeypatch.setattr(RDFAnnotationData, "query_ols", _ols(label="indocyanine green"))
    monkeypatch.setattr(
        annotations.ChebiQuery,
        "query",
        staticmethod(
            lambda chebi: {
                "formula": "C43H47N2O6S2.Na",
                "charge": 0,
                "mass": "774.981",
                "inchikey": "MOFV",
            }
        ),
    )
    info = resolve_resource("https://identifiers.org/CHEBI:31696")
    assert info.chebi is not None
    assert (
        info.chebi.formula,
        info.chebi.charge,
        info.chebi.mass,
        info.chebi.structure,
    ) == ("C43H47N2O6S2.Na", 0, "774.981", True)


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
                "accession": "P69905",
                "entry": "HBA_HUMAN",
                "name": "Hemoglobin subunit alpha",
                "organism": "Homo sapiens",
                "genes": ["HBA1", "HBA2"],
                "length": 142,
                "function": "Involved in oxygen transport.",
            }
        ),
    )
    info = resolve_resource("https://identifiers.org/uniprot/P69905")
    assert info.uniprot is not None and info.uniprot.entry == "HBA_HUMAN"
    assert info.uniprot.genes == ["HBA1", "HBA2"]
    assert info.url is not None and "uniprot.org" in info.url


def test_errors_are_a_short_text_and_logged(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """A failing request of OLS is shown as a short text, its raw message is logged."""
    raw = (
        "Service is not reachable for 'https://www.ebi.ac.uk/ols4/api/x': "
        "HTTPSConnectionPool(host='www.ebi.ac.uk', port=443)"
    )
    monkeypatch.setattr(
        RDFAnnotationData,
        "query_ols",
        _ols(errors=[OSError(raw), raw], warnings=[1]),
    )
    with caplog.at_level(logging.WARNING, logger="sbml4humans.annotations"):
        info = resolve_resource("https://identifiers.org/GO:0006096")
    assert info.errors == ["The Ontology Lookup Service could not be reached."]
    assert info.warnings == ["1"]
    assert "HTTPSConnectionPool" in caplog.text


@pytest.mark.parametrize(
    "url", ["javascript:alert(1)", "JavaScript:alert(1)", "data:text/html,x", "ftp://x"]
)
def test_urls_which_are_not_http_are_dropped(
    monkeypatch: pytest.MonkeyPatch, url: str
) -> None:
    """An url of OLS, the registry or a provider which is not http(s) is no link."""
    monkeypatch.setattr(
        RDFAnnotationData,
        "query_ols",
        _ols(
            label="glycolytic process",
            iri=url,
            ols_url=url,
            xrefs=[{"database": "MetaCyc", "id": "X", "url": url}],
            url=url,
            collection_homepage=url,
            providers=[
                Provider(name="evil", url=url, official=True),
                Provider(name="good", url="https://example.org/x", official=False),
            ],
        ),
    )
    info = resolve_resource("https://identifiers.org/GO:0006096")
    assert info.url is None
    assert info.collection is not None and info.collection.homepage is None
    assert [(p.name, p.url) for p in info.providers] == [
        ("good", "https://example.org/x")
    ]
    assert info.ontology is not None
    assert info.ontology.iri is None and info.ontology.ols_url is None
    assert [(x.label, x.url) for x in info.ontology.xrefs] == [("MetaCyc:X", None)]


def test_taxonomy(monkeypatch: pytest.MonkeyPatch) -> None:
    """A taxon carries its collection, its providers and the label of OLS."""
    monkeypatch.setattr(
        RDFAnnotationData,
        "query_ols",
        _ols(
            label="Homo sapiens",
            ontology="ncbitaxon",
            iri="http://purl.obolibrary.org/obo/NCBITaxon_9606",
        ),
    )
    info = resolve_resource("https://identifiers.org/taxonomy/9606")
    assert info.collection is not None and info.collection.prefix == "taxonomy"
    assert info.identifier == "9606"
    assert info.pattern_match is True
    assert info.providers and info.url == info.providers[0].url
    assert info.ontology is not None and info.ontology.label == "Homo sapiens"
    assert info.chebi is None and info.uniprot is None


def test_pubmed_has_no_ontology_term(monkeypatch: pytest.MonkeyPatch) -> None:
    """A publication is no term of OLS, it has its providers only."""
    monkeypatch.setattr(RDFAnnotationData, "query_ols", _ols())
    info = resolve_resource("https://identifiers.org/pubmed/10659856")
    assert info.collection is not None and info.collection.prefix == "pubmed"
    assert info.identifier == "10659856"
    assert info.ontology is None
    assert info.providers and info.url == info.providers[0].url
    assert info.warnings == [] and info.errors == []


def test_pattern_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    """An identifier which violates the pattern of its collection is resolved, unmatched."""
    monkeypatch.setattr(RDFAnnotationData, "query_ols", _ols())
    info = resolve_resource("https://identifiers.org/GO:abc")
    assert info.identifier == "GO:abc"
    assert info.pattern_match is False
    assert info.collection is not None and info.collection.prefix == "go"


def test_url_of_another_site() -> None:
    """An url which is not of identifiers.org has no collection, the url is its identifier.

    OLS is not asked without a collection, pymetadata answers a warning instead.
    """
    resource = "https://en.wikipedia.org/wiki/Cytosol"
    info = resolve_resource(resource)
    assert info.collection is None
    assert info.identifier == resource
    assert info.url is None and info.providers == []
    assert info.pattern_match is None and info.ontology is None
    assert info.warnings == ["No collection."] and info.errors == []


def test_unknown_collection() -> None:
    """A collection which is not in the registry raises."""
    with pytest.raises(ValueError):
        resolve_resource("https://identifiers.org/notacollection:123")


def test_cache_directory_from_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`SBML4HUMANS_CACHE` is where pymetadata caches the web services."""
    import pymetadata

    from sbml4humans import annotations

    # set the attribute to its current value so that monkeypatch restores it afterwards
    monkeypatch.setattr(pymetadata, "CACHE_PATH", pymetadata.CACHE_PATH)
    monkeypatch.setenv(annotations.CACHE_VARIABLE, str(tmp_path))
    annotations.configure_cache()
    assert tmp_path == pymetadata.CACHE_PATH


@pytest.mark.parametrize("value", [None, ""])
def test_cache_directory_unset_keeps_default(
    monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    """An unset or empty `SBML4HUMANS_CACHE` leaves the cache of pymetadata alone."""
    import pymetadata

    from sbml4humans import annotations

    before = pymetadata.CACHE_PATH
    monkeypatch.setattr(pymetadata, "CACHE_PATH", before)
    if value is None:
        monkeypatch.delenv(annotations.CACHE_VARIABLE, raising=False)
    else:
        monkeypatch.setenv(annotations.CACHE_VARIABLE, value)
    annotations.configure_cache()
    assert before == pymetadata.CACHE_PATH


class Resolver:
    """Counts the resolves and answers what it was told."""

    def __init__(self, **fields: Any) -> None:
        """Answer resources with the given fields."""
        self.calls = 0
        self.fields = fields

    def __call__(self, resource: str) -> AnnotationResource:
        """Count the call and answer the resource."""
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


class WaiterFuture(Future[AnnotationResource]):
    """A future which counts the requests waiting in `result`."""

    waiting = 0
    all_waiting = threading.Event()
    expected = 3
    guard = threading.Lock()

    def result(self, timeout: float | None = None) -> AnnotationResource:
        """Register the waiter, then wait for the result."""
        with WaiterFuture.guard:
            WaiterFuture.waiting += 1
            if WaiterFuture.waiting >= WaiterFuture.expected:
                WaiterFuture.all_waiting.set()
        return super().result(timeout)


def _run_requests(
    cache: ResourceCache, started: threading.Event, outcomes: list[Any], count: int = 4
) -> None:
    """Run `count` requests of "a", the first one owns the lookup."""

    def request() -> None:
        try:
            outcomes.append(cache.get("a"))
        except BaseException as err:
            outcomes.append(err)

    threads = [threading.Thread(target=request, daemon=True) for _ in range(count)]
    threads[0].start()
    assert started.wait(5)
    for thread in threads[1:]:
        thread.start()
    for thread in threads:
        thread.join(5)
        assert not thread.is_alive()


@pytest.fixture
def waiter_future(monkeypatch: pytest.MonkeyPatch) -> type[WaiterFuture]:
    """Replace the future of the cache by one which counts its waiters."""
    WaiterFuture.waiting = 0
    WaiterFuture.all_waiting = threading.Event()
    monkeypatch.setattr(annotations, "Future", WaiterFuture)
    return WaiterFuture


def test_concurrent_requests_share_one_lookup(
    waiter_future: type[WaiterFuture],
) -> None:
    """Requests of one resource while it resolves wait for that one lookup."""
    started = threading.Event()
    calls = []

    def resolve(resource: str) -> AnnotationResource:
        calls.append(resource)
        started.set()
        assert waiter_future.all_waiting.wait(5)
        return AnnotationResource(resource=resource)

    outcomes: list[Any] = []
    _run_requests(ResourceCache(resolve), started, outcomes)
    assert len(calls) == 1
    assert len(outcomes) == 4
    assert isinstance(outcomes[0], AnnotationResource)
    assert all(outcome == outcomes[0] for outcome in outcomes)


def test_waiters_get_the_exception_of_the_owner(
    waiter_future: type[WaiterFuture],
) -> None:
    """Requests which wait for a lookup which raises get its exception, and do not hang."""
    started = threading.Event()
    calls = []

    def resolve(resource: str) -> AnnotationResource:
        calls.append(resource)
        started.set()
        assert waiter_future.all_waiting.wait(5)
        raise ValueError("unknown collection")

    outcomes: list[Any] = []
    _run_requests(ResourceCache(resolve), started, outcomes)
    assert len(calls) == 1
    assert len(outcomes) == 4
    assert all(isinstance(outcome, ValueError) for outcome in outcomes)


def test_waiters_do_not_hang_when_the_cache_fails(
    waiter_future: type[WaiterFuture],
) -> None:
    """A failure after the lookup completes the waiters with that failure."""
    started = threading.Event()

    def clock() -> float:
        raise RuntimeError("clock broke")

    def resolve(resource: str) -> AnnotationResource:
        started.set()
        assert waiter_future.all_waiting.wait(5)
        return AnnotationResource(resource=resource)

    outcomes: list[Any] = []
    _run_requests(ResourceCache(resolve, clock=clock), started, outcomes)
    assert len(outcomes) == 4
    assert all(isinstance(outcome, RuntimeError) for outcome in outcomes)


def test_expired_entry_is_dropped() -> None:
    """An expired entry is removed when it is found, even if the new lookup is not kept."""
    now = [0.0]
    answers = [
        AnnotationResource(resource="a"),
        AnnotationResource(resource="a", errors=["down"]),
    ]
    cache = ResourceCache(lambda resource: answers.pop(0), clock=lambda: now[0])
    cache.get("a")
    assert len(cache._entries) == 1
    now[0] = 86401.0
    cache.get("a")
    assert len(cache._entries) == 0
