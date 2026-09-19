# QualitativeSpecies

An entity of a qualitative model, which carries a level instead of an amount.

A qualitative species is what a [species](species.md) is to a kinetic model: the thing the model is about. Its state is not a concentration but a level, a whole number between zero and its [maximum level](qualitativespecies.md#maxlevel), which stands for a range of activity, for example "the gene is off" and "the gene is on".

It is the node of the influence graph of a logical model and the place of a Petri net. Which of the two a file writes is read from the [transitions](transition.md) which change it.

The report shows the qualitative species of a model in a section of their own, with their levels, and links every transition which reads or changes one in its inspector.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [compartment](#compartment) | [`SIdRef`](datatypes.md#sidref) | required | the compartment the qualitative species is located in | [qual 3.5](https://sbml.org/documents/specifications/level-3/version-1/qual/) |
| [constant](#constant) | [`boolean`](datatypes.md#boolean) | required | whether no transition may change the level of the species | [qual 3.5](https://sbml.org/documents/specifications/level-3/version-1/qual/) |
| [initialLevel](#initiallevel) | [`integer`](datatypes.md#integer) | optional | the level of the species at the start of a simulation | [qual 3.5](https://sbml.org/documents/specifications/level-3/version-1/qual/) |
| [maxLevel](#maxlevel) | [`integer`](datatypes.md#integer) | optional | the highest level the species can take | [qual 3.5](https://sbml.org/documents/specifications/level-3/version-1/qual/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="compartment"></span>**compartment**

The attribute is required and names a [compartment](compartment.md) of the model, the same way a [species](species.md) names one. The compartment of a qualitative model carries no size which enters a formula; it says where in the cell the entity is, which is what tells two copies of one protein in two compartments apart.

The report links the compartment in the column "compartment" and in the inspector.

- `3020308` (error): The value of the attribute 'qual:compartment' in a &lt;qualitativeSpecies&gt; object must be the identifier of an existing &lt;compartment&gt; object defined in the enclosing &lt;model&gt; object.

<span id="constant"></span>**constant**

A constant qualitative species is an input of the system: transitions read it and none of them is allowed to change it, so its level is a condition of the experiment and not a result of the model. The attribute is required.

The report shows the flag as a mark in the column "constant" and in the inspector.

- `3020304` (error): The attribute 'qual:constant' in &lt;qualitativeSpecies&gt; must be of the data type Boolean.
- `3020310` (error): A &lt;qualitativeSpecies&gt; with attribute 'qual:constant' set to 'true' can only be referred to by an &lt;input&gt;. It cannot be the subject of an &lt;output&gt; in a &lt;transition&gt;.
- `3020509` (error): An &lt;input&gt; that refers to a &lt;qualitativeSpecies&gt; that has a 'qual:constant' attribute set to 'true' cannot have the attribute 'qual:transitionEffect' set to 'consumption'.
- `3020608` (error): The &lt;qualitativeSpecies&gt; referred to by the attribute 'qual:qualitativeSpecies' in an &lt;output&gt; object must have the value of its 'qual:constant' attribute set to 'false'.

<span id="initiallevel"></span>**initialLevel**

The initial level is the state the entity starts in, a whole number which cannot be negative and cannot exceed the maximum level. It is optional: a model which is analysed over all of its states, which is what an attractor analysis of a logical model does, gives no starting state.

The report shows the level in the column "initial level" and in the inspector, and an unset level as a dash.

Default: the level the entity starts at is not fixed by the model.

- `3020306` (error): The attribute 'qual:initialLevel' in &lt;qualitativeSpecies&gt; must be of the data type integer.
- `3020309` (error): The value of the attribute 'qual:initialLevel' in a &lt;qualitativeSpecies&gt; object cannot be greater than the value of the 'qual:maxLevel' attribute for the given &lt;qualitativeSpecies&gt; object.
- `3020312` (error): The attribute 'qual:initialLevel' in &lt;qualitativeSpecies&gt; must not be negative.

<span id="maxlevel"></span>**maxLevel**

The maximum level decides how the whole model is read: with the value one the entity is Boolean, off or on, and every condition over it is a logical one; with a higher value it is multi valued and its levels stand for the thresholds at which it acts differently on the things it regulates.

It is optional, because the levels a species actually takes can be derived from the [result levels](functionterm.md#resultlevel) of the transitions which change it.

The report shows the level in the column "max level" and in the inspector.

Default: the levels the species takes follow from the result levels of the transitions alone.

- `3020307` (error): The attribute 'qual:maxLevel' in &lt;qualitativeSpecies&gt; must be of the data type integer.
- `3020309` (error): The value of the attribute 'qual:initialLevel' in a &lt;qualitativeSpecies&gt; object cannot be greater than the value of the 'qual:maxLevel' attribute for the given &lt;qualitativeSpecies&gt; object.
- `3020313` (error): The attribute 'qual:maxLevel' in &lt;qualitativeSpecies&gt; must not be negative.
- `3020413` (error): No element of the &lt;listOfFunctionTerms&gt; object may cause the level of a &lt;qualitativeSpecies&gt; to exceed the value 'qual:maxLevel' attribute.

## Validation rules

- `3010301` (error): (Extends validation rule #10301 in the SBML Level 3 Version 1 Core specification.) Within a &lt;model&gt; the values of the attributes 'id' and 'qual:id' on every instance of the following classes of objects must be unique across the set of all 'id' and 'qual:id' attribute values of all such objects in a model: the &lt;model&gt; itself, plus all contained &lt;functionDefinition&gt;, &lt;compartment&gt;, &lt;species&gt;, &lt;reaction&gt;, &lt;speciesReference&gt;, &lt;modifierSpeciesReference&gt;, &lt;event&gt;, and &lt;parameter&gt; objects, plus the &lt;qualitativeSpecies&gt;, &lt;transition&gt;, &lt;input&gt; and &lt;output&gt; objects defined by the Qualitative Models package.
- `3020301` (error): A &lt;qualitativeSpecies&gt; object may have the optional 'metaid' and 'sboTerm' defined by SBML Level 3 Core. No other attributes from the SBML Level 3 Core namespace or the Qualitative Models namespace are permitted on a &lt;qualitativeSpecies&gt; object.
- `3020302` (error): A &lt;qualitativeSpecies&gt; object may have the optional SBML Level 3 Core subobjects for notes and annotations. No other elements from the SBML Level 3 Core namespaces are permitted on a &lt;qualitativeSpecies&gt;.
- `3020303` (error): A &lt;qualitativeSpecies&gt; object must have the required attributes 'qual:id', 'qual:compartment' and 'qual:constant', and may have the optional attributes 'qual:name', 'qual:initialLevel' and 'qual:maxLevel'. No other attributes from the SBML Level 3 Qualitative Models namespace are permitted on a &lt;qualitativeSpecies&gt; object.

## Related elements

- [Transition](transition.md): what the level of a qualitative species becomes, and under which condition
- [Input](input.md): a qualitative species a transition reads, with the sign of its influence
- [Output](output.md): a qualitative species a transition changes, with the effect it has on it
- [Compartment](compartment.md): a bounded space in which species are located
- [Qualitative Models (qual)](qual.md): the package which describes a model whose entities carry a level

## Specification

[SBML Level 3 Package: Qualitative Models, Version 1 Release 1](https://sbml.org/documents/specifications/level-3/version-1/qual/), Section 3.5 (Chaouiya et al. 2013, BMC Syst Biol 7:135).
