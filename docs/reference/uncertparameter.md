# UncertParameter

One statistical measure of an uncertainty.

An uncert parameter is one measure of the [uncertainty](uncertainty.md) it belongs to: its mean, its standard deviation, the size of the sample it was measured on, or the distribution the value was drawn from. Its [type](uncertparameter.md#type) says which of the sixteen measures of the package it is, and the number behind that measure is either its [value](uncertparameter.md#value) or the element its [var](uncertparameter.md#var) names.

It is an element of the report and not a row of its uncertainty, because the specification derives it from `SBase` and from the `DistribBase` of the package: it may carry an identifier, a name, an SBO term, notes and annotations, and the notes of a measure are where a file records which paper or which experiment the number comes from, which is what the package exists for.

A measure which is an interval is an [uncert span](uncertspan.md), a class of its own, and a measure of the type `distribution` or `externalParameter` carries the parameters which define it as [uncert parameters](uncertparameter.md#uncertparameters) of its own.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [type](#type) | [`UncertKind`](datatypes.md#uncertkind) | required | which statistical measure the parameter is | [distrib 3.11.1](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf) |
| [value](#value) | [`double`](datatypes.md#double) | optional | the number of the measure | [distrib 3.11.2](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf) |
| [var](#var) | [`SIdRef`](datatypes.md#sidref) | optional | the element of the model which holds the number of the measure | [distrib 3.11.2](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf) |
| [units](#units) | [`UnitSIdRef`](datatypes.md#unitsidref) | optional | the units the measure is given in | [distrib 3.11.3](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf) |
| [definitionURL](#definitionurl) | [`anyURI`](datatypes.md#anyuri) | optional | what a distribution or an external parameter means | [distrib 3.11.4](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf) |
| [math](#math) | [`Math`](datatypes.md#math) | optional | the formula which defines a distribution | [distrib 3.11.6](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf) |
| [uncertParameters](#uncertparameters) | [`list`](datatypes.md#list) | optional | the parameters which define a distribution or an external parameter | [distrib 3.11.7](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="type"></span>**type**

The attribute is required and is one of sixteen values. Ten of them are a single number: `mean`, `median`, `mode`, `variance`, `standardDeviation`, `standardError`, `coefficientOfVariation`, `skewness`, `kurtosis` and `sampleSize`. Four of them are an interval and are written as an [uncert span](uncertspan.md): `range`, `confidenceInterval`, `credibleInterval` and `interquartileRange`, where the confidence and the credible interval are always the 95 percent interval. The last two say where a value comes from: `distribution`, the distribution it was drawn from, and `externalParameter`, a measure this specification does not define, which names what it means in its [definition](uncertparameter.md#definitionurl).

The report shows the type in the first column of the parameters of an uncertainty and as the name of a parameter which carries no identifier.

- `1520308` (error): The value of the attribute 'distrib:type' of an &lt;uncertParameter&gt; object must conform to the syntax of SBML data type 'UncertType' and may only take on the allowed values of 'UncertType' defined in SBML; that is, the value must be one of the following: 'distribution', 'externalParameter', 'coeffientOfVariation', 'kurtosis', 'mean', 'median', 'mode', 'sampleSize', 'skewness', 'standardDeviation', 'standardError', 'variance', 'confidenceInterval', 'credibleInterval', 'interquartileRange' or 'range'.

<span id="value"></span>**value**

A measure which is a single number carries it here, in the [units](uncertparameter.md#units) of the parameter. A file writes either the value or the [var](uncertparameter.md#var), never both: the value is the measurement as it was made, the var is the element of the model which holds it.

The report shows the value in the column "value" of the parameters of an uncertainty and in the inspector of the parameter.

Default: a measure which is a single number names the element which holds it in var.

- `1520305` (error): The attribute 'distrib:value' on an &lt;uncertParameter&gt; must have a value of data type 'double'.

<span id="var"></span>**var**

Where the measure is not a fixed number but a quantity of the model, the parameter names that element instead of writing a value: the standard deviation of a parameter may be a parameter of its own, which a simulation reads and a sampling changes. The identifier of the uncert parameter itself has no mathematical meaning and cannot be used for this, which is why the specification defines the attribute.

The report links the element the var names, and the inspector of that element shows the measure under "referenced by".

Default: a measure which is a single number writes that number in value.

- `1520306` (error): The value of the attribute 'distrib:var' of an &lt;uncertParameter&gt; object must be the identifier of an existing object derived from the 'SBase' class and defined in the enclosing &lt;model&gt; object.

<span id="units"></span>**units**

The units are either a [unit definition](unitdefinition.md) of the model or one of the base units of SBML. They are usually the units of the element the uncertainty belongs to, for a mean or a standard deviation, or dimensionless, for a coefficient of variation or a sample size.

The report links the unit definition where the units name one.

- `1520307` (error): The value of the attribute 'distrib:units' on an &lt;uncertParameter&gt; must have a taken from the following: the identifier of a &lt;unitDefinition&gt; object in the enclosing &lt;model,&gt; or one of the base units in SBML.

<span id="definitionurl"></span>**definitionURL**

A parameter of the type `distribution` may name the distribution it stands for, and a parameter of the type `externalParameter` has to name what it is: an entry of an ontology such as ProbOnto, the `csymbol` of a distribution of this package, or another definition which says what the number means. No other type of parameter carries it, because the specification defines the others completely.

The report shows the last segment of the url as a link in the table of the parameters of an uncertainty.

Default: the type of the measure says completely what it means.

- `1520309` (error): The attribute 'distrib:definitionURL' on an &lt;uncertParameter&gt; must have a value of data type 'string'.

<span id="math"></span>**math**

Only a parameter of the type `distribution` or `externalParameter` carries math, and for a distribution the formula is the distribution itself, usually one of the `csymbol` distributions the package defines, such as `normal(2, 2)`.

The report renders the formula and links every element it names, from the parameter which carries the math and not from the uncertainty around it, so that two parameters of one uncertainty stay apart.

Default: a distribution is defined by its definition url and the parameters below it.

<span id="uncertparameters"></span>**uncertParameters**

A distribution is defined by the parameters it takes: a Beta distribution by its alpha and its beta, a zeta distribution by its shape. They are uncert parameters of the parameter which names the distribution, of any type and to any depth, and without them a report shows the name of a distribution and none of its numbers.

The report shows every one of them indented below the parameter it defines, in the table of the measures of the uncertainty and in the inspector of that parameter.

- `1520304` (error): An &lt;uncertParameter&gt; object may contain one and only one instance of the &lt;listOfUncertParameters&gt; element. No other elements from the SBML Level 3 Distributions namespaces are permitted on an &lt;uncertParameter&gt; object.
- `1520310` (error): Apart from the general notes and annotations subobjects permitted on all SBML objects, a &lt;listOfUncertParameters&gt; container object may only contain &lt;uncertParameter&gt; objects.

## Validation rules

- `1520301` (error): An &lt;uncertParameter&gt; object may have the optional SBML Level 3 Core attributes 'metaid' and 'sboTerm'. No other attributes from the SBML Level 3 Core namespaces are permitted on an &lt;uncertParameter&gt;.
- `1520302` (error): An &lt;uncertParameter&gt; object may have the optional SBML Level 3 Core subobjects for notes and annotations. No other elements from the SBML Level 3 Core namespaces are permitted on an &lt;uncertParameter&gt;.
- `1520303` (error): An &lt;uncertParameter&gt; object may have the optional attributes 'distrib:value', 'distrib:var', 'distrib:units', 'distrib:type' and 'distrib:definitionURL'. No other attributes from the SBML Level 3 Distributions namespaces are permitted on an &lt;uncertParameter&gt; object.
- `1520304` (error): An &lt;uncertParameter&gt; object may contain one and only one instance of the &lt;listOfUncertParameters&gt; element. No other elements from the SBML Level 3 Distributions namespaces are permitted on an &lt;uncertParameter&gt; object.

## Related elements

- [Uncertainty](uncertainty.md): a set of statistical measures of the value of an element
- [UncertSpan](uncertspan.md): a measure of an uncertainty which is an interval
- [Parameter](parameter.md): a named value which the mathematics of the model can use
- [Distributions (distrib)](distrib.md): the package which records the uncertainty of a value

## Specification

[The Distributions Package for SBML Level 3, Version 1 Release 1](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf), Section 3.11 (Smith et al. 2020, J Integr Bioinform 17(2-3):20200018).
