# Output

A qualitative species a transition changes, with the effect it has on it.

An output names the [qualitative species](qualitativespecies.md) whose level a [transition](transition.md) changes. Its [transition effect](output.md#transitioneffect) is what tells the two formalisms of the package apart: `assignmentLevel` for a logical model, `production` for a Petri net.

It is an element of the report and not a row of its transition, because the specification derives it from `SBase`: it may carry an identifier, a name, an SBO term, notes and annotations, and the reference to its species starts here, not at the transition around it.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [qualitativeSpecies](#qualitativespecies) | [`SIdRef`](datatypes.md#sidref) | required | the species whose level the transition changes | [qual 3.6.2](https://sbml.org/documents/specifications/level-3/version-1/qual/) |
| [outputLevel](#outputlevel) | [`integer`](datatypes.md#integer) | optional | the level the transition produces per result level | [qual 3.6.2](https://sbml.org/documents/specifications/level-3/version-1/qual/) |
| [transitionEffect](#transitioneffect) | [`transitionOutputEffect`](datatypes.md#transitionoutputeffect) | required | whether the transition sets the level of the species or adds to it | [qual 3.6.2](https://sbml.org/documents/specifications/level-3/version-1/qual/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="qualitativespecies"></span>**qualitativeSpecies**

The attribute is required and names a [qualitative species](qualitativespecies.md) of the model which is not constant, since a constant species is an input of the system which no transition may change. The report links it, and the inspector of that species shows the output under "referenced by", which is how the transitions that decide the level of an entity are found.

- `3020311` (warning): A &lt;qualitativeSpecies&gt; that is referenced by an &lt;output&gt; with the 'qual:transitionEffect' attribute set to 'assignmentLevel' should not be referenced by any other &lt;output&gt; with the same 'transitionEffect' throughout the set of transitions for the containing model.
- `3020607` (error): The value of the attribute 'qual:qualitativeSpecies' in an &lt;output&gt; object must be the identifier of an existing &lt;qualitativeSpecies&gt; object defined in the enclosing &lt;model&gt; object.
- `3020608` (error): The &lt;qualitativeSpecies&gt; referred to by the attribute 'qual:qualitativeSpecies' in an &lt;output&gt; object must have the value of its 'qual:constant' attribute set to 'false'.

<span id="outputlevel"></span>**outputLevel**

Where the transition effect is `production`, the level the species gains is the result level of the term which fires multiplied by the output level, which is the weight of the arc of a Petri net. The attribute is required there and has no meaning for an `assignmentLevel` output, where the level is the result level itself.

The report shows the output level in the table of the outputs in the inspector of the transition.

Default: the transition effect is assignmentLevel, where the output level has no meaning.

- `3020606` (error): The attribute 'qual:outputLevel' in &lt;output&gt; must be of the data type 'integer'.
- `3020609` (error): When the value of the attribute 'qual:transitionEffect' of an &lt;output&gt; object is set to the value 'production' the attribute 'qual:outputLevel' for that particular &lt;output&gt; object must have a value set.
- `3020610` (error): The attribute 'qual:outputLevel' in &lt;output&gt; must not be negative.

<span id="transitioneffect"></span>**transitionEffect**

The effect is `assignmentLevel`, where the level of the species becomes the result level of the term which fires, which is how a logical model is written, or `production`, where the result level multiplied by the output level is added to it, which is how a Petri net is written. The attribute is required, and it is the attribute which says in which of the two formalisms a file is written.

The report shows the effect in the table of the outputs in the inspector of the transition.

- `3020311` (warning): A &lt;qualitativeSpecies&gt; that is referenced by an &lt;output&gt; with the 'qual:transitionEffect' attribute set to 'assignmentLevel' should not be referenced by any other &lt;output&gt; with the same 'transitionEffect' throughout the set of transitions for the containing model.
- `3020605` (error): The value of the attribute 'qual:transitionEffect' of an &lt;output&gt; object must conform to the syntax of the SBML data type 'transitionOutputEffect' and may only take on the allowed values of 'transitionOutputEffect' defined in SBML; that is, the value must be one of the following: 'production' or 'assignmentLevel'.
- `3020609` (error): When the value of the attribute 'qual:transitionEffect' of an &lt;output&gt; object is set to the value 'production' the attribute 'qual:outputLevel' for that particular &lt;output&gt; object must have a value set.

## Validation rules

- `3010301` (error): (Extends validation rule #10301 in the SBML Level 3 Version 1 Core specification.) Within a &lt;model&gt; the values of the attributes 'id' and 'qual:id' on every instance of the following classes of objects must be unique across the set of all 'id' and 'qual:id' attribute values of all such objects in a model: the &lt;model&gt; itself, plus all contained &lt;functionDefinition&gt;, &lt;compartment&gt;, &lt;species&gt;, &lt;reaction&gt;, &lt;speciesReference&gt;, &lt;modifierSpeciesReference&gt;, &lt;event&gt;, and &lt;parameter&gt; objects, plus the &lt;qualitativeSpecies&gt;, &lt;transition&gt;, &lt;input&gt; and &lt;output&gt; objects defined by the Qualitative Models package.
- `3020601` (error): An &lt;output&gt; object may have the optional 'metaid' and 'sboTerm' defined by SBML Level 3 Core. No other attributes from the SBML Level 3 Core namespace or the Qualitative Models namespace are permitted on an &lt;output&gt; object.
- `3020602` (error): An &lt;output&gt; object may have the optional SBML Level 3 Core subobjects for notes and annotations. No other elements from the SBML Level 3 Core namespaces are permitted on an &lt;output&gt;.
- `3020603` (error): An &lt;output&gt; object must have the required attributes 'qual:qualitativeSpecies' as well as 'qual:transitionEffect' and may have the optional attributes 'qual:id', 'qual:name' and 'qual:outputLevel'. No other attributes from the SBML Level 3 Qualitative Models namespace are permitted on an &lt;output&gt; object.

## Related elements

- [Transition](transition.md): what the level of a qualitative species becomes, and under which condition
- [QualitativeSpecies](qualitativespecies.md): an entity of a qualitative model, which carries a level instead of an amount
- [Input](input.md): a qualitative species a transition reads, with the sign of its influence
- [Qualitative Models (qual)](qual.md): the package which describes a model whose entities carry a level

## Specification

[SBML Level 3 Package: Qualitative Models, Version 1 Release 1](https://sbml.org/documents/specifications/level-3/version-1/qual/), Section 3.6.2 (Chaouiya et al. 2013, BMC Syst Biol 7:135).
