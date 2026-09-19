# Qualitative Models (qual)

The package which describes a model whose entities carry a level.

A qualitative model does not integrate rate laws over time. Its entities carry a level, a whole number which stands for a range of activity, and a rule says which level an entity takes next given the levels of the entities which act on it. It is how a regulatory network is written down when the kinetics are unknown, which is the usual case for a network of genes, and it covers the logical models of the Boolean school as well as Petri nets.

The qual package holds what such a model needs beyond the core: the [qualitative species](qualitativespecies.md) with their levels, and the [transitions](transition.md) with the [inputs](input.md) they read, the [outputs](output.md) they change and the [function terms](functionterm.md) which decide between them.

The report shows the qualitative species and the transitions of a model as sections of their own, the inputs of a transition with the sign of their influence, and the function terms as the transition table they are.

## Validation rules

- `3010101` (error): To conform to Version 1 of the Qualitative Models package specification for SBML Level 3, an SBML document must declare the use of the following XML Namespace: 'http://www.sbml.org/sbml/level3/version1/qual/version1'
- `3010102` (error): Wherever they appear in an SBML document, elements and attributes from the Qualitative Models package must be declared either implicitly or explicitly to be in the XML namespace 'http://www.sbml.org/sbml/level3/version1/qual/version1'
- `3020101` (error): In all SBML documents using the Qualitative Models package, the SBML object must include a value for the attribute 'qual:required' attribute.
- `3020102` (error): The value of attribute 'qual:required' on the SBML object must be of the data type Boolean.
- `3020103` (error): The value of attribute 'qual:required' on the SBML object must be set to 'true' if if the model contains any &lt;transition&gt; objects.

## Related elements

- [QualitativeSpecies](qualitativespecies.md): an entity of a qualitative model, which carries a level instead of an amount
- [Transition](transition.md): what the level of a qualitative species becomes, and under which condition
- [Input](input.md): a qualitative species a transition reads, with the sign of its influence
- [Output](output.md): a qualitative species a transition changes, with the effect it has on it
- [FunctionTerm](functionterm.md): one row of the transition table: a condition and the level it results in

## Specification

[SBML Level 3 Package: Qualitative Models, Version 1 Release 1](https://sbml.org/documents/specifications/level-3/version-1/qual/) (Chaouiya et al. 2013, BMC Syst Biol 7:135).
