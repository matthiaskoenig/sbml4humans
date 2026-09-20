# Explanations which teach: the help dialog of the report

**Issue:** [#49](https://github.com/matthiaskoenig/sbml4humans/issues/49) - "Provide more detailed tooltips with technical details": the tooltips should allow to learn about SBML and provide technical information, as a larger dialog which opens with a lot of background information.

**Goal:** the report is a learning resource. Every type, attribute, link kind, concept and data type the report shows can be opened in a dialog which explains it on two levels: the high level (what it means for the model, the existing descriptions of the glossary) and the low level (data type, required or optional, the value when it is absent, the validation rules of the specification, the section of the specification). The dialog is navigable like a small reference inside the application, works offline, and is fed by the glossary alone, which stays the single source of every explanation.

## Decisions

1. **Hover for the summary, click for the dialog.** The hover tooltip stays the one sentence it is. A long text in a hover surface disappears on mouse-out, is hard to scroll and does not work on touch or with the keyboard; a docked help pane costs permanent space in a dense layout. Neither is built.
2. **The glossary carries the low level as structured fields**, not as prose: `required`, `default` and `rules` on an attribute, and a new section `datatypes`. XML examples are not part of it.
3. **A validation rule is cited by its libsbml number and never written by hand.** `libsbml.SBMLError` answers with the message, the severity and, for most rules, the section of the specification of a rule number, so the generator resolves the numbers and the text cannot drift from the validator which judges the model of the user. `python-libsbml` is a runtime dependency already.
4. **The details are a second, lazy output of the generator**, markdown rendered in the browser. `glossary.json` stays as it is and stays in the initial bundle for the tooltips; `glossary-details.json` and `markdown-it` are loaded with the first dialog. Pre-rendered HTML in the repository and fetching the documentation site (no offline use, which is the main case of `sbml4humans.show`) are not built.
5. **The open entry is part of the route**, `help=<key>`: an explanation can be linked, survives a reload, and the back button of the browser walks back through the entries visited in the dialog, so the dialog has no history of its own.

## The glossary

**New keys of an attribute entry**, all closed under the known keys of an entry:

```toml
[types.Species.attributes.initialAmount]
label = "initialAmount"
type = "double"
spec = { doc = "l3v2", section = "4.6.4" }
required = false
default = "set by an initial assignment or a rule, otherwise undefined"
rules = [20609, 20611]
summary = "..."
description = """..."""
```

- `required`, a boolean: whether the specification requires the attribute. Every attribute which cites a `spec` states it, an attribute the report adds (`derived units`) must not. This mirrors the rule of the labels.
- `default`, optional plain words without a final period: what holds when the attribute is absent, a literal default or an inherited value ("the substance units of the model"). Only allowed next to `required = false`.
- `rules`, optional, on an attribute and on a type (the rules about the element as a whole): numbers of libsbml validation rules, unique within the entry. The generator resolves a number into `{id, severity, message, section}`; the message is whitespace-normalised and its trailing "Reference: ..." is split off into the optional `section` (not every rule names one). The package of a rule follows from its number: core below 1,000,000, a package by the largest error id offset of the libsbml extension registry which is not above the number (comp 1,000,000, distrib 1,500,000, fbc 2,000,000, qual 3,000,000). A core rule resolves with `SBMLError(code, level, version)`, a rule of a package through the error table of its extension (`getErrorTableIndex`, `getSeverity`, `getMessage`), because the `SBMLError` constructor answers a package rule with the severity its caller passes, not with the one of the rule. A rule which is "not applicable" in the newest version (a rule of Level 2, of Level 3 Version 1 or of fbc Version 1, which the report reads as well) is resolved in the newest version which has it, core in the order L3V2, L3V1, L2V5 and a package from its newest version down. A number libsbml does not know is an error of the glossary: for core an empty message or the category "Internal", for a package the index 0 of the error table. A rule whose package is neither the package of the citing type nor core is an error as well. Which rules are cited no check can judge, the header comment of `glossary/core.toml` holds the rule which was followed: the SBO rule of a type is cited at that type, and a rule about MathML, about units consistency or about modelling practice in general is left out, as are the rules that a `ListOfX` object carries no attribute beyond `metaid` and `sboTerm`, which is not true of a list of Level 3 Version 2, and distrib 1520303 and 1520503, whose messages contradict the specification.

**New section `datatypes`**, in `core.toml` for core and the report, in `packages.toml` for the packages. An entry has the shape of every entry (`label`, `summary`, `description`, optional `spec`, optional `related`), and optionally `values`, the list of the literals of an enumeration (`FbcType`: `maximize`, `minimize`). An entry which cites a `spec` is a data type of that specification (`SId`, `SIdRef`, `UnitSIdRef`, `ID`, `IDREF`, `SBOTerm`, `boolean`, `double`, `integer`, `positiveInteger`, `string`, `anyURI`, `XHTML`, `PortSIdRef`, the enumerations); an entry without one is a value type of the report (`list`, `latex`, `Math`). The `type` of every attribute has to name a `datatypes` entry or a glossary type (`KineticLaw`, `SpeciesFbc`); a `type` which names nothing is an error, so that the type badge of the dialog always leads somewhere. A data type no attribute uses is an error as well.

**Keys.** Every entry has one key, used by the links of the details, by the route and by the frontend: `types/Species`, `types/Species/initialAmount`, `links/compartment`, `concepts/pk`, `datatypes/SIdRef`. The segment of an attribute is its key in the glossary (the field of the report, `initialAmount`, `fbc.charge`), not its label.

## The generator

`sbml4humans.glossary` writes three outputs, `--check` diffs all of them:

1. `frontend/src/data/glossary.json`, byte-identical to today: label, summary, package, page.
2. `frontend/src/data/glossary-details.json`, new: one object `entries`, keyed by the keys above, sorted. An entry carries `kind` (`type`, `attribute`, `link`, `concept`, `datatype`), `label`, `summary`, `description`, `package`, `docs` (the page and the anchor of the entry on the documentation site, relative to its root), and where they apply `owner` (the key of the type of an attribute), `type` (`{label, key}`, the key of the data type or of the glossary type, `list` elements included), `spec` (`{label, section, url}`), `required`, `default`, `values`, `rules`, `related` (keys) and, on a type, `attributes` (the keys of its attributes in the order of the glossary; the common attributes of `SBase` are not repeated, the dialog links them).
3. `docs/reference/*.md`: the attribute table gains the column `required` (`required`, `optional`, empty for what the report adds), the detail of an attribute states its default and lists its validation rules (number, severity, message), a type page lists the rules of the type, and the new page `datatypes.md` (in the navigation of `zensical.toml` below the overview) explains the data types, to which the `type` cells link.

**The links of a description.** A description links other entries by their reference page (`compartment.md`, `concepts.md#primary-key`), which the generator resolves and checks already. For the details it rewrites them with the same resolution: a link to a reference page becomes `glossary:types/Compartment`, a link to an anchor the key of the attribute, concept, link kind or data type behind it, a link to another page of the documentation (`../report.md`) the absolute url of the site, and an external link stays. A link into the reference which resolves to no entry is an error.

## The frontend

**`report/glossary.ts`** gains the keys: `typeKey(type)`, `attributeKey(type, field)`, `linkKey(kind)`. `attributeKey` resolves with the chain `attributeEntry` uses (the field on the type, on `SBase`, then the first segment of a dotted field on both), and both share one lookup, so that a label and its dialog can never disagree. A key is `undefined` where there is no entry, and such a label is not clickable. Built without a key of a concept and one of a data type: no label of the report opens either, the dialog reads the key of a data type from the `type.key` of the entry it has, and `entryOfKey` resolves a `concepts/...` key of the url all the same.

**`report/query.ts`**: `ViewState.help: string | null`, the query parameter `help`. Opening an entry from the page pushes a route, navigating inside the dialog pushes as well, closing removes the parameter. A key which is no entry closes the dialog, like a pk which is no element. The three of them are `openHelp(key)`, `closeHelp(mode)` and `helpRoute(key)` of `report/view.ts`; `closeHelp` takes the mode because a key which is no entry replaces the route instead of pushing one.

**`report/glossaryDetails.ts`**: `loadGlossaryDetails()`, one cached promise of the fetch of `glossary-details.json`, whose url the build emits as a file of its own (`?url`) rather than as a chunk; a rejected promise is dropped so that the next open tries again. `report/helpMarkdown.ts`: `renderHelpMarkdown(markdown, hrefOf)`, which takes the href of an entry as a function and stays free of the router, `markdown-it` (html off, linkify off) through DOMPurify, a `glossary:` link rendered as `<a data-help-key="...">` with the href of the route, every other link with `target="_blank" rel="noopener"`; `validateLink` is an allowlist of `glossary:`, `https:`, `http:` and `mailto:`, so a link of any other scheme and a relative url render as their own text. `markdown-it` (MIT) is imported by this module only, which the dialog imports dynamically.

**`components/help/`**:

- `HelpDialog.vue`, mounted once by the report page and driven by `help`: a native `<dialog>` opened with `showModal()`, which gives the focus trap, Escape, the inert page and the return of the focus to the opener. `max-w-2xl`, at most 80vh, the body scrolls between a fixed header and footer. A click on the backdrop closes it.
  - header: the breadcrumb `Species > initialAmount` (the owner opens its entry, a type carries its `TypeMark`), the data type as a badge which opens its entry, `required` or `optional`, the close button.
  - body: the summary as the lead, **Overview** (the description), **Technical** (a definition list: data type, values of an enumeration, required, default, specification with the link to its section), **Validation rules** (number in mono, severity mark, message), on a type **Attributes** (label, type, required, summary; a row opens the attribute, and a last row leads to the common attributes of `SBase`), **Related** (chips). A part without content is not rendered. Built with the values of an enumeration at the end of the overview, where the sentence which announces them is, and not as a row of the technical list; the technical row `required` answers `yes` or `no`, which its label asks, while the badge of the header says `required` or `optional`; the attributes of a type are a table which states the role of every one of its parts, because the narrow layout lays its rows out as blocks and a browser then drops the roles the elements carry by themselves.
  - the words of the dialog itself, the headings of its parts, the link of its footer and the two words above, are chrome of the interface: they stand in the components which show them and in `components/help/words.ts` where more than one shows them, and are no entries of the glossary.
  - footer: "Open in the documentation", the page and anchor of the entry on the site.
  - while the details load, the header shows what the eager glossary knows and the body a skeleton; when they cannot be loaded, the body is the summary and the link to the documentation.
- `HelpMarkdown.vue`: the rendered description; a click on a `[data-help-key]` link is handled by the router instead of the browser.
- `HelpLabel.vue`: the clickable label, a button with a dotted underline on hover and `cursor-help`, which keeps the hover tooltip; without a key it renders the plain text it replaces.
- `HelpButton.vue`: the small help icon (Lucide `CircleHelp`) for the places where a click is taken. It carries the name `explain <label>`, since it shows no words of its own.
- Both are built on `HelpLink.vue`, a real anchor with the href of the report at `help=<key>`, and not on a button: a plain left click opens the entry in place, and a ctrl click, a middle click or a shift click opens it in a new tab or window, as of any link. `plainClick.ts` is the one test which tells the two apart, shared with the links of a description.

**Entry points.**

| place | opens |
| --- | --- |
| label of an attribute row of the inspector (`AttributeRow`) | the attribute, `HelpLabel` |
| type name in the header of the inspector | the type, `HelpLabel`; the external link to the reference page moves into the footer of the dialog |
| heading of a link group (`LinksColumn`) | the link kind, `HelpLabel` |
| column header of a nested table (`NestedTable`) | the attribute, `HelpLabel` |
| column header of an element table (`ElementTable`) | the attribute, `HelpButton` shown on hover and focus of the header cell; the click on the header still sorts |
| heading of a section (`ElementSection`) | the type, `HelpButton` |
| type bar, element links, type marks | nothing, they navigate |

The home page and the examples page have no explanations and get none. Not in scope: content about the instance ("this species is constant because ..."), a search inside the dialog, a page of its own for the glossary; the keys and the details file carry such a page if it is wanted later.

## Tests

- `backend/tests/test_glossary.py`: the new keys are read and an unknown key is refused; `required` is demanded with a `spec` and refused without, `default` refused next to `required = true`; a rule resolves into id, severity, message and section, an unknown number, a duplicate and a rule of a foreign package fail with the path and the file of the entry; a `type` which names nothing and an unused data type fail; the rewriting of the links (page, anchor, other page of the site, external, unresolvable); the details are deterministic and `--check` fails when they are stale; `glossary.json` is unchanged by the new keys; the reference pages carry the column, the defaults, the rules and `datatypes.md`.
- vitest: every key the helpers produce for every type and field of the columns and of the glossary exists in `glossary-details.json`, and every key inside the details (owner, type, related, attributes, the `glossary:` links of the descriptions) resolves; `help` round-trips through the query; `renderHelpMarkdown` (glossary link, external link, no raw html, inline code); `HelpDialog` with stubbed details (type entry, attribute entry, no empty parts, skeleton, fallback); `HelpLabel` without a key is plain text.
- Playwright, `help.spec.ts`: from the label of `initialAmount` of a species to the dialog and the url, to the type by the breadcrumb, to an attribute by its row, back with the browser, Escape closes and the focus is on the label again; the header of an element table still sorts and its help button opens the dialog without sorting; the type badge opens the data type and a link of a description navigates inside the dialog; a deep link with `help` opens the dialog, an unknown key opens nothing; the details are not requested before the first open. The test of the documentation link of the inspector header follows the link into the dialog.

## Documentation

`docs/report.md` gains the section on the explanations (hover, click, the badges, the parameter `help`) with a screenshot of the dialog from `frontend/scripts/screenshots.mjs`; screenshots which the clickable labels or the header of the inspector make wrong are retaken. `docs/development.md` and the header comment of `glossary/core.toml` document `required`, `default`, `rules` (and how to find the number of a rule) and `datatypes`. `CLAUDE.md` follows (the third output, `components/help/`, `help` in the view state, `markdown-it`). `release-notes/0.7.0.md` is written; the version bump and the tag are a step of their own after the merge of this work.

## Order of the work

One branch, one pull request against `develop`, every step green on its own.

1. The generator: the new keys, `datatypes`, the resolution of the rules, the rewriting of the links, the three outputs and their checks, with `required` not yet demanded.
2. The content: `required`, `default` and `rules` for every attribute of a specification, per package (core, comp, fbc, distrib, qual), and the data types, each from its specification. A second pass per package derives `required` and the attribute of every cited rule from the specification again and independently, because no check can verify them; the differences are resolved against the specification. Then `--check` demands `required`.
3. The frontend: the keys and `help`, the lazy details, the markdown, the dialog, then the entry points one place at a time.
4. The end to end tests, the screenshots, the documentation, `CLAUDE.md`, the release notes.
