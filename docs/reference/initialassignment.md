# Initial assignment

A formula which computes the value of an element at the start of the simulation.

An initial assignment computes the value of a compartment, a species, a parameter or a stoichiometry before the simulation starts, from the values of other elements. It exists because the attributes of an element can only hold a literal number, and an initial value is often derived from other quantities. It applies up to the start of time and, unlike an assignment rule, it may also set a constant.

The report shows the element which is assigned, the rendered formula and the units the formula produces.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [symbol](#symbol) | `SIdRef` | the element whose initial value the assignment computes | [core 4.8.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [math](#math) | `Math` | the formula which computes the initial value | [core 4.8.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="symbol"></span>**symbol**

The symbol names the compartment, species, species reference or parameter which receives the value. It is called symbol rather than variable because an initial assignment may also set an element which is constant.

The report links the named element in the column "symbol" and in the inspector.

<span id="math"></span>**math**

The math is an arbitrary expression over the elements of the model. Its units should be the units of the element it assigns to.

The report renders the formula in the column "math" and in the inspector.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [derived units](#derived-units) | `latex` | the units of the formula as the report derives them |

<span id="derived-units"></span>**derived units**

The report derives the units of the formula from the units of the quantities it uses and renders them as a formula. Comparing them with the units of the assigned element is the quickest check of an initial assignment.

## Related elements

- [Assignment rule](assignmentrule.md): a formula which holds at every moment of the simulation
- [Parameter](parameter.md): a named value which the mathematics of the model can use
- [Species](species.md): a pool of a chemical entity in a compartment
- [Compartment](compartment.md): a bounded space in which species are located

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.8 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
