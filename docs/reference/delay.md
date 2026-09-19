# Delay

The formula which gives the time between the trigger of an event and its execution.

The delay of an [event](event.md) postpones its assignments: the event fires at one moment and is carried out later. It is an element of its own, which a model can annotate and explain; whether the values of the assignments are taken from the moment of the trigger or from the moment of the execution is decided by the flag "values from trigger time" of the event.

The report shows the delay as an element of its own and its rendered formula in the table and in the inspector of the event.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [math](#math) | [`Math`](datatypes.md#math) | optional | the formula which gives the time between the trigger and the execution | [core 4.12.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="math"></span>**math**

The math is evaluated at the moment the event triggers and has to give a value which is not negative, in the time units of the model. An event without a delay is executed immediately.

The report renders the formula in the column "delay" of the events and in the inspector, and links the elements it reads.

Default: the event is executed as one without a delay.

- `21210` (error): A Delay object must contain exactly one MathML &lt;math&gt; element. The &lt;math&gt; element is optional in L3V2 and beyond.

## Validation rules

- `10717` (warning): The value of the 'sboTerm' attribute on a &lt;delay&gt; is expected to be an SBO identifier (http://www.biomodels.net/SBO/) referring to a mathematical expression (i.e., terms derived from SBO:0000064, "mathematical expression").
- `21227` (error): A Delay object may have the optional attributes 'metaid' and 'sboTerm'. No other attributes from the SBML Level 3 Core namespace are permitted on a Delay object.

## Related elements

- [Event](event.md): an instantaneous change of the model when a condition becomes true
- [Trigger](trigger.md): the condition of an event, whose change from false to true fires it
- [Priority](priority.md): the formula which orders an event against the other events of the same moment

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.12.4 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
