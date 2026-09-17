# Uncertainty

A set of statistical measures of the value of an element.

An uncertainty collects the measures which belong together, for example the mean and the standard deviation of one experiment. Every measure appears at most once in it, so measures from another source belong into another uncertainty of the same element.

The measures do not affect a simulation. They say where a number comes from and how well it is known, which is what a reader of a published model wants to see and what a sampling of the parameters of a model needs.

The report shows every uncertainty as an element of its own, with the table of its parameters, and lists the uncertainties of an element in its inspector.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| uncert parameters | `list` | <span id="uncert-parameters"></span>the statistical measures which make up the uncertainty | [Section 3.11](https://sbml.org/documents/specifications/level-3/version-1/distrib/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## Related elements

- [Parameter](parameter.md): a named value which the mathematics of the model can use
- [Species](species.md): a pool of a chemical entity in a compartment
- [Distributions (distrib)](distrib.md): the package which records the uncertainty of a value

## Specification

[SBML Level 3 Package: Distributions (distrib)](https://sbml.org/documents/specifications/level-3/version-1/distrib/), Section 3.10 (Smith et al. 2020, Version 1 Release 1).
