# Documentation of sbml4humans

Date: 2026-09-17. Status: approved design. Implements issue #12.

## Goal

sbml4humans renders SBML models as reports, but nothing in the application says what SBML is, what an element type means or what an attribute stands for, and the repository documentation is a README of setup instructions. This adds a documentation site built with Zensical and makes the report self explaining: every element type, every attribute and every link kind of the report carries its explanation in the application and has a page in the reference of the documentation.

The explanations of the application and of the documentation come from one glossary, so they cannot drift apart.

## Non-goals

- No documentation of SBML beyond what the report shows: the site explains the elements of a model and the packages the report supports (comp, fbc, distrib), it is not a replacement for the specification.
- No API reference generated from the python docstrings; the backend is an internal package, its http endpoints are documented by hand.
- No translation, no versioned documentation (the site documents the released state of `develop`).
- No change of the report itself beyond the tooltips, the reference links and the help link.

## Sources

The prose of the glossary and of the background pages is written from these sources and cites them:

- SBML Level 3 Version 2 Core, Release 2 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021, doi:10.1515/jib-2019-0021), the specification of the core classes and their attributes. The LaTeX sources are available locally in `/home/mkoenig/git/sbml-specifications/sbml-level-3/version-2/core/spec/` (`components.tex` holds the class by class chapter, `preliminary.tex` the `SBase` attributes), the RelaxNG grammars under `RelaxNG/` list every element and attribute.
- SBML Level 3: an extensible format for the exchange and reuse of biological models (Keating et al. 2020, Mol Syst Biol 16(8):e9110, doi:10.15252/msb.20199110), the background of SBML and of the Level 3 packages.
- The package specifications in the same repository: comp (`sbml-level-3/version-1/comp/spec/syntax.tex`), fbc (`.../fbc/spec/syntax.tex`), distrib (`.../distrib/sbml-level-3-distrib-package-proposal.tex`).
- The Google Summer of Code 2021 project "Interactive SBML report for Humans (SBML4Humans)" by Sankha Das, mentored by Matthias König and Ralf Steuer (NRNB GoogleSummerOfCode issue #164, https://github.com/nrnb/GoogleSummerOfCode/issues/164, and the project blog https://sbml4humans-gsoc-2021.blogspot.com/) for the motivation of the application.
- MIRIAM (Le Novère et al. 2005, Nat Biotechnol 23:1509-1515, doi:10.1038/nbt1156), the SBO (https://www.ebi.ac.uk/ols4/ontologies/sbo), identifiers.org (https://registry.identifiers.org/) and the COMBINE archive specification (https://co.mbine.org/standards/omex) for the annotation and archive pages.

## The glossary

`glossary/*.toml` in the repository root, written by hand, is the only place where an explanation is written:

- `glossary/core.toml`: the SBML core types and their attributes, including the shared `SBase` attributes.
- `glossary/packages.toml`: the types of the comp, fbc and distrib packages.
- `glossary/report.toml`: the link kinds of the report and the concepts the report adds (derived units, reaction equation, the rendered math, the primary key of an element, the model kind).

Structure (TOML, read with `tomllib` of the standard library, no new dependency):

```toml
[specs.l3v2]
label = "SBML Level 3 Version 2 Core"
citation = "Hucka et al. 2019, J Integr Bioinform 16(2):20190021"
url = "https://sbml.org/documents/specifications/level-3/version-2/core/"

[types.Species]
label = "Species"                          # the label the report uses
package = "core"                           # core, comp, fbc, distrib or report
spec = { doc = "l3v2", section = "4.6" }   # optional
summary = "A pool of a chemical entity in a compartment."   # one sentence, shown as tooltip
description = """
Markdown prose for the reference page, several paragraphs.
"""
related = ["Compartment", "SpeciesReference", "UnitDefinition"]   # links between the reference pages

[types.Species.attributes.initialAmount]
label = "initial amount"                   # the label the report shows
type = "double"                            # the type of the attribute in SBML, or the type of a report field
summary = "The amount of the species at the start of the simulation."
description = """..."""
spec = { doc = "l3v2", section = "4.6.5" }

[links.compartment]
label = "compartment"
summary = "..."
description = """..."""

[concepts.derivedUnits]
label = "derived units"
summary = "..."
description = """..."""
```

Every entry has `label`, `summary` and `description`; `spec`, `type` and `related` are optional. `summary` is one sentence without a final period, because it is shown as a tooltip. `description` is markdown and may link to other reference pages with `[Compartment](compartment.md)` and to external documents by url.

### What the glossary has to cover

- every type of `frontend/src/data/sbmlTypes.ts` (the 3 document types, the 16 element types, the 6 nested types)
- the shared `SBase` attributes `id`, `name`, `metaId`, `sbo`, `notes`, `cvterms`, `history`, `xml`
- every field the report shows for a type: the columns of `frontend/src/report/columns/` and the rows of `frontend/src/components/inspector/attributes/`
- every link kind of `frontend/src/data/edgeKinds.ts`
- the report concepts: `pk`, `sbmlType`, `derivedUnits`, `equation`, `math` (latex and formula), `unitsLatex`, the model `kind`, the manifest of an archive

## Generation

`backend/sbml4humans/glossary.py`, run as `python -m sbml4humans.glossary`, reads the TOML files and writes:

1. `frontend/src/data/glossary.json`: the entries the application needs, i.e. for every type its label, summary, package and the anchor of its reference page, for every attribute its label and summary, and the same for link kinds and concepts. The descriptions stay out of the json, the application shows summaries.
2. `docs/reference/<type>.md`: one page per type with its description, an attribute table (attribute, type, meaning, specification section), the related types as links, and a list of the fields the report adds for the type.
3. `docs/reference/index.md`: the types grouped by package, each with its summary, as a table with links.
4. `docs/reference/links.md` and `docs/reference/concepts.md`: the link kinds and the report concepts.

Both outputs are committed. `python -m sbml4humans.glossary --check` regenerates into a temporary directory and fails when the committed files differ, and the same command validates:

- every type, attribute, link kind and concept listed under "What the glossary has to cover" has an entry (the list of types and fields is read from `frontend/src/schema/report.schema.json`, the link kinds from `glossary/report.toml` against `frontend/src/data/edgeKinds.ts`)
- every `[...](...)` link of a description resolves to a page or an external url
- every image referenced by a page under `docs/` exists

The `docs` job of the documentation workflow runs `--check` before the build, so a change of the report model or of the glossary that is not regenerated fails the pull request.

The frontend has a unit test asserting that every column field, every inspector attribute label, every element type and every edge kind resolves to an entry of `glossary.json`.

## The site

Zensical, configured in `zensical.toml` in the repository root, sources in `docs/`, built into the git ignored `site/`, published to https://matthiaskoenig.github.io/sbml4humans/ by the `documentation` workflow. The configuration follows sbmlutils: same theme features, palette (teal), markdown extensions, social links, `edit_uri` pointing at `develop`. No mkdocstrings.

Navigation:

| page | content |
| --- | --- |
| Home (`index.md`) | what sbml4humans is, the motivation of the Google Summer of Code project, a screenshot of a report, what the report shows, where to start |
| SBML (`sbml.md`) | what SBML is and why it exists (Keating et al. 2020), levels and versions, the structure of a model (compartments, species, reactions, rules, events), the Level 3 packages with the ones the report supports, annotations, SBO and MIRIAM, COMBINE archives |
| Loading a model (`inputs.md`) | the upload, url and paste inputs, which formats are accepted (SBML, gzipped SBML, COMBINE archive), the examples, what happens with an invalid model, screenshots |
| Reading a report (`report.md`) | the type rail, the element tables (sorting, selection, search, the filter of types), the inspector with its three columns, the links between elements, notes, annotations, history and the XML view, the url of a report, screenshots |
| Reference (`reference/`) | the generated pages: index, one page per type, the link kinds, the report concepts |
| References (`references.md`) | the citations of the specification, the Keating paper, MIRIAM, SBO, identifiers.org, the COMBINE archive, and the Google Summer of Code project |
| Development (`development.md`) | repository layout, setup of backend and frontend, tests, the branch model and the rulesets, the documentation itself, the release process |
| Deployment (`deployment.md`) | the server, the containers, the proxy and the certificates, from `deploy.md` |

`docs/images/` holds the screenshots.

## Screenshots

`frontend/scripts/screenshots.mjs` drives the built application with Playwright against a running backend and writes png files into `docs/images/`: the home page with the three inputs, the examples page, a report of the repressilator, the inspector of a species, the annotations of an element with resolved labels, the notes of a model, the search with a filtered table, and the entry selection of a COMBINE archive. `npm run screenshots` runs it, `docs/development.md` documents when to rerun it. The images are committed. The generator's `--check` fails when a page references an image which does not exist.

## The application

- `frontend/src/report/glossary.ts` loads `glossary.json` and resolves an entry for a type, for an attribute of a type (falling back to the shared `SBase` attributes), for a link kind and for a concept. It also builds the url of the reference page of a type from `VITE_DOCS_URL` (default `https://matthiaskoenig.github.io/sbml4humans/`), for example `<base>reference/species/#initialamount`.
- Tooltips (the existing `v-tooltip` directive, which takes a string):
  - the header of every column of an element table shows the summary of the attribute
  - the label of every attribute row of the inspector shows the summary of the attribute
  - the type mark of a section header, of the type rail and of the inspector header shows the summary of the type
  - the label of a link group in the inspector shows the summary of the link kind
- The type label in the inspector header links to the reference page of the type, with an external link icon.
- The app bar has a "Documentation" link to the site.
- Nothing else of the report changes: the same rows, the same layout, the same columns.

## Documentation of the repository

- `README.md` keeps the motivation, one screenshot, a short feature list, the links to the site and to the api, the funding and the license. Everything else moves to the site.
- `docs/development.md` receives the repository layout, the setup and commands of the backend and the frontend, the checks, the branch model and the rulesets, the documentation build and the release process, i.e. what the README holds today.
- `docs/deployment.md` receives `deploy.md`, which is deleted.
- `frontend/README.md` keeps the frontend specific commands and points to the site.
- `CLAUDE.md` mentions the glossary, the generation and the documentation build.

## Testing

- `python -m sbml4humans.glossary --check` in the `docs` job of the workflow.
- Backend unit tests of the generator: the entries of a small fixture glossary render the expected markdown, a missing entry fails the check, a broken link fails the check.
- Frontend unit tests: every column field, inspector label, element type and edge kind resolves to a glossary entry; the tooltips of a rendered table header, inspector row, type mark and link group carry the summary; the reference url is built from `VITE_DOCS_URL`.
- An end to end test opens a report, hovers a column header and asserts the tooltip shows the summary of that attribute, and follows the reference link of the inspector header to the documentation url.
- The `documentation` workflow builds the site on every pull request; `docs` becomes a required check of the `develop` ruleset (`.github/rulesets/develop.json`, applied with `.github/rulesets/apply.sh`).

## Delivery

One branch `documentation`, one pull request against `develop`. GitHub Pages has to be switched to "GitHub Actions" in the repository settings once, which the pull request states.
