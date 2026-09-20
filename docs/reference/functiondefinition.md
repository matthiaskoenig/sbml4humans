# FunctionDefinition

A named function which the mathematics of the model can call.

A function definition gives a name to a formula with arguments, so that a rate law which appears in many reactions is written once. The capabilities are deliberately limited: a function may only use its own arguments and other functions, it cannot read a species or a parameter, and it cannot call itself.

The report shows the body of the function as rendered mathematics, in the table and in the inspector.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [math](#math) | [`Math`](datatypes.md#math) | optional | the formula of the function, with its arguments | [core 4.3.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="math"></span>**math**

The math of a function definition is a MathML lambda expression: it declares the arguments and the expression which is computed from them. It is the only place in SBML core where a lambda is allowed.

The report renders the formula and shows it in the column "math" and in the inspector.

Default: the function has no mathematical meaning in SBML core.

- `20301` (error): The top-level element within &lt;math&gt; in a &lt;functionDefinition&gt; is restricted.
- `20303` (error): Inside the &lt;lambda&gt; of a &lt;functionDefinition&gt;, the identifier of that &lt;functionDefinition&gt; cannot appear as the value of a &lt;ci&gt; element. SBML functions are not permitted to be recursive.
- `20304` (error): Inside the &lt;lambda&gt; of a &lt;functionDefinition&gt;, if a &lt;ci&gt; element is not the first element within a MathML &lt;apply&gt;, then the &lt;ci&gt;'s value can only be the value of a &lt;bvar&gt; element declared in that &lt;lambda&gt;. In other words, all model entities referenced inside a function definition must be passed arguments to that function.
- `20305` (error): The value type returned by a &lt;functionDefinition&gt;'s &lt;lambda&gt; must be either Boolean or numeric.
- `20306` (error): A FunctionDefinition object must contain exactly one MathML math element. The &lt;math&gt; element is optional in L3V2 and beyond.

## Validation rules

- `10702` (warning): The value of the 'sboTerm' attribute on a &lt;functionDefinition&gt; is expected to be an SBO identifier (http://www.biomodels.net/SBO/) referring to a mathematical expression (i.e., terms derived from SBO:0000064, "mathematical expression").
- `20307` (error): FunctionDefinition object must have the required attribute 'id', and may have the optional attributes 'metaid', 'sboTerm' and 'name'. No other attributes from the SBML Level 3 Core namespace are permitted on a FunctionDefinition object.

## Related elements

- [Model](model.md): the container of everything a model is made of

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.3 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
