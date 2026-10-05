# Annotation details resolved via OLS, ChEBI and UniProt (#92)

Design approved on 2026-10-05. Prototype of the layout: `.lavish/issue-92-annotations.html` (git ignored), option A with the cross references of OLS.

## Goal

The Annotations section of the inspector shows every resource of an annotation in full, as cy3sbml does: the collection, the identifier, the ontology term with its label, synonyms, description and cross references, the providers of the collection, and for ChEBI and UniProt the information of their own web services. The information is resolved through pymetadata and cached.

## Today

- `GET /api/annotation_resource?resource=` calls `RDFAnnotationData` of pymetadata 0.6.6 and answers an untyped dict (`resource`, `resource_normalized`, `collection`, `term`, `label`, `description`, `url`, `synonyms`, `xrefs`, `errors`, `warnings`).
- pymetadata caches OLS answers on disk for 30 days (`~/.cache/pymetadata/ols`), the identifiers.org registry for 24 hours, with a stale fallback when a service is down. In production the cache lives in the home directory of the container and is lost with it.
- The frontend (`components/misc/CvTermList.vue`, `CvTermResourceList.vue`) shows the label, the term and the description; synonyms, cross references, the collection, the providers and the warnings are dropped. The resolve queue (`api/annotations.ts`) resolves at most 4 at a time and 100 of an element automatically.
- For UniProt pymetadata links NCBI Protein instead of UniProt.

## Scope

In: OLS and the identifiers.org registry for every collection, ChEBI (formula, charge, mass, structure) and UniProt (name, entry, organism, genes, length, function). Out: other web services, rendering of markup inside OLS labels.

## 1. pymetadata 0.7.0

- `webservices/uniprot.py`: `UniprotQuery.query(accession) -> dict` against `https://rest.uniprot.org/uniprotkb/{acc}.json`, returning `name`, `entry`, `organism`, `genes`, `length`, `function`. Disk cache `CACHE_PATH/uniprot/<acc>.json` for `CACHE_DURATION_ONTOLOGY`, stale fallback when UniProt cannot be reached, `{}` for an unknown accession.
- `ChebiQuery.structure(chebi) -> bytes | None`: the structure SVG of the ChEBI backend api, cached as `CACHE_PATH/chebi/<id>.svg` with the same expiry and fallback, `None` without a structure.
- The primary provider of a collection is the official non-deprecated resource of the registry, else the first non-deprecated, else the first.
- `RDFAnnotationData` additionally returns `providers` (name, url, official), the collection `name`, `homepage` and `description`, `pattern_match`, the OLS `ontology` name and the OLS term page `ols_url`.
- A collection without an ontology on OLS gets no warning "not on OLS"; a collection with one whose term OLS does not know keeps a warning.
- Tests with recorded responses, a release, then `pymetadata>=0.7.0` in `backend/pyproject.toml` with the updated `uv.lock`.

## 2. Backend

**Model** (`model.py`, in the JSON schema, `npm run types` regenerates `types/report.ts`):

- `AnnotationResource`: `resource`, `collection: Collection | None`, `identifier`, `url`, `pattern_match`, `providers: list[Provider]`, `ontology: OntologyTerm | None`, `chebi: ChebiInfo | None`, `uniprot: UniprotInfo | None`, `warnings: list[str]`
- `Collection`: `prefix`, `name`, `homepage`
- `Provider`: `name`, `url`, `official`
- `OntologyTerm`: `ontology`, `label`, `iri`, `ols_url`, `description`, `synonyms: list[str]`, `xrefs: list[CrossReference]` (`label`, `url | None`)
- `ChebiInfo`: `formula`, `charge`, `mass`, `structure: bool`
- `UniprotInfo`: `entry`, `name`, `organism`, `genes: list[str]`, `length`, `function`

**Endpoints**

- `GET /api/annotation_resource?resource=` answers `AnnotationResource`, built in `annotations.py` from `RDFAnnotationData`, plus `ChebiQuery` for `chebi` and `UniprotQuery` for `uniprot`. An unknown collection or a malformed resource is answered by `error_response` (status 200, error contract). A resource longer than 2,000 characters is refused.
- `GET /api/annotation_structure/{chebi}` answers the cached SVG. The id must match `CHEBI:\d+`. Served as `image/svg+xml` with `Content-Security-Policy: sandbox; default-src 'none'` and `X-Content-Type-Options: nosniff`, used only as an `<img>` source. It answers 404 when there is no structure; this is the one answer outside the JSON error contract (an image), documented in `CLAUDE.md`.

**Cache**: an in-process cache in front of the disk cache of pymetadata, at most 5,000 built `AnnotationResource`s keyed by resource. A resolved resource stays 24 hours, "not found" 10 minutes, an error of a web service is not cached. Concurrent requests of one resource share one lookup. Responses carry `Cache-Control: public, max-age=86400`.

**Deployment**: the cache path of pymetadata is set from `SBML4HUMANS_CACHE` (default `~/.cache/pymetadata`); the production compose file sets it to `/cache` on a named volume `cache`, like `uploads`. The local server of `show` keeps the default.

## 3. Frontend

One card per resource (layout A), `components/misc/AnnotationCard.vue`, rendered by `CvTermResourceList.vue`, a rounded card on gray-50:

1. Head: qualifier badge (green `#13721c`), collection badge (black, links the homepage), identifier badge (orange, mono, links the primary provider).
2. A warning line when the identifier does not match the pattern of its collection.
3. Ontology line: ontology badge (teal, links the OLS page), the label in bold, the IRI as a muted link.
4. Synonyms: the first 5 and a "show all".
5. Description.
6. ChEBI: the structure `<img src="/api/annotation_structure/CHEBI:n">`, linked to ChEBI, next to a table of formula, charge and mass.
7. UniProt: a table of name with entry, organism, genes, length, function.
8. Cross references of OLS: a link where OLS gives a url, text otherwise.
9. Providers: every non-deprecated provider, joined by " · ".

While a resource resolves the card shows its head and a quiet loading line; a failed resolve keeps the head with a warning line, the identifier link still works. Nested CV terms keep their indentation. Resolve queue, `MAX_AUTO_RESOLVES`, `LIST_LIMIT` and "resolve all" stay as they are. On a phone the card wraps and the structure image is at most the width of the card.

**Names**: every label of the card comes from the glossary. `glossary/report.toml` gets entries for the fields of the new model (synonyms, cross references, providers, formula, charge, mass, organism, genes, length, function, qualifier, collection, identifier, ontology); their summaries are the tooltips and the labels open the help dialog. The qualifier badge explains its qualifier through `[datatypes.*]` values of the qualifiers.

**Escaping**: every text is Vue text, never `v-html`. Markup in an OLS label shows as text.

## 4. Testing and documentation

- Backend: `test_annotations.py` builds `AnnotationResource` for GO, ChEBI, UniProt, Taxonomy, PubMed, an unknown collection and a pattern mismatch with recorded answers of pymetadata (monkeypatched, no network on CI); the cache (hit, "not found" for 10 minutes, an error not cached, one lookup for concurrent requests); `test_api.py` for the error contract, the length limit, the structure endpoint (headers, 404, an invalid id) and the current schema.
- Frontend unit: `AnnotationCard` for ontology, ChEBI, UniProt, a plain collection, a warning, loading and failure; the synonym limit; no text as html.
- E2E: `tests/e2e/annotations.spec.ts` with `page.route` fixtures for both endpoints, deterministic and offline; the cards in the inspector, badges and links, the structure image, "show all" of the synonyms. Every element a test uses carries a `data-testid`.
- Docs: the Annotations part of `docs/report.md`, the regenerated glossary outputs, the retaken screenshot `docs/images/inspector-annotations.png`, the cache volume in `docs/development.md` and `deploy.md`.

## Order

1. pymetadata 0.7.0: pull request, release.
2. sbml4humans: backend (model, endpoints, cache, deployment) and frontend in one pull request which closes #92.
