# Qualitative Models (qual)

The package which describes a model whose entities carry a level.

A qualitative model does not integrate rate laws over time. Its entities carry a level, a whole number which stands for a range of activity, and a rule says which level an entity takes next given the levels of the entities which act on it. It is how a regulatory network is written down when the kinetics are unknown, which is the usual case for a network of genes, and it covers the logical models of the Boolean school as well as Petri nets.

The qual package holds what such a model needs beyond the core: the [qualitative species](qualitativespecies.md) with their levels, and the [transitions](transition.md) with the [inputs](input.md) they read, the [outputs](output.md) they change and the [function terms](functionterm.md) which decide between them.

The report shows the qualitative species and the transitions of a model as sections of their own, the inputs of a transition with the sign of their influence, and the function terms as the transition table they are.

## Related elements

- [Qualitative species](qualitativespecies.md): an entity of a qualitative model, which carries a level instead of an amount
- [Transition](transition.md): what the level of a qualitative species becomes, and under which condition
- [Input](input.md): a qualitative species a transition reads, with the sign of its influence
- [Output](output.md): a qualitative species a transition changes, with the effect it has on it
- [Function term](functionterm.md): one row of the transition table: a condition and the level it results in

## Specification

[SBML Level 3 Package: Qualitative Models, Version 1 Release 1](https://sbml.org/documents/specifications/level-3/version-1/qual/) (Chaouiya et al. 2013, BMC Syst Biol 7:135).
