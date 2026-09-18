# Reference

Every element type a report shows, the attributes of the elements and the fields the report adds. The pages are generated from the glossary of the repository, which is also the source of the tooltips of the application.

The [link kinds](links.md) explain how the elements of a report reference each other, the [report concepts](concepts.md) explain what the report computes on top of the model.

## Core

| element | meaning |
| --- | --- |
| [SBase](sbase.md) | the attributes every element of an SBML model carries |
| [Document](sbmldocument.md) | the container of an SBML file, with its level, version and packages |
| [Model](model.md) | the container of everything a model is made of |
| [Function definition](functiondefinition.md) | a named function which the mathematics of the model can call |
| [Unit definition](unitdefinition.md) | a named unit built from the base units of SBML |
| [Compartment](compartment.md) | a bounded space in which species are located |
| [Species](species.md) | a pool of a chemical entity in a compartment |
| [Parameter](parameter.md) | a named value which the mathematics of the model can use |
| [Initial assignment](initialassignment.md) | a formula which computes the value of an element at the start of the simulation |
| [Assignment rule](assignmentrule.md) | a formula which holds at every moment of the simulation |
| [Rate rule](raterule.md) | a formula which gives the rate of change of an element |
| [Algebraic rule](algebraicrule.md) | an equation which has to hold at every moment of the simulation |
| [Constraint](constraint.md) | a condition which a valid simulation of the model has to satisfy |
| [Reaction](reaction.md) | a process which changes the quantities of species |
| [Event](event.md) | an instantaneous change of the model when a condition becomes true |
| [Species reference](speciesreference.md) | the participation of a species in a reaction as a reactant or a product |
| [Modifier species reference](modifierspeciesreference.md) | the participation of a species in a reaction as a modifier |
| [Kinetic law](kineticlaw.md) | the formula which gives the speed of a reaction |
| [Local parameter](localparameter.md) | a named value which only one kinetic law uses |
| [Event assignment](eventassignment.md) | the new value an event gives to one element of the model |

## Hierarchical models (comp)

| element | meaning |
| --- | --- |
| [Hierarchical Model Composition (comp)](comp.md) | the package which builds a model out of other models |
| [External model definition](externalmodeldefinition.md) | a model of another SBML file which this document can instantiate |
| [Submodel](submodel.md) | the instantiation of another model inside this model |
| [Port](port.md) | an element of the model which other models are meant to connect to |

## Flux balance constraints (fbc)

| element | meaning |
| --- | --- |
| [Flux Balance Constraints (fbc)](fbc.md) | the package which describes a constraint based model |
| [Gene product](geneproduct.md) | a gene or one of its products which the reactions of the model depend on |
| [Objective](objective.md) | the function a flux balance analysis maximises or minimises |

## Distributions (distrib)

| element | meaning |
| --- | --- |
| [Distributions (distrib)](distrib.md) | the package which records the uncertainty of a value |
| [Uncertainty](uncertainty.md) | a set of statistical measures of the value of an element |
