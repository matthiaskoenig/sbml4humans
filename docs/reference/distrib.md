# Distributions (distrib)

The package which records the uncertainty of a value.

The distrib package attaches statistical measures to the elements of a model which have a mathematical meaning: a mean, a standard deviation, a variance, a confidence interval or the distribution a value was drawn from. The measures describe the value at the moment it is computed, not how it changes during a simulation.

They do not affect the mathematics of the model. They are a controlled format for the provenance of a number, which a modeller would otherwise write into the notes of an element, and a tool may use them as it uses any other annotation.

The report shows the [uncertainties](uncertainty.md) of an element in its inspector and every uncertainty as an element of its own.

## Validation rules

- `1510101` (error): To conform to the Distributions Package specification for SBML Level 3 Version 1, an SBML document must declare 'http://www.sbml.org/sbml/level3/version1/distrib/version1' as the XMLNamespace to use for elements of this package.
- `1510102` (error): Wherever they appear in an SBML document, elements and attributes from the Distributions Package must use the 'http://www.sbml.org/sbml/level3/version1/distrib/version1' namespace, declaring so either explicitly or implicitly.
- `1520101` (error): In all SBML documents using the Distributions Package, the &lt;sbml&gt; object must have the 'distrib:required' attribute.
- `1520102` (error): The value of attribute 'distrib:required' on the &lt;sbml&gt; object must be of data type 'boolean'.
- `1520103` (error): The value of attribute 'distrib:required' on the &lt;sbml&gt; object must be set to 'true'.

## Related elements

- [Uncertainty](uncertainty.md): a set of statistical measures of the value of an element
- [Parameter](parameter.md): a named value which the mathematics of the model can use
- [Species](species.md): a pool of a chemical entity in a compartment

## Specification

[The Distributions Package for SBML Level 3, Version 1 Release 1](https://sbml.org/specifications/sbml-level-3/version-1/distrib/version-1/release-1/sbml-level-3-version-1-distrib-version-1-release-1.pdf) (Smith et al. 2020, J Integr Bioinform 17(2-3):20200018).
