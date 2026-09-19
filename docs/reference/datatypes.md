# Data types

A data type is the kind of value an attribute or a field the report adds carries, for example a number, an identifier or a fragment of markup. The `type` column of every other page of the reference links here.

## `string` {#string}

A sequence of characters with no further restriction.

The XML Schema type `string` holds any finite sequence of characters, every character of Unicode except the two delimiters 0xFFFE and 0xFFFF, and the only further rules are those of XML itself: an ampersand is written `&amp;`, and an apostrophe or a quotation mark which would end the value is written `&apos;` or `&quot;`. Nothing else is asked of it and nothing references it: a string is read by a person, not by the model. The [name](sbase.md#name) of an element is the string every type carries.

The report shows a string as the text the file writes and a dash where the file writes nothing. Several of the fields the report adds are strings as well, the [equation](concepts.md#equation) of a reaction or the XML of an element, and the entry of the field says what they hold.

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 3.1.1.

## `boolean` {#boolean}

A flag which is either true or false.

The XML Schema type `boolean` is the type of the flags of SBML: whether a species is [constant](species.md#constant), whether a reaction is [reversible](reaction.md#reversible), whether an event uses the values of the moment its trigger fired. An attribute writes `true` or `false`, and `1` and `0` are legal spellings of the same two values. In a MathML formula they are not: there `0` and `1` are numbers, and a Boolean value is the element `<true/>` or `<false/>`.

A flag the file leaves out is not the same as a flag set to false, and what an absent flag means is written in the entry of the attribute. The report keeps the two apart: a true flag is a check mark, a false flag a cross, and an attribute the file does not set the dash every empty value of the report shows.

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 3.1.2.

## `integer` {#integer}

A whole number.

Decimal digits with an optional leading sign and nothing after them. The core specification calls this type `int` and holds it to the range of a signed 32 bit number, from -2147483648 to 2147483647; a package may narrow it where it uses a whole number, as the qual package does for the initial level of a [qualitative species](qualitativespecies.md) and for the result level of a [function term](functionterm.md), which its specification writes as a non-negative `int`. A whole number is exact and, unlike a [double](#double), carries neither a fractional part nor an exponent, which is what makes it the type of a count and of a level.

The report shows a whole number as the file writes it, and what the report counts itself, the number of elements of a [list](listof.md), is a whole number as well.

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 3.1.3.

## `positiveInteger` {#positiveinteger}

A whole number greater than zero.

The XML Schema type `positiveInteger` holds 1, 2, 3 and so on, decimal digits with an optional leading plus, and neither zero nor a negative value. XML Schema sets no upper bound on it, but SBML uses the type only where the numbers are small: the [level](sbmldocument.md#level) and the [version](sbmldocument.md#version) of a file, which say which edition of the language the file is written in, are of this type.

The report shows both in the attributes of the document, which is where reading an unfamiliar file starts.

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 3.1.4.

## `double` {#double}

A floating point number, which may be infinite or not a number.

The XML Schema type `double` is the type of every numerical quantity of SBML: the size of a compartment, the initial amount of a species, the value of a parameter, the stoichiometry of a reactant. It is an IEEE 754 double precision number written as a mantissa with an optional exponent, `2`, `-0.3`, `234.234e3`, `6.02E-23`. Its value space holds three values which are no ordinary number: positive infinity, negative infinity and the value which is not a number, written `INF`, `-INF` and `NaN`.

These three are values like any other and say something a reader has to see: the upper flux bound of an unbounded reaction is `INF`, and a `NaN` is a quantity which is declared but whose number is not known. None of them is what an attribute the file leaves out means. The report shows a number with six significant digits and the unrounded value as its tooltip, an infinite value as the sign of infinity with its direction and a `NaN` as itself; [number](concepts.md#number) describes the three of them.

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 3.1.5.

## `ID` {#id}

An identifier which is unique in the whole file.

`ID` is the identifier type of XML 1.0, which SBML takes over unchanged: `ID ::= ( letter | '_' | ':' ) NameChar*`, where a `NameChar` is a letter, a digit, `.`, `-`, `_`, `:`, a combining character or an extender, and where a letter is one of the upper and lower case letters of the Latin alphabet together with the many related characters Unicode 2.0 defines. Every value of this type lives in one namespace which spans the whole document, whatever element carries it and however deeply that element is nested, so no two elements of a file may carry the same one.

The [metaid](sbase.md#metaid) of an element is the only attribute of the core with this type, and the RDF of an [annotation](sbase.md#annotations) names the element it describes by it. A meta id which is used twice makes the file invalid, and an annotation which names a meta id no element carries describes nothing. The report shows the meta id in the attributes of the inspector and falls back to it to name an element which has no id.

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 3.1.6.

## `SId` {#sid}

The identifier of an element inside a model.

The type of the [id](sbase.md#id) every element may carry: `SId ::= ( letter | '_' ) idChar*`, where an `idChar` is a letter, a digit or an underscore. The letters are the plain Latin ones, `a` to `z` and `A` to `Z`, so an identifier holds no accent, no space and no dot, and two identifiers are equal only when they match character by character: `S1` and `s1` are two different elements.

An identifier is unique within one model and not within the file, so a reaction and a species of one model cannot share one, while two models of a file may each have a species `S1`. Two further spaces of identifiers sit next to this one: the units of a model, whose identifiers are compared only against each other and against the base units of SBML and which are named by a [UnitSIdRef](#unitsidref), and the local parameters of a reaction, whose identifiers are private to that reaction and hide an identifier of the model inside its kinetic law. A package may narrow a space further, as the comp package does for its ports, whose identifiers have to be unique only among the ports of their model.

The report shows the id in the first column of every table, uses it as the label of every link to the element, and builds the [primary key](concepts.md#primary-key) of the element from it.

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 3.1.7.

## `SIdRef` {#sidref}

A reference to an element of the same model by its identifier.

An attribute of type `SIdRef` holds the [SId](#sid) of an element of the model it is written in: the compartment of a species names a compartment, the variable of a rule names the element the rule computes, the conversion factor of a species names a parameter. Which kind of element a given attribute may name is no part of the type but of the attribute, and the entry of the attribute says it. A package may widen where the value is looked up: the references of the comp package which reach into a submodel name an identifier of that submodel and not of the model they are written in, the model reference of a submodel names a model of the document it is written in, and the model reference of an external model definition a model of the document at its source. The value is compared character by character like an identifier, and it has to exist where it is looked up: a reference which ends nowhere is a dangling reference, which makes the file invalid and leaves a simulation without a quantity it needs.

The report resolves every reference of a model against the elements of that model and shows a resolved one as a link to the element it names, while the element at the other end lists the reference under "Referenced by", so that a reference can be followed in both directions. A reference the report cannot resolve stays the text the file writes, without a link.

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 3.1.8.

## `UnitSIdRef` {#unitsidref}

A reference to a unit by its identifier.

The identifiers of units live in a space of their own: the id of a [unit definition](unitdefinition.md) is of the type `UnitSId`, which has the syntax of an [SId](#sid) but is compared only against the other unit identifiers of the model and against the base unit names SBML reserves, `mole`, `litre`, `second`, `kilogram` and the other base units of Table 2 of the specification. An attribute of type `UnitSIdRef`, the units of a compartment, of a parameter or of a species, must name one of the two, a unit definition of the model or a base unit, and anything else is a dangling reference. Because the space is separate from the identifiers of the model, a parameter `volume` and a unit definition `volume` can exist side by side.

The report links a value which names a unit definition to that definition and renders the unit next to the identifier as a formula, the [rendered units](concepts.md#rendered-units); a base unit is no element of the model, so it stays text and only its rendering is added. The units an element ends up with, declared here or inherited from the model, are the [derived units](concepts.md#derived-units) the report computes on top of this.

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 3.1.10.

## `SBOTerm` {#sboterm}

The identifier of a term of the Systems Biology Ontology.

The pattern is fixed: `SBO:` followed by exactly seven digits, for example `SBO:0000014`. The value names a term of the Systems Biology Ontology, a controlled vocabulary of the entities, the roles, the processes and the modelling frameworks a model is built from, and it states in that vocabulary what the class of an element alone does not: that a modifier is a catalyst, that a kinetic law is Michaelis-Menten kinetics, that a parameter is a Michaelis constant. Section 5 of the specification describes how the terms are meant to be used.

The report shows the term in the attributes of the inspector and links it to its page at identifiers.org, where the label and the definition of the term are read.

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 3.1.12.

## `XHTML` {#xhtml}

A fragment of markup written for human readers.

The [notes](sbase.md#notes) of an element and the [message](constraint.md#message) of a constraint hold XHTML 1.0 in the namespace `http://www.w3.org/1999/xhtml`, which is declared either on the content itself, `<body xmlns="http://www.w3.org/1999/xhtml">`, or with a prefix on the `sbml` element of the file. The specification asks for no particular element, any well formed XHTML content is allowed, with the single restriction that it carries neither an XML declaration nor a DOCTYPE. This is where the documentation of a published model is written: paragraphs, headings, tables, links to the paper it comes from.

The report renders the markup which notes really use, among it paragraphs, lists, tables, images and links, and drops everything else, so that nothing a file brings with it can act on the page.

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 3.2.5.

## `Math` {#math}

A formula of the model in the two renderings the report gives it.

SBML writes every formula as content MathML, which is exact and unreadable. The report converts each formula once and keeps two renderings of it: the latex which the page typesets the way a textbook prints a formula, and the same expression in the infix notation of Level 3, `k1 * S1 - k2 * S2`, which is one line of text and can be copied into another tool.

Every formula the report shows is of this kind: the kinetic law of a reaction, the formula of a function definition, of an initial assignment, of a rule, of a constraint and of an event assignment, the trigger, the delay and the priority of an event, the condition of a function term of the qual package and the math of a parameter of an uncertainty of the distrib package. A table and the inspector show the typeset formula, the infix formula is its tooltip and what a click copies, and a formula too long to typeset stays text, which the inspector offers to render on demand where it shows the formula on a line of its own, while a table leaves it as it is. [Rendered math](concepts.md#rendered-math) describes this, and every element a formula names becomes a link of the kind [math](links.md#math).

## `ModelHistory` {#modelhistory}

Who created an element and when it was changed.

The standard annotation of an element may carry its history, written in RDF: the terms of Dublin Core name the creators of the element, the date it was created and one date for every time it was changed, and inside a creator the name, the organisation and the electronic mail address are written with the terms of vCard. The report reads that block out of the annotation and keeps it as one value of the element, instead of leaving it in the XML for a reader to decipher.

Most files carry a history on the model alone, where it is the closest thing a model has to an author line. The report shows the creators with their organisation and their address, the date of creation and every date of modification, below the annotations in the inspector of the element.

## `latex` {#latex}

Units the report has rendered as a formula.

A field of this kind holds the latex of a unit which the page typesets with KaTeX: the units an element declares, resolved from the unit definition it names ([rendered units](concepts.md#rendered-units)), and the units the report derives for an element or for a formula ([derived units](concepts.md#derived-units)). Both are a product of base units with their exponent, so that millimole over litre is shown as that fraction and not as the identifier `mmol_per_l` a file happens to give it.

A dash stands where a model declares no units and where the report cannot derive any. A units attribute which names `dimensionless` shows its identifier alone, because a quantity without a dimension has no symbol which is shorter than the word.

## `list` {#list}

A field which holds as many values as the element has.

A field of this kind holds every value of an attribute which is not a single one, in the order the file writes them: the species of a model, the reactants of a reaction, the units of a unit definition, the annotations of any element. What the entries are is what the entry of the field says.

Where they are shown depends on the field: the elements of a list of the model are the rows of the table of their type, the elements a list of an element holds are a table in the inspector of that element, and a list without entries is the dash of an empty value. The `listOf` element of the file is not part of what such a field holds: where it states something of its own, a meta id, an SBO term, notes, an annotation, an id or a name, the report keeps it as a [ListOf](listof.md) element of its own, which the element owning the list points at.
