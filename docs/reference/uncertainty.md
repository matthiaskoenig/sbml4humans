# Uncertainty

A set of statistical measures of the value of an element.

An uncertainty collects the measures which belong together, for example the mean and the standard deviation of one experiment. Every measure appears at most once in it, so measures from another source belong into another uncertainty of the same element.

The measures do not affect a simulation. They say where a number comes from and how well it is known, which is what a reader of a published model wants to see and what a sampling of the parameters of a model needs.

The report shows every uncertainty as an element of its own, with the table of its parameters, and lists the uncertainties of an element in its inspector.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [uncert parameters](#uncert-parameters) | `list` | the statistical measures which make up the uncertainty | [distrib 3.11](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="uncert-parameters"></span>**uncert parameters**

Every parameter names the statistic it describes, for example `mean`, `standardDeviation`, `variance`, `sampleSize`, a span such as `confidenceInterval` or `range`, or the `distribution` the value was drawn from. It gives the statistic either as a number in its value, or as a reference to an element of the model in its variable, and it may carry its own units. A parameter of the type `distribution` carries the math of the distribution or a definition url instead of a value; a parameter of the type `externalParameter` has to carry a definition url and may use everything else next to it, a value, a span, math or parameters of its own.

The report shows every parameter of an uncertainty as a row of the table in the inspector of that uncertainty, with its value or the interval of a span, its units, its definition and its math, and links every parameter to the element it is, where its notes say where the measurement comes from.

## Related elements

- [Parameter](parameter.md): a named value which the mathematics of the model can use
- [Species](species.md): a pool of a chemical entity in a compartment
- [Distributions (distrib)](distrib.md): the package which records the uncertainty of a value

## Specification

[The Distributions Package for SBML Level 3, Version 1 Release 1](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf), Section 3.10 (Smith et al. 2020, J Integr Bioinform 17(2-3):20200018).
