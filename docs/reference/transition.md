# Transition

What the level of a qualitative species becomes, and under which condition.

A transition is to a qualitative model what a [reaction](reaction.md) with its kinetic law is to a kinetic one: it holds the dynamics. It reads the [qualitative species](qualitativespecies.md) of its [inputs](input.md), it changes those of its [outputs](output.md), and its [function terms](functionterm.md) say which level the outputs take: the result level of the first term whose condition holds, and the level of the [default term](defaultterm.md) where none of them holds.

Its identifier is optional and has no mathematical meaning, because nothing in a qualitative model refers to a transition.

The report shows the transitions of a model in a section of their own, with the species they read and the species they change, and the inspector shows the function terms as the table of condition and result level they are.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [listOfInputs](#listofinputs) | [`list`](datatypes.md#list) | optional | the qualitative species the transition reads | [qual 3.6.1](https://sbml.org/documents/specifications/level-3/version-1/qual/) |
| [listOfOutputs](#listofoutputs) | [`list`](datatypes.md#list) | optional | the qualitative species the transition changes | [qual 3.6.2](https://sbml.org/documents/specifications/level-3/version-1/qual/) |
| [listOfFunctionTerms](#listoffunctionterms) | [`list`](datatypes.md#list) | required | the terms which decide the level, in the order in which they are read | [qual 3.6.3](https://sbml.org/documents/specifications/level-3/version-1/qual/) |
| [defaultTerm](#defaultterm) | [`DefaultTerm`](defaultterm.md) | required | the term which holds in every state no function term covers | [qual 3.6.4](https://sbml.org/documents/specifications/level-3/version-1/qual/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="listofinputs"></span>**listOfInputs**

Every [input](input.md) names one [qualitative species](qualitativespecies.md) whose level the condition of a function term may read, with the threshold at which it matters and the sign of its influence. A transition may list none of them, in which case its terms read no species at all.

The report shows the species of the inputs with their sign in the column "inputs" and the table of the inputs in the inspector.

Default: the function terms of the transition read no species.

- `3020405` (error): A &lt;transition&gt; must have one and only one instance of the &lt;listOfFunctionTerms&gt; objects and may have at most one instance of the &lt;listOfInputs&gt; and &lt;listOfOutputs&gt; objects from the Qualitative Models namespace.
- `3020406` (error): The &lt;listOfInputs&gt; and &lt;listOfOutputs&gt; subobjects on a &lt;transition&gt; object are optional, but if present, these container object must not be empty.
- `3020407` (error): Apart from the general notes and annotation subobjects permitted on all SBML objects, a &lt;listOfInputs&gt; container object may only contain &lt;input&gt; objects.

<span id="listofoutputs"></span>**listOfOutputs**

Every [output](output.md) names one [qualitative species](qualitativespecies.md) whose level the transition sets or increases. A transition without outputs changes nothing, which is why a model which does something has at least one.

The report shows the species of the outputs in the column "outputs" and the table of the outputs in the inspector.

Default: the transition changes no species.

- `3020405` (error): A &lt;transition&gt; must have one and only one instance of the &lt;listOfFunctionTerms&gt; objects and may have at most one instance of the &lt;listOfInputs&gt; and &lt;listOfOutputs&gt; objects from the Qualitative Models namespace.
- `3020406` (error): The &lt;listOfInputs&gt; and &lt;listOfOutputs&gt; subobjects on a &lt;transition&gt; object are optional, but if present, these container object must not be empty.
- `3020408` (error): Apart from the general notes and annotation subobjects permitted on all SBML objects, a &lt;listOfOutputs&gt; container object may only contain &lt;output&gt; objects.

<span id="listoffunctionterms"></span>**listOfFunctionTerms**

The list is the transition table of the transition. Its [terms](functionterm.md) are read in the order in which the file writes them and the first one whose condition holds decides the result level, so two terms whose conditions overlap are not a contradiction: the earlier one wins.

The report shows the terms as a table of condition and result level in the inspector of the transition, with the default term as its last row.

- `3020405` (error): A &lt;transition&gt; must have one and only one instance of the &lt;listOfFunctionTerms&gt; objects and may have at most one instance of the &lt;listOfInputs&gt; and &lt;listOfOutputs&gt; objects from the Qualitative Models namespace.
- `3020409` (error): Apart from the general notes and annotation subobjects permitted on all SBML objects, a &lt;listOfFunctionTerms&gt; container object must contain one and only one &lt;defaultTerm&gt; object and then may only contain &lt;functionTerm&gt; objects.
- `3020413` (error): No element of the &lt;listOfFunctionTerms&gt; object may cause the level of a &lt;qualitativeSpecies&gt; to exceed the value 'qual:maxLevel' attribute.
- `3020414` (error): No element of the &lt;listOfFunctionTerms&gt; object may cause the level of a &lt;qualitativeSpecies&gt; to become negative.

<span id="defaultterm"></span>**defaultTerm**

Every transition has exactly one [default term](defaultterm.md), which makes the transition table total: whatever the levels of the inputs, some term gives a result level.

The report shows it as the last row of the table of the function terms, under the condition "otherwise".

- `3020409` (error): Apart from the general notes and annotation subobjects permitted on all SBML objects, a &lt;listOfFunctionTerms&gt; container object must contain one and only one &lt;defaultTerm&gt; object and then may only contain &lt;functionTerm&gt; objects.

## Validation rules

- `3010301` (error): (Extends validation rule #10301 in the SBML Level 3 Version 1 Core specification.) Within a &lt;model&gt; the values of the attributes 'id' and 'qual:id' on every instance of the following classes of objects must be unique across the set of all 'id' and 'qual:id' attribute values of all such objects in a model: the &lt;model&gt; itself, plus all contained &lt;functionDefinition&gt;, &lt;compartment&gt;, &lt;species&gt;, &lt;reaction&gt;, &lt;speciesReference&gt;, &lt;modifierSpeciesReference&gt;, &lt;event&gt;, and &lt;parameter&gt; objects, plus the &lt;qualitativeSpecies&gt;, &lt;transition&gt;, &lt;input&gt; and &lt;output&gt; objects defined by the Qualitative Models package.
- `3020401` (error): A &lt;transition&gt; object may have the optional 'metaid' and 'sboTerm' defined by SBML Level 3 Core. No other attributes from the SBML Level 3 Core namespace or the Qualitative Models namespace are permitted on a &lt;transition&gt; object.
- `3020402` (error): A &lt;transition&gt; object may have the optional SBML Level 3 Core subobjects for notes and annotations. No other elements from the SBML Level 3 Core namespaces are permitted on a &lt;transition&gt;.
- `3020403` (error): A &lt;transition&gt; object may have the optional attributes 'qual:name' and 'qual:id'. No other attributes from the SBML Level 3 Qualitative Models namespace are permitted on a &lt;transition&gt; object.
- `3020405` (error): A &lt;transition&gt; must have one and only one instance of the &lt;listOfFunctionTerms&gt; objects and may have at most one instance of the &lt;listOfInputs&gt; and &lt;listOfOutputs&gt; objects from the Qualitative Models namespace.

## Related elements

- [QualitativeSpecies](qualitativespecies.md): an entity of a qualitative model, which carries a level instead of an amount
- [Input](input.md): a qualitative species a transition reads, with the sign of its influence
- [Output](output.md): a qualitative species a transition changes, with the effect it has on it
- [FunctionTerm](functionterm.md): one row of the transition table: a condition and the level it results in
- [DefaultTerm](defaultterm.md): the level of a transition in every state no function term covers
- [Qualitative Models (qual)](qual.md): the package which describes a model whose entities carry a level

## Specification

[SBML Level 3 Package: Qualitative Models, Version 1 Release 1](https://sbml.org/documents/specifications/level-3/version-1/qual/), Section 3.6 (Chaouiya et al. 2013, BMC Syst Biol 7:135).
