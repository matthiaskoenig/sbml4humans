# SBML4Humans

[![CI/CD](https://github.com/matthiaskoenig/sbml4humans/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/matthiaskoenig/sbml4humans/actions/workflows/ci-cd.yml)
[![PyPI version](https://img.shields.io/pypi/v/sbml4humans.svg)](https://pypi.org/project/sbml4humans/)
[![Python versions](https://img.shields.io/pypi/pyversions/sbml4humans.svg)](https://pypi.org/project/sbml4humans/)
[![Documentation](https://img.shields.io/badge/docs-sbml4humans-008080.svg)](https://matthiaskoenig.github.io/sbml4humans/)
[![MIT License](https://img.shields.io/github/license/matthiaskoenig/sbml4humans.svg)](https://opensource.org/license/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22827237.svg)](https://doi.org/10.5281/zenodo.22827237)

[SBML4Humans](https://sbml4humans.de) renders [SBML](sbml.md) models as interactive, human readable reports. Give it a model and it gives you a page which shows what the model contains: its compartments, species, reactions, rules and events, the mathematics of the model as typeset formulas, the units it computes from the file, the references between the elements, and the annotations resolved to the entries they point at. It reads SBML of every level and version libsbml reads, and the four Level 3 packages [comp](reference/comp.md), [fbc](reference/fbc.md), [qual](reference/qual.md) and [distrib](reference/distrib.md), so a hierarchical model, a genome scale reconstruction, a logical model and a model whose values carry their uncertainty are shown with everything the package adds to them.

[![The report of the repressilator model, with the type bar, the element tables and the inspector of a selected species](images/report-overview.png)](images/report-overview.png)

## Why it exists

[SBML](sbml.md) is the de facto standard for the representation and exchange of mathematical models of biological systems, from a single process to a multi-scale model, and it is read and written by a large ecosystem of [software](https://sbml.org/software/). Its information is organized as lists of components, such as compartments, species, parameters and reactions, written in XML.

XML is written for programs. A model file states everything and shows nothing: the mathematics is content MathML, a unit is a product of base units spread over several elements, a species is a line of attributes among thousands of other lines, and an annotation is a URI in an RDF block. Reading a model in a text editor means reassembling it in your head, and a model of a genome scale reconstruction cannot be read that way at all. Tools are needed which provide an abstraction layer to interact with the SBML objects and the relationships between them.

SBML4Humans provides that layer: an interactive and reactive report which allows humans, experts as well as novices, to comprehend the content of a model. It is the view of a model which the file itself does not give you. It does not edit models and it does not simulate them, it reads them.

It is written for the people who have to read models rather than write them:

- modellers who open a model they did not build, or their own model after a year, and need to know what is in it
- reviewers and curators who check whether a model is annotated, whether its units are consistent and whether it says what the paper says
- students and lecturers who learn what SBML is, because the report explains its types, the columns of its tables and the attributes of its inspector where it shows them

## What a report shows

A report is one page per model. The bar at the top lists every element type the model uses with the number of elements of that type, the tables under it show the elements of each type with the columns which matter for that type, and the inspector at the right shows one element in full: its attributes, everything it references and everything which references it, its notes, its annotations and its history, and the raw XML when that is what you need. Every column header of an element table, every attribute label of the inspector, every mark of a type and every group of links carries a one sentence explanation on hover, and the type in the header of the inspector links its page in the reference.

The report carries the data model of the file rather than a summary of it. The objects a file nests inside another are elements of the report like the species and the reactions, each with a page of its own in the [reference](reference/index.md): the trigger, the priority and the delay of an event, the participation of a species in a reaction, the deletions and replacements of a hierarchical model, the tree of genes a reaction needs, the terms of a transition and the measures of an uncertainty. A reference between two elements is a link a reader follows in both directions, from the element which states it to the element it names and back.

[Reading a report](report.md) walks through all of it.

## Where to start

Open [sbml4humans.de](https://sbml4humans.de) and give it a model. There are three ways to do that, and an [examples](inputs.md#the-examples) page with models which are already there:

- upload an SBML file or a COMBINE archive from your computer
- give the url of a model, for example of an entry of BioModels
- paste the content of an SBML file

[Loading a model](inputs.md) explains the inputs, the formats which are accepted and what happens when a file cannot be read.

If a term of a report is unfamiliar, the [reference](reference/index.md) explains it: one page per element type with every attribute the report shows, the kinds of links between the elements, and what the report computes on top of the model. [SBML](sbml.md) is the background: what the format is, how a model is built from its elements, and what the Level 3 packages add.

## How to cite

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22827237.svg)](https://doi.org/10.5281/zenodo.22827237)

If you use SBML4Humans please cite the archived software on [Zenodo](https://doi.org/10.5281/zenodo.22827237):

> König, M., & Das, S. (2026). *SBML4Humans: interactive reports of SBML models* (Version 0.5.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.22841376

```bibtex
@software{koenig_sbml4humans,
  author    = {König, Matthias and Das, Sankha},
  title     = {SBML4Humans: interactive reports of SBML models},
  year      = {2026},
  month     = sep,
  version   = {0.5.0},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.22841376},
  url       = {https://doi.org/10.5281/zenodo.22841376},
}
```

## Funding and license

SBML4Humans is developed at [github.com/matthiaskoenig/sbml4humans](https://github.com/matthiaskoenig/sbml4humans). Its first version was written in 2021 by Sankha Das as the project "Interactive SBML report for Humans", mentored by Matthias König and Ralf Steuer, with the [National Resource for Network Biology](https://nrnb.org/) (NRNB) as the mentoring organisation and funded by [Google Summer of Code 2021](https://summerofcode.withgoogle.com/).

Matthias König is supported by the Federal Ministry of Education and Research (BMBF, Germany) within the research network Systems Medicine of the Liver ([LiSyM](https://lisym.org/), grant number 031L0054) and by the German Research Foundation (DFG) within the Research Unit Programme FOR 5151 "[QuaLiPerF](https://qualiperf.de) (Quantifying Liver Perfusion-Function Relationship in Complex Resection - A Systems Medicine Approach)" by grant number 436883643.

The source code is under the [MIT](https://opensource.org/license/MIT) license, this documentation under [CC BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/).

The sources this documentation is written from are listed under [References](references.md).
