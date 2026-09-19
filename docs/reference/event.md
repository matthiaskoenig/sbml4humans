# Event

An instantaneous change of the model when a condition becomes true.

An event describes a discontinuous change: when its trigger turns from false to true, the assignments of the event are executed and set new values for compartments, species, stoichiometries or parameters. A dose which is given at a fixed time, a switch which flips at a threshold or a medium which is exchanged are events. The change can be delayed, and a priority decides which of several simultaneous events is executed first.

The report shows the rendered trigger, the priority and the delay of an event, the flags of its trigger and the table of its assignments, and opens the [trigger](trigger.md), the [priority](priority.md) and the [delay](delay.md) as elements of their own.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [useValuesFromTriggerTime](#usevaluesfromtriggertime) | [`boolean`](datatypes.md#boolean) | required | whether the assignments use the values of the moment the event was triggered | [core 4.12.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [trigger](#trigger) | [`Trigger`](trigger.md) | optional | the condition of the event, as an element of its own | [core 4.12.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [trigger](#trigger-2) | [`Math`](datatypes.md#math) | optional | the condition whose change from false to true fires the event | [core 4.12.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [initialValue](#initialvalue) | [`boolean`](datatypes.md#boolean) | required | whether the condition is taken to be true just before the simulation starts | [core 4.12.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [persistent](#persistent) | [`boolean`](datatypes.md#boolean) | required | whether the event is still executed when its condition becomes false again before execution | [core 4.12.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [priority](#priority) | [`Priority`](priority.md) | optional | the element which orders the event against other events of the same moment | [core 4.12.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [priority](#priority-2) | [`Math`](datatypes.md#math) | optional | the formula which orders this event against other events of the same moment | [core 4.12.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [delay](#delay) | [`Delay`](delay.md) | optional | the element which postpones the execution of the event | [core 4.12.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [delay](#delay-2) | [`Math`](datatypes.md#math) | optional | the formula which gives the time between the trigger and the execution | [core 4.12.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [listOfEventAssignments](#listofeventassignments) | [`list`](datatypes.md#list) | optional | the changes the event makes when it is executed | [core 4.12.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="usevaluesfromtriggertime"></span>**useValuesFromTriggerTime**

An event which is delayed is triggered at one moment and executed at another, and the two moments can give different values. With "true" the formulas of the assignments are evaluated when the event triggers, with "false" when it is executed.

The report shows the flag as a mark in the column "values from trigger time".

- `21206` (error): If an &lt;event&gt;'s 'useValuesFromTriggerTime' attribute has the value 'false', then the &lt;event&gt; must contain a &lt;delay&gt; element. The implication of 'useValuesFromTriggerTime=false' is that there is a delay between the time of trigger and the time of value assignments performed by the &lt;event&gt;.

<span id="trigger"></span>**trigger**

Every event has a [trigger](trigger.md), the element which holds the condition and the two flags which say how it is read. The report opens it in the inspector, with its own SBO term, notes and annotations.

Default: the event can never be triggered.

- `21201` (error): An &lt;event&gt; object must have a 'trigger'. In SBML Level 3 Version 2 this rule was relaxed to stating that an &lt;event&gt; object must have at most one 'trigger' element.

<span id="trigger-2"></span>**trigger**

The trigger holds an expression which returns a boolean value, and the event fires at the moment that expression turns from false to true. It can fire again whenever the expression makes that transition again. An event without a trigger can never fire.

The report renders the condition in the column "trigger" and in the inspector.

Default: the event is never triggered.

- `21202` (error): An &lt;event&gt;'s &lt;trigger&gt; expression must evaluate to a value of type Boolean.
- `21209` (error): A Trigger object must contain exactly one MathML &lt;math&gt; element. The &lt;math&gt; element is optional in L3V2 and beyond.

<span id="initialvalue"></span>**initialValue**

To know whether an event may already fire at time zero, a simulator has to know what the condition was just before. With "true" it is taken to have been true, so the event cannot fire at the start; with "false" it may fire immediately.

The report shows the flag as a mark, in the column "initial value" and in the inspector.

- `21229` (error): The attribute 'initialValue' on a Trigger object must have a value of type Boolean.

<span id="persistent"></span>**persistent**

Between the moment an event triggers and the moment it is executed, its condition may turn false again, because the event is delayed or because another event changed the model. With "true" the assignments are carried out anyway, with "false" the event is dropped.

The report shows the flag as a mark, in the column "persistent" and in the inspector.

- `21228` (error): The attribute 'persistent' on a Trigger object must have a value of type Boolean.

<span id="priority"></span>**priority**

An event may carry a [priority](priority.md), the element whose formula decides which of several events of one moment is executed first. An event without a priority has none, and the order of simultaneous events is then not fixed.

Default: the order of the event among simultaneous events is not fixed.

- `21230` (error): An Event object may contain at most one Priority object.

<span id="priority-2"></span>**priority**

When several events are executed at the same moment, the one with the higher priority goes first; a larger number means a higher priority and the value is dimensionless.

The report renders the priority in the column "priority" of the events and in the inspector.

Default: the event behaves as one without a priority.

- `21231` (error): An Priority object must contain exactly one MathML &lt;math&gt; element. The &lt;math&gt; element is optional in L3V2 and beyond.

<span id="delay"></span>**delay**

An event may carry a [delay](delay.md), the element whose formula gives the time between the trigger and the execution. An event without a delay is executed immediately.

Default: the event is executed at the moment it triggers.

- `21221` (error): An Event object may contain at most one Delay object.

<span id="delay-2"></span>**delay**

The delay is evaluated at the moment the event triggers and has to be a value which is not negative, in the time units of the model.

The report renders the delay in the column "delay" of the events and in the inspector.

Default: the event is executed as one without a delay.

- `21210` (error): A Delay object must contain exactly one MathML &lt;math&gt; element. The &lt;math&gt; element is optional in L3V2 and beyond.

<span id="listofeventassignments"></span>**listOfEventAssignments**

The list holds the [event assignments](eventassignment.md) of the event, each of which sets one element of the model to the value of a formula.

The report shows the assignments in the column "assignments", every one of them as the element it sets and the formula it assigns, and as a table in the inspector of the event.

Default: the event changes nothing when it is executed.

- `21203` (error): An &lt;event&gt; object must have at least one &lt;eventAssignment&gt; object in its &lt;listOfEventAssignments&gt;.
- `21222` (error): An Event object may contain at most one ListOfEventAssignments object.
- `21223` (error): Apart from the general Notes and Annotation subobjects permitted on all SBML components, a ListOfEventAssignments container object may only contain EventAssignment objects.

## Validation rules

- `10710` (warning): The value of the 'sboTerm' attribute on an &lt;event&gt; is expected to be an SBO identifier (http://www.biomodels.net/SBO/) referring to an occurring entity representation defined in SBO (i.e., terms derived from SBO:0000231, "occurring entity representation").
- `21205` (error): The order of subelements within &lt;event&gt; must be the following: &lt;trigger&gt;, &lt;delay&gt;, &lt;listOfEventAssignments&gt;. The &lt;delay&gt; element is optional, but if present, must follow &lt;trigger&gt;.
- `21225` (error): An Event object must have the required attribute 'useValuesFromTriggerTime' and in addition may have the optional attributes 'metaid', 'sboTerm', 'id', and 'name'. No other attributes from the SBML Level 3 Core namespace are permitted on an Event object.

## Related elements

- [Trigger](trigger.md): the condition of an event, whose change from false to true fires it
- [Priority](priority.md): the formula which orders an event against the other events of the same moment
- [Delay](delay.md): the formula which gives the time between the trigger of an event and its execution
- [EventAssignment](eventassignment.md): the new value an event gives to one element of the model

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.12 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
