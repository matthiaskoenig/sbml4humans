# UncertSpan

A measure of an uncertainty which is an interval.

Four of the sixteen measures of the package are an interval and not a number: the [range](uncertspan.md#type) of a measurement, its 95 percent confidence interval, its 95 percent credible interval and its interquartile range. A span is the [uncert parameter](uncertparameter.md) of such a measure, with the two ends of the interval in the place of the single value of a parameter.

Each end is either a number, in [value lower](uncertspan.md#valuelower) and [value upper](uncertspan.md#valueupper), or an element of the model, in [var lower](uncertspan.md#varlower) and [var upper](uncertspan.md#varupper). An end which is set by neither is not defined, so a span may be open at one end.

The report shows a span as the interval it is, `1 to 4`, with a link where an end names an element.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [valueLower](#valuelower) | [`double`](datatypes.md#double) | optional | the lower end of the interval as a number | [distrib 3.12](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf) |
| [valueUpper](#valueupper) | [`double`](datatypes.md#double) | optional | the upper end of the interval as a number | [distrib 3.12](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf) |
| [varLower](#varlower) | [`SIdRef`](datatypes.md#sidref) | optional | the element of the model which holds the lower end | [distrib 3.12](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf) |
| [varUpper](#varupper) | [`SIdRef`](datatypes.md#sidref) | optional | the element of the model which holds the upper end | [distrib 3.12](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf) |
| [type](#type) | [`UncertKind`](datatypes.md#uncertkind) | required | which interval the span is | [distrib 3.11.1](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf) |
| [units](#units) | [`UnitSIdRef`](datatypes.md#unitsidref) | optional | the units both ends of the interval are given in | [distrib 3.12](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf) |
| [value](#value) | [`double`](datatypes.md#double) | optional | the single number of a measure, which a span does not use | [distrib 3.11.2](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf) |
| [var](#var) | [`SIdRef`](datatypes.md#sidref) | optional | the element of a single number, which a span does not use | [distrib 3.11.2](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf) |
| [definitionURL](#definitionurl) | [`anyURI`](datatypes.md#anyuri) | optional | what an external parameter which is an interval means | [distrib 3.11.4](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf) |
| [math](#math) | [`Math`](datatypes.md#math) | optional | the formula of an external parameter which is an interval | [distrib 3.11.6](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf) |
| [uncertParameters](#uncertparameters) | [`list`](datatypes.md#list) | optional | the parameters which define an external parameter | [distrib 3.11.7](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="valuelower"></span>**valueLower**

The number in the [units](uncertspan.md#units) of the span. A file writes either this attribute or [var lower](uncertspan.md#varlower) for the lower end, and where it writes neither the interval is open at the bottom.

The report shows it as the left side of the interval.

Default: the lower end is the element var lower names, or the interval is open at the bottom.

- `1520505` (error): The attribute 'distrib:valueLower' on an &lt;uncertSpan&gt; must have a value of data type 'double'.

<span id="valueupper"></span>**valueUpper**

The number in the [units](uncertspan.md#units) of the span. A file writes either this attribute or [var upper](uncertspan.md#varupper) for the upper end, and where it writes neither the interval is open at the top.

The report shows it as the right side of the interval.

Default: the upper end is the element var upper names, or the interval is open at the top.

- `1520507` (error): The attribute 'distrib:valueUpper' on an &lt;uncertSpan&gt; must have a value of data type 'double'.

<span id="varlower"></span>**varLower**

Where the lower end of the interval is a quantity of the model and not a fixed number, the span names that element, the way the [var](uncertparameter.md#var) of a parameter names one. Its units are the units of the element it names.

The report links the element, and the inspector of that element shows the span under "referenced by".

Default: the lower end is the number in value lower, or the interval is open at the bottom.

- `1520504` (error): The value of the attribute 'distrib:varLower' of an &lt;uncertSpan&gt; object must be the identifier of an existing object derived from the 'SBase' class and defined in the enclosing &lt;model&gt; object.

<span id="varupper"></span>**varUpper**

Where the upper end of the interval is a quantity of the model and not a fixed number, the span names that element, the way the [var](uncertparameter.md#var) of a parameter names one. Its units are the units of the element it names.

The report links the element, and the inspector of that element shows the span under "referenced by".

Default: the upper end is the number in value upper, or the interval is open at the top.

- `1520506` (error): The value of the attribute 'distrib:varUpper' of an &lt;uncertSpan&gt; object must be the identifier of an existing object derived from the 'SBase' class and defined in the enclosing &lt;model&gt; object.

<span id="type"></span>**type**

The attribute is required. A span carries one of the four measures which are an interval, `range`, `confidenceInterval`, `credibleInterval` and `interquartileRange`, or `externalParameter`, the measure the package does not define, which may be an interval as well. The other eleven values are a single number and belong to an [uncert parameter](uncertparameter.md#type).

The report shows the type in the first column of the parameters of an uncertainty and as the name of a span which carries no identifier.

- `1520308` (error): The value of the attribute 'distrib:type' of an &lt;uncertParameter&gt; object must conform to the syntax of SBML data type 'UncertType' and may only take on the allowed values of 'UncertType' defined in SBML; that is, the value must be one of the following: 'distribution', 'externalParameter', 'coeffientOfVariation', 'kurtosis', 'mean', 'median', 'mode', 'sampleSize', 'skewness', 'standardDeviation', 'standardError', 'variance', 'confidenceInterval', 'credibleInterval', 'interquartileRange' or 'range'.

<span id="units"></span>**units**

The units of the two ends of the span, which have to be the same, given as a [unit definition](unitdefinition.md) of the model or as a base unit of SBML. An end which names an element carries the units of that element instead.

The report links the unit definition where the units name one.

Default: an end which names an element carries the units of that element.

- `1520307` (error): The value of the attribute 'distrib:units' on an &lt;uncertParameter&gt; must have a taken from the following: the identifier of a &lt;unitDefinition&gt; object in the enclosing &lt;model,&gt; or one of the base units in SBML.

<span id="value"></span>**value**

A span carries its numbers in [value lower](uncertspan.md#valuelower) and [value upper](uncertspan.md#valueupper). The attribute belongs to the [uncert parameter](uncertparameter.md#value) a span derives from and is left unset by every interval, so the report shows the interval in its place.

Default: a span carries its numbers in value lower and value upper.

- `1520305` (error): The attribute 'distrib:value' on an &lt;uncertParameter&gt; must have a value of data type 'double'.

<span id="var"></span>**var**

A span names the elements of its two ends in [var lower](uncertspan.md#varlower) and [var upper](uncertspan.md#varupper). The attribute belongs to the [uncert parameter](uncertparameter.md#var) a span derives from and is left unset by every interval.

Default: a span names the elements of its ends in var lower and var upper.

- `1520306` (error): The value of the attribute 'distrib:var' of an &lt;uncertParameter&gt; object must be the identifier of an existing object derived from the 'SBase' class and defined in the enclosing &lt;model&gt; object.

<span id="definitionurl"></span>**definitionURL**

A span of the type `externalParameter` names what its interval is, an entry of an ontology or another definition which says what the two ends mean, the way an [uncert parameter](uncertparameter.md#definitionurl) does. The four intervals the specification defines carry no definition url.

The report shows the last segment of the url as a link in the table of the parameters of an uncertainty.

Default: the four intervals the specification defines say completely what they mean.

- `1520309` (error): The attribute 'distrib:definitionURL' on an &lt;uncertParameter&gt; must have a value of data type 'string'.

<span id="math"></span>**math**

Only a span of the type `externalParameter` carries math, the way an [uncert parameter](uncertparameter.md#math) of the type `distribution` does.

The report renders the formula and links every element it names from the span which carries it.

<span id="uncertparameters"></span>**uncertParameters**

A span of the type `externalParameter` may be defined by parameters of its own, the way a [distribution](uncertparameter.md#uncertparameters) is. The four intervals the specification defines need none, because their two ends define them.

The report shows every one of them indented below the span it defines.

- `1520304` (error): An &lt;uncertParameter&gt; object may contain one and only one instance of the &lt;listOfUncertParameters&gt; element. No other elements from the SBML Level 3 Distributions namespaces are permitted on an &lt;uncertParameter&gt; object.
- `1520310` (error): Apart from the general notes and annotations subobjects permitted on all SBML objects, a &lt;listOfUncertParameters&gt; container object may only contain &lt;uncertParameter&gt; objects.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [interval](#interval) | - | the two ends of the span as the interval they stand for |

<span id="interval"></span>**interval**

The report shows the four attributes of a span as one row, because they are one interval: `1 to 4` where both ends are numbers, the identifier of the element as a link where an end names one, and `from 1` or `to 4` where the file defines one end only.

The row is the reading of [value lower](uncertspan.md#valuelower), [value upper](uncertspan.md#valueupper), [var lower](uncertspan.md#varlower) and [var upper](uncertspan.md#varupper), each of which the file writes on its own.

## Validation rules

- `1520501` (error): An &lt;uncertSpan&gt; object may have the optional SBML Level 3 Core attributes 'metaid' and 'sboTerm'. No other attributes from the SBML Level 3 Core namespaces are permitted on an &lt;uncertSpan&gt;.
- `1520502` (error): An &lt;uncertSpan&gt; object may have the optional SBML Level 3 Core subobjects for notes and annotations. No other elements from the SBML Level 3 Core namespaces are permitted on an &lt;uncertSpan&gt;.
- `1520503` (error): An &lt;uncertSpan&gt; object may have the optional attributes 'distrib:varLower', 'distrib:valueLower', 'distrib:varUpper' and 'distrib:valueUpper'. No other attributes from the SBML Level 3 Distributions namespaces are permitted on an &lt;uncertSpan&gt; object.

## Related elements

- [UncertParameter](uncertparameter.md): one statistical measure of an uncertainty
- [Uncertainty](uncertainty.md): a set of statistical measures of the value of an element
- [Distributions (distrib)](distrib.md): the package which records the uncertainty of a value

## Specification

[The Distributions Package for SBML Level 3, Version 1 Release 1](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf), Section 3.12 (Smith et al. 2020, J Integr Bioinform 17(2-3):20200018).
