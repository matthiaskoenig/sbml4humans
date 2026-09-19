# Deletion

An element which is removed from a submodel before it is instantiated.

A deletion names one element of the model a [submodel](submodel.md) instantiates and removes it from the composed model. It is how a model uses a part of another model: the initial assignment which the containing model provides itself, the reaction which does not belong in the new context, the parameter which is set from outside.

The removal reaches further than the named element. Everything which depends on it goes with it: a species takes the species references which name it, and with them the reactions which become meaningless, and a compartment takes the species inside it.

A deletion carries an identifier of its own, so that a [replaced element](replacedelement.md) can say that it takes the place of what was deleted, and a name, because deletions are shown to modellers.

The report shows the deletions of a submodel in its inspector, links the element every one of them removes and shows each deletion as an element of its own.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [portRef](#portref) | `PortSIdRef` | - | the port of the submodel whose element is removed | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [idRef](#idref) | `SIdRef` | - | the element which is removed, by its identifier | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [unitRef](#unitref) | `UnitSIdRef` | - | the unit definition which is removed | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [metaIdRef](#metaidref) | `IDREF` | - | the element which is removed, by its meta id | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [sBaseRef](#sbaseref) | [`SBaseRef`](sbaseref.md) | - | the reference which reaches into a submodel of the submodel | [comp 3.7.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="portref"></span>**portRef**

The deletion names a [port](port.md) of the model the submodel instantiates, and the element behind that port is what is removed. Naming the port instead of the element is the friendlier way, because the port is the interface the other model offers.

<span id="idref"></span>**idRef**

The identifier is resolved in the model the submodel instantiates, not in the model which declares the deletion.

<span id="unitref"></span>**unitRef**

Unit identifiers live in a namespace of their own. The units which SBML reserves cannot be deleted.

<span id="metaidref"></span>**metaIdRef**

This is the way to delete an element which carries no identifier, for example a rule or a reaction written without one.

<span id="sbaseref"></span>**sBaseRef**

A deletion which names a submodel of the instantiated model carries a [nested reference](sbaseref.md) which names the element inside it, so that an element of a sub-submodel can be removed.

## Related elements

- [Submodel](submodel.md): the instantiation of another model inside this model
- [ReplacedElement](replacedelement.md): an element of a submodel which the element carrying it takes the place of
- [Port](port.md): an element of the model which other models are meant to connect to
- [Hierarchical Model Composition (comp)](comp.md): the package which builds a model out of other models

## Specification

[SBML Level 3 Package: Hierarchical Model Composition, Version 1 Release 3](https://sbml.org/documents/specifications/level-3/version-1/comp/), Section 3.5.3 (Smith et al. 2015, J Integr Bioinform 12(2):268).
