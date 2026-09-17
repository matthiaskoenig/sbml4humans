# Event

An instantaneous change of the model when a condition becomes true.

An event describes a discontinuous change: when its trigger turns from false to true, the assignments of the event are executed and set new values for compartments, species, stoichiometries or parameters. A dose which is given at a fixed time, a switch which flips at a threshold or a medium which is exchanged are events. The change can be delayed, and a priority decides which of several simultaneous events is executed first.

The report shows the rendered trigger, the priority and the delay of an event, the flags of its trigger and the table of its assignments.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| values from trigger time | `boolean` | <span id="values-from-trigger-time"></span>whether the assignments use the values of the moment the event was triggered | [Section 4.12.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| trigger | `Trigger` | <span id="trigger"></span>the condition whose change from false to true fires the event | [Section 4.12.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| trigger initial value | `boolean` | <span id="trigger-initial-value"></span>whether the condition is taken to be true just before the simulation starts | [Section 4.12.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| trigger persistent | `boolean` | <span id="trigger-persistent"></span>whether the event is still executed when its condition becomes false again before execution | [Section 4.12.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| priority | `Math` | <span id="priority"></span>the formula which orders this event against other events of the same moment | [Section 4.12.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| delay | `Math` | <span id="delay"></span>the formula which gives the time between the trigger and the execution | [Section 4.12.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| event assignments | `list` | <span id="event-assignments"></span>the changes the event makes when it is executed | [Section 4.12.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## Related elements

- [Event assignment](eventassignment.md): the new value an event gives to one element of the model
- [Parameter](parameter.md): a named value which the mathematics of the model can use
- [Species](species.md): a pool of a chemical entity in a compartment

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.12 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
