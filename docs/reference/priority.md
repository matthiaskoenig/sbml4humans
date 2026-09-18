# Priority

The formula which orders an event against the other events of the same moment.

The priority of an [event](event.md) decides which of several events executed at the same moment goes first: the one with the larger value. It is an element of its own, which a model can annotate and explain, and only a Level 3 model can carry one.

The report shows the priority as an element of its own and its rendered formula in the table and in the inspector of the event.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [math](#math) | `Math` | the formula whose value orders the events of one moment | [core 4.12.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="math"></span>**math**

The math returns a dimensionless number, and a larger value means the event is executed earlier. An event without a priority has none, and the order of simultaneous events is then not fixed.

The report renders the formula in the column "priority" of the events and in the inspector, and links the elements it reads.

## Related elements

- [Event](event.md): an instantaneous change of the model when a condition becomes true
- [Trigger](trigger.md): the condition of an event, whose change from false to true fires it
- [Delay](delay.md): the formula which gives the time between the trigger of an event and its execution

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.12.3 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
