# Report concepts

A report shows more than the model file contains: it resolves references, derives units, renders the math and names every element. These are the fields the report computes.

## primary key

The identifier the report gives to every element it shows.

SBML identifies an element by its id, which is unique within one model, and many elements of a model have no id at all. The report therefore builds a key of its own for every element, of the form `<scope>/<type>:<id>`: the scope, which is the model the element belongs to or the document for an element of the document, the type of the element and its id. An element without an id falls back to the element it sets, for an [initial assignment](initialassignment.md) or a rule, then to its meta id, and then to a key of what it is about: an element nested in another one is keyed after its parent and what it names, a reactant after its reaction and its species (`Reaction1.reactant.X`), a replacement after its element, its submodel and the element it reaches, a measure of an uncertainty after its type (`u_Km.standardDeviation`), and an element which names nothing, an algebraic rule, a constraint, an event or a transition, after its place among the elements of its type (`algebraicRule.0`). Where a list repeats such a key, a species which a reaction lists twice among its reactants, the repetition is told apart by its occurrence (`Reaction1.reactant.X.1`). The model of a document without an id is scoped as `model`, and only an element which the specification requires an id of, and which the file leaves without one, is keyed by a digest of its XML.

The primary key is what the links of a report point at and what the url of a report names when an element is selected. An element without an id is shown by the key alone, without the scope and the type in front of it, in the header of the inspector and as the label of every link to it. An element which the file nests in another one is named after that element and its place in it instead, because a meta id says nothing about where it sits: the kinetic law of `Reaction1` reads `Reaction1.kineticLaw`, the trigger of the event `Start` reads `Start.trigger`, an assignment of that event to `kp` reads `Start.kp` and a reactant `X` of `Reaction1` reads `Reaction1.X`.

## sbml type

The kind of element, which decides how the report shows it.

Every element of a report carries the name of its SBML class, for example `Species`, `AssignmentRule` or `Objective`. The report groups the elements of a model by it, and it decides the section of the report, the colour and the icon of the type mark, the columns of the table and the attributes the inspector shows.

The type is shown as the mark in front of every element, as the header of every section of the report and in the header of the inspector.

## derived units

The units of a quantity or of a formula as they follow from the model.

A model does not have to declare units everywhere: a compartment, a species or a parameter inherits the units of the model when it declares none, and the units of a formula follow from the units of the elements it uses. The report derives the units which follow from the model, reduces them to base units with their exponent, scale and multiplier, and renders the result as a formula.

Derived units are shown in the column "derived units" of the tables and in the inspector. They are the fastest check whether a kinetic law is dimensionally what it should be, because the derived units of a kinetic law are extent per time when the law is right.

## number

How the report shows a number which is infinite or not a number.

A double of SBML may be infinite or not a number, `INF`, `-INF` and `NaN` as a file writes them, and both are ordinary values: the upper bound of an unbounded flux is `INF`, and a `NaN` says that a quantity is defined but its number is not known. JSON has no literal for either of them, so the report sends them as the three constants `"Infinity"`, `"-Infinity"` and `"NaN"`, which keeps them apart from `null`, the attribute a file does not set at all.

The report shows an infinite value as the sign of infinity with the direction of its bound, ∞ and -∞, with the `INF` or `-INF` of the file as its tooltip, and a value which is not a number as `NaN`. An attribute which is not set stays the dash every empty cell of the report shows. Every other number is shown with six significant digits, and the full number is the tooltip of the rounded one.

## equation

The reaction written as a chemical equation.

The report writes every reaction as its reactants, an arrow and its products, with the stoichiometry in front of a species when it is not one, a minus in front of it when the stoichiometry is minus one, and the identifier of the species reference, or a question mark, when the stoichiometry is set by a rule instead of by a number. The arrow is a double arrow when the reaction is reversible and a single arrow when it is not.

The equation is a column of the table of reactions and a row of the inspector of a reaction, and it is what makes a list of reactions readable without opening any of them.

## rendered math

The formula of an element as the report renders it.

SBML stores a formula as content MathML, which is precise and unreadable. The report turns it into the typeset formula a textbook would print, with fractions, powers, subscripts for the parts of a name and greek letters where a name is one, and keeps the same expression as an infix formula next to it, so that it can be read and copied as text.

The rendered formula is the column "math" of the tables of rules, function definitions, constraints and events, the kinetic law of a reaction, and the mathematics shown in the inspector. Where a formula names an element of the model, the report also links that element as a link of the kind "math".

## rendered units

The units an element declares, rendered as a formula.

A units attribute names a unit definition, and a unit definition is a list of base units with an exponent, a scale and a multiplier. The report resolves the reference and renders the product as a formula, so that a table shows millimole over litre as a fraction instead of the identifier `mmol_per_l`, next to the identifier it comes from.

The rendered units appear in the units columns of the tables, in the units of the inspector and in the units column of the table of unit definitions, whose inspector shows them as the formula above the units the definition is built from.

## model kind

Whether a model is the model of the document or a model definition.

A document contains at most one model, but the comp package adds model definitions, which exist to be instantiated by a submodel and are not simulated themselves. The report reads both and marks every model as `model` or `modelDefinition`.

The kind is shown in the attributes of a model. The report opens the model of the document first and lets the model definitions be selected next to it.

## manifest

The entries of the COMBINE archive a report was built from.

A COMBINE archive holds the files of a modelling study with a manifest which names every entry, its format and whether it is a master file. The report is built for every SBML entry of the archive, and a plain SBML file which is submitted on its own is wrapped in an archive with one master entry, so that a report always comes with a manifest.

The manifest decides which report is shown first: the master entry when that entry has a report, and the first entry otherwise, because an archive does not have to mark one. It is also what the report offers when an archive holds more than one model.
