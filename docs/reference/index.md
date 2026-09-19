# Reference

Every element type a report shows, the attributes of the elements and the fields the report adds. The pages are generated from the glossary of the repository, which is also the source of the tooltips of the application.

The [link kinds](links.md) explain how the elements of a report reference each other, the [report concepts](concepts.md) explain what the report computes on top of the model.

## Core

| element | meaning |
| --- | --- |
| [SBase](sbase.md) | the attributes every element of an SBML model carries |
| [SBMLDocument](sbmldocument.md) | the container of an SBML file, with its level, version and packages |
| [Model](model.md) | the container of everything a model is made of |
| [FunctionDefinition](functiondefinition.md) | a named function which the mathematics of the model can call |
| [UnitDefinition](unitdefinition.md) | a named unit built from the base units of SBML |
| [Compartment](compartment.md) | a bounded space in which species are located |
| [Species](species.md) | a pool of a chemical entity in a compartment |
| [Parameter](parameter.md) | a named value which the mathematics of the model can use |
| [InitialAssignment](initialassignment.md) | a formula which computes the value of an element at the start of the simulation |
| [AssignmentRule](assignmentrule.md) | a formula which holds at every moment of the simulation |
| [RateRule](raterule.md) | a formula which gives the rate of change of an element |
| [AlgebraicRule](algebraicrule.md) | an equation which has to hold at every moment of the simulation |
| [Constraint](constraint.md) | a condition which a valid simulation of the model has to satisfy |
| [Reaction](reaction.md) | a process which changes the quantities of species |
| [Event](event.md) | an instantaneous change of the model when a condition becomes true |
| [SpeciesReference](speciesreference.md) | the participation of a species in a reaction as a reactant or a product |
| [ModifierSpeciesReference](modifierspeciesreference.md) | the participation of a species in a reaction as a modifier |
| [KineticLaw](kineticlaw.md) | the formula which gives the speed of a reaction |
| [LocalParameter](localparameter.md) | a named value which only one kinetic law uses |
| [Trigger](trigger.md) | the condition of an event, whose change from false to true fires it |
| [Priority](priority.md) | the formula which orders an event against the other events of the same moment |
| [Delay](delay.md) | the formula which gives the time between the trigger of an event and its execution |
| [EventAssignment](eventassignment.md) | the new value an event gives to one element of the model |

## Hierarchical models (comp)

| element | meaning |
| --- | --- |
| [Hierarchical Model Composition (comp)](comp.md) | the package which builds a model out of other models |
| [ExternalModelDefinition](externalmodeldefinition.md) | a model of another SBML file which this document can instantiate |
| [Submodel](submodel.md) | the instantiation of another model inside this model |
| [Port](port.md) | an element of the model which other models are meant to connect to |
| [SBaseRef](sbaseref.md) | a link of a chain which reaches into a submodel of a submodel |
| [Deletion](deletion.md) | an element which is removed from a submodel before it is instantiated |
| [ReplacedElement](replacedelement.md) | an element of a submodel which the element carrying it takes the place of |
| [ReplacedBy](replacedby.md) | the element of a submodel which takes the place of the element carrying it |

## Flux balance constraints (fbc)

| element | meaning |
| --- | --- |
| [Flux Balance Constraints (fbc)](fbc.md) | the package which describes a constraint based model |
| [GeneProduct](geneproduct.md) | a gene or one of its products which the reactions of the model depend on |
| [Objective](objective.md) | the function a flux balance analysis maximises or minimises |
| [FluxObjective](fluxobjective.md) | one term of an objective: a reaction weighted by a coefficient |
| [FluxBound](fluxbound.md) | a constraint on the flux of a reaction, as fbc Version 1 writes it |
| [UserDefinedConstraint](userdefinedconstraint.md) | a constraint over a combination of fluxes and parameters, added in Version 3 |
| [UserDefinedConstraintComponent](userdefinedconstraintcomponent.md) | one weighted variable of a user defined constraint |
| [GeneProductAssociation](geneproductassociation.md) | the genes a reaction needs, as the tree of operators over them |
| [And](and.md) | the associations below it are all needed at once |
| [Or](or.md) | one of the associations below it suffices |
| [GeneProductRef](geneproductref.md) | the leaf of an association: one gene product the reaction depends on |

## Qualitative models (qual)

| element | meaning |
| --- | --- |
| [Qualitative Models (qual)](qual.md) | the package which describes a model whose entities carry a level |
| [QualitativeSpecies](qualitativespecies.md) | an entity of a qualitative model, which carries a level instead of an amount |
| [Transition](transition.md) | what the level of a qualitative species becomes, and under which condition |
| [Input](input.md) | a qualitative species a transition reads, with the sign of its influence |
| [Output](output.md) | a qualitative species a transition changes, with the effect it has on it |
| [FunctionTerm](functionterm.md) | one row of the transition table: a condition and the level it results in |
| [DefaultTerm](defaultterm.md) | the level of a transition in every state no function term covers |

## Distributions (distrib)

| element | meaning |
| --- | --- |
| [Distributions (distrib)](distrib.md) | the package which records the uncertainty of a value |
| [Uncertainty](uncertainty.md) | a set of statistical measures of the value of an element |
| [UncertParameter](uncertparameter.md) | one statistical measure of an uncertainty |
| [UncertSpan](uncertspan.md) | a measure of an uncertainty which is an interval |
