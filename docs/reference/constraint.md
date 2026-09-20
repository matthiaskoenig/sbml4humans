# Constraint

A condition which a valid simulation of the model has to satisfy.

A constraint is an expression which has to stay true while a simulation runs, for example that a concentration stays inside the range in which a rate law was measured. It does not change anything in the model: as soon as it is violated, the results from that moment on are no longer valid, and the software has to tell the user.

The report shows the rendered condition and the message which explains a violation.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [math](#math) | [`Math`](datatypes.md#math) | optional | the condition which has to stay true | [core 4.10.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [message](#message) | [`XHTML`](datatypes.md#xhtml) | optional | the text which is shown when the condition is violated | [core 4.10.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="math"></span>**math**

The math is an expression which returns a boolean value. It is checked at the start of the simulation and at every moment after it.

The report renders the condition in the column "math" and in the inspector.

Default: the constraint puts no restriction on the model.

- `21001` (error): A &lt;constraint&gt;'s &lt;math&gt; expression must evaluate to a value of type Boolean.
- `21007` (error): A &lt;constraint&gt; object must contain exactly one MathML &lt;math&gt; element. The &lt;math&gt; element is optional in L3V2 and beyond.

<span id="message"></span>**message**

The message is XHTML written for the user of a simulation, for example "the concentration of S1 left the range of the rate law". It is the place where the model author explains why the constraint exists.

The report shows the message next to the condition.

Default: nothing is shown to the user when the condition is violated.

- `21003` (error): The contents of the &lt;message&gt; element in a &lt;constraint&gt; must be explicitly placed in the XHTML XML namespace.
- `21004` (error): The contents of the &lt;message&gt; element must not contain an XML declaration (i.e., a string of the form "&lt;?xml version="1.0" encoding="UTF-8"?&gt;" or similar).
- `21005` (error): The contents of the &lt;message&gt; element must not contain an XML DOCTYPE declaration (i.e., a string beginning with the characters "&lt;!DOCTYPE".
- `21006` (error): The XHTML content inside a &lt;constraint&gt;'s &lt;message&gt; element can only take one of the following general forms: (1) a complete XHTML document beginning with the element &lt;html&gt; and ending with &lt;/html&gt;; (2) the "body" portion of a document beginning with the element &lt;body&gt; and ending with &lt;/body&gt;; or (3) XHTML content that is permitted within a &lt;body&gt; ... &lt;/body&gt; elements.
- `21008` (error): A &lt;constraint&gt; object may contain at most one &lt;message&gt; subobject.

## Validation rules

- `10706` (warning): The value of the 'sboTerm' attribute on a &lt;constraint&gt; is expected to be an SBO identifier (http://www.biomodels.net/SBO/) referring to a mathematical expression (i.e., terms derived from SBO:0000064, "mathematical expression").
- `21002` (error): The order of subelements within &lt;constraint&gt; must be the following: &lt;math&gt;, &lt;message&gt;. The &lt;message&gt; element is optional, but if present, must follow the &lt;math&gt; element.
- `21009` (error): A &lt;constraint&gt; object may have the optional attributes 'metaid' and 'sboTerm'. No other attributes from the SBML Level 3 Core namespace are permitted on a Constraint object.

## Related elements

- [Model](model.md): the container of everything a model is made of
- [Parameter](parameter.md): a named value which the mathematics of the model can use

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.10 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
