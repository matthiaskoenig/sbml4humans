# Report concepts

A report shows more than the model file contains: it resolves references, derives units, renders the math and names every element. These are the fields the report computes.

## primary key

The identifier the report gives to every element it shows.

SBML identifies an element by its id, which is unique within one model, and many elements of a model have no id at all. The report therefore builds a key of its own for every element, of the form `<scope>/<type>:<id>`: the scope, which is the model the element belongs to or the document for an element of the document, the type of the element and its id. An element without an id falls back to the element it sets, for an [initial assignment](initialassignment.md) or a rule, then to its meta id, and then to a key of what it is about: an element nested in another one is keyed after its parent and what it names, a reactant after its reaction and its species (`Reaction1.reactant.X`), a replacement after its element, its submodel and the element it reaches, a measure of an uncertainty after its type (`u_Km.standardDeviation`), a [list](listof.md) after its owner and its name in the file (`J0.listOfReactants`, and `listOfRules` for a list of the model), and an element which names nothing, an algebraic rule, a constraint, an event or a transition, after its place among the elements of its type (`algebraicRule.0`). Where a list repeats such a key, a species which a reaction lists twice among its reactants, the repetition is told apart by its occurrence (`Reaction1.reactant.X.1`). The model of a document without an id is scoped as `model`, and only an element which the specification requires an id of, and which the file leaves without one, is keyed by a digest of its XML.

The primary key is what the links of a report point at and what the url of a report names when an element is selected. An element without an id is shown by the key alone, without the scope and the type in front of it, in the header of the inspector and as the label of every link to it. An element which the file nests in another one is named after that element and its place in it instead, because a meta id says nothing about where it sits: the kinetic law of `Reaction1` reads `Reaction1.kineticLaw`, the trigger of the event `Start` reads `Start.trigger`, an assignment of that event to `kp` reads `Start.kp`, a reactant `X` of `Reaction1` reads `Reaction1.X` and the list of the reactants of `Reaction1` reads `Reaction1.listOfReactants`.

## sbml type

The kind of element, which decides how the report shows it.

Every element of a report carries the name of its SBML class, for example `Species`, `AssignmentRule` or `Objective`. The report groups the elements of a model by it, and it decides the section of the report, the colour and the icon of the type mark, the columns of the table and the attributes the inspector shows.

The type is shown as the mark in front of every element, as the header of every section of the report and in the header of the inspector.

## derived units

The units of a quantity or of a formula as they follow from the model.

A model does not have to declare units everywhere: a compartment, a species or a parameter inherits the units of the model when it declares none, and the units of a formula follow from the units of the elements it uses. The report derives the units which follow from the model, reduces them to base units with their exponent, scale and multiplier, and renders the result as a formula. A quantity without a dimension reads `dimensionless`, and a dash says that the units are not declared or that the model does not say enough to derive them.

Derived units are shown in the column "derived units" of the tables, right of the size or the value they belong to, and in the inspector. They are the only units of a table, the units an element declares are a row of the inspector. They are the fastest check whether a kinetic law is dimensionally what it should be, because the derived units of a kinetic law are extent per time when the law is right.

## number

How the report shows a number which is infinite or not a number.

A double of SBML may be infinite or not a number, `INF`, `-INF` and `NaN` as a file writes them, and both are ordinary values: the upper bound of an unbounded flux is `INF`, and a `NaN` says that a quantity is defined but its number is not known. JSON has no literal for either of them, so the report sends them as the three constants `"Infinity"`, `"-Infinity"` and `"NaN"`, which keeps them apart from `null`, the attribute a file does not set at all.

The report shows an infinite value as the sign of infinity with the direction of its bound, ∞ and -∞, with the `INF` or `-INF` of the file as its tooltip, and a value which is not a number as `NaN`. An attribute which is not set stays the dash every empty cell of the report shows. Every other number is shown with six significant digits, and the full number is the tooltip of the rounded one.

## equation

The reaction written as a chemical equation.

The report writes every reaction as its reactants, an arrow and its products, with the stoichiometry in front of a species when it is not one, a minus in front of it when the stoichiometry is minus one, and the identifier of the species reference, or a question mark, when the stoichiometry is set by a rule instead of by a number. The arrow is a double arrow when the reaction is reversible and a single arrow when it is not.

The equation is a column of the table of reactions and a row of the inspector of a reaction, and it is what makes a list of reactions readable without opening any of them.

## qualifier

The relation between the element and the resource, from MIRIAM.

An annotation is a statement with three parts: the element, a qualifier and a resource. The qualifier says how the element relates to the resource, so that "is" and "is described by" are not mistaken for each other. The qualifiers are those of the [BioModels.net qualifiers](http://co.mbine.org/standards/qualifiers), which MIRIAM defines in two groups: the biology qualifiers (`BQB_`) relate the biological object an element stands for to the resource, the model qualifiers (`BQM_`) relate the modelling object an element stands for, for example the model itself or a kinetic law, to the resource.

Every card shows the qualifier of its term as its first badge, in front of the collection and the identifier, so that each resource says how it relates to the element. A term with several resources therefore shows the same qualifier on each of their cards.

| qualifier | meaning |
|---|---|
| `BQB_IS` | the biological entity has identity with the resource, for example a reaction and its exact counterpart in a database |
| `BQB_HAS_PART` | the biological entity includes the resource, physically or logically, for example a complex and one of its components |
| `BQB_IS_PART_OF` | the biological entity is a physical or logical part of the resource, for example a component and the complex it is part of |
| `BQB_IS_VERSION_OF` | the biological entity is a more specific version or an instance of the resource, for example a specific process and a generic process of the Gene Ontology |
| `BQB_HAS_VERSION` | the biological entity is a more general version of the resource, for example a generic protein and its species specific version in UniProt |
| `BQB_IS_HOMOLOG_TO` | the biological entity is homologous to the resource, the two share a common ancestor |
| `BQB_IS_DESCRIBED_BY` | the biological entity is described by the resource, for example a species or a parameter and the literature which describes it |
| `BQB_IS_ENCODED_BY` | the biological entity is encoded, directly or transitively, by the resource, for example a protein and its DNA sequence |
| `BQB_ENCODES` | the biological entity encodes, directly or transitively, the resource, for example a DNA sequence and a protein |
| `BQB_OCCURS_IN` | the biological entity is physically limited to a location which is the resource, for example the compartment a reaction takes place in |
| `BQB_HAS_PROPERTY` | the resource is a property of the biological entity, for example an enzymatic activity or a function it exerts |
| `BQB_IS_PROPERTY_OF` | the biological entity is a property of the resource |
| `BQB_HAS_TAXON` | the biological entity is taxonomically restricted to the resource, for example a reaction which only takes place in one species |
| `BQM_IS` | the modelling object is identical with the resource, for example a model and its entry in a database of models |
| `BQM_IS_DESCRIBED_BY` | the modelling object is described by the resource, for example a model or a kinetic law and the literature which describes it |
| `BQM_IS_DERIVED_FROM` | the modelling object is derived from the resource, for example a refinement or an adaptation of a previously described component |
| `BQM_IS_INSTANCE_OF` | the modelling object is an instance of the resource, for example a specific model and its generic form |
| `BQM_HAS_INSTANCE` | the modelling object has the resource as an instance, it is a class of the resource, for example a generic model and its specific forms |

## collection

The database of identifiers.org the resource belongs to.

A resource is named by a url of [identifiers.org](https://identifiers.org), which consists of a collection, the database or the ontology the entry is from, and the identifier of the entry in it. The collection is the part of the url which says where to look, for example `chebi`, `uniprot` or `go`.

The card shows the collection next to the identifier, so that an identifier such as `15377` is not read without knowing which database it belongs to.

## identifier

The identifier of the resource in its collection, linked to its primary provider.

The identifier is the part of the identifiers.org url which names the entry within its collection, for example `CHEBI:15377` in the collection `chebi`. It is unique within the collection, but not across collections.

The card shows the identifier as a link to the primary provider of the collection, the web site which identifiers.org recommends for it. The other web sites which show the entry are listed as the providers of the resource.

## ontology

The ontology of the Ontology Lookup Service which defines the term.

When a resource is a term of an ontology, the report asks the [Ontology Lookup Service](https://www.ebi.ac.uk/ols4) (OLS) of the EMBL-EBI for it. The label of the term, its IRI, its synonyms, its description and its cross references come from OLS, and the card shows them below the identifier. The ontology is the one of OLS which defines the term, for example the Gene Ontology or the Systems Biology Ontology.

The answers of OLS are cached by the report for 30 days, so a term is not asked for again with every report. A resource which is no term of an ontology of OLS shows no ontology.

## synonyms

Other names of the term in its ontology.

An ontology names a term once as its label and may know further names for it, which are the synonyms of the term. They come from the [Ontology Lookup Service](https://www.ebi.ac.uk/ols4) together with the rest of the term.

The card shows the first five synonyms below the label of the term and the rest behind "show all", because a term can have many, a compound of ChEBI often dozens.

## cross references

Entries of other databases which the ontology names for the term.

An ontology often states that a term corresponds to an entry of another database, for example a term of the Gene Ontology to an entry of Reactome or of the Enzyme Commission. These are the cross references of the term, and they come from the [Ontology Lookup Service](https://www.ebi.ac.uk/ols4) together with the rest of the term.

The card lists them below the description of the term and below the information of a ChEBI compound or a UniProt protein, with the database and the identifier of every entry, as a link where the ontology names one.

## providers

The web sites which show the entry of the resource.

A collection of [identifiers.org](https://identifiers.org) is shown by one or more web sites, its providers, and every provider has its own url for an entry. The report lists the providers which identifiers.org knows for the collection, so that an entry can be opened where it is best presented.

The card shows the providers in its last line, as links to the entry. The identifier itself links to the primary provider.

## formula

The molecular formula of the compound in ChEBI.

For a resource of the collection `chebi` the report asks [ChEBI](https://www.ebi.ac.uk/chebi/), the database of chemical entities of biological interest, for the compound. The formula is the molecular formula of the compound as ChEBI states it, for example `H2O`.

The card shows it in the information of the ChEBI compound, above the charge and the mass, next to the structure of the compound.

## charge

The net charge of the compound in ChEBI.

The charge is the net charge of the compound as [ChEBI](https://www.ebi.ac.uk/chebi/) states it, in units of the elementary charge. A charge of 0 means that the compound is neutral; a compound for which ChEBI states no charge shows no charge.

The card shows it in the information of the ChEBI compound, so that the charge of a species can be compared with the charge the model assumes for it.

## mass

The average mass of the compound in ChEBI, in Dalton.

The mass is the average mass of the compound as [ChEBI](https://www.ebi.ac.uk/chebi/) states it, in Dalton, which is numerically equal to the molar mass in grams per mole. It is the average over the natural distribution of the isotopes of the elements of the compound.

The card shows it in the information of the ChEBI compound.

## name

The recommended name of the protein in UniProt.

For a resource of the collection `uniprot` the report asks [UniProt](https://www.uniprot.org/), the database of protein sequences and their annotation, for the protein. The name is the recommended name of the protein as UniProt states it.

The card shows it, followed by the entry name of UniProt, in the first row of the information of the UniProt protein, above the organism and the genes.

## organism

The organism the protein is from.

The organism is the species the protein is from, as [UniProt](https://www.uniprot.org/) states it. The same protein can exist in many organisms with a different entry for each, so the organism tells which of them an annotation means.

The card shows it in the information of the UniProt protein.

## genes

The genes which encode the protein.

The genes are the names of the genes which encode the protein, as [UniProt](https://www.uniprot.org/) states them. A protein can be encoded by more than one gene, and a gene can have several names.

The card shows them in the information of the UniProt protein.

## length

The number of amino acids of the canonical sequence.

The length is the number of amino acids of the canonical sequence of the protein, the sequence which [UniProt](https://www.uniprot.org/) displays for the entry. Isoforms of the protein can be shorter or longer.

The card shows it in the information of the UniProt protein.

## function

What the protein does, as UniProt describes it.

The function is the text with which [UniProt](https://www.uniprot.org/) describes what the protein does, for example the reaction an enzyme catalyses or the process it takes part in. It is written by the curators of UniProt from the literature, and it can be long.

The card shows it in the information of the UniProt protein, below the other values.

## rendered math

The formula of an element as the report renders it.

SBML stores a formula as content MathML, which is precise and unreadable. The report turns it into the typeset formula a textbook would print, with fractions, powers, subscripts for the parts of a name and greek letters where a name is one, and keeps the same expression as an infix formula next to it, so that it can be read and copied as text.

The rendered formula is the column "math" of the tables of rules, function definitions, constraints and events, the kinetic law of a reaction, and the mathematics shown in the inspector. Where a formula names an element of the model, the report also links that element as a link of the kind "math".

## rendered units

The units an element declares, rendered as a formula.

A units attribute names a unit definition, and a unit definition is a list of base units with an exponent, a scale and a multiplier. The report resolves the reference and renders the product as a formula, so that the inspector shows millimole over litre as a fraction next to the identifier `mmol_per_l` it comes from.

The rendered units appear in the units of the inspector and in the units column of the table of unit definitions, whose inspector shows them as the formula above the units the definition is built from.

## model kind

Whether a model is the model of the document or a model definition.

A document contains at most one model, but the comp package adds model definitions, which exist to be instantiated by a submodel and are not simulated themselves. The report reads both and marks every model as `model` or `modelDefinition`.

The kind is shown in the attributes of a model. The report opens the model of the document first and lets the model definitions be selected next to it.

## manifest

The entries of the COMBINE archive a report was built from.

A COMBINE archive holds the files of a modelling study with a manifest which names every entry, its format and whether it is a master file. The report is built for every SBML entry of the archive, and a plain SBML file which is submitted on its own is wrapped in an archive with one master entry, so that a report always comes with a manifest.

The manifest decides which report is shown first: the master entry when that entry has a report, and the first entry otherwise, because an archive does not have to mark one. It is also what the report offers when an archive holds more than one model.

## link into another document

A link which ends at an element of another entry of the archive.

The links of a report stay inside one SBML document, with one exception: a model of the comp package may instantiate a model of another document through an [external model definition](externalmodeldefinition.md), and its [replacements](replacedelement.md), [deletions](deletion.md) and [ports](port.md) then name elements of that document. Where the other document is part of the report, as another entry of the same COMBINE archive, the link ends at the element inside it.

Such a link shows the file name of the other entry next to the element, and following it opens the report of that entry. The element lists the link under "Referenced by" with the file name of the entry it comes from.

## validation

The errors and warnings libsbml finds in the document.

sbml4humans runs the consistency checks of [libsbml](https://sbml.org/software/libsbml/) on every document with the categories libsbml checks by default: the identifiers, the general rules of the specification and of its packages, the SBO terms, the math, the units, whether the model is overdetermined and the modelling practice. The errors libsbml finds while it reads the file are part of it too.

libsbml checks in stages and stops after the first stage which finds an error, so a document with an error of its identifiers shows none of its unit warnings until that error is fixed.

libsbml reports where in the file an issue is, not which element it concerns, so the report gives an issue to the element which starts closest before that position, and to the document when none does. For a document of the comp package libsbml instantiates the submodels to check them and says itself that its line numbers are unreliable: the element of such an issue can be the wrong one.

The external model definitions are checked against the documents which are part of the report; the validation reads no other file and fetches no url.

The validation runs apart from the report, in a process of its own on the server: the report appears first, and the errors and warnings appear when the validation is done, while a chip "validating" stands in the place of the counts. A validation which failed says so in that place, with the message of the failure, and a click on it opens the inspector of the document, which shows the failure with its details.

To check a model of the comp package libsbml instantiates every submodel of its main model, the submodels of those in turn, along the [model](model.md) definitions and the [external model definitions](externalmodeldefinition.md), so the work grows with the product of the submodels of every level. A document with submodels which expands to more than 10,000 elements, its own and those of every instance, is not validated, and only the errors libsbml finds while it reads the file are listed; a document without submodels is never skipped for its size.

A validation may take 60 seconds and its process may reserve 2 GiB of memory; one which runs out of either is stopped, and close to the memory limit libsbml may report fewer issues than the document has. The server runs a few validations at a time, and one it has no room for is not run: reloading the report later tries again. A document which was not validated says so and why in the place of the counts and in the inspector of the document. These limits keep the server responsive, they do not make a validation complete.

## rule

The number of the validation rule of libsbml.

Every issue names the rule it breaks by its number in libsbml. A rule of SBML core has a number below 99000 and is one of the validation rules of the appendix of the specification, a number from 99000 to 99999 is a check of libsbml of its own, and a rule of a package carries the offset of the package, such as 1000000 and above for the comp package. Where the glossary cites a rule, its text is part of the explanation of the element in the help.

## severity

Whether an issue is an error, a warning or a note.

- `error`: the document breaks a rule the specification requires; a tool may refuse or misread it.
- `warning`: the document follows the rules, but something is likely not what was meant, such as a quantity without units.
- `info`: a note of libsbml, which usually needs no change.

## category

Which check of libsbml found the issue.

libsbml groups its checks in categories, such as the unit consistency, the identifier consistency or the consistency of a package. The list of all issues can be filtered by them.

## tables

The elements of the model in one table per type.

The report shows the elements of a model in one table per type, the compartments, the species, the reactions and every other type the model uses, in the order of the specification. The type bar above them filters the tables by type, the search filters their rows, and a click on a row opens the element in the inspector. The tables are one of the two views of a model, next to the [equations](#equations).

## equations

The model as its system of ordinary differential equations.

A model in SBML describes a system of ordinary differential equations, but it is not written as one: the equations follow from the reactions, the rules, the events and the units of the model. The view "equations" shows this system as it would be printed in a paper, from the definitions to the system: the [function definitions](#function-definitions), the [assignment rules](#assignment-rules), the [reaction rates](#reaction-rates), the [ODE system](#ode-system) of the states, the [initial assignments](#initial-assignments) and the [events](#events).

Every symbol of an equation stands for an element of the model: a click on it opens the element in the inspector, and the inspector of a species, a reaction, a parameter or a compartment shows the equation of the element with a link to it in the view. The symbols are written from the identifiers, a subscript after an underscore and a greek letter where an identifier is one, `tau_mRNA` as τ with the subscript mRNA; the rate of a reaction is `v` with the identifier of the reaction as subscript.

The system is the one of the model of the document; a model with submodels is flattened first, and a symbol which the flattening makes up, the identifier of a submodel joined to the identifier of its element, links to no element. The equations are written by [sbmlode](https://matthiaskoenig.github.io/sbmlode/), which also writes the system as python, julia and R code and as LaTeX, typst and markdown documents: the tabs of the view show the [code](#code) of each format next to the math.

## ODE system

The rate of change of every state of the model.

A state is a quantity of the model which changes in time and is not given by an assignment rule: a species which takes part in reactions and is no boundary condition, or a species, a compartment, a parameter or a species reference with a rate rule. Its derivative in time is either written by its rate rule, or is the sum of the rates of the reactions it takes part in, each times its stoichiometry, negative as a reactant and positive as a product.

Every species is a state in the quantity the model declares, its amount if it has only substance units, else its concentration. A reaction changes the amount of a species, so the rate of change of a species in concentration is divided by the size of its compartment. If the size changes as well, the concentration changes with it while the amount stays: the derivative is the one of SBML Level 3 Version 2, section 3.4.6, `d[S]/dt = (1/V) dS/dt - ([S]/V) dV/dt`, the rates of the reactions divided by the size minus the dilution by the rate of the size. A boundary, constant or not reacting species in such a compartment keeps its amount and is diluted alone. A conversion factor of the species, else of the model, multiplies the rates of its reactions.

## reaction rates

The kinetic law of every reaction, the rate the ODE system is written with.

The rate of a reaction is its kinetic law, a rate of change of the extent of the reaction, in the units of extent per time. The [ODE system](#ode-system) is written with the rates, `v` with the identifier of the reaction as subscript, so that it stays as short as the network of the model. A local parameter of a kinetic law is written with the identifier of its reaction in front of its own, which keeps it apart from a parameter of the model of the same identifier. A reaction without a kinetic law has the rate zero.

## assignment rules

The quantities which are given by a formula at every time.

An assignment rule gives a quantity by a formula at every time, which is evaluated before the derivatives: the rate of a reaction or the derivative of a state may use it. The rules are listed in the order of their dependencies, a rule after the rules it uses. The size of a compartment with an assignment rule which changes in time has its rate of change as an assignment of its own, the derivative of the rule in time with the rates of the states it depends on, which dilutes the species in concentration in the compartment; the rate of a size with a rate rule is the rate rule itself.

## function definitions

The functions the math of the model calls.

A function definition names a formula of its arguments, which every other math of the model can call like a function of the math itself. Its arguments are its own symbols, they stand for no element of the model.

## initial assignments

The values at the start which are given by a formula.

The value of a quantity at the start, at time zero, is its value in the file, unless an initial assignment gives it by a formula or an assignment rule gives it at every time. The list holds the initial assignments and the initial values which convert between amount and concentration, the initial amount of a species in concentration divided by the size of its compartment and the reverse; a value which is a number stands in the tables.

## events

The changes of the model at the moment a condition becomes true.

An event changes the values of the model at the moment its trigger becomes true, after its delay if it has one; events at the same moment are carried out by their priority. An event which changes the size of a compartment, directly or through a parameter of the assignment rule of the size, keeps the amounts of the species in it, so that their concentrations are converted from the size before the event to the size after it.

## unsupported constructs

The parts of the model which the ODE system does not hold.

An algebraic rule makes the system a system of differential algebraic equations, a `delay` function makes it a system of delay differential equations, and a fast reaction is in equilibrium at every time. None of them is part of an ODE system, so the equations are shown without them and say which elements they leave out: the system they show is not the whole model. The size of a compartment whose assignment rule has no derivative, for example a rule with `rem`, has no rate of change, which the dilution of its species needs.

## code

The equations as code or as a document, to copy or download.

The tabs of the view show the equations in the formats of [sbmlode](https://matthiaskoenig.github.io/sbmlode/), to copy or to download: as python (numpy), julia or R code, the ODE system as functions of the time, the states and the constants (the initial values, the rates of change and the assigned values), and as a LaTeX, typst or markdown document with the units, the tables and the equations of the model. A model with an unsupported construct is written as a document, but not as code.

The code holds the system alone. sbmlode writes more: code which integrates the model with scipy, OrdinaryDiffEq or deSolve and is verified against libroadrunner over the SBML test suite, documents with the names of the elements as symbols, and formats of templates of one's own. These custom exports are made with sbmlode itself, see its [formats](https://matthiaskoenig.github.io/sbmlode/formats/).
