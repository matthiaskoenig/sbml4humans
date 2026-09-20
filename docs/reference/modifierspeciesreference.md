# ModifierSpeciesReference

The participation of a species in a reaction as a modifier.

A modifier is a species which appears in the rate formula of a reaction but is neither consumed nor produced by it, for example an enzyme or an inhibitor. SBML calls all of them modifiers and leaves the precise role to the term of the Systems Biology Ontology. A modifier has no stoichiometry.

The report shows a modifier species reference with a link to its reaction and to the species.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [species](#species) | [`SIdRef`](datatypes.md#sidref) | required | the species which modifies the reaction | [core 4.11.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="species"></span>**species**

The value is the identifier of a species of the model. Every species which appears in the kinetic law of a reaction has to be declared as a reactant, a product or a modifier of it.

The report links the species in the list of modifiers of the reaction and in the inspector.

- `21111` (error): The value of a &lt;speciesReference&gt; 'species' attribute must be the identifier of an existing &lt;species&gt; in the model.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [reaction](#reaction) | [`Reaction`](reaction.md) | the reaction which lists this modifier |

<span id="reaction"></span>**reaction**

A modifier species reference is written inside the list of modifiers of one reaction. The report shows it as an element of its own, so it names the reaction it belongs to and links it.

The reaction is the first row of the inspector of a modifier species reference.

## Validation rules

- `10708` (warning): The value of the 'sboTerm' attribute on a &lt;speciesReference&gt; or &lt;modifierSpeciesReference&gt; is expected to be an SBO identifier (http://www.biomodels.net/SBO/) referring to a participant role. The appropriate term depends on whether the object is a reactant, product or modifier. If a reactant, then it should be a term in the SBO:0000010, "reactant" hierarchy; if a product, then it should be a term in the SBO:0000011, "product" hierarchy; and if a modifier, then it should be a term in the SBO:0000019, "modifier" hierarchy.
- `21117` (error): A &lt;modifierSpeciesReference&gt; object must have the required attribute 'species' and may have the optional attributes 'metaid', 'sboTerm', 'id' and 'name'. No other attributes from the SBML Level 3 Core namespace are permitted on a &lt;modifierSpeciesReference&gt; object.

## Related elements

- [Reaction](reaction.md): a process which changes the quantities of species
- [Species](species.md): a pool of a chemical entity in a compartment
- [SpeciesReference](speciesreference.md): the participation of a species in a reaction as a reactant or a product

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.11.4 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
