# DefaultTerm

The level of a transition in every state no function term covers.

The default term carries no condition: it is what makes the transition table of a [transition](transition.md) total, the row "otherwise" behind the [function terms](functionterm.md). Every transition has exactly one of them.

The specification notes that the class is not derived from `SBase` while libsbml gives it the full surface of one, so the report reads it as it reads every other element, with its meta id, its SBO term, its notes and its annotations.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [resultLevel](#resultlevel) | [`integer`](datatypes.md#integer) | required | the level the outputs take where no function term holds | [qual 3.6.4](https://sbml.org/documents/specifications/level-3/version-1/qual/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="resultlevel"></span>**resultLevel**

The result level is a whole number which cannot be negative, and it is required. In most files it is zero, which reads as "the entity is off unless one of the terms switches it on".

The report shows it as the last row of the table of the terms in the inspector of the transition, under the condition "otherwise".

- `3020704` (error): The attribute 'qual:resultLevel' in &lt;defaultTerm&gt; must be of the data type 'integer'.
- `3020705` (error): The attribute 'qual:resultLevel' in &lt;defaultTerm&gt; must not be negative.

## Validation rules

- `3020701` (error): A &lt;defaultTerm&gt; object may have the optional 'metaid' and 'sboTerm' defined by SBML Level 3 Core. No other attributes from the SBML Level 3 Core namespace or the Qualitative Models namespace are permitted on a &lt;defaultTerm&gt; object.
- `3020702` (error): A &lt;defaultTerm&gt; object may have the optional SBML Level 3 Core subobjects for notes and annotations. No other elements from the SBML Level 3 Core namespaces are permitted on a &lt;defaultTerm&gt;.
- `3020703` (error): A &lt;defaultTerm&gt; object must have the required attributes 'qual:resultLevel'. No other attributes from the SBML Level 3 Qualitative Models namespace are permitted on a &lt;defaultTerm&gt; object.

## Related elements

- [Transition](transition.md): what the level of a qualitative species becomes, and under which condition
- [FunctionTerm](functionterm.md): one row of the transition table: a condition and the level it results in
- [Qualitative Models (qual)](qual.md): the package which describes a model whose entities carry a level

## Specification

[SBML Level 3 Package: Qualitative Models, Version 1 Release 1](https://sbml.org/documents/specifications/level-3/version-1/qual/), Section 3.6.4 (Chaouiya et al. 2013, BMC Syst Biol 7:135).
