# Trigger

The condition of an event, whose change from false to true fires it.

The trigger holds the condition of an [event](event.md) as a formula which returns a boolean value, and it decides when the event fires: at the moment the formula turns from false to true. It is an element of its own, so a model can say with an SBO term what kind of condition it is and explain in its notes what the condition stands for.

The report shows the trigger as an element of its own, and its rendered condition and its two flags in the table and in the inspector of the event.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [math](#math) | `Math` | - | the condition whose change from false to true fires the event | [core 4.12.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [initialValue](#initialvalue) | `boolean` | - | whether the condition is taken to be true just before the simulation starts | [core 4.12.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [persistent](#persistent) | `boolean` | - | whether the event is still executed when its condition becomes false again before execution | [core 4.12.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="math"></span>**math**

The math is an expression which returns a boolean value, and the event fires at the moment it turns from false to true. It can fire again whenever the expression makes that transition again. A trigger without a formula can never fire.

The report renders the condition in the column "trigger" of the events and in the inspector, and links the elements the condition reads.

<span id="initialvalue"></span>**initialValue**

To know whether an event may already fire at time zero, a simulator has to know what the condition was just before. With "true" it is taken to have been true, so the event cannot fire at the start; with "false" it may fire immediately.

The report shows the flag as a mark, in the column "initial value" of the events and in the inspector.

<span id="persistent"></span>**persistent**

Between the moment an event triggers and the moment it is executed, its condition may turn false again, because the event is delayed or because another event changed the model. With "true" the assignments are carried out anyway, with "false" the event is dropped.

The report shows the flag as a mark, in the column "persistent" of the events and in the inspector.

## Related elements

- [Event](event.md): an instantaneous change of the model when a condition becomes true
- [Priority](priority.md): the formula which orders an event against the other events of the same moment
- [Delay](delay.md): the formula which gives the time between the trigger of an event and its execution
- [EventAssignment](eventassignment.md): the new value an event gives to one element of the model

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.12.2 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
