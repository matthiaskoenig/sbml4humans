# Report concepts

A report shows more than the model file contains: it resolves references, derives units, renders the math and names every element. These are the fields the report computes.

## primary key

The identifier the report gives to every element it shows.

SBML identifies an element by its id, which is unique within one model, and many elements of a model have no id at all. The report therefore builds a key of its own for every element, of the form `<scope>/<type>:<id>`: the scope, which is the model the element belongs to or the document for an element of the document, the type of the element and its id. An element without an id falls back to its meta id, then to a key derived from its parent and its position, and finally to a digest of its XML, so that two reactants of one reaction without ids stay distinct.

The primary key is what the links of a report point at, what the url of a report names when an element is selected and what the inspector shows when an element has neither an id nor a meta id.

## sbml type

The kind of element, which decides how the report shows it.

Every element of a report carries the name of its SBML class, for example `Species`, `AssignmentRule` or `Objective`. The report groups the elements of a model by it, and it decides the section of the report, the colour and the icon of the type mark, the columns of the table and the attributes the inspector shows.

The type is shown as the mark in front of every element, as the header of every section of the report and in the header of the inspector.

## derived units

The units of a quantity or of a formula as they follow from the model.

A model does not have to declare units everywhere: a compartment, a species or a parameter inherits the units of the model when it declares none, and the units of a formula follow from the units of the elements it uses. The report derives the units which follow from the model, reduces them to base units with their exponent, scale and multiplier, and renders the result as a formula.

Derived units are shown in the column "derived units" of the tables and in the inspector. They are the fastest check whether a kinetic law is dimensionally what it should be, because the derived units of a kinetic law are amount per time when the law is right.

## equation

The reaction written as a chemical equation.

The report writes every reaction as its reactants, an arrow and its products, with the stoichiometry in front of a species when it is not one and the identifier of the species reference when the stoichiometry is set by a rule instead of by a number. The arrow is a double arrow when the reaction is reversible and a single arrow when it is not.

The equation is a column of the table of reactions and a row of the inspector of a reaction, and it is what makes a list of reactions readable without opening any of them.

## rendered math

The formula of an element as the report renders it.

SBML stores a formula as content MathML, which is precise and unreadable. The report turns it into the typeset formula a textbook would print, with fractions, powers, subscripts for the parts of a name and greek letters where a name is one, and keeps the same expression as an infix formula next to it, so that it can be read and copied as text.

The rendered formula is the column "math" of the tables of rules, function definitions, constraints and events, the kinetic law of a reaction, and the mathematics shown in the inspector. Where a formula names an element of the model, the report also links that element as a link of the kind "math".

## rendered units

The units an element declares, rendered as a formula.

A units attribute names a unit definition, and a unit definition is a list of base units with an exponent, a scale and a multiplier. The report resolves the reference and renders the product as a formula, so that a table shows millimole over litre as a fraction instead of the identifier `mmol_per_l`, next to the identifier it comes from.

The rendered units appear in the units columns of the tables, in the units of the inspector and as the whole content of the table of unit definitions.

## model kind

Whether a model is the model of the document or a model definition.

A document contains at most one model, but the comp package adds model definitions, which exist to be instantiated by a submodel and are not simulated themselves. The report reads both and marks every model as `model` or `modelDefinition`.

The kind is shown in the attributes of a model. The report opens the model of the document first and lets the model definitions be selected next to it.

## manifest

The entries of the COMBINE archive a report was built from.

A COMBINE archive holds the files of a modelling study with a manifest which names every entry, its format and whether it is a master file. The report is built for every SBML entry of the archive, and a plain SBML file which is submitted on its own is wrapped in an archive with one master entry, so that a report always comes with a manifest.

The manifest decides which report is shown first, the master entry, and is what the report offers when an archive holds more than one model.
