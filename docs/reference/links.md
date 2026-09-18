# Link kinds

An element of a report references other elements, and is referenced by others. The inspector groups both directions by kind under "References" and "Referenced by", the tables link the referenced element directly.

## compartment

The compartment a species is located in or a reaction takes place in.

Every [species](species.md) names the compartment it is located in, and a [reaction](reaction.md) may name the compartment it takes place in.

The link is shown under "References" of the species or of the reaction, and under "Referenced by" of the compartment, which is where every species of a compartment can be seen at once.

## reactant

A species a reaction consumes.

The link is two links of one kind: from the [reaction](reaction.md) to every [species reference](speciesreference.md) of its list of reactants, and from each of those to the [species](species.md) it names. Every link starts at the element which carries the reference, so a species reference is part of the graph instead of standing alone.

It is shown under "References" of the reaction, where it lists what the reaction consumes, and under "Referenced by" of the species, where it answers which reactions consume it.

## product

A species a reaction produces.

The link is two links of one kind: from the [reaction](reaction.md) to every [species reference](speciesreference.md) of its list of products, and from each of those to the [species](species.md) it names.

It is shown under "References" of the reaction and under "Referenced by" of the species, where it answers which reactions produce it.

## modifier

A species which influences a reaction without being consumed.

The link is two links of one kind: from the [reaction](reaction.md) to every [modifier species reference](modifierspeciesreference.md) of its list of modifiers, and from each of those to the [species](species.md) it names: a catalyst, an inhibitor or an activator.

It is shown under "References" of the reaction and under "Referenced by" of the species. A species which is a modifier of a reaction usually also appears in the math of its kinetic law, which is a link of the kind "math".

## kinetic law

The formula which gives the speed of a reaction.

A [reaction](reaction.md) holds the formula of its speed in a [kinetic law](kineticlaw.md) of its own, and the link runs from the reaction to it. The elements the formula reads are linked from the kinetic law with [math](links.md#math) links, and its local parameters are among them.

It is shown under "References" of the reaction and under "Referenced by" of the kinetic law. A reaction has one kinetic law at most, and its formula is the speed of the reaction, so the other links look across it: the reaction lists what its formula reads under "math", and a species or a parameter the formula reads lists the reaction there, not the kinetic law. The kinetic law keeps its own links.

## trigger

The condition an event fires on.

An [event](event.md) holds its condition in a [trigger](trigger.md) of its own, and the link runs from the event to it. The elements the condition reads are linked from the trigger, not from the event, so a reader sees which of the formulas of an event uses a species or a parameter.

It is shown under "References" of the event and under "Referenced by" of the trigger.

## priority

The formula which orders an event against the events of the same moment.

An [event](event.md) may hold a [priority](priority.md) of its own, and the link runs from the event to it.

It is shown under "References" of the event and under "Referenced by" of the priority.

## delay

The formula which postpones the execution of an event.

An [event](event.md) may hold a [delay](delay.md) of its own, and the link runs from the event to it.

It is shown under "References" of the event and under "Referenced by" of the delay.

## event assignment

A new value an event gives to an element of the model.

An [event](event.md) names every [event assignment](eventassignment.md) of its list, and each assignment names the element it sets with a [variable](links.md#variable) link and the elements its formula reads with [math](links.md#math) links. An assignment carries no identifier in most models, so this link is what says which event it belongs to.

It is shown under "References" of the event and under "Referenced by" of the assignment.

## variable

The element a rule, an event assignment or a constraint component is about.

An [assignment rule](assignmentrule.md), a [rate rule](raterule.md) and an [event assignment](eventassignment.md) name the element they set in their variable: a compartment, a species, a parameter or the stoichiometry of a species reference. A [component](userdefinedconstraintcomponent.md) of a user defined constraint of fbc names the reaction or the parameter it weighs with the same attribute, which it does not set but reads.

The link is shown under "References" of the rule or of the assignment, and under "Referenced by" of the element, where it shows what determines its value.

## symbol

The element whose initial value an initial assignment computes.

An [initial assignment](initialassignment.md) names the element it computes in its symbol. It is the same relation as the variable of a rule, at the start of the simulation instead of during it, and the specification gives it a name of its own.

The link is shown under "References" of the initial assignment and under "Referenced by" of the element.

## units

The unit definition an element declares its units with.

A [model](model.md), a [compartment](compartment.md), a [species](species.md), a [parameter](parameter.md) and a [local parameter](localparameter.md) may name a [unit definition](unitdefinition.md) of the model in one of their units attributes. A units attribute which names a base unit of SBML instead of a unit definition produces no link, because there is no element to link to.

The link is shown under "References" of the element and under "Referenced by" of the unit definition, where it shows which elements are measured in it.

## conversion factor

The parameter which converts the values of an element.

A [model](model.md) and a [species](species.md) name a conversion factor parameter for the amounts of species, and a [submodel](submodel.md) names one for its time and one for its reaction extent. In every case the link goes to a constant [parameter](parameter.md) of the model.

It is shown under "References" of the element and under "Referenced by" of the parameter.

## flux bound

What bounds the flux of a reaction.

A [reaction](reaction.md) of a model which uses fbc Version 2 or later names the [parameter](parameter.md) of its lower and of its upper flux bound. Both links are of this kind, which parameter is which bound is shown in the attributes of the reaction.

In a document of Version 1 the link runs the other way: a [flux bound](fluxbound.md) is an object of its own there and names the reaction it constrains, so the kind is the same relation seen from the other end.

The link is shown under "References" of the reaction or of the flux bound, and under "Referenced by" of the parameter or of the reaction, where it shows what bounds a flux.

## gene product

The gene product a reference of an association names.

The link goes from a [gene product reference](geneproductref.md), the leaf of the gene product association of a reaction, to the [gene product](geneproduct.md) it names. It starts at the reference and not at the [reaction](reaction.md) because that is where the file writes the identifier, and because a reaction may name one gene in several branches of its association.

It is shown under "References" of the reference and under "Referenced by" of the gene product; the reaction of a gene is one hop further, over the gene product association.

## gene product association

A node of the gene association of a reaction, from the reaction down to its genes.

A [reaction](reaction.md) names the [gene product association](geneproductassociation.md) it carries, the association names the node at the root of its tree, and every [and](and.md) and [or](or.md) names the nodes below it, all of them with this kind. The tree ends at the [gene product references](geneproductref.md), which name the genes.

The chain is what makes the structure of the association walkable: it says which genes belong to the same complex and which of them are alternatives, which the flat list of the genes of a reaction cannot.

It is shown under "References" of the reaction and of every node, and under "Referenced by" of the node below.

## associated species

The species a gene product stands for.

A [gene product](geneproduct.md) may name the [species](species.md) which represents it in the reaction network, which is how some reconstructions encode gene products.

The link is shown under "References" of the gene product and under "Referenced by" of the species.

## flux objective

A term of an objective function and the reaction whose flux it weighs.

An [objective](objective.md) names every [flux objective](fluxobjective.md) it is the sum of, and each of those names the [reaction](reaction.md) whose flux it weighs, or from Version 3 of fbc on the two reactions of a quadratic term. Both hops carry this kind, the way a reaction and its species reference both carry the kind of the participation.

The coefficient is an attribute of the flux objective, not of the link. The chain is shown under "References" of the objective and of the flux objective, and under "Referenced by" of the reaction, where it says that this reaction is what the model optimises.

## active objective

The objective a model declares as the one which is optimised.

A [model](model.md) which defines several [objectives](objective.md) names the one an analysis optimises unless it is told otherwise. It is the only link which starts at the model itself, because the attribute belongs to the list of the objectives, which the report shows as the section of that type.

It is shown under "References" of the model and under "Referenced by" of the objective, where it says that this objective is the one the model was published with.

## constraint component

A term of a user defined constraint.

A [user defined constraint](userdefinedconstraint.md) names every [component](userdefinedconstraintcomponent.md) it is the sum of, the way a reaction names its species references, and each component names the variable it weighs and the parameter of its coefficient with links of their own.

It is shown under "References" of the constraint and under "Referenced by" of the component.

## coefficient

The parameter which holds the weight of a term.

A [component](userdefinedconstraintcomponent.md) of a user defined constraint does not write its weight into the file: it names the [parameter](parameter.md) which holds it, so that the weights of a model are changed in one place.

It is shown under "References" of the component and under "Referenced by" of the parameter, where it says which constraints a number belongs to.

## input

A qualitative species a transition reads.

A [transition](transition.md) names every [input](input.md) it lists and each input names the [qualitative species](qualitativespecies.md) whose level it reads, the way a reaction names its species references. The [sign](input.md#sign) of the input says whether that species activates or inhibits, so the inputs and the [outputs](links.md#output) of a model together are its influence graph.

It is shown under "References" of the transition and of the input and under "Referenced by" of the qualitative species, where it says which transitions read it.

## output

A qualitative species a transition changes.

A [transition](transition.md) names every [output](output.md) it lists and each output names the [qualitative species](qualitativespecies.md) whose level it changes.

It is shown under "References" of the transition and of the output and under "Referenced by" of the qualitative species, where it says which transitions decide its level.

## function term

A row of the transition table of a transition.

A [transition](transition.md) names every [function term](functionterm.md) of its list, in the order in which they are read, and the math of a term reaches the qualitative species, the inputs and the outputs it names with [math](links.md#math) links of its own.

It is shown under "References" of the transition and under "Referenced by" of the term. The terms are the rows of the table of their transition, so the other links look across them, the way they look across the kinetic law of a reaction: the transition lists what its conditions read under "math", and a qualitative species a condition reads lists the transition there. A term keeps its own links.

## default term

The term of a transition which holds where no other one does.

A [transition](transition.md) has exactly one [default term](defaultterm.md), which gives the level of every state its function terms do not cover. It is a link of its own and not a function term link, because the term carries no condition and is the last row of the transition table whatever the order of the others.

It is shown under "References" of the transition and under "Referenced by" of the term.

## uncert parameter

A measure of an uncertainty.

An [uncertainty](uncertainty.md) names every [uncert parameter](uncertparameter.md) it lists, and a parameter of the type `distribution` or `externalParameter` names the parameters which define it in turn, so the link carries the whole tree of a distribution.

It is shown under "References" of the uncertainty and of a parameter with parameters of its own, and under "Referenced by" of the measure, which is how a reader gets from a measure back to the set it belongs to.

## var

The element which holds the number of a measure.

A measure of an [uncertainty](uncertainty.md) which is not a fixed number names the element of the model which holds it: the [var](uncertparameter.md#var) of an [uncert parameter](uncertparameter.md), and the [var lower](uncertspan.md#var-lower) and the [var upper](uncertspan.md#var-upper) of an [uncert span](uncertspan.md), which are the two ends of its interval.

It is shown under "References" of the measure and under "Referenced by" of the element it names, where it says which measurement that element stands for.

## model reference

The model a submodel instantiates.

A [submodel](submodel.md) names the model it instantiates, which is either a [model](model.md) definition of the document or an [external model definition](externalmodeldefinition.md). The reference is resolved against the models of the document, not within one model, because model identifiers live in a namespace of the document.

The link is shown under "References" of the submodel and under "Referenced by" of the model, where it shows who uses it.

## port

The element a port names.

A [port](port.md) names exactly one element of its model, by its identifier, by the identifier of a unit definition or by its meta id. All three produce a link of this kind; a port which names a port of a submodel instead is not resolved, because the element lies inside another model.

The link is shown under "References" of the port and under "Referenced by" of the element, where it says that the element is part of the interface of the model.

## deletion

An element which a submodel removes, and the deletion which removes it.

A [submodel](submodel.md) names every [deletion](deletion.md) it carries, and each deletion names the element of the instantiated model which it removes, so the link leads from the submodel over the deletion to the element which the composed model does not contain. The same kind leads from a [replaced element](replacedelement.md) to the deletion it stands for, which is how a model records that an element of its own takes the place of something a submodel lost.

Where the model of the submodel is an external one, which the report does not read, the deletion has no element to name and the link ends at the deletion.

The link is shown under "References" of the submodel and of the deletion, and under "Referenced by" of the element which is removed.

## replaced by

The element of a submodel which replaces this one.

An element which is replaced names the [replacement](replacedby.md) it carries, and the replacement names the element of the [submodel](submodel.md) which takes the place of the element, so the link leads from the replaced element over the replacement to the element which stays in the composed model.

Where the reference cannot be resolved, because the model of the submodel is an external one which the report does not read or because the named element is not part of it, the link ends at the submodel, which is as far as the report can follow it.

The link is shown under "References" of the replaced element and of the replacement, and under "Referenced by" of the element which replaces it.

## replaced element

The element of a submodel which this one replaces.

An element may replace elements of submodels. It names every [replacement](replacedelement.md) it carries, and each replacement names the [submodel](submodel.md) it reaches into and the element inside it which disappears from the composed model. It is the opposite direction of "replaced by" and the usual way a composed model connects its parts.

Where the reference cannot be resolved, because the model of the submodel is an external one which the report does not read or because the named element is not part of it, the link ends at the submodel.

The link is shown under "References" of the replacing element and of the replacement, and under "Referenced by" of the element which is replaced.

## math

An element a formula refers to.

Every formula of a model refers to elements by their identifier: the species and the parameters of a kinetic law, the elements a rule or a trigger reads, the function definition a formula calls. The report collects these symbols of every formula and links each of them to the element it names, resolving the local parameters of a kinetic law before the elements of the model. The arguments of a function definition are local to it and are no references, and a symbol which names nothing, such as the symbol of time, produces no link.

The link is shown under "References" of the element which carries the formula and under "Referenced by" of the element the formula uses, where it answers in which equations a species or a parameter occurs. The formula of a [kinetic law](links.md#kinetic-law) is the speed of its reaction and the condition of a [function term](links.md#function-term) a row of the table of its transition, so their links are shown as those of the reaction and of the transition, and the kinetic law and the term keep their own.
