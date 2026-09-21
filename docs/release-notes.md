# Release notes

What changed in every version of SBML4Humans, the newest first. The notes of a version are the text of its [release on GitHub](https://github.com/matthiaskoenig/sbml4humans/releases), where the source of that version is archived. The footer of the application names the version it runs.

## 0.8.0

A report can be read on a phone: below 768 px the report shows the tables or the inspector, one at a time, and no page scrolls sideways any more.

### The report on a phone
- a window narrower than 768 px shows one pane at a time: the report opens with the tables, a tap on a row shows the inspector in their place, and the arrow at the start of its header and the back button of the browser return to the tables where they were left ([#74](https://github.com/matthiaskoenig/sbml4humans/issues/74))
- a report on a phone opens without the model selected, since the inspector would stand in place of the tables; the model and the document are opened from their marks in the type bar
- the type bar is one row: the types are behind a button which says how many of them the tables show, and the bar gives way to the inspector while an element is read
- the search has a row of its own in the app bar, the links of the bar are behind a menu button, and the footer is left to the home page and the examples page
- the explanation of a name fills the window, the examples page stacks its heading and its filter, the rows of a table are as high as a finger needs to hit them
- a tap leaves no tooltip behind: a finger does not hover, and the tooltip of a tapped button stayed over the page until the next tap

### The tables
- the id of a row stays in view while its table scrolls sideways, in every window: the column of the ids is pinned to the left edge of the table, with a line at its right edge while the table is scrolled. A table which fits its window looks as before
- on a phone the pinned column is as wide as its ids and a long id is cut off at 40% of the window, the inspector shows it whole

### Fixes
- the links of the app bar no longer run into the context of a report between 768 px and 1024 px, they are behind the menu button below 1024 px

### Development
- one breakpoint, the `md` of Tailwind: the styles of a narrow window are `max-md:` variants, and what is not a style asks `useNarrow()` of `src/narrow.ts`
- the tables of the report are `report/ReportTables.vue`, which the split of a wide window and the page of a narrow one both render; `SplitPane` did not change
- the Playwright project `mobile` (Pixel 7) runs `tests/e2e/mobile.spec.ts`, the end to end tests of the narrow window, with every run of `npm run test:e2e`
- `docs/report.md` has the section "On a phone" with the picture `report-phone.png`, which `scripts/screenshots.mjs` takes
- the api of the backend and the data model of the report did not change: the release is the frontend and the documentation

## 0.7.2

The tables of a report say more on less space: a value is read together with its units, and the table of the transitions of a qualitative model shows the rules instead of their number.

### The tables
- the derived units stand in the column right of the value they belong to, the size of a compartment, the value of a parameter and the initial amount and concentration of a species, so that a value and its units are read together ([#72](https://github.com/matthiaskoenig/sbml4humans/issues/72))
- the derived units are the only units of a table: the column of the units attribute, `units` of a compartment and of a parameter and `substanceUnits` of a species, is gone, since the derived units are the rendered units of the element and say the same. The attribute stays a row of the inspector, with the link to its unit definition ([#71](https://github.com/matthiaskoenig/sbml4humans/issues/71))
- the column `listOfFunctionTerms` of the table of the transitions shows the rule of the transition instead of the number of its function terms: `level if condition` for every function term in the order of the file and `level otherwise` for the default term, for example `1 if (S ≥ theta_G_S) ∧ (P < theta_G_P); 1 if (G ≥ theta_G_G) ∧ (P < theta_G_P); 0 otherwise`, which gives an overview of the rules of a qualitative model ([#70](https://github.com/matthiaskoenig/sbml4humans/issues/70))

### The examples
- two published logical models of the qual package are examples, written by [TabularQual](https://github.com/sys-bio/TabularQual): `Faure2006`, the Boolean model of the mammalian cell cycle, in which every input of a transition carries its sign, and `ThieffryThomas1995_multivalue`, the decision between lysis and lysogeny of the phage lambda, whose qualitative species have up to four levels ([#78](https://github.com/matthiaskoenig/sbml4humans/issues/78))

### Fixes
- the entries of a COMBINE archive are in the order of its manifest, in the description of an archive example, in the manifest of a report and in the context bar. The order was the one of the file system the archive was extracted to and differed between machines; it is fixed in pymetadata 0.6.4, which the backend requires now

### Development
- the table and the inspector build the rows of the function terms of a transition from one place, `report/transitionTerms.ts`, the inspector had its own copy
- the cell kind `count`, the units link of a table cell and the `latexField` of a column are removed, nothing uses them any more
- the architecture notes of `CLAUDE.md` are split per directory, `backend/CLAUDE.md`, `frontend/CLAUDE.md` and `glossary/CLAUDE.md`, and are loaded with the work below that directory only
- the api of the backend and the data model of the report did not change: the release is the frontend, the glossary, the documentation, the examples and the requirement of pymetadata 0.6.4

### Documentation
- [reading a report](https://matthiaskoenig.github.io/sbml4humans/report/) describes the columns of the tables as they are now, and the screenshots which show a table are retaken
- `CITATION.cff` and the "How to cite" sections name version 0.7.1 and its DOI [10.5281/zenodo.22854257](https://doi.org/10.5281/zenodo.22854257)

## 0.7.1

A maintenance release: SBML4Humans reads its models with libsbml 5.21.2. The application is the one of [0.7.0](https://github.com/matthiaskoenig/sbml4humans/releases/tag/0.7.0), whose notes describe the explanations of a report.

### Dependencies
- `python-libsbml` is 5.21.2 or newer, formerly 5.21.1. [libsbml 5.21.2](https://github.com/sbmlteam/libsbml/releases/tag/v5.21.2) fixes the conversion between markdown and html, a memory leak of the gene product association of fbc and the copy of an `ASTNode` of a constant, and is the first version built for python 3.15
- nothing a report shows changed with it: the reports of the examples are the same with both versions, and so are the message, the severity and the section of the 458 validation rules the glossary cites, which the reference and the explanations read from libsbml

### Known issue
- libsbml 5.21.2 still knows the `UncertKind` value of the coefficient of variation under the misspelling `coeffientOfVariation` only. A distrib file which writes `coefficientOfVariation`, as Section 3.3.2 of the distrib specification spells it, is refused by libsbml with the error 1520308, and its measure is shown without its type ([#66](https://github.com/matthiaskoenig/sbml4humans/issues/66)). A file which a tool built on libsbml wrote carries the misspelling and is shown with its type. Reported to libsbml as [sbmlteam/libsbml#492](https://github.com/sbmlteam/libsbml/issues/492): the body of the specification spells the value correctly, the validation rules of its Appendix A misspell it, and libsbml follows the appendix

## 0.7.0

Every name a report shows explains itself. A click on the label of an attribute, on the name of a type or on the heading of a group of links opens a dialog which says what the thing is and what the specification asks of it: the data type of its value, whether it is required, what holds when a file does not set it, and the validation rules it is held to, as libsbml states them. The glossary carries all of this, so the reference of the documentation states it as well, and a report which was opened from python explains itself without a network.

### The explanations
- a click on a name of the report opens its explanation in a dialog over the report ([#49](https://github.com/matthiaskoenig/sbml4humans/issues/49)): the labels of the rows of the inspector, the name of the type in its header, the headings of the groups of links and the headers of the columns of a small table. Where the name is a control already, a small help icon next to it opens the dialog: in the header of a column of an element table, where a click sorts the table, and next to the heading of a table. Hovering a name shows the one sentence it showed before
- the dialog shows the summary, the description, the technical detail of the entry (data type, required or optional, what holds when the attribute is absent, the section of the specification), the validation rules of the specification with their number, their severity and their message, for a type its attributes and the entries which are read next to it, and it links the page of the entry in the documentation
- it is a small reference of its own: the type an attribute belongs to, the badge of the data type, a row of the attributes, a related element and every name the text links open the entry they name, and the back button of the browser walks back through the entries which were opened. Every opener is a real link, so a ctrl-click or a middle click opens an explanation in a new tab
- the open entry is the parameter `help` of the url, `?help=types/Species/initialAmount`, so an explanation can be linked and survives a reload
- the explanations ship with the application: a report which `sbml4humans.show` opens needs no network for them. They are a file of the build, which the first dialog of a session fetches together with the renderer of their markdown, and no other page pays for either
- the header of the inspector no longer links the reference page of the type: the name of the type opens its explanation, whose footer links that page

### The glossary and the reference
- every attribute which cites a specification says whether that specification requires it, 205 of them, and 80 say in plain words what holds when a file does not set them: the value which is assumed, the element the value is taken from, or that the quantity is simply unknown. The fields the report adds itself state neither of the two, no specification asks anything of them
- an entry cites the validation rules of the specification which concern it, by the number a validator reports. Their text is never written in the glossary: the generator reads the message, the severity and the section of the specification from libsbml 5.21.1, the library which judges the file of a reader, so no rule of the documentation can drift from the validator. 458 rules are cited, at the 243 types and attributes they are about
- [Data types](https://matthiaskoenig.github.io/sbml4humans/reference/datatypes/) is a new page of the reference: the 30 data types an attribute of the report can carry, the `SId` and its references, the numbers, the strings, the seven enumerations with their values and the kinds of value the report adds itself. The `type` of every attribute of the reference links its entry there
- the reference pages carry the rest of it: the table of the attributes of a type has the column `required`, the entry of an attribute states its default and lists its rules, and a type lists the rules about the element as a whole
- the values of `UncertKind` are spelt as the distrib specification spells them. Note that libsbml 5.21.1 knows the coefficient of variation under the misspelling `coeffientOfVariation` and not under `coefficientOfVariation`, so a file which a tool built on libsbml writes carries the misspelling

### Corrections
- `fbc:charge` is a `double`, as fbc Version 3 defines it, where the glossary called it an integer
- a [port](https://matthiaskoenig.github.io/sbml4humans/reference/port/) of comp names its element in one of three ways and not four: no port may name a port of its own model, it reaches a port of one of its parts through a nested reference
- the `listOfDeletions` of a [submodel](https://matthiaskoenig.github.io/sbml4humans/reference/submodel/) is Section 3.5.2 of the comp specification
- an end of an [uncert span](https://matthiaskoenig.github.io/sbml4humans/reference/uncertspan/) which a file sets by neither a value nor a variable is undefined, as distrib says of it, where the glossary called the interval open at that end
- the fbc block of a model, which holds `strict` and the active objective, is optional
- the gene association of the example of Section 3.9 of fbc is an `or` of three complexes, and the report writes it with the identifiers of the gene product references and not with the labels the reconstruction knows the genes by
- the data types, the references of comp and the defaults of qual and distrib say what their specifications say, in the places where the first draft of the glossary was shorter than the specification

### Fixes
- a tooltip of an element inside a modal dialog was painted behind the dialog, because the dialog is drawn in the top layer of the browser and above everything the page paints

### Development
- the glossary generator writes a third file, `frontend/src/data/glossary-details.json`, the description and the technical detail of every entry for the dialog: 54 types, 241 attributes, 49 link kinds, 10 concepts of the report and 30 data types. `glossary.json`, which every page loads for its tooltips, is unchanged
- `sbml4humans.glossaryrules` resolves a rule number into its message, its severity and its section with libsbml: a rule of the core through `SBMLError` in the newest version which has the rule, a rule of a package through the error table of its extension
- `python -m sbml4humans.glossary --check` demands `required` of every attribute of a specification, refuses it on an attribute the report adds, resolves every cited rule and refuses one of a foreign package, and demands that every `type` names a data type or a type of the glossary and that every data type is used
- the api of the backend and the report it answers did not change: the whole release is the glossary, its generated files and the frontend
- the backend has 660 tests, the frontend 438 unit tests and 90 end to end tests

### Documentation
- [reading a report](https://matthiaskoenig.github.io/sbml4humans/report/#explanations) has the section "Explanations": where an explanation is opened, what the dialog shows and how it is linked
- [development](https://matthiaskoenig.github.io/sbml4humans/development/#documentation) describes the keys an entry of the glossary states, how the number of a validation rule is found and what the check of the documentation refuses

## 0.6.2

A report names things as the specification does: a type is written as the name of its class and an attribute as the file writes it, so that a name which is read in a report is the name to look for in the specification, in the XML and in a library such as libsbml. The report page opens with the model in an inspector at the left of the tables, the `ListOf` containers of a model which state something of their own are elements of the report, and the documentation carries the release notes.

### Names of the specification
- a type is written as the name of its class, `FunctionDefinition`, `AssignmentRule`, `SBMLDocument`, in the type bar, over its table, in the header of the inspector and in the reference, where it was "Function definitions" and "Assignment rule" before ([#48](https://github.com/matthiaskoenig/sbml4humans/issues/48))
- an attribute is written as the file writes it, `initialConcentration`, `hasOnlySubstanceUnits`, `listOfReactants`, `metaid`, `sboTerm`, as the header of a column, as the label of a row of the inspector and in the reference. An attribute which a package adds to a type of the core carries the prefix of the package, `fbc:charge`, `comp:replacedBy`, and a group of links is named after the attribute which makes the reference, `kineticLaw`, `lowerFluxBound`
- what the report adds itself keeps plain words and is told apart by that: the derived units, the equation of a reaction, the status of an external model definition
- the label column of the inspector is as wide as the longest label of the element, so that no label is cut, whatever the font is
- the anchors of the reference pages follow the names, e.g. `reference/species/#initialconcentration`; a link to an anchor of an attribute of an older version of the documentation ends at the top of its page

### The report page
- the inspector is at the left of the tables ([#44](https://github.com/matthiaskoenig/sbml4humans/issues/44))
- a report opens with its model in the inspector, and so does the model or the entry of an archive a reader switches to ([#40](https://github.com/matthiaskoenig/sbml4humans/issues/40)). An inspector which is closed stays closed, a url which names an element keeps it, and the selection adds no step to the history of the browser
- the inspector has a notes section only for an element whose notes show something ([#41](https://github.com/matthiaskoenig/sbml4humans/issues/41))
- the unit definitions are the last entry of the type bar and the last table: they are what the other tables link to for their units, not what a model is about ([#39](https://github.com/matthiaskoenig/sbml4humans/issues/39))

### ListOf containers
- every `ListOf` class of SBML derives from `SBase`, and a file may write a `metaid`, an `sboTerm`, notes and an annotation on a list, from Level 3 Version 2 an `id` and a `name` as well, for example a note which says why a list is empty. The report dropped all of it and carries it now ([#35](https://github.com/matthiaskoenig/sbml4humans/issues/35)): a list which states something of its own is an element of the type `ListOf`, with the name of the list in the file, its size, its notes, its annotations and the XML of the list without its elements. A model whose lists state nothing has the report it had
- a list is linked behind the count in the heading of the table of its type and in the `lists` row of the element which owns it, which reaches an empty list and the lists of a reaction, a kinetic law or a unit definition. A list without an id is named after its owner and its element, `J0.listOfReactants`
- a list is a node of the link graph: its owner names it by a link of the kind `listOf`, and a port, a deletion or a replacement of comp which references a list by its `metaIdRef` or `idRef` ends at it
- the api carries the lists as `lists` of every element, each with `sbmlType: "ListOf"`, `element` and `size`, and the edge kind `listOf`
- `list_of` is a new example which states something on five of its lists

### Application
- the version in the footer links its release on GitHub, next to the commit the application was built from ([#42](https://github.com/matthiaskoenig/sbml4humans/issues/42))
- "Feedback" in the bar opens a new issue on GitHub with the version, the page, the model and the browser already written ([#43](https://github.com/matthiaskoenig/sbml4humans/issues/43)). For an example and for a model behind a url the issue names the model and the state of the report; for a file of the reader it names neither the file nor the ids of its elements, and nothing is sent before the issue is submitted

### Fixes
- a model definition of comp carried its whole XML in the report, every element of the definition a second time, which nothing showed; it is left out like the XML of a model
- the python package ships the text of its license: the wheel and the sdist of 0.6.1 contained none ([#53](https://github.com/matthiaskoenig/sbml4humans/pull/53))

### Documentation
- the [release notes](https://matthiaskoenig.github.io/sbml4humans/release-notes/) of every version are a page of the documentation ([#45](https://github.com/matthiaskoenig/sbml4humans/issues/45)), generated from the files which are the text of the GitHub releases
- [reading a report](https://matthiaskoenig.github.io/sbml4humans/report/) explains the names, the lists and the feedback, the reference has the page [ListOf](https://matthiaskoenig.github.io/sbml4humans/reference/listof/), and the screenshots show the application as it is
- the README of the package, which is the page of the project on PyPI, carries the badges, the funding and the license

### Development
- the glossary is the single source of every name as it is of every explanation: the frontend states no header of a column, no label of a row of the inspector and no label of a type or of a link group of its own. `python -m sbml4humans.glossary --check` refuses a label of a specification which is not a name of it, a test of the frontend refuses a row which states a label
- `python -m sbml4humans.releasenotes` writes `docs/release-notes.md`, its `--check` runs in the `docs` job and fails when the page is stale or when the version of the package has no release notes, and the version bump runs the generator as a hook
- the `package` job checks that the wheel and the sdist carry the license
- the backend has 600 tests, the frontend 345 unit tests and 76 end to end tests

## 0.6.1

The first version of SBML4Humans on [PyPI](https://pypi.org/project/sbml4humans/): `pip install sbml4humans`. The release 0.6.0 introduced the python package, but its upload was refused, so 0.6.0 exists as a GitHub release only. The application itself is the one of [0.6.0](https://github.com/matthiaskoenig/sbml4humans/releases/tag/0.6.0), whose notes describe the python interface and the external model definitions.

### Development
- the workflow which tests, releases and publishes is `ci-cd.yml` with the name `CI/CD`, formerly `ci.yml` ([#51](https://github.com/matthiaskoenig/sbml4humans/pull/51)). The trusted publisher of the project on PyPI names this workflow, and the upload of 0.6.0 was refused with `invalid-publisher` because the file had another name. The required checks are the names of the jobs and did not change

## 0.6.0

SBML4Humans is a python package now: `sbml4humans.show("model.xml")` opens the report of a file of your machine in the browser, served by a local server, and the file never leaves the machine. A model of the comp package is shown with the models it is built from: an external model definition is followed into the document it names, and the replacements, the deletions and the ports end at the element they name in it.

### Reports from python
- `from sbml4humans import show; show("model.xml")` and the command `sbml4humans model.xml` open the report of an SBML file, plain or gzipped, or of a COMBINE archive in the browser ([#33](https://github.com/matthiaskoenig/sbml4humans/issues/33)). The package is on [PyPI](https://pypi.org/project/sbml4humans/), `pip install sbml4humans`, needs python 3.14 and ships the application itself, the api and the built user interface. The new page [Reports from python](https://matthiaskoenig.github.io/sbml4humans/python/) describes it
- the file is not uploaded anywhere: `show` starts a server on a free port of `127.0.0.1`, lets it create the report and opens `/report?local=<token>`. The report needs no network, apart from the labels of the annotations, which are looked up when an element which has some is opened, and the build which ships with the package reports no page views
- the server is a process of its own which outlives the call, so a script which calls `show` and ends leaves a working page behind. Later calls use the same server, a server of another version is replaced, and it ends itself a quarter of an hour after the last report was closed, which an open report prevents. `sbml4humans --stop` and `sbml4humans.stop()` end it, `show(path, open_browser=False)` and `--no-browser` give the url without opening it
- the server answers its own page only: a request which names another host or which comes from the page of another site is refused, creating the report of a path and ending the server need a secret from a file only the user can read, and a report is read by its random token of 128 bits
- a file which does not exist raises `FileNotFoundError`, a file without an SBML model raises `ValueError` with the errors libsbml reports, and the command prints the message and exits with the code 1

### External model definitions
- an external model definition of comp is resolved against the other entries of its COMBINE archive, and the replacements, the deletions and the ports which reach into a submodel that instantiates it end at the element they name in the other entry, through the ports of that model and into external models of its own ([#36](https://github.com/matthiaskoenig/sbml4humans/issues/36)). All 368 comp references of the examples end at an element now, where every reference into an external model ended at the submodel before
- a link into another entry shows the file name of that entry behind the element and opens the report of that entry with the element selected, and the element lists the link under "Referenced by" with the file name of the entry it comes from
- the inspector of an external model definition says how far it was followed: the status, the document and the model it resolves to, and whether the md5 checksum of the definition is the one of the document. A checksum which does not match is stated and the definition is still followed. A submodel links the external model behind it, or says why there is none
- nothing is ever fetched: a source which is a URL is marked as a remote source, so that the time of a report does not depend on another server and a model cannot make the server request an address. An SBML file which is uploaded on its own has no file next to it, so its references end at the submodel as before; a COMBINE archive with both files resolves them
- a path which was chosen on the machine is read with the files next to it which its external model definitions name, as further entries of the report: the single file examples (`comp_deletion`, `icg_body`, `dex_body`, `spt_body`, `minimal_model_comp`) and every file which is opened from python. A source which leaves that directory, by its path or through a symbolic link, is not read. The entry of such a file is named after the file instead of `./model.xml`
- the api carries the entry of the target on an edge which leaves its entry (`targetEntry`) and the resolution of an external model definition (`resolution` with `status`, `entry`, `model` and `md5Matches`); a primary key stays local to its entry

### Documentation
- [Reports from python](https://matthiaskoenig.github.io/sbml4humans/python/) is a new page of the user guide, and [reading a report](https://matthiaskoenig.github.io/sbml4humans/report/#models-of-other-documents) says which models of other documents are read and why none is fetched
- the reference of the [external model definition](https://matthiaskoenig.github.io/sbml4humans/reference/externalmodeldefinition/) explains the resolution and every one of its statuses, and the concepts gained the link into another document

### Development
- the `package` job of the CI builds the frontend into the package (`npm run build:package`), builds the wheel and the sdist, installs the wheel into a fresh environment and opens a report with it; on a tag the `publish` job uploads these artifacts to PyPI by trusted publishing
- the backend has 562 tests, the frontend 317 unit tests and 67 end to end tests

## 0.5.0

SBML4Humans reads the complete data model of SBML now: the core of Level 3 and the packages comp, fbc, qual and distrib, with every reference between two objects an edge of the link graph and every object explained where it is shown. The report page is laid out anew, with the elements of a model on top and the detail next to the tables, and the application has its logo and a footer again.

### The complete data model
The report carries the data model of SBML Level 3 core and of the packages comp, fbc, qual and distrib: the objects of the specification with the attributes libsbml reads of them, the references between them as the edges of the link graph, and every one of them rendered, explained on hover and documented in the reference ([#11](https://github.com/matthiaskoenig/sbml4humans/issues/11)). The lists of the specification are the one part which is not an object of its own: a list is the table of its elements, and notes or annotations on a list itself stay in the XML of the file ([#35](https://github.com/matthiaskoenig/sbml4humans/issues/35)). A replacement into a submodel whose model is defined in another document of the same archive still ends at the submodel ([#36](https://github.com/matthiaskoenig/sbml4humans/issues/36)).

- qual is read: the qualitative species with their levels and the transitions with their inputs, outputs, function terms and default term are sections of the report, the transitions table shows the influence of every input with the sign which says whether it activates or inhibits, and the inspector of a transition writes the transition table the specification defines
- fbc is read in all three of its versions: the flux bound objects of Version 1, the strictness of a model from Version 2 on, and the user defined constraints, the quadratic flux objectives, the key value pairs and the charge of a pseudoisomer of Version 3, while every version names its active objective and makes a flux objective an element of its own. The genes a reaction needs are the tree of `and` and `or` the specification defines instead of one string, shown as the expression that tree stands for with every gene a link, and the species and reactions tables carry the columns a reader of a flux model comes for: the chemical formula, the charge, the two flux bounds and the association
- comp is complete: a deletion, a replaced element, a replaced by and every link of a chain of references are elements of the report with their own attributes, notes and annotations. A replacement which names an element inside a submodel resolves to that element instead of stopping at the submodel, the conversion factor of a replacement and the md5 of an external model definition are read, and the identifiers of the ports keep the namespace of their own the specification gives them instead of sharing the one of the other identifiers of the model
- distrib carries the measures of an uncertainty as the elements they are: an uncert parameter with its identifier, its notes and its annotations, which is where a file records which experiment or which publication a number comes from, an uncert span with the interval it stands for, and the parameters a distribution is defined by, however deep they nest
- core gained the objects it flattened: the units a unit definition is built from, next to the formula they render to; the trigger, the priority and the delay of an event, each with its own attributes and its own math; the message of a constraint, rendered as the XHTML it is instead of as markup; and the annotation of the document and of the model, with the controlled vocabulary terms nested inside a term
- three defects which lost data are fixed. Every local parameter of a Level 2 kinetic law was dropped, because libsbml keeps those parameters in another list than the Level 3 ones: the curated BioModels of the examples gained 1473 of them with their values, their units and their links, and the constants of a Level 2 rate law link to the values they stand for. An uncertainty which is a span lost its numbers and showed the word of its type followed by five empty cells. The identity of an initial assignment, a rule and an event assignment came from an alias of libsbml which answers the symbol or the variable, so an element with an identifier of its own was keyed by a digest of its XML, its permalink changed whenever its math changed, and a rule could shadow the species reference it sets
- every edge of the link graph starts at the object which carries the reference: the edge to the species of a reactant at the species reference which names it and not at the reaction, the edge to a gene product at the gene product reference, the edge to the reaction of an objective at the flux objective, the math edges of an event at its trigger, its priority or its delay and those of an uncertainty at the measure which holds that math. A reaction names its kinetic law and an event its trigger, its priority, its delay and its assignments. The inspector still answers which species a reaction consumes and which reactions consume a species, across the species reference, and it looks across a kinetic law the same way: a species lists the reactions whose kinetic law reads it, where it listed the meta ids of the kinetic laws before, and a transition lists what the conditions of its function terms read. An element which a file nests in another one and which carries no id of its own is named after that element and its place in it, such as `Reaction7.kineticLaw` or `Start.trigger`, instead of by a meta id which says nothing about where it sits. Together with the objects which were missing this connects what stood outside the graph: 46072 of the 74585 nodes of the reports of the examples had no edge at all before this release, 387 of 109489 have none now, 370 of them unit definitions no element uses and the rest parameters, compartments and one function definition nothing in their model reads, and no edge of the 192789 is there twice
- an infinite value and a value which is not a number are carried as what they are. The api sends `Infinity`, `-Infinity` and `NaN`, which JSON has no literal for, the report shows ∞, -∞ and `NaN`, with the `INF` of the file as the tooltip of the sign, and `null` keeps its one meaning, that the file does not set the attribute: one dash stood for both an infinite bound and an unset one before
- a document of Level 3 Version 2 no longer lists a package without a name: libsbml reports the namespace of the core as a plugin of such a document, which the inspector of the document showed as an empty chip and the api carried in the report and in the metadata of the examples
- a column which no row of a table fills is left out of it, so that the fbc columns fit next to the columns of the core and every table shows what its model actually uses
- every relation of the graph which is an attribute of its own has a link kind of its own, 48 kinds in all, so that an element says which end of which relation it is: the lower and the upper bound of a flux and of a user defined constraint, the two ends of an interval, the second reaction of a quadratic flux objective and the second variable of a quadratic component, the time and the extent conversion factor of a submodel. The document names its models and its external model definitions, a kinetic law its local parameters, a reference of comp the reference it carries, an element its uncertainties, and a formula the unit definition a number of it names
- an element the file gives no identifier is keyed by what it names or by its place, instead of by a digest of its XML or its position in a list: a flux objective by the fluxes it multiplies, a measure of an uncertainty by its type, a replacement by the element it reaches, an algebraic rule, a constraint or an event by its place among the elements of its type. A repetition of such a key, a species which a reaction lists twice among its reactants, is told apart by its occurrence, so that no two elements of a report share a key
- the numbers of a model read as what they are: the dot of a product is set as the operator it is instead of glued to its left operand, a dimensionless quantity has the derived units `dimensionless` instead of a dash or a fraction of ones, a species reference of Level 1 or 2 without a number has the stoichiometry one its level defines, and a reaction of those levels which does not write its flags is reversible and, from Level 2 Version 2 on, not fast, as its level defines. A unit which leaves out its scale no longer keeps a report from ever finishing
- a hierarchical model whose replacement names no submodel, or whose model definition instantiates itself, is reported with that reference logged instead of failing the whole report, and the report of Recon3D is back at the time it took before this release while it carries the complete data model
- six example models ship with the application, one per part of the data model which no published model contains: `constraint_event`, `comp_deletion`, `fbc_bounds_v1`, `fbc_constraints_v3`, `qual_example` and `distrib_spans`, each of them free of errors and warnings of `checkConsistency`

### Report
- the fast column of a reactions table is shown only when a reaction of the model is fast: a file of Level 2 gives every reaction the default false of its level and Level 3 Version 2 has no such flag, so the column read the same mark in every row of every curated model, while a single fast reaction is what a reader has to see
- a boolean has three marks for its three states: a check for true, a thin cross for false and the dash of an attribute the file does not set, where `false` and an unset attribute read as the same dash before, so that "reversible" and "fast" of one reaction said two different things with one sign
- an element the file gives no identifier is named in its row as the inspector and every link name it, in italics, which tells a name the report gives from an identifier of the file: the rules and the initial assignments of a curated model show the element they set in the id column again instead of a dash, and the column sorts by that name. A row of a small table of the inspector names its element the same way, a species reference `R_PFK.M_atp_c` where it showed the identifier of the species as its own, a kinetic law `R1.kineticLaw` where it read "kinetic law"
- a gene product names the reactions which need it, looked across the tree of their gene association the way a species names the reactions which consume it, where it listed its own identifier once for every reaction; a reaction names the genes it needs in the same way, a reference of an association is named after its reaction and its gene and a flux objective after its objective and its reaction, so that neither reads as what it points at
- the inspector of an element shows the measures of each of its uncertainties, the table its uncertainty shows, where it counted them; the uncertainty names the element it describes, and the search finds an element by the names, the notes and the measures of its uncertainties
- the tables of the objectives and of the user defined constraints show the sum they are, `1 × EX_biomass` or `c_two × v1 + c_one × v2`, and the table of the submodels links their deletions, where each of them counted its list; a column which still counts says so in its tooltip
- the search finds a rule by the name of the element it sets, which the documentation promised, a row by the identifiers and the names of the elements it holds, such as the inputs of a transition or the deletions of a submodel, an element by the port its replacement names and a gene product by its label
- the header of the inspector stays one line: a long type such as "User defined constraint component" wrapped onto three lines of it and lost two of them at 1280 px, where the name of the element now gives way first
- the tables one element shows under each other, the reactants, the products and the modifiers of a reaction, the inputs and the outputs of a transition and the measures of its uncertainties, line up their columns, and every header of such a table explains its column on hover
- the three sections of the inspector are as high as what they hold, where a tall window stretched them to a third each, and the attributes carry their heading in the three columns as well
- a gene of an association stays on the line of its parenthesis, a small group of genes is written out instead of a button as wide as it, a resolved annotation breaks between its words, an example card shows the whole identifier of its example, and the gene association of a table is cut later
- the value of a key value pair or a name which reads `Infinity` is shown as the word it is, only a number of the report is the sign of infinity, and an external parameter of a distribution which has a value and a formula shows both
- the events table shows what an event does: the column "assignments" lists every event assignment as the element it sets and the formula it assigns, instead of counting them ([#2](https://github.com/matthiaskoenig/sbml4humans/issues/2))
- every row of every element table carries the mark of its type in the id column, so a row says on its own which kind of element it is: an initial assignment, which has no identifier of its own and shows the symbol it sets, is no longer indistinguishable from the parameter of that name or from an assignment rule ([#4](https://github.com/matthiaskoenig/sbml4humans/issues/4))
- the report page says on top what a model is made of: the element types are a row over the tables instead of a rail on the left, and a type the model has no element of is not listed at all. The tables and the inspector are next to each other now, the inspector a column at the right of them which opens at a third of the window, the search sits next to the logo, the location a plain SBML file never chose is gone from the bar, and the report page carries the footer of the home and the examples pages ([#25](https://github.com/matthiaskoenig/sbml4humans/issues/25))

### Application
- the logo of SBML4Humans is back: in the app bar of every page, on the landing page next to the title, and as the logo of the documentation site ([#23](https://github.com/matthiaskoenig/sbml4humans/issues/23))
- the home page and the examples page carry a footer which states the version and the commit the application was built from, with the commit linking to its page on GitHub, how to cite SBML4Humans, and the repository, the documentation, the privacy notice and the lab the application comes from ([#24](https://github.com/matthiaskoenig/sbml4humans/issues/24))
- the footer cited the wrong archive: its "Zenodo DOI" link pointed at the record of another repository. It carries the DOI of SBML4Humans now

### Documentation
- the reference has a page per element type the report gained, generated from the glossary like every other: the trigger, the priority and the delay of the core, the deletion, the replacements and the reference of comp, the association tree, the flux bound, the flux objective and the user defined constraints of fbc, the qual package with its six types, and the uncert parameter and the uncert span of distrib
- the pages say what a report shows today: [SBML](https://matthiaskoenig.github.io/sbml4humans/sbml/) names qual among the packages the report reads, says what it shows of comp, fbc and distrib and where a reference into another document ends, [reading a report](https://matthiaskoenig.github.io/sbml4humans/report/) describes the layout of the page, the columns which a table leaves out, the three marks of a boolean, the names in italics, the tables of a qualitative model, the elements a file nests inside another, the gene association, the objectives table, the interval of an uncertainty, the sign of infinity and what the search finds, and [loading a model](https://matthiaskoenig.github.io/sbml4humans/inputs/) lists the new examples
- the reference page of fbc names every section the package adds to a model, the flux bounds of Version 1 and the user defined constraints of Version 3 among them, and says what each of the three versions writes differently
- the README and the home page of the documentation say how to cite SBML4Humans, with the DOI of the release archived on Zenodo and its badge, and `CITATION.cff` lets GitHub offer the citation on the page of the repository
- the qual specification with its citation and the Version 1 and Version 3 specifications of fbc are in the [references](https://matthiaskoenig.github.io/sbml4humans/references/)
- the screenshots of the site were taken again, with the report of a qualitative model and the attributes of a reaction of a constraint based model among them. The qualitative model is taken at the width of the column of the site, where the signs of its influences read at the size of the text next to them, and the attributes of the reaction are taken with the header of the inspector above them, which tells them from a table of the page

### Development
- the production build takes the commit as the build argument `VITE_COMMIT`, which `deploy.sh` exports and `docker-compose-production.yml` passes on, so the deployed application can name the commit it runs; a build without it shows the version alone
- opening an example in an end to end test waits for the report as long as a busy runner needs to create it, where the ten seconds of the expect timeout let the test of an archive fail the release run of 0.4.0
- the backend has 481 tests, the frontend 300 unit tests and 62 end to end tests, among them a walk over every example and one over every shape of the packages

## 0.4.0

SBML4Humans explains itself now: the report shows what every type, column and attribute means where it is shown, and the documentation site at [matthiaskoenig.github.io/sbml4humans](https://matthiaskoenig.github.io/sbml4humans/) says what SBML is, how to load a model, how to read a report and what every element type carries.

### Documentation
- the documentation site is built with [Zensical](https://zensical.org/) from `docs/` and published to GitHub Pages from `develop`: the home page, [SBML](https://matthiaskoenig.github.io/sbml4humans/sbml/) as the background, [loading a model](https://matthiaskoenig.github.io/sbml4humans/inputs/), [reading a report](https://matthiaskoenig.github.io/sbml4humans/report/), the [reference](https://matthiaskoenig.github.io/sbml4humans/reference/), the [references](https://matthiaskoenig.github.io/sbml4humans/references/) it is written from, and the [development](https://matthiaskoenig.github.io/sbml4humans/development/) of the application
- the reference holds one page per element type and per package: every attribute of the specification with its type, its meaning and the section it comes from, the fields the report computes, the kinds of links between elements and the concepts the report adds
- every claim about SBML cites the Level 3 Version 2 core specification, Keating et al. 2020 or the specification of the comp, fbc or distrib package
- the README states what SBML4Humans is and links the site; the repository layout, the setup, the commands, the checks, the branches and the releases are documented on the site

### Explanations in the report
- every column header of an element table, every attribute row of the inspector, every type mark and every group of links carries a one sentence explanation on hover, and the type in the header of the inspector links its page in the reference
- the explanations come from the glossary in `glossary/*.toml`, the single source of both the tooltips of the application and the reference pages of the site
- the `docs` check of the CI fails when the report has a type or a field the glossary does not explain, when the glossary explains something the report does not have, when a generated file is stale, when a link, an anchor or an image does not resolve, or when a generated page is missing from the navigation, so the documentation cannot drift away from the application

### Fixes
- a term without a definition no longer shows `[]` as its description: the Ontology Lookup Service reports a missing definition as an empty list, and the resolution of an annotation resource now reports every field the report shows as text
- a COMBINE archive example is described by the SBML entries it holds instead of by the `repr` of its manifest
- content which is not SBML is reported with the errors of libsbml alone, without the temporary path the server read it from
- the tables inside the inspector keep an identifier whole instead of breaking it in the middle of a token, the label column fits the longest attribute label, and the type rail fits the longest type name next to its count
- the tooltips are shown in the font of the application, and the type of an element icon and a truncated inspector label can be read in full again

### Development
- `docs` is a required check of `develop`: it validates the glossary against the report and builds the site in strict mode, so a broken link fails the build
- the screenshots of the documentation are taken by `frontend/scripts/screenshots.mjs` (`npm run screenshots`), each at the width the documentation renders it
- the backend has 322 tests, the frontend 210 unit tests and 26 end to end tests
- the deployment of the server moved out of the documentation into `deploy.md` in the repository

## 0.3.0

The report of a model is now a typed data model with a link graph, and the frontend which renders it was rebuilt on Vite and Vue 3.5.

### Breaking changes
- the api returns the typed `ReportResponse`: the manifest of the archive and one report per SBML entry, every element with its primary key `<model id>/<sbml_type>:<id>`, its attributes as typed fields, math as formula, latex and symbols, and the link graph of the document as edges between primary keys. The JSON schema of the response is generated from the pydantic model into `frontend/src/schema/report.schema.json`, clients can generate their types from it
- the frontend is a new application: the Vue CLI 4 project is replaced by a Vite 8 project with Vue 3.5, TypeScript, Pinia and Vue Router 5. Building it needs node 24 (`frontend/.nvmrc`)
- the report of a document is created in sbml4humans itself, the report no longer comes from sbmlutils

### Report page
- the type rail on the left lists the element types of the model with their counts and toggles them, the tables in the middle show one table per type, the inspector below shows the selected element
- the element tables sort by every column, select a row by click or keyboard, and render only the rows in view above 200 rows, so a model with thousands of reactions stays responsive
- the inspector shows the attributes of the element by type, the elements it references and the elements referencing it, its annotations with the resolved labels and descriptions, its notes, its history and its XML
- the search filters every table by id, name, notes and math; the report, the selected element, the search and the type filter live in the url, so a report page can be shared as a link
- units, math and the equation of a reaction are rendered with KaTeX, notes are sanitised before they are shown

### Frontend stack
- PrimeVue and PrimeIcons are gone: from PrimeVue 5 and PrimeIcons 8 on they are commercial, and the element table, the dropdowns and the tooltip are components of the application now. Lucide provides the icons (ISC), Floating UI positions the tooltip (MIT)
- tooltips are visible again: the formula of a math cell shows its source and copies it on click
- the packages are updated to their current releases, `@types/katex`, `tailwindcss-primeui` and `vue-eslint-parser` are removed, TypeScript is 6.0

### Security and privacy
- the notes of a model are restricted to the markup real notes use: no style elements, no form controls, no dialogs, no media elements, no ids; images and inline styles stay, positioned content stays inside the notes box
- a formula longer than 10,000 characters shows as text with a "render formula" action in the inspector, so one model cannot block the browser with a single expression
- the inspector shows the first 50 entries of a list with a "show all", resolves at most 4 annotation resources at a time, at most 100 of an element automatically, and gives up on a request after 15 seconds
- page views report the path of the page without its query, so the url of a loaded model, the search and the selected element are not sent to Google Analytics, and the page sends only its origin as the referrer

  Before deploying this release, switch off the Enhanced measurement options of the Google Analytics data stream which read the full url themselves: page changes based on browser history events, site search, outbound clicks, file downloads and form interactions, and switch off the automatic collection of user provided data.

### Fixes
- the CORS headers are sent with the error responses as well
- the manifest, the charge and fractional dimensions are reported faithfully, the bound variables of a lambda are skipped, and the edges of the link graph are complete
- a species reference, a kinetic law and a local parameter are named by their parent, so nested elements no longer collide

### Development
- `develop` takes every change through a pull request: the rulesets in `.github/rulesets/` require the `test`, `schema`, `frontend`, `e2e`, `ruff` and `ty` checks, forbid force pushes and deletions on `develop` and `main`, and keep tags immutable. `main` tracks the latest release and is fast-forwarded by the release workflow
- the release is prepared on a branch and tagged on `develop` after the merge, see the Releases section of the README
- the backend has 280 tests, the frontend 195 unit tests (Vitest) and 20 end to end tests (Playwright) which run against the real backend, including a walk over every example
- the JSON schema of the report is checked against the committed one in the CI, so the generated frontend types cannot drift

## 0.2.0

The first release of sbml4humans from its own repository. Until sbmlutils 0.10.0 the application lived in the sbmlutils repository, the backend api was `sbmlutils.report.api` with version 0.1.2.

### Breaking changes
- the backend is the `sbml4humans` Python package in `backend/`, installed with `uv sync` from a `pyproject.toml`; `backend/requirements.txt` and the `api:api` module are gone. The server starts with `uvicorn sbml4humans.api:api`
- Python 3.14 is required
- the example list of `/api/examples` no longer exposes the server path of the example files

### Fixes
- the backend did not start against pymetadata >= 0.6.0, which moved `BQB` to `pymetadata.core.miriam`
- uploaded and downloaded files were decoded as text, so COMBINE archives and gzipped SBML could not be reported; the content is handled as bytes and gzipped SBML is decompressed
- invalid content returned an empty report which broke the frontend, it returns an error payload with the libsbml messages now
- the examples were read at import time and the backend crashed without the curated BioModels, which are not part of the sbmlutils distribution; the BioModels are optional and the examples are read once on startup
- the example of a BioModels archive is its master SBML entry (or the first entry by location) instead of the first entry in an order which differed between machines
- CORS no longer combines `allow_origins=["*"]` with credentials, which browsers reject
- the reaction equation of models with a variable (NaN) or negative stoichiometry is created by sbmlutils >= 0.10.1

### Development
- the backend is split into `report.py` (report data), `examples.py` (example metadata), `annotations.py` (annotation resources) and `api.py` (the http layer); failures are reported to the frontend by one exception handler instead of a try/except per route
- 96 tests cover the report creation, the examples and every endpoint (`backend/tests`), run with `uv run pytest`
- ruff with the rule set of sbmlutils and ty for type checking, both clean; they run as GitHub Actions on every push together with the tests
- development runs against the sbmlutils checkout next to the repository (`[tool.uv.sources]` in `backend/pyproject.toml`), which provides the curated BioModels served as examples
- the backend container installs the latest `develop` branch of sbmlutils into `/opt/sbmlutils`, outside of the repository mount of docker compose
- the version lives in `backend/sbml4humans/__init__.py` and is bumped with `bump-my-version`, which tags the release; a tag creates a GitHub release with the notes from `release-notes/`
- dependencies updated to their current releases
