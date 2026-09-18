# Reading a report

A report shows one [model](reference/model.md) of one SBML file at a time. The type rail on the left says what the model is made of, the tables in the middle show the elements of every type, and the inspector at the bottom shows one element in full. The whole model is on the page, the three parts are three views of it.

[![The type rail and the element tables of the repressilator report](images/report-tables.png)](images/report-tables.png)

The rail, the tables and the inspector are separated by draggable dividers, and the position of a divider is kept for the next report.

## The type rail

The rail lists what the file contains, in two groups.

"Document" holds the [document](reference/sbmldocument.md) itself, the model which is currently shown, and the [external model definitions](reference/externalmodeldefinition.md) of a file which uses the comp package. A click selects the element and opens it in the inspector, which is how the level, the version, the packages and the units of a model are read.

"Elements" holds one row per element type: a checkbox, the coloured mark of the type, its name in the plural and the number of elements of that type. The types of a package appear only when the file declares that package, and the types without elements are listed last and greyed out, so the rail is also the answer to what a model does and does not use.

Three things can be done with a row. The name scrolls the tables to the section of that type, as far as there is one: a type whose checkbox is off, whose elements a search filtered away or which the model does not use at all has no section to scroll to. The checkbox hides that section, which is the filter of types, and the state of the checkboxes is part of the url of the report. The count shows the number of elements, and while a search is active it shows the number of matching elements in front of the total.

Hovering the mark of a type shows one sentence explaining what the type is. It is the same sentence the [reference](reference/index.md) page of that type begins with.

## The element tables

Every type with at least one element gets a section: the mark of the type, its name, the number of elements and a table.

The columns of a table are those of the type, and every table starts with the id and the name of its elements:

- a table of [species](reference/species.md) has the [compartment](reference/compartment.md), the initial amount, the initial concentration, the substance units, the flags for only substance units, boundary condition and constant, and the derived units
- a table of [reactions](reference/reaction.md) has the reversible flag, the fast flag, the compartment, the equation, the [kinetic law](reference/kineticlaw.md) and the derived units of that law
- a table of [assignment rules](reference/assignmentrule.md) has the variable, the formula and the derived units of the formula

The [reference](reference/index.md) page of a type explains every attribute the report shows for it, in two tables: the attributes the specification gives the type, and the fields the report computes on top of them. The columns of the table are spread over both tables, and the id and the name, with which every table starts, are explained once for all types on the [SBase](reference/sbase.md) page which every type page links. Hovering a column header shows the same explanation as one sentence.

The values are shown as what they are. A boolean is a mark instead of the words true and false, a reference to another element is a link, a unit is rendered as a formula next to the identifier of the [unit definition](reference/unitdefinition.md) it comes from, and a formula is typeset the way a textbook would print it instead of as the MathML of the file. Three columns are computed by the report rather than read from the file: the [derived units](reference/concepts.md#derived-units) of a quantity or of a formula, the [equation](reference/concepts.md#equation) of a reaction, which is the fastest way to read a list of reactions, and the [rendered units](reference/concepts.md#rendered-units) which fill the units column of the table of unit definitions.

A click on a column header sorts the table by that column, a second click reverses the order. Empty values sort to the end in both directions, and text sorts with numbers in mind, so `x2` comes before `x10`. Two kinds of column cannot be sorted: a column of rendered mathematics, and a column which holds nothing but rendered units, such as the units of a unit definition or the derived units of an element. A units column which names a unit definition, for example the substance units of a species or the units of a [parameter](reference/parameter.md), sorts by that identifier like any other link.

A click on a row opens that element in the inspector, a click on the selected row closes it again. A click on a link inside a row follows the link instead and selects the element the link points at, and a click on a rendered formula copies the formula as text instead of selecting the row. With the keyboard, the arrow keys move from row to row and Enter or Space selects the row.

A table with more than 200 rows shows 15 rows in a scroll area of its own and renders only the rows which are in view. This keeps a reconstruction such as Recon3D, which has tens of thousands of elements, as fast as a small model. Sorting, selecting and searching work the same in such a table.

## Searching

The search box in the bar at the top filters every table at once. It matches the text of an element without regard to case: the id, the name, the meta id, the SBO term, the text of the notes, the formulas of the element and the equation of a reaction.

[![The search box filtering the tables and the rail counts for the text "laci"](images/report-search.png)](images/report-search.png)

While a search is active, every table shows only the matching rows, a type without a match disappears from the tables, and the rail counts the matches per type in front of the totals. `Esc` in the box clears the search. The search text is part of the url of the report.

## The inspector

The inspector opens at the bottom of the page for the selected element and shows everything the report has about it.

[![The inspector of a species, with its attributes, links and annotations columns filled](images/inspector-species.png)](images/inspector-species.png)

Its header carries the mark and the name of the type, the id of the element, its name, and two buttons. The name of the type is a link into the [reference](reference/index.md) of this documentation, which explains the type and all of its attributes. The "XML" button switches the inspector to the XML of the element, and the cross closes it.

Below the header are three columns.

**Attributes** lists what the file states about the element: the meta id, the SBO term as a link to its entry in the Systems Biology Ontology, and then the attributes of its type, for example the compartment, the initial amount and the units of a species, or the reversible flag, the reactants, the products, the modifiers and the kinetic law of a reaction. A list inside an element, such as the [event assignments](reference/eventassignment.md) of an [event](reference/event.md), the flux objectives of an [objective](reference/objective.md) or the [uncertainties](reference/uncertainty.md) of a value, is shown as a small table of its own. Hovering the label of a row shows what the attribute means. A formula which is too long to typeset is shown as its text, shortened. The rows which show the formula of the element itself, among them the math of a rule, the kinetic law of a reaction and the trigger of an event, carry a "render formula" button below the text, which typesets it anyway; in a cell of a table and in the small tables inside the inspector the shortened text is all there is.

**Links** answers where an element is used. "References" lists the elements this element names, "Referenced by" lists the elements which name it, and both are grouped by the kind of the link: the compartment of a species, the reactants of a reaction, the variable of a rule, the units of a parameter, the elements a formula uses, and so on. The [link kinds](reference/links.md) page explains every kind, and hovering the label of a group shows its explanation. Every entry is a link which selects that element, so a model can be walked through along its references. A group with more than 50 entries shows the first 50 and a button for the rest, which matters for a compartment of a genome scale model.

**Annotations** shows the metadata of the element.

![The annotations column of a species, with three of its resources resolved to their names](images/inspector-annotations.png)

The annotations themselves are the controlled vocabulary terms of the element, one block per term, headed by the qualifier of that term, with its resources below it. An element with two terms of the same qualifier therefore shows two blocks under the same heading. Each resource is a link to the entry it identifies, and the report asks its backend what the entry is, so that a resource shows the name of the molecule, of the pathway or of the publication instead of an identifier alone. A term of the Systems Biology Ontology which the element carries is listed here as well. Long lists of terms and of resources are cut off, with one button which shows the rest and one which resolves the rest.

The notes of the element follow, rendered as the XHTML the author wrote, and the history of the SBML encoding last: who created it, with which organization and mail address, when it was created and when it was modified.

The "XML" button in the header replaces the three columns by the SBML of the element as it stands in the file, with a button which copies it. It is there for what a report cannot show better than the file itself: an annotation in a format the report does not read, an element of a package it does not support, or simply the exact text. The button is there for every element, including the document and the model, but for those two the view stays empty and says that their XML is not part of the report, because it would be the whole file.

## Archives and models

The bar at the top says which file and which model the report shows: the entry of the COMBINE archive, the model inside it, the level and the version of SBML and the packages the file declares. A model which was not submitted as an archive is wrapped in one by the backend, under the location `./model.xml`, which is the entry the bar then shows.

![The bar of a COMBINE archive report, with the select of its entries, the model of the entry which is shown, and the level, version and packages of the document](images/archive-entries.png)

An archive with more than one SBML entry offers its entries for selection, named by their location in the archive. The report opens the master entry of the manifest when that entry has a report of its own, and the first entry otherwise; an archive does not have to mark a master entry, and `CompModels`, one of the example archives, marks none. A file which uses the comp package can hold model definitions next to its model; they are offered in the same way, with "(definition)" behind the id of a model definition, and the report opens the model of the document first. A [submodel](reference/submodel.md) is an element of the model which instantiates it, and the model definition it instantiates is one of the models offered here.

Switching the entry or the model closes the inspector, because the selected element belongs to the model it was selected in. The search and the filter of types stay as they are.

## The url of a report

The state of a report is part of its address, so a report can be linked in the state it is in: a selected element, a search, a filter of types, one entry of an archive and one model of a document.

| parameter | meaning |
| --- | --- |
| `pk` | the selected element, given by its [primary key](reference/concepts.md#primary-key), which the report builds for every element because not every element of SBML has an id |
| `q` | the text of the search |
| `types` | the types the rail shows, separated by commas; without the parameter every type is shown |
| `entry` | the location of the SBML entry inside the COMBINE archive |
| `model` | the id of the model or of the model definition |
| `url` | the address the model was downloaded from, for a report which was loaded from a url |

Selecting an element adds a step to the history of the browser, so the back button walks back through the elements you looked at. Typing in the search box does not, so the back button does not step through every keystroke.
