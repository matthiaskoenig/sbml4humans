# SBML

The Systems Biology Markup Language ([SBML](https://sbml.org)) is the format sbml4humans reads. This page is the background a report assumes: what SBML is, how a model is built from its elements, what the Level 3 packages add, and how a model carries its metadata. The [reference](reference/index.md) explains every element type and every attribute a report shows, one page per type; the sources of this page are listed under [References](references.md).

## What SBML is

SBML is a machine readable format for computational models of biological processes. It is written in XML, it belongs to no single program, and it is what lets a model which was built in one tool be simulated, analysed and published with another (Keating et al. 2020, [doi:10.15252/msb.20199110](https://doi.org/10.15252/msb.20199110)). The alternative is a model which exists only in the file format of the program it was written in, or as equations printed in a paper, and neither can be executed by anyone else.

A model in SBML does not have to be written as a system of equations, and usually is not. It is written as biology: entities which are located in containers and are acted upon by processes (Keating et al. 2020). The entities are the [species](reference/species.md), the containers are the [compartments](reference/compartment.md), the processes are the [reactions](reference/reaction.md), and the equations a simulator integrates follow from that description. This is why the same file can be simulated, checked for consistency, drawn as a network and read by a person.

The format is defined by a specification document, not by an implementation. Everything a report of sbml4humans shows is taken from that specification, which is why every reference page names the section it comes from.

## Levels and versions

A level is a major edition of the language and represents a substantial change of its composition and structure; a version is a minor revision within a level which corrects, adjusts and refines its features (Hucka et al. 2019, [doi:10.1515/jib-2019-0021](https://doi.org/10.1515/jib-2019-0021)). The levels stay distinct: all constructs of Level 1 can be mapped to Level 2 and all constructs of Level 2 to Level 3, but a valid Level 1 document is not a valid Level 2 document. A release is a corrected edition of one specification document and changes no syntax and no semantics.

SBML Level 3 Version 2 Core, Release 2 is the current core specification, and Level 3 is the only level which is modular, that is the only level with packages. Every file states the level and the version it is written in as attributes of its [document](reference/sbmldocument.md), because they decide which constructs may appear in the file and how they are read. A report shows them in the context bar as `L3V2` and in the attributes of the document.

Models of Level 1 and Level 2 are still common, for example in the curated models of BioModels. sbml4humans reads a file in the level it is written in and does not convert it, so a report of a Level 2 model shows the elements that model actually has.

## The structure of a model

A [document](reference/sbmldocument.md) contains at most one [model](reference/model.md), and the model contains the lists which everything else lives in. The model is also where the units of the whole model are declared, in particular the unit of time, which exists in no other element.

A [compartment](reference/compartment.md) is a bounded space with a size, for example a cell, the cytosol or the plasma of an organism. A [species](reference/species.md) is a pool of a chemical entity located in exactly one compartment, for example a metabolite, a protein or an ion; its quantity is an amount or a concentration and is what most simulations compute. A [parameter](reference/parameter.md) is a named value the mathematics of the model can use, constant or changing over time.

A [reaction](reference/reaction.md) is a process which changes the quantities of species. Its reactants and products are [species references](reference/speciesreference.md), which name a species and the stoichiometry it enters the reaction with, and its modifiers are [modifier species references](reference/modifierspeciesreference.md), which name a species that influences the reaction without being consumed, such as a catalyst or an inhibitor. How fast the reaction proceeds is given by its [kinetic law](reference/kineticlaw.md), a formula which may use [local parameters](reference/localparameter.md) visible only inside that law. A reaction without a kinetic law is a structural statement, which is what a constraint based model is made of.

Not everything in a model is a reaction. An [initial assignment](reference/initialassignment.md) computes the value of an element at the start of the simulation. An [assignment rule](reference/assignmentrule.md) states a formula which holds for its variable at every moment, a [rate rule](reference/raterule.md) gives the rate of change of its variable, and an [algebraic rule](reference/algebraicrule.md) states an equation which has to hold at every moment without naming the variable it determines. A [constraint](reference/constraint.md) states a condition a valid simulation has to satisfy; it changes nothing, but once it is violated the results from that moment on are no longer valid and the software has to say so.

An [event](reference/event.md) is an instantaneous change of the model when a condition becomes true, for example a dose which is given at a fixed time. What it changes is given by its [event assignments](reference/eventassignment.md), one per element it sets.

Two element types exist for the mathematics itself. A [function definition](reference/functiondefinition.md) is a named function which every formula of the model can call, so that a formula used in many reactions is written once. A [unit definition](reference/unitdefinition.md) is a named unit built from the base units of SBML with an exponent, a scale and a multiplier, for example millimole per litre, and it is what the units attributes of the other elements reference.

Every one of these elements carries the [common attributes](reference/sbase.md) of `SBase`: the identifier other elements reference it by, a readable name, the meta id its annotations point at, a term of the Systems Biology Ontology, the notes for human readers and the annotations for machines.

## Packages

A package of Level 3 adds elements and attributes for a domain which not every model needs. A file declares the packages it uses and whether understanding them is required to interpret the model, so that a tool knows what it is looking at instead of failing on unknown elements. This is what makes Level 3 an extensible format rather than one language which grows with every new need (Keating et al. 2020).

These are the packages with a published specification; further ones, among them arrays, dyn and spatial, exist as drafts.

| package | what it adds |
| --- | --- |
| [comp](reference/comp.md) | hierarchical model composition: a model is built out of other models, which are instantiated as submodels and connected through ports and replacements |
| [fbc](reference/fbc.md) | flux balance constraints: flux bounds, objective functions and gene products, that is what a constraint based model needs beyond the core |
| [distrib](reference/distrib.md) | distributions: the uncertainty of a value and the distribution it was drawn from |
| groups | groups: a set of elements which belong together, for example the reactions of a pathway |
| layout | layout: the positions and the sizes of the elements in a diagram of the model |
| render | rendering: how the elements of a layout are drawn, with colours, strokes and gradients |
| multi | multistate, multicomponent and multicompartment species: species with an internal state and components, and the rules which generate their reactions |
| qual | qualitative models: species with discrete levels and processes which are transitions between them, for example logical models |

Of these packages sbml4humans reads comp, fbc and distrib, which are the three the table links to their reference page. The [submodels](reference/submodel.md) and the [ports](reference/port.md) of comp and the [gene products](reference/geneproduct.md) and the [objectives](reference/objective.md) of fbc become sections of the report like the types of the core. The [external model definitions](reference/externalmodeldefinition.md) of comp belong to the document and are listed with it at the top of the type rail, and an [uncertainty](reference/uncertainty.md) of distrib belongs to the element whose value it describes and is shown in the inspector of that element. The attributes these three packages add to the elements of the core are shown with the other attributes of the element.

The packages a file declares are shown in the context bar of the report, whether the report reads them or not, and the type rail offers the element types of a package only when the file declares it. What another package adds is not lost: it stays in the XML of the element which carries it, which the inspector shows.

## Annotations

A model which is only correct is not yet reusable: a species called `x1` says nothing about which molecule it is. SBML therefore gives every element two places for metadata, and the report shows both.

The notes of an element are XHTML written for human readers, for example the derivation of a rate law or the source of a parameter value. The annotation of an element is RDF written for machines and follows the MIRIAM guidelines for the annotation of biochemical models (Le Novère et al. 2005, [doi:10.1038/nbt1156](https://doi.org/10.1038/nbt1156)).

A MIRIAM style annotation is a set of controlled vocabulary terms, each of which is a qualifier and the resources it relates the element to. The qualifier states the relation and comes from one of two BioModels.net namespaces: a biological qualifier such as `bqbiol:is`, `bqbiol:hasPart` or `bqbiol:isVersionOf` relates the biological entity the element stands for to the resource, a model qualifier such as `bqmodel:is` or `bqmodel:isDerivedFrom` relates the model itself to it. The distinction matters: `bqbiol:is` on a species says the species is that molecule, `bqmodel:is` on a model says the model is that entry in a model database.

A resource is a URI which identifies an entry of a database, usually of the form `https://identifiers.org/<collection>/<identifier>`, for example `https://identifiers.org/uniprot/P12999` or `https://identifiers.org/chebi/CHEBI:17234`. Older files write the same reference as a MIRIAM URN, for example `urn:miriam:kegg.compound:C00046`, which the repressilator example of the application uses; the report links such a URN to the same entry. The registry behind [identifiers.org](https://registry.identifiers.org/) resolves the identifier to the databases which hold the entry. The report asks its backend to do that for the first hundred resources of an element, so that the annotations column shows what an entry is called instead of the identifier alone, and resolves the rest on a click.

Independently of these annotations, every element may carry a term of the [Systems Biology Ontology](https://www.ebi.ac.uk/ols4/ontologies/sbo) in its `sbo` attribute. The ontology names what an element is in the vocabulary of systems biology, for example `SBO:0000247` for a simple chemical or `SBO:0000185` for a transport reaction, which is a statement about the role of the element in the model rather than about the molecule it represents. The report links the term to its entry and also lists it among the annotations of the element.

Besides the qualifiers, the RDF annotation carries the history of the SBML encoding, in elements of its own which stand in front of them: who created it, with which organization and mail address, when it was created and when it was modified. It is the history of the encoding, not of the model the encoding stands for. The report shows it below the notes of an element.

## COMBINE archives

A model is rarely the whole story of a study: there are the simulation descriptions, the data, the figures and the documentation next to it. A [COMBINE archive](https://co.mbine.org/standards/omex) is the standard container for these files. It is a zip file with a manifest which lists every entry with its location and its format, and marks the entries a reader should start with as master entries. Its usual file extension is `.omex`.

sbml4humans creates one report per SBML entry of an archive and offers the entries in the context bar, starting with the master entry. An SBML file which is submitted on its own is wrapped in an archive with a single master entry, so that every report comes with a [manifest](reference/concepts.md#manifest) and an archive and a plain file are read the same way.
