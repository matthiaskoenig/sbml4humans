# Event

An instantaneous change of the model when a condition becomes true.

An event describes a discontinuous change: when its trigger turns from false to true, the assignments of the event are executed and set new values for compartments, species, stoichiometries or parameters. A dose which is given at a fixed time, a switch which flips at a threshold or a medium which is exchanged are events. The change can be delayed, and a priority decides which of several simultaneous events is executed first.

The report shows the rendered trigger, the priority and the delay of an event, the flags of its trigger and the table of its assignments.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [values from trigger time](#values-from-trigger-time) | `boolean` | whether the assignments use the values of the moment the event was triggered | [core 4.12.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [trigger](#trigger) | `Math` | the condition whose change from false to true fires the event | [core 4.12.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [initial value](#initial-value) | `boolean` | whether the condition is taken to be true just before the simulation starts | [core 4.12.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [persistent](#persistent) | `boolean` | whether the event is still executed when its condition becomes false again before execution | [core 4.12.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [priority](#priority) | `Math` | the formula which orders this event against other events of the same moment | [core 4.12.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [delay](#delay) | `Math` | the formula which gives the time between the trigger and the execution | [core 4.12.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [assignments](#assignments) | `list` | the changes the event makes when it is executed | [core 4.12.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="values-from-trigger-time"></span>**values from trigger time**

An event which is delayed is triggered at one moment and executed at another, and the two moments can give different values. With "true" the formulas of the assignments are evaluated when the event triggers, with "false" when it is executed.

The report shows the flag as a mark in the column "values from trigger time".

<span id="trigger"></span>**trigger**

The trigger holds an expression which returns a boolean value, and the event fires at the moment that expression turns from false to true. It can fire again whenever the expression makes that transition again. An event without a trigger can never fire.

The report renders the condition in the column "trigger" and in the inspector.

<span id="initial-value"></span>**initial value**

To know whether an event may already fire at time zero, a simulator has to know what the condition was just before. With "true" it is taken to have been true, so the event cannot fire at the start; with "false" it may fire immediately.

The report shows the flag as a mark, in the column "initial value" and in the inspector.

<span id="persistent"></span>**persistent**

Between the moment an event triggers and the moment it is executed, its condition may turn false again, because the event is delayed or because another event changed the model. With "true" the assignments are carried out anyway, with "false" the event is dropped.

The report shows the flag as a mark, in the column "persistent" and in the inspector.

<span id="priority"></span>**priority**

When several events are executed at the same moment, the one with the higher priority goes first; a larger number means a higher priority and the value is dimensionless. An event without a priority has none, and the order of simultaneous events is then not fixed.

The report renders the priority in the column "priority" and in the inspector.

<span id="delay"></span>**delay**

The delay is evaluated at the moment the event triggers and has to be a value which is not negative, in the time units of the model. An event without a delay is executed immediately.

The report renders the delay in the column "delay" and in the inspector.

<span id="assignments"></span>**assignments**

The list holds the [event assignments](eventassignment.md) of the event, each of which sets one element of the model to the value of a formula.

The report shows the assignments in the column "assignments", every one of them as the element it sets and the formula it assigns, and as a table in the inspector of the event.

## Related elements

- [Event assignment](eventassignment.md): the new value an event gives to one element of the model
- [Parameter](parameter.md): a named value which the mathematics of the model can use
- [Species](species.md): a pool of a chemical entity in a compartment

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.12 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
