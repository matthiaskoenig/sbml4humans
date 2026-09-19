"""Tests of the report information of a document."""

import json

import libsbml
import pytest

from sbml4humans.model import (
    And,
    EdgeKind,
    GeneProductRef,
    Model,
    Or,
    Parameter,
    Reaction,
    Report,
    UncertSpan,
)
from sbml4humans.resources import (
    COMP_ICG_BODY,
    EXAMPLES_DIR,
    FBC_ECOLI_CORE_SBML,
    REPRESSILATOR_SBML,
)
from sbml4humans.sbml import read_sbml
from sbml4humans.sbmlinfo import SBMLDocumentInfo
from sbml4humans.units import udef_to_string


@pytest.fixture(scope="module")
def repressilator() -> Report:
    """The report of the repressilator."""
    return SBMLDocumentInfo.from_sbml(REPRESSILATOR_SBML)


@pytest.fixture(scope="module")
def constraint_event() -> Report:
    """The report of the constraint, event and local parameter example."""
    return SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "constraint_event.xml")


@pytest.fixture(scope="module")
def comp_deletion() -> Report:
    """The report of the deletion and replacement example of comp."""
    return SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "comp_deletion.xml")


@pytest.fixture(scope="module")
def distrib_spans() -> Report:
    """The report of the example of the spans and distributions of distrib."""
    return SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "distrib_spans.xml")


def _parameter(report: Report, sid: str) -> Parameter:
    """The parameter of the first model of the report with the id."""
    return next(p for p in report.models[0].list_of_parameters if p.id == sid)


def test_document(repressilator: Report) -> None:
    """The document carries level, version and its pk."""
    doc = repressilator.document
    assert doc.pk == "document/SBMLDocument:document"
    assert (doc.level, doc.version) == (2, 3)
    assert doc.xml is None


def test_packages_of_a_document() -> None:
    """A document lists the Level 3 packages it declares, with their versions."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "qual_example.xml")
    assert [(p.prefix, p.version) for p in report.document.packages] == [("qual", 1)]


@pytest.mark.parametrize("core_prefix", [None, "sbml"])
def test_core_namespace_is_no_package(core_prefix: str | None) -> None:
    """The core namespace of a Level 3 Version 2 document is not a package.

    libsbml implements the math of Level 3 Version 2 as a plugin of the
    document which carries the namespace of core, with the prefix the file
    gives that namespace: none on a root which declares it as the default, and
    a prefix of its own where the root declares it once more. Neither is a
    package the file uses.
    """
    text = (EXAMPLES_DIR / "constraint_event.xml").read_text(encoding="utf-8")
    if core_prefix is not None:
        core = "http://www.sbml.org/sbml/level3/version2/core"
        text = text.replace("<sbml ", f'<sbml xmlns:{core_prefix}="{core}" ', 1)
    doc: libsbml.SBMLDocument = libsbml.readSBMLFromString(text)
    assert doc.getNumPlugins() > 0
    report = SBMLDocumentInfo.from_doc(doc)
    assert (report.document.level, report.document.version) == (3, 2)
    assert report.document.packages == []


def test_model_and_lists(repressilator: Report) -> None:
    """The main model has the lists of its elements."""
    assert len(repressilator.models) == 1
    model: Model = repressilator.models[0]
    assert model.kind == "model"
    assert model.pk == "BIOMD0000000012/Model:BIOMD0000000012"
    assert [c.id for c in model.list_of_compartments] == ["cell"]
    assert [s.id for s in model.list_of_species] == ["PX", "PY", "PZ", "X", "Y", "Z"]
    assert len(model.list_of_reactions) == 12
    assert len(model.list_of_rules) == 9
    assert [u.id for u in model.list_of_unit_definitions] == [
        "volume",
        "substance",
        "time",
    ]


def test_pks_are_scoped_by_model(repressilator: Report) -> None:
    """Element pks carry the model id, the type and the id."""
    species = repressilator.models[0].list_of_species[0]
    assert species.pk == "BIOMD0000000012/Species:PX"
    assert species.compartment == "cell"


def test_reaction(repressilator: Report) -> None:
    """A reaction has its participants, equation and kinetic law."""
    reaction = repressilator.models[0].list_of_reactions[0]
    assert reaction.id == "Reaction1"
    assert [r.species for r in reaction.list_of_reactants] == ["X"]
    assert reaction.list_of_products == []
    assert reaction.equation == "X ➞ "
    assert reaction.kinetic_law is not None
    assert reaction.kinetic_law.math is not None
    assert reaction.kinetic_law.math.formula == "kd_mRNA * X"
    assert (
        reaction.list_of_reactants[0].pk == "BIOMD0000000012/SpeciesReference:_420973"
    )


def test_math_symbols_are_collected(repressilator: Report) -> None:
    """The symbols of every math are collected by the pk of its owner."""
    info = SBMLDocumentInfo(libsbml.readSBMLFromFile(str(REPRESSILATOR_SBML)))
    info.build()
    reaction = info.report.models[0].list_of_reactions[0]
    assert reaction.kinetic_law is not None
    assert info.symbols[reaction.kinetic_law.pk] == {"kd_mRNA", "X"}


def test_variable_stoichiometry() -> None:
    """Reactions with variable (NaN) stoichiometry get an equation."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "reaction.xml")
    equations = {r.id: r.equation for r in report.models[0].list_of_reactions}
    assert equations["v1"] == "x ➞ y"
    assert equations["v2"] == "x ➞ 2.0 y"
    assert equations["v3"] == "f1 x ➞ f2 y"
    assert equations["v4"] == "v4_x x ➞ v4_y y"


def test_stoichiometry_of_a_level_2_reference_is_its_default() -> None:
    """A Level 2 reference without a stoichiometry has the stoichiometry one.

    Level 1 and 2 define the default 1 (L2V4 §4.13.2), which libsbml answers
    without calling the attribute set, so every reference of a curated
    BioModel read as a dash. A reference whose stoichiometry is a formula has
    no number, and a Level 3 reference has no default.
    """
    level_2 = SBMLDocumentInfo.from_sbml(
        '<sbml xmlns="http://www.sbml.org/sbml/level2/version4" level="2" '
        'version="4"><model id="m"><listOfCompartments><compartment id="c"/>'
        '</listOfCompartments><listOfSpecies><species id="s" compartment="c"/>'
        '</listOfSpecies><listOfReactions><reaction id="r"><listOfReactants>'
        '<speciesReference species="s"/><speciesReference species="s">'
        '<stoichiometryMath><math xmlns="http://www.w3.org/1998/Math/MathML">'
        "<cn> 2 </cn></math></stoichiometryMath></speciesReference>"
        '<speciesReference species="s" stoichiometry="3"/>'
        "</listOfReactants></reaction></listOfReactions></model></sbml>"
    )
    (reaction,) = level_2.models[0].list_of_reactions
    assert [sr.stoichiometry for sr in reaction.list_of_reactants] == [1.0, None, 3.0]
    level_3 = SBMLDocumentInfo.from_sbml(
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" '
        'version="2"><model id="m"><listOfCompartments>'
        '<compartment id="c" constant="true"/></listOfCompartments><listOfSpecies>'
        '<species id="s" compartment="c" hasOnlySubstanceUnits="false" '
        'boundaryCondition="false" constant="false"/></listOfSpecies>'
        '<listOfReactions><reaction id="r" reversible="false"><listOfReactants>'
        '<speciesReference species="s" constant="true"/></listOfReactants>'
        "</reaction></listOfReactions></model></sbml>"
    )
    (reaction,) = level_3.models[0].list_of_reactions
    assert reaction.list_of_reactants[0].stoichiometry is None


def _reaction_of_level(level: int, version: int, attributes: str = "") -> Reaction:
    """The one reaction of a document of that level and version."""
    namespace = (
        "http://www.sbml.org/sbml/level1"
        if level == 1
        else f"http://www.sbml.org/sbml/level{level}/version{version}"
        + ("/core" if level == 3 else "")
    )
    info = SBMLDocumentInfo.from_sbml(
        f'<sbml xmlns="{namespace}" level="{level}" version="{version}">'
        '<model id="m"><listOfCompartments><compartment id="c"/>'
        '</listOfCompartments><listOfSpecies><species id="s" compartment="c"/>'
        f'</listOfSpecies><listOfReactions><reaction id="r" {attributes}>'
        '<listOfReactants><speciesReference species="s"/></listOfReactants>'
        "</reaction></listOfReactions></model></sbml>"
    )
    (reaction,) = info.models[0].list_of_reactions
    return reaction


@pytest.mark.parametrize(
    ("level", "version", "reversible", "fast"),
    [
        (1, 2, True, False),
        (2, 1, True, None),
        (2, 2, True, False),
        (2, 4, True, False),
        (2, 5, True, False),
        (3, 1, None, None),
        (3, 2, None, None),
    ],
)
def test_flags_of_a_reaction_without_them_are_their_defaults(
    level: int, version: int, reversible: bool | None, fast: bool | None
) -> None:
    """A reaction which does not write its flags has the defaults of its level.

    Level 1 and 2 make a reaction reversible unless it says otherwise, and
    from Level 2 Version 2 on, as in Level 1, a reaction is not fast unless it
    says so (L2V4 §4.13.1, appendix of the changes: Version 1 of Level 2 gave
    `fast` no default). libsbml answers the defaults without calling them set,
    and in Level 2 Version 1 not even the one of `reversible`, so a curated
    BioModel showed an unset fast flag where its level says false. Level 3
    has no defaults: Version 1 requires both flags and Version 2 has no fast
    flag at all.
    """
    reaction = _reaction_of_level(level, version)
    assert (reaction.reversible, reaction.fast) == (reversible, fast)


def test_flags_a_reaction_writes_are_kept() -> None:
    """A flag the file writes is reported as the file writes it."""
    reaction = _reaction_of_level(2, 4, 'reversible="false" fast="true"')
    assert (reaction.reversible, reaction.fast) == (False, True)


def test_nan_values_become_none() -> None:
    """NaN attributes are not JSON and are reported as unset."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "reaction.xml")
    reaction = next(r for r in report.models[0].list_of_reactions if r.id == "v3")
    assert reaction.list_of_reactants[0].stoichiometry is None


@pytest.mark.parametrize(
    "stoichiometry, expected",
    [
        (1.0, "x"),
        (-1.0, "-x"),
        (2.0, "2.0 x"),
        (-2.5, "-2.5 x"),
        (0.0, "0.0 x"),
        (float("nan"), "sr x"),
    ],
)
def test_half_equation(stoichiometry: float, expected: str) -> None:
    """Half equations for the different stoichiometries."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    reaction = model.createReaction()
    sr = reaction.createReactant()
    sr.setId("sr")
    sr.setSpecies("x")
    sr.setStoichiometry(stoichiometry)
    assert SBMLDocumentInfo._half_equation(reaction.getListOfReactants()) == expected


def test_half_equation_nan_without_id() -> None:
    """A variable stoichiometry without species reference id is marked."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    reaction = model.createReaction()
    sr = reaction.createReactant()
    sr.setSpecies("x")
    sr.setStoichiometry(float("nan"))
    assert SBMLDocumentInfo._half_equation(reaction.getListOfReactants()) == "? x"


def test_document_without_model() -> None:
    """A document without model has no models."""
    report = SBMLDocumentInfo.from_sbml(
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" '
        'level="3" version="2"/>'
    )
    assert report.models == []


def test_model_without_an_identifier_is_scoped_as_the_model() -> None:
    """A model without an id and a metaId is the model of its document.

    Its id is optional in Level 3, and a scope of the digest of the whole
    model moved every permalink of it whenever any value of it changed.
    """

    def model(value: str) -> Model:
        """The report of the model without identifier with a parameter of the value."""
        report = SBMLDocumentInfo.from_sbml(
            '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" '
            'level="3" version="2"><model><listOfParameters>'
            f'<parameter id="k" value="{value}" constant="true"/>'
            "</listOfParameters></model></sbml>"
        )
        return report.models[0]

    first, second = model("1"), model("2")
    assert first.pk == second.pk == "model/Model:model"
    assert first.list_of_parameters[0].pk == "model/Parameter:k"
    assert second.list_of_parameters[0].pk == "model/Parameter:k"


def test_model_without_id_is_scoped_by_its_key() -> None:
    """A model without id uses its metaId as scope of the pks."""
    report = SBMLDocumentInfo.from_sbml(
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" version="2">'
        '<model metaid="meta_m"><listOfCompartments>'
        '<compartment id="c" constant="true"/>'
        "</listOfCompartments></model></sbml>"
    )
    model = report.models[0]
    assert model.pk == "meta_m/Model:meta_m"
    assert model.list_of_compartments[0].pk == "meta_m/Compartment:c"


def test_sbo_is_added_as_cvterm() -> None:
    """The SBO term of an element is reported as BQB_IS annotation."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "annotation.xml")
    model = report.models[0]
    annotated = [s for s in model.list_of_species if s.sbo]
    assert annotated
    species = annotated[0]
    assert any(
        cv.qualifier == "BQB_IS"
        and f"https://identifiers.org/{species.sbo}" in cv.resources
        for cv in species.cvterms
    )


def test_read_sbml_from_string_and_path() -> None:
    """A document is read from a path and from an SBML string."""
    doc = read_sbml(REPRESSILATOR_SBML)
    assert doc.getModel() is not None
    doc = read_sbml(REPRESSILATOR_SBML.read_text())
    assert doc.getModel() is not None


def test_read_sbml_invalid() -> None:
    """An unreadable source gives a document without model."""
    doc = read_sbml("not sbml")
    assert doc.getModel() is None
    assert doc.getNumErrors() > 0


@pytest.mark.parametrize(
    "definition, expected",
    [
        ("mmole/min", r"\frac{mmol}{min}"),
        ("meter^3", "m^3"),
        # dimensionless is a unit, the dash is the placeholder of units which
        # are not declared or cannot be derived
        ("dimensionless", "dimensionless"),
        ("1/dimensionless", "dimensionless"),
        ("mole*dimensionless", "mol"),
        ("empty", "-"),
        # Level 3 allows a fractional exponent, which `getExponent` truncates
        ("sqrt(meter)", "m^0.5"),
    ],
)
def test_udef_to_string(definition: str, expected: str) -> None:
    """Unit definitions are rendered as latex."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    udef = libsbml.UnitDefinition(3, 2)
    udef.setId("u")
    for kind, exponent, scale, multiplier in _units(definition):
        unit = udef.createUnit()
        unit.setKind(kind)
        unit.setExponent(exponent)
        unit.setScale(scale)
        unit.setMultiplier(multiplier)
    model.addUnitDefinition(udef)
    assert udef_to_string(udef) == expected


def _units(definition: str) -> list[tuple[int, float, int, float]]:
    """Units of the test definitions as (kind, exponent, scale, multiplier)."""
    units: dict[str, list[tuple[int, float, int, float]]] = {
        "mmole/min": [
            (libsbml.UNIT_KIND_MOLE, 1, -3, 1.0),
            (libsbml.UNIT_KIND_SECOND, -1, 0, 60.0),
        ],
        "meter^3": [(libsbml.UNIT_KIND_METRE, 3, 0, 1.0)],
        "dimensionless": [(libsbml.UNIT_KIND_DIMENSIONLESS, 1, 0, 1.0)],
        "1/dimensionless": [(libsbml.UNIT_KIND_DIMENSIONLESS, -1, 0, 1.0)],
        "mole*dimensionless": [
            (libsbml.UNIT_KIND_MOLE, 1, 0, 1.0),
            (libsbml.UNIT_KIND_DIMENSIONLESS, 1, 0, 1.0),
        ],
        "empty": [],
        "sqrt(meter)": [(libsbml.UNIT_KIND_METRE, 0.5, 0, 1.0)],
    }
    return units[definition]


def test_udef_to_string_of_a_unit_without_its_attributes() -> None:
    """A unit which leaves out the attributes Level 3 requires renders at once.

    libsbml reads a `<unit kind="second" multiplier="60"/>` of Level 3 and
    answers the unset scale with the largest integer, which the rendering
    raised ten to the power of: the report of such a file never finished. The
    rendering reads a missing attribute as the value Level 2 gives it.
    """
    doc = libsbml.readSBMLFromString(
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" '
        'version="2"><model id="m"><listOfUnitDefinitions>'
        '<unitDefinition id="per_min"><listOfUnits>'
        '<unit kind="second" exponent="-1" multiplier="60"/>'
        '</listOfUnits></unitDefinition><unitDefinition id="huge"><listOfUnits>'
        '<unit kind="mole" exponent="1" scale="400" multiplier="1"/>'
        "</listOfUnits></unitDefinition></listOfUnitDefinitions></model></sbml>"
    )
    model = doc.getModel()
    assert udef_to_string(model.getUnitDefinition("per_min")) == r"\frac{1}{min}"
    assert udef_to_string(model.getUnitDefinition("huge")) == r"10^{400} \cdot mol"


def test_comp_model_definitions() -> None:
    """Model definitions are further models of the report."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "model_definitions.xml")
    assert [(m.id, m.kind) for m in report.models] == [
        ("model_definitions", "model"),
        ("m1", "modelDefinition"),
    ]
    assert report.models[1].pk == "m1/Model:m1"
    assert report.models[1].list_of_species[0].pk.startswith("m1/Species:")


def test_comp_sbase_without_replacements() -> None:
    """An element of a comp document without replacements has no comp extension."""
    report = SBMLDocumentInfo.from_sbml(COMP_ICG_BODY)
    model = report.models[0]
    assert model.list_of_submodels
    assert [c for c in model.list_of_compartments if c.comp is None]
    assert [s for s in model.list_of_species if s.comp is not None]


def test_comp_submodels_ports_and_replacements() -> None:
    """Submodels, ports, external model definitions and replacements are reported."""
    report = SBMLDocumentInfo.from_sbml(COMP_ICG_BODY)
    model = report.models[0]
    assert [(s.id, s.model_ref) for s in model.list_of_submodels] == [("LI", "liver")]
    assert [
        (e.id, e.source, e.model_ref) for e in report.external_model_definitions
    ] == [("liver", "icg_liver.xml", "icg_liver")]
    assert (
        report.external_model_definitions[0].pk
        == "document/ExternalModelDefinition:liver"
    )
    port = model.list_of_ports[0]
    assert (port.id, port.id_ref) == ("Vre_tissue_port", "Vre_tissue")
    species = next(s for s in model.list_of_species if s.id == "Cli_plasma_icg")
    assert species.comp is not None
    replaced = species.comp.replaced_elements[0]
    assert (replaced.submodel_ref, replaced.port_ref) == ("LI", "icg_ext_port")


def test_fractional_spatial_dimensions() -> None:
    """The spatial dimensions of an L3 compartment can be fractional."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    model.setId("m")
    compartment = model.createCompartment()
    compartment.setId("c")
    compartment.setSpatialDimensions(2.5)
    report = SBMLDocumentInfo.from_doc(doc)
    assert report.models[0].list_of_compartments[0].spatial_dimensions == 2.5


def test_spatial_dimensions_unset() -> None:
    """A compartment without spatial dimensions reports them as unset."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    model.setId("m")
    model.createCompartment().setId("c")
    report = SBMLDocumentInfo.from_doc(doc)
    assert report.models[0].list_of_compartments[0].spatial_dimensions is None


def test_species_units_are_the_substance_units() -> None:
    """The units of a species are its substance units, rendered as latex."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "multiple_substance_units.xml")
    species = [s for s in report.models[0].list_of_species if s.substance_units]
    assert species
    assert all(s.units_latex for s in species)


def test_fbc() -> None:
    """Flux bounds, gene product associations, gene products and objectives are reported."""
    report = SBMLDocumentInfo.from_sbml(FBC_ECOLI_CORE_SBML)
    model = report.models[0]
    reaction = next(r for r in model.list_of_reactions if r.id == "R_PFK")
    assert reaction.fbc is not None
    assert reaction.fbc.lower_flux_bound == "cobra_0_bound"
    assert reaction.fbc.upper_flux_bound == "cobra_default_ub"
    association = reaction.fbc.gene_product_association
    assert association is not None
    root = association.association
    assert isinstance(root, Or)
    refs = [ref for ref in root.associations if isinstance(ref, GeneProductRef)]
    assert [ref.gene_product for ref in refs] == ["G_b3916", "G_b1723"]
    assert len(model.list_of_gene_products) == 137
    objective = model.list_of_objectives[0]
    assert objective.id == "obj"
    assert [(f.reaction, f.coefficient) for f in objective.list_of_flux_objectives] == [
        ("R_BIOMASS_Ecoli_core_w_GAM", 1.0)
    ]


def test_charge_zero_is_reported() -> None:
    """A charge of zero is a charge, not an unset attribute."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "fbc_mass_charge.xml")
    species = next(s for s in report.models[0].list_of_species if s.id == "glc")
    assert species.fbc is not None
    assert species.fbc.charge == 0


def test_flux_objective_without_coefficient() -> None:
    """A flux objective without coefficient reports None instead of NaN."""
    doc = libsbml.SBMLDocument(libsbml.SBMLNamespaces(3, 1, "fbc", 2))
    model = doc.createModel()
    model.setId("m")
    plugin: libsbml.FbcModelPlugin = model.getPlugin("fbc")
    objective: libsbml.Objective = plugin.createObjective()
    objective.setId("obj")
    objective.setType("maximize")
    objective.createFluxObjective().setReaction("r")
    report = SBMLDocumentInfo.from_doc(doc)
    flux_objective = report.models[0].list_of_objectives[0].list_of_flux_objectives[0]
    assert flux_objective.coefficient is None
    assert "NaN" not in json.dumps(report.model_dump(mode="json", by_alias=True))


def test_distrib_uncertainties() -> None:
    """Uncertainties of the distrib package are reported with their parameters."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "distrib_uncertainties.xml")
    model = report.models[0]
    with_uncertainty = [
        e for e in model.list_of_parameters + model.list_of_species if e.uncertainties
    ]
    assert with_uncertainty
    uncertainty = with_uncertainty[0].uncertainties[0]
    assert uncertainty.sbml_type == "Uncertainty"
    assert uncertainty.uncert_parameters
    assert uncertainty.uncert_parameters[0].type is not None


def test_infinite_flux_bound_of_an_example() -> None:
    """The unbounded direction of a flux stays infinite through the report."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "fbc_bounds_v1.xml")
    bound = next(b for b in report.models[0].list_of_flux_bounds if b.id == "v1_ub")
    assert bound.value == float("inf")
    data = json.loads(report.model_dump_json(by_alias=True))
    values = {b["id"]: b["value"] for b in data["models"][0]["listOfFluxBounds"]}
    assert values["v1_ub"] == "Infinity"


def test_distrib_span_of_the_shipped_example() -> None:
    """A span of the shipped example carries the two ends of its interval.

    An `uncertSpan` was read as a plain `uncertParameter`, so the four
    attributes of the span were lost and the range of `p1` was reported as the
    word "range" without a single number (distrib §3.12).
    """
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "distrib_uncertainties.xml")
    uncertainty = report.models[0].list_of_parameters[0].uncertainties[0]
    span = uncertainty.uncert_parameters[0]
    assert isinstance(span, UncertSpan)
    assert span.sbml_type == "UncertSpan"
    assert span.type == "range"
    assert (span.value_lower, span.value_upper) == (1.0, 4.0)
    assert (span.var_lower, span.var_upper) == (None, None)


def test_distrib_span_by_reference(distrib_spans: Report) -> None:
    """A span names the two parameters which hold its ends (distrib §3.12)."""
    km = _parameter(distrib_spans, "Km")
    span = km.uncertainties[1].uncert_parameters[1]
    assert isinstance(span, UncertSpan)
    assert span.id == "Km_lysate_ci"
    assert span.name == "95% confidence interval"
    assert span.type == "confidenceInterval"
    assert (span.var_lower, span.var_upper) == ("Km_lower", "Km_upper")
    assert (span.value_lower, span.value_upper) == (None, None)


def test_distrib_uncert_parameter_is_an_element(distrib_spans: Report) -> None:
    """An uncert parameter carries the attributes of an SBase (distrib §3.11.5).

    The provenance of a measurement is what the package exists to record, and
    the notes of the parameter are where a file writes it.
    """
    km = _parameter(distrib_spans, "Km")
    mean = km.uncertainties[0].uncert_parameters[0]
    assert mean.sbml_type == "UncertParameter"
    assert mean.pk == "distrib_spans/UncertParameter:Km_purified_mean"
    assert mean.id == "Km_purified_mean"
    assert mean.name == "mean of the fitted constants"
    assert mean.meta_id == "meta_u_Km_purified_mean"
    assert mean.notes is not None
    assert "the parameter of the model is set to" in mean.notes
    assert (mean.type, mean.value, mean.units) == ("mean", 0.5, "mmole_per_l")


def test_distrib_uncert_parameter_without_an_id(distrib_spans: Report) -> None:
    """A measure without an id is keyed by its uncertainty and its type.

    An uncertainty carries each type of measure at most once (distrib §3.10),
    so the type names the measure within it whatever the order of the list.
    """
    km = _parameter(distrib_spans, "Km")
    deviation = km.uncertainties[0].uncert_parameters[1]
    assert deviation.id is None
    assert deviation.pk == (
        "distrib_spans/UncertParameter:u_Km_purified.standardDeviation"
    )
    span = km.uncertainties[0].uncert_parameters[3]
    assert span.sbml_type == "UncertSpan"
    assert span.pk == "distrib_spans/UncertSpan:Km_purified_range"
    (species,) = distrib_spans.models[0].list_of_species
    assert [m.pk for m in species.uncertainties[0].uncert_parameters] == [
        "distrib_spans/UncertParameter:u_S.mean",
        "distrib_spans/UncertSpan:u_S.confidenceInterval",
    ]


def test_distrib_external_parameters_are_keyed_by_their_definition() -> None:
    """An external parameter is keyed by its definition, a nested one by its place.

    An uncertainty may carry several external parameters, each with a
    definition url of its own (distrib §3.10), while the parameters nested in
    a distribution have no uniqueness rule at all (distrib §3.11.7).
    """
    sbml = """<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core"
      xmlns:distrib="http://www.sbml.org/sbml/level3/version1/distrib/version1"
      level="3" version="1" distrib:required="true">
      <model id="m">
        <listOfParameters>
          <parameter id="k" value="1" constant="true">
            <distrib:listOfUncertainties>
              <distrib:uncertainty>
                <distrib:uncertParameter distrib:type="externalParameter"
                    distrib:definitionURL="http://dist.org/CI" distrib:value="0.1"/>
                <distrib:uncertParameter distrib:type="externalParameter"
                    distrib:definitionURL="http://dist.org/CIpercent"
                    distrib:value="99"/>
                <distrib:uncertParameter distrib:type="distribution"
                    distrib:definitionURL="http://dist.org/beta">
                  <distrib:listOfUncertParameters>
                    <distrib:uncertParameter distrib:type="externalParameter"
                        distrib:definitionURL="http://dist.org/beta#alpha"
                        distrib:value="2"/>
                    <distrib:uncertParameter distrib:type="externalParameter"
                        distrib:definitionURL="http://dist.org/beta#beta"
                        distrib:value="5"/>
                  </distrib:listOfUncertParameters>
                </distrib:uncertParameter>
              </distrib:uncertainty>
            </distrib:listOfUncertainties>
          </parameter>
        </listOfParameters>
      </model>
    </sbml>"""
    report = SBMLDocumentInfo.from_sbml(sbml)
    (uncertainty,) = _parameter(report, "k").uncertainties
    first, second, distribution = uncertainty.uncert_parameters
    key = "k.uncertainty.0"
    assert first.pk == f"m/UncertParameter:{key}.externalParameter.http://dist.org/CI"
    assert second.pk == (
        f"m/UncertParameter:{key}.externalParameter.http://dist.org/CIpercent"
    )
    assert distribution.pk == f"m/UncertParameter:{key}.distribution"
    assert [m.pk for m in distribution.uncert_parameters] == [
        f"m/UncertParameter:{key}.distribution.uncertParameter.0",
        f"m/UncertParameter:{key}.distribution.uncertParameter.1",
    ]


def test_distrib_nested_uncert_parameters(distrib_spans: Report) -> None:
    """A distribution carries the parameters it is defined by (distrib §3.11.7)."""
    vmax = _parameter(distrib_spans, "Vmax")
    distribution = vmax.uncertainties[0].uncert_parameters[1]
    assert distribution.type == "distribution"
    assert (
        distribution.definition_url == "https://en.wikipedia.org/wiki/Beta_distribution"
    )
    assert [p.name for p in distribution.uncert_parameters] == ["alpha", "beta"]
    alpha, beta = distribution.uncert_parameters
    assert (alpha.type, alpha.value) == ("externalParameter", 2.0)
    assert (beta.type, beta.value) == ("externalParameter", 5.0)
    assert beta.definition_url == "https://en.wikipedia.org/wiki/Beta_distribution#beta"


def test_distrib_several_uncertainties_of_one_element(distrib_spans: Report) -> None:
    """Measurements from two sources are two uncertainties (distrib §3.10)."""
    km = _parameter(distrib_spans, "Km")
    assert [u.id for u in km.uncertainties] == ["u_Km_purified", "u_Km_lysate"]
    assert [u.name for u in km.uncertainties] == [
        "Wilson 1997, purified enzyme",
        "Baker 2012, cell lysate",
    ]
    assert all(u.notes for u in km.uncertainties)
    assert km.uncertainties[0].notes != km.uncertainties[1].notes


def test_distrib_uncertainty_of_a_species_and_of_a_rule(distrib_spans: Report) -> None:
    """An uncertainty belongs to any element with a mathematical meaning."""
    model = distrib_spans.models[0]
    (species,) = model.list_of_species
    assert [u.id for u in species.uncertainties] == ["u_S"]
    assert species.uncertainties[0].uncert_parameters[1].sbml_type == "UncertSpan"
    (rule,) = model.list_of_rules
    assert [u.id for u in rule.uncertainties] == ["u_v"]
    distribution = rule.uncertainties[0].uncert_parameters[1]
    assert distribution.math is not None
    assert "normal" in distribution.math.formula


def test_reactant_pks_are_unique_across_reactions() -> None:
    """Species references and local parameters without model-wide ids differ.

    Species references without an id are byte identical xml across reactions
    consuming the same species, so the digest fallback of the pk used to
    collide; the pk is now keyed by the reaction and the side instead. A
    local parameter has a genuine id, but it is scoped to its own kinetic
    law, so two kinetic laws with a same-named local parameter (`k`) used to
    collide the same way; the pk is now keyed by the kinetic law too, and the
    math of each kinetic law links to its own local parameter.
    """
    sbml = (
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" '
        'level="3" version="2">'
        '<model id="m"><listOfCompartments>'
        '<compartment id="c" constant="true"/>'
        "</listOfCompartments><listOfSpecies>"
        '<species id="s" compartment="c" hasOnlySubstanceUnits="false" '
        'boundaryCondition="false" constant="false"/>'
        "</listOfSpecies><listOfReactions>"
        '<reaction id="r1" reversible="false"><listOfReactants>'
        '<speciesReference species="s" constant="true"/>'
        "</listOfReactants><kineticLaw>"
        '<math xmlns="http://www.w3.org/1998/Math/MathML"><ci> k </ci></math>'
        '<listOfLocalParameters><localParameter id="k" value="1"/>'
        "</listOfLocalParameters></kineticLaw></reaction>"
        '<reaction id="r2" reversible="false"><listOfReactants>'
        '<speciesReference species="s" constant="true"/>'
        "</listOfReactants><kineticLaw>"
        '<math xmlns="http://www.w3.org/1998/Math/MathML"><ci> k </ci></math>'
        '<listOfLocalParameters><localParameter id="k" value="2"/>'
        "</listOfLocalParameters></kineticLaw></reaction>"
        "</listOfReactions></model></sbml>"
    )
    report = SBMLDocumentInfo.from_sbml(sbml)
    reactions = report.models[0].list_of_reactions
    reactant_pks = [r.list_of_reactants[0].pk for r in reactions]
    assert reactant_pks == [
        "m/SpeciesReference:r1.reactant.s",
        "m/SpeciesReference:r2.reactant.s",
    ]
    assert len(reactant_pks) == len(set(reactant_pks))

    klaw1, klaw2 = reactions[0].kinetic_law, reactions[1].kinetic_law
    assert klaw1 is not None
    assert klaw2 is not None
    local_parameters = [
        klaw1.list_of_local_parameters[0],
        klaw2.list_of_local_parameters[0],
    ]
    assert [lp.id for lp in local_parameters] == ["k", "k"]
    local_parameter_pks = [lp.pk for lp in local_parameters]
    assert local_parameter_pks == [
        "m/LocalParameter:r1.kineticLaw.k",
        "m/LocalParameter:r2.kineticLaw.k",
    ]
    assert len(local_parameter_pks) == len(set(local_parameter_pks))

    math_edges = {
        (e.source, e.target) for e in report.link_graph.edges if e.kind == EdgeKind.MATH
    }
    assert math_edges == {
        (klaw1.pk, local_parameter_pks[0]),
        (klaw2.pk, local_parameter_pks[1]),
    }


# -------------------------------------------------------------------------------------
# the local parameters of a kinetic law, which Level 2 writes as parameters
# -------------------------------------------------------------------------------------
def _kinetic_law_sbml(level: int) -> str:
    """The same one reaction model as Level 2 Version 4 and as Level 3 Version 2.

    The kinetic law carries one parameter with a value and units, written as
    `<parameter>` in Level 2 and as `<localParameter>` in Level 3.
    """
    namespace = (
        "http://www.sbml.org/sbml/level2/version4"
        if level == 2
        else "http://www.sbml.org/sbml/level3/version2/core"
    )
    version = 4 if level == 2 else 2
    parameters = (
        '<listOfParameters><parameter id="k" value="0.1" units="per_second"/>'
        "</listOfParameters>"
        if level == 2
        else '<listOfLocalParameters><localParameter id="k" value="0.1" '
        'units="per_second"/></listOfLocalParameters>'
    )
    constant = "" if level == 2 else ' constant="true"'
    species_attributes = (
        "" if level == 2 else ' hasOnlySubstanceUnits="false" constant="false"'
    )
    return (
        f'<sbml xmlns="{namespace}" level="{level}" version="{version}">'
        '<model id="m"><listOfUnitDefinitions>'
        '<unitDefinition id="per_second"><listOfUnits>'
        '<unit kind="second" exponent="-1" scale="0" multiplier="1"/>'
        "</listOfUnits></unitDefinition></listOfUnitDefinitions>"
        f'<listOfCompartments><compartment id="c" size="1"{constant}/>'
        "</listOfCompartments><listOfSpecies>"
        f'<species id="s" compartment="c" initialAmount="1"'
        f' boundaryCondition="false"{species_attributes}/>'
        "</listOfSpecies><listOfReactions>"
        '<reaction id="r1" reversible="false"><listOfReactants>'
        f'<speciesReference species="s"{constant}/>'
        "</listOfReactants><kineticLaw>"
        '<math xmlns="http://www.w3.org/1998/Math/MathML">'
        "<apply><times/><ci> k </ci><ci> s </ci></apply></math>"
        f"{parameters}</kineticLaw></reaction>"
        "</listOfReactions></model></sbml>"
    )


@pytest.mark.parametrize("level", [2, 3])
def test_kinetic_law_parameters_of_both_levels(level: int) -> None:
    """A kinetic law of either level carries its parameters as local parameters.

    libsbml fills `getListOfLocalParameters` for a Level 3 document only; in a
    Level 2 document the parameters of a kinetic law are `Parameter` objects of
    `getListOfParameters` (core §4.11.5).
    """
    report = SBMLDocumentInfo.from_sbml(_kinetic_law_sbml(level))
    assert report.document.level == level
    kinetic_law = report.models[0].list_of_reactions[0].kinetic_law
    assert kinetic_law is not None
    (local_parameter,) = kinetic_law.list_of_local_parameters
    assert local_parameter.sbml_type == "LocalParameter"
    assert local_parameter.id == "k"
    assert local_parameter.value == 0.1
    assert local_parameter.units == "per_second"
    assert local_parameter.units_latex == "\\frac{1}{s}"
    assert local_parameter.pk == "m/LocalParameter:r1.kineticLaw.k"


def test_level_2_biomodel_reports_its_kinetic_law_parameters(
    level2_biomodel: Report,
) -> None:
    """The parameters of the kinetic laws of a curated Level 2 biomodel."""
    report = level2_biomodel
    assert report.document.level == 2
    reaction = next(
        r for r in report.models[0].list_of_reactions if r.id == "reaction1"
    )
    assert reaction.kinetic_law is not None
    (local_parameter,) = reaction.kinetic_law.list_of_local_parameters
    assert local_parameter.id == "vi"
    assert local_parameter.value == 0.025
    assert local_parameter.sbml_type == "LocalParameter"
    # the metaId of the file keys the parameter, as it keys its kinetic law
    assert local_parameter.pk == "BIOMD0000000003/LocalParameter:_961167"


# -------------------------------------------------------------------------------------
# the identity of an initial assignment, a rule and an event assignment
# -------------------------------------------------------------------------------------
def _identifier_sbml(math: str = "<ci> p1 </ci>") -> str:
    """A Level 3 Version 2 model whose assignments and rules carry an id.

    `math` is the math of the algebraic rule, so that the same document can be
    read twice with a different formula.
    """
    return (
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" '
        'level="3" version="2"><model id="m">'
        '<listOfCompartments><compartment id="c" constant="true" size="1"/>'
        "</listOfCompartments><listOfSpecies>"
        '<species id="S1" compartment="c" hasOnlySubstanceUnits="false" '
        'boundaryCondition="false" constant="false" initialConcentration="1"/>'
        "</listOfSpecies><listOfParameters>"
        '<parameter id="p1" value="1" constant="false"/>'
        "</listOfParameters><listOfInitialAssignments>"
        '<initialAssignment id="ia1" symbol="S1">'
        '<math xmlns="http://www.w3.org/1998/Math/MathML"><ci> p1 </ci></math>'
        "</initialAssignment></listOfInitialAssignments><listOfRules>"
        '<algebraicRule id="ar1" name="my rule" sboTerm="SBO:0000064">'
        f'<math xmlns="http://www.w3.org/1998/Math/MathML">{math}</math>'
        "</algebraicRule>"
        '<rateRule id="rr1" variable="p1">'
        '<math xmlns="http://www.w3.org/1998/Math/MathML"><cn> 1 </cn></math>'
        "</rateRule></listOfRules><listOfEvents>"
        '<event id="e1" useValuesFromTriggerTime="true"><trigger '
        'initialValue="false" persistent="true">'
        '<math xmlns="http://www.w3.org/1998/Math/MathML"><true/></math>'
        "</trigger><listOfEventAssignments>"
        '<eventAssignment id="ea1" variable="S1">'
        '<math xmlns="http://www.w3.org/1998/Math/MathML"><cn> 1 </cn></math>'
        "</eventAssignment></listOfEventAssignments></event>"
        "</listOfEvents></model></sbml>"
    )


def test_identifier_of_assignments_and_rules() -> None:
    """The id of the file is reported, not the symbol or the variable.

    libsbml aliases `getId()` of an initial assignment, a rule and an event
    assignment to the target they set; the identifier of Level 3 Version 2 is
    `getIdAttribute()` (core §4.8.1, §4.9.1, §4.12.5).
    """
    model = SBMLDocumentInfo.from_sbml(_identifier_sbml()).models[0]
    initial_assignment = model.list_of_initial_assignments[0]
    assert (initial_assignment.id, initial_assignment.symbol) == ("ia1", "S1")
    assert initial_assignment.pk == "m/InitialAssignment:ia1"

    algebraic, rate = model.list_of_rules
    assert algebraic.id == "ar1"
    assert algebraic.name == "my rule"
    assert algebraic.pk == "m/AlgebraicRule:ar1"
    assert rate.sbml_type == "RateRule"
    assert (rate.id, getattr(rate, "variable", None)) == ("rr1", "p1")
    assert rate.pk == "m/RateRule:rr1"

    assignment = model.list_of_events[0].list_of_event_assignments[0]
    assert (assignment.id, assignment.variable) == ("ea1", "S1")
    assert assignment.pk == "m/EventAssignment:ea1"


def test_identified_rule_keeps_its_key_when_its_math_changes() -> None:
    """The permalink of a rule with an id does not depend on its formula."""
    first = SBMLDocumentInfo.from_sbml(_identifier_sbml()).models[0].list_of_rules[0]
    second = (
        SBMLDocumentInfo.from_sbml(_identifier_sbml(math="<cn> 2 </cn>"))
        .models[0]
        .list_of_rules[0]
    )
    assert first.pk == second.pk == "m/AlgebraicRule:ar1"


def test_assignments_without_an_identifier_keep_their_key() -> None:
    """Without an id, an assignment or a rule is keyed by what it sets.

    A Level 2 document has no id on these elements at all, so the key stays
    the symbol of the initial assignment and the variable of the rule, and the
    id of the report is empty.
    """
    report = SBMLDocumentInfo.from_sbml(
        '<sbml xmlns="http://www.sbml.org/sbml/level2/version4" '
        'level="2" version="4"><model id="m">'
        '<listOfCompartments><compartment id="c" size="1"/></listOfCompartments>'
        '<listOfSpecies><species id="S1" compartment="c" '
        'initialConcentration="1"/></listOfSpecies>'
        '<listOfParameters><parameter id="p1" value="1" constant="false"/>'
        "</listOfParameters><listOfInitialAssignments>"
        '<initialAssignment symbol="S1">'
        '<math xmlns="http://www.w3.org/1998/Math/MathML"><ci> p1 </ci></math>'
        "</initialAssignment></listOfInitialAssignments><listOfRules>"
        '<assignmentRule variable="p1">'
        '<math xmlns="http://www.w3.org/1998/Math/MathML"><cn> 1 </cn></math>'
        "</assignmentRule></listOfRules><listOfEvents>"
        '<event id="e1"><trigger>'
        '<math xmlns="http://www.w3.org/1998/Math/MathML"><true/></math>'
        "</trigger><listOfEventAssignments>"
        '<eventAssignment variable="S1">'
        '<math xmlns="http://www.w3.org/1998/Math/MathML"><cn> 1 </cn></math>'
        "</eventAssignment></listOfEventAssignments></event>"
        "</listOfEvents></model></sbml>"
    )
    model = report.models[0]
    initial_assignment = model.list_of_initial_assignments[0]
    assert initial_assignment.id is None
    assert initial_assignment.pk == "m/InitialAssignment:S1"
    rule = model.list_of_rules[0]
    assert rule.id is None
    assert rule.pk == "m/AssignmentRule:p1"
    assignment = model.list_of_events[0].list_of_event_assignments[0]
    assert assignment.id is None
    assert assignment.pk == "m/EventAssignment:e1.S1"


def test_elements_without_an_identifier_are_keyed_by_their_place() -> None:
    """An algebraic rule, a constraint and an event without an id are keyed by place.

    None of them sets an element which could name it, a Level 2 or Level 3
    Version 1 file cannot give a rule or a constraint an id, and the digest of
    their xml which keyed them moved their permalink with every change of
    their formula. They are keyed by their place among the elements of their
    type, the way a transition without an id is.
    """

    def report(algebraic_math: str) -> Report:
        """The report of the model whose first algebraic rule has the math."""
        return SBMLDocumentInfo.from_sbml(
            '<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" '
            'level="3" version="1"><model id="m"><listOfParameters>'
            '<parameter id="x" value="1" constant="false"/>'
            '<parameter id="y" value="1" constant="false"/>'
            "</listOfParameters><listOfRules><algebraicRule>"
            f'<math xmlns="http://www.w3.org/1998/Math/MathML">{algebraic_math}</math>'
            '</algebraicRule><assignmentRule variable="y">'
            '<math xmlns="http://www.w3.org/1998/Math/MathML"><cn> 1 </cn></math>'
            "</assignmentRule><algebraicRule>"
            '<math xmlns="http://www.w3.org/1998/Math/MathML"><ci> x </ci></math>'
            "</algebraicRule></listOfRules><listOfConstraints><constraint>"
            '<math xmlns="http://www.w3.org/1998/Math/MathML"><true/></math>'
            "</constraint><constraint>"
            '<math xmlns="http://www.w3.org/1998/Math/MathML"><false/></math>'
            "</constraint></listOfConstraints><listOfEvents>"
            '<event useValuesFromTriggerTime="true">'
            '<trigger initialValue="false" persistent="true">'
            '<math xmlns="http://www.w3.org/1998/Math/MathML"><true/></math>'
            "</trigger></event></listOfEvents></model></sbml>"
        )

    model = report("<ci> x </ci>").models[0]
    assert [r.pk for r in model.list_of_rules] == [
        "m/AlgebraicRule:algebraicRule.0",
        "m/AssignmentRule:y",
        "m/AlgebraicRule:algebraicRule.1",
    ]
    assert [c.pk for c in model.list_of_constraints] == [
        "m/Constraint:constraint.0",
        "m/Constraint:constraint.1",
    ]
    (event,) = model.list_of_events
    assert event.pk == "m/Event:event.0"
    assert event.trigger is not None
    assert event.trigger.pk == "m/Trigger:event.0.trigger"
    changed = report("<apply><minus/><ci> x </ci><cn> 1 </cn></apply>").models[0]
    assert changed.list_of_rules[0].pk == "m/AlgebraicRule:algebraicRule.0"


# -------------------------------------------------------------------------------------
# the objects of core which carry their own attributes
# -------------------------------------------------------------------------------------
def test_constraint_event_example(constraint_event: Report) -> None:
    """The example carries the objects it was written for.

    `constraint_event.xml` is the Level 3 Version 2 example of the elements no
    other shipped model contains: a constraint with a message (core §4.10), an
    event with a trigger, a priority and a delay (§4.12), a kinetic law with
    local parameters (§4.11.6) and unit definitions built from several units
    (§4.4.2).
    """
    model = constraint_event.models[0]
    assert model.id == "constraint_event"
    (constraint,) = model.list_of_constraints
    assert constraint.math is not None
    assert constraint.message is not None
    (reaction,) = model.list_of_reactions
    assert reaction.kinetic_law is not None
    assert [lp.id for lp in reaction.kinetic_law.list_of_local_parameters] == [
        "Vmax",
        "Km",
    ]
    (event,) = model.list_of_events
    assert event.trigger is not None
    assert event.priority is not None
    assert event.delay is not None
    assert [ea.id for ea in event.list_of_event_assignments] == [
        "E1_dose",
        "E1_switch",
    ]
    assert [ud.id for ud in model.list_of_unit_definitions] == [
        "min",
        "mmole",
        "mM",
        "mmole_per_min_l",
    ]


def test_unit_definition_carries_its_units(constraint_event: Report) -> None:
    """A unit definition carries the units of the file next to the formula.

    The four attributes of a unit are what the file says (core §4.4.2), the
    formula is what the report makes of them, and a reader needs both to check
    one against the other.
    """
    definitions = {
        ud.id: ud for ud in constraint_event.models[0].list_of_unit_definitions
    }
    definition = definitions["mmole_per_min_l"]
    assert definition.units_latex == "\\frac{mmol}{min \\cdot l}"
    assert [
        (unit.kind, unit.exponent, unit.scale, unit.multiplier)
        for unit in definition.list_of_units
    ] == [
        ("mole", 1.0, -3, 1.0),
        ("second", -1.0, 0, 60.0),
        ("litre", -1.0, 0, 1.0),
    ]
    assert len(definitions["min"].list_of_units) == 1


def test_trigger_priority_and_delay_are_objects(constraint_event: Report) -> None:
    """The three children of an event carry the attributes of the file.

    A trigger, a priority and a delay are `SBase` in Level 3 Version 2 (core
    §4.12.2 to §4.12.4), so each of them carries an id, a metaId, an SBO term
    and notes of its own, which the report reduced to two flags and three
    formulas before.
    """
    (event,) = constraint_event.models[0].list_of_events
    trigger = event.trigger
    assert trigger is not None
    assert trigger.sbml_type == "Trigger"
    assert trigger.pk == "constraint_event/Trigger:E1_trigger"
    assert trigger.id == "E1_trigger"
    assert trigger.meta_id == "meta_E1_trigger"
    assert trigger.sbo == "SBO:0000064"
    assert trigger.notes is not None
    assert trigger.initial_value is False
    assert trigger.persistent is True
    assert trigger.math is not None
    assert trigger.math.formula == "time >= t_dose"

    priority = event.priority
    assert priority is not None
    assert priority.sbml_type == "Priority"
    assert priority.pk == "constraint_event/Priority:E1_priority"
    assert priority.notes is not None
    assert priority.math is not None

    delay = event.delay
    assert delay is not None
    assert delay.sbml_type == "Delay"
    assert delay.pk == "constraint_event/Delay:E1_delay"
    assert delay.notes is not None
    assert delay.math is not None
    assert delay.math.formula == "t_delay"


def test_trigger_priority_and_delay_without_an_identifier() -> None:
    """Without an id or a metaId the three are keyed by their event."""
    report = SBMLDocumentInfo.from_sbml(
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" '
        'level="3" version="1"><model id="m"><listOfEvents>'
        '<event id="e1" useValuesFromTriggerTime="true">'
        '<trigger initialValue="false" persistent="true">'
        '<math xmlns="http://www.w3.org/1998/Math/MathML"><true/></math></trigger>'
        '<delay><math xmlns="http://www.w3.org/1998/Math/MathML">'
        "<cn> 1 </cn></math></delay>"
        '<priority><math xmlns="http://www.w3.org/1998/Math/MathML">'
        "<cn> 2 </cn></math></priority>"
        "</event></listOfEvents></model></sbml>"
    )
    (event,) = report.models[0].list_of_events
    assert event.trigger is not None
    assert event.trigger.id is None
    assert event.trigger.pk == "m/Trigger:e1.trigger"
    assert event.priority is not None
    assert event.priority.pk == "m/Priority:e1.priority"
    assert event.delay is not None
    assert event.delay.pk == "m/Delay:e1.delay"


def test_constraint_message_is_the_xhtml_of_the_file(constraint_event: Report) -> None:
    """The message of a constraint is the XHTML of the file (core §4.10.2)."""
    (constraint,) = constraint_event.models[0].list_of_constraints
    assert constraint.message is not None
    assert constraint.message.startswith("<message>")
    assert "<b>S1</b>" in constraint.message


def test_document_and_model_carry_their_annotation(constraint_event: Report) -> None:
    """The annotation element of the document and of the model is part of the report.

    The report does not carry the xml of the document and of the model, which
    is the whole file, but a tool writes its own vocabulary into their
    annotation (core §3.2.6) and a reader has to be able to see it.
    """
    document = constraint_event.document
    assert document.xml is None
    assert document.annotation_xml is not None
    assert "sbml4humans:document" in document.annotation_xml

    model = constraint_event.models[0]
    assert model.xml is None
    assert model.annotation_xml is not None
    assert "sbml4humans:model" in model.annotation_xml
    # the annotation element, not the model element
    assert "<listOfSpecies>" not in model.annotation_xml


def test_annotation_of_a_model_without_one(repressilator: Report) -> None:
    """A model without an annotation carries none."""
    assert repressilator.document.annotation_xml is None


def test_nested_cvterms_are_read(constraint_event: Report) -> None:
    """A CV term qualified by another CV term keeps the term below it (core §6)."""
    model = constraint_event.models[0]
    (term,) = [cv for cv in model.cvterms if cv.qualifier == "BQB_HAS_TAXON"]
    assert term.resources == ["https://identifiers.org/taxonomy/9606"]
    (nested,) = term.nested
    assert nested.qualifier == "BQB_IS_DESCRIBED_BY"
    assert nested.resources == ["https://identifiers.org/pubmed/31219795"]
    assert nested.nested == []


# -------------------------------------------------------------------------------------
# the objects of comp which the report carried as values
# -------------------------------------------------------------------------------------
def test_deletion_is_an_element_of_the_report(comp_deletion: Report) -> None:
    """A deletion is an element with its own identity and its `SBase` attributes.

    comp §3.5.3 gives a deletion an id, a name and everything an `SBase`
    carries, so that a containing model can name it and a report can show it.
    """
    cell1 = comp_deletion.models[0].list_of_submodels[0]
    del_k, del_sink = cell1.list_of_deletions
    assert del_k.sbml_type == "Deletion"
    assert del_k.pk == "comp_deletion/Deletion:del_k"
    assert del_k.id == "del_k"
    assert del_k.name == "deletion of the rate constant"
    assert del_k.meta_id == "meta_del_k"
    assert del_k.sbo == "SBO:0000002"
    assert del_k.notes is not None
    assert "rate constant of the medium" in del_k.notes
    assert del_k.xml is not None
    assert del_k.id_ref == "k"
    assert del_k.port_ref is None
    assert del_sink.pk == "comp_deletion/Deletion:del_sink"
    assert del_sink.meta_id_ref == "meta_sink"


def test_replaced_element_carries_its_deletion_and_conversion_factor(
    comp_deletion: Report,
) -> None:
    """A replaced element carries the two attributes comp adds to a reference.

    The conversion factor changes the mathematics of the composed model (comp
    §3.6.2 and §3.8.1) and the deletion says that the replacement stands for an
    element which the submodel lost.
    """
    model = comp_deletion.models[0]
    (glc,) = model.list_of_species
    assert glc.comp is not None
    first, second = glc.comp.replaced_elements
    assert first.sbml_type == "ReplacedElement"
    assert first.pk == "comp_deletion/ReplacedElement:meta_glc_cell1"
    assert first.submodel_ref == "cell1"
    assert first.port_ref == "glc_port"
    assert first.conversion_factor == "f_amount"
    assert first.deletion is None
    assert second.conversion_factor is None

    k_total = model.list_of_parameters[0]
    assert k_total.comp is not None
    (replaced,) = k_total.comp.replaced_elements
    assert replaced.deletion == "del_k"
    assert replaced.port_ref is None


def test_replaced_by_is_an_sbase_of_the_report(comp_deletion: Report) -> None:
    """A replaced by carries the attributes of an `SBase` (comp §3.7)."""
    vmax = comp_deletion.models[0].list_of_parameters[1]
    assert vmax.comp is not None
    replaced_by = vmax.comp.replaced_by
    assert replaced_by is not None
    assert replaced_by.sbml_type == "ReplacedBy"
    assert replaced_by.pk == "comp_deletion/ReplacedBy:meta_Vmax_shared"
    assert replaced_by.meta_id == "meta_Vmax_shared"
    assert replaced_by.submodel_ref == "cell2"
    assert replaced_by.port_ref == "Vmax_port"


def test_nested_sbase_ref_is_read(comp_deletion: Report) -> None:
    """A reference which reaches into a submodel of a submodel keeps its chain.

    comp §3.7.2 lets an `SBaseRef` carry an `SBaseRef` of its own, which names
    an element of the model the referenced submodel instantiates.
    """
    (medium,) = comp_deletion.models[0].list_of_compartments
    assert medium.comp is not None
    through_tissue = medium.comp.replaced_elements[2]
    assert through_tissue.submodel_ref == "tissue1"
    assert through_tissue.id_ref == "cell_in_tissue"
    nested = through_tissue.sbase_ref
    assert nested is not None
    assert nested.sbml_type == "SBaseRef"
    assert nested.pk == "comp_deletion/SBaseRef:meta_medium_tissue.sBaseRef"
    assert nested.port_ref == "cell_port"
    assert nested.sbase_ref is None


def test_port_carries_the_nested_reference_of_its_class(comp_deletion: Report) -> None:
    """A port is an `SBaseRef` and may carry a nested reference (comp §3.4.3)."""
    ports = {port.id: port for port in comp_deletion.models[0].list_of_ports}
    assert ports["per_min_port"].unit_ref == "per_min"
    assert ports["per_min_port"].sbase_ref is None
    assert ports["glc_amount_rule_port"].meta_id_ref == "meta_glc_amount_rule"


def test_external_model_definition_carries_its_md5(comp_deletion: Report) -> None:
    """The checksum of the referenced document is read (comp §3.3.2)."""
    (emd,) = comp_deletion.external_model_definitions
    assert emd.source == "unit_definitions.xml"
    assert emd.model_ref == "unit_definitions"
    assert emd.md5 == "bde1522151d26d8fbca09893ce85ac52"


def test_gene_product_association_is_the_tree_of_the_specification() -> None:
    """The association of a reaction is the tree of fbc §3.9, not an infix string."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "fbc_constraints_v3.xml")
    reaction = next(r for r in report.models[0].list_of_reactions if r.id == "v1")
    assert reaction.fbc is not None
    association = reaction.fbc.gene_product_association
    assert association is not None
    assert association.sbml_type == "GeneProductAssociation"
    assert association.id == "gpa_v1"
    assert association.name == "association of the uptake"
    assert association.pk == "fbc_constraints_v3/GeneProductAssociation:gpa_v1"

    root = association.association
    assert isinstance(root, Or)
    assert root.pk == "fbc_constraints_v3/Or:gpa_v1.association"
    complex_, single = root.associations
    assert isinstance(complex_, And)
    refs = [ref for ref in complex_.associations if isinstance(ref, GeneProductRef)]
    assert [ref.gene_product for ref in refs] == ["g_ptsG", "g_ptsH"]
    assert isinstance(single, GeneProductRef)
    assert single.id == "ref_galP"
    assert single.gene_product == "g_galP"


def test_the_nodes_of_an_association_leave_their_xml_to_the_reaction() -> None:
    """The xml of an association is part of the xml of its reaction.

    Every node of the tree repeated the xml of its subtree, so the bytes of an
    association grew with its depth times its size: 5 MB of the report of
    Recon3D. The reaction carries the whole association as the file writes it.
    """
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "fbc_constraints_v3.xml")
    reaction = next(r for r in report.models[0].list_of_reactions if r.id == "v1")
    assert reaction.xml is not None
    assert '<fbc:geneProductRef fbc:id="ref_galP"' in reaction.xml
    assert reaction.fbc is not None
    association = reaction.fbc.gene_product_association
    assert association is not None
    root = association.association
    assert isinstance(root, Or)
    nodes = [association, root, *root.associations]
    assert [node.xml for node in nodes] == [None] * len(nodes)


def test_the_json_of_an_association_node_leaves_out_what_it_does_not_carry() -> None:
    """A node of an association tree is written without its empty attributes.

    The 33000 nodes of the association trees of Recon3D carry none of the
    attributes of `SBase` in the file, and their nulls and empty lists were
    4.5 MB of the report. Every one of the attributes is optional in the
    schema, and the JSON reads back into the same node.
    """
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "fbc_constraints_v3.xml")
    reaction = next(r for r in report.models[0].list_of_reactions if r.id == "v1")
    assert reaction.fbc is not None
    association = reaction.fbc.gene_product_association
    assert association is not None
    data = json.loads(association.model_dump_json(by_alias=True))
    assert data["id"] == "gpa_v1"
    root = data["association"]
    assert set(root) == {"pk", "sbmlType", "associations"}
    complex_, single = root["associations"]
    assert set(complex_) == {"pk", "sbmlType", "associations"}
    assert set(complex_["associations"][0]) == {"pk", "sbmlType", "geneProduct"}
    assert set(single) == {"pk", "sbmlType", "id", "geneProduct"}
    assert type(association).model_validate(data) == association
    # an element of every other type keeps its attributes, empty or not
    assert "notes" in json.loads(reaction.model_dump_json(by_alias=True))


def test_the_document_is_keyed_without_writing_its_xml(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The key of the document is given, so the report never serialises the file.

    Every call of the key of an element fell back to the digest of its xml,
    and for the document, whose key is fixed, that was the whole file three
    times over: 0.8 s of the report of Recon3D, for a key nothing used.
    """
    doc = read_sbml(EXAMPLES_DIR / "fbc_constraints_v3.xml")

    def to_sbml(_: libsbml.SBMLDocument) -> str:
        raise AssertionError("the document is written to xml")

    monkeypatch.setattr(libsbml.SBMLDocument, "toSBML", to_sbml)
    assert SBMLDocumentInfo(doc).document().pk == "document/SBMLDocument:document"


def test_association_of_a_single_gene_product() -> None:
    """An association which is one gene product is a reference without a node above it."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "fbc_constraints_v3.xml")
    reaction = next(r for r in report.models[0].list_of_reactions if r.id == "v2")
    assert reaction.fbc is not None
    association = reaction.fbc.gene_product_association
    assert association is not None
    assert association.id is None
    assert association.pk == (
        "fbc_constraints_v3/GeneProductAssociation:v2.geneProductAssociation"
    )
    root = association.association
    assert isinstance(root, GeneProductRef)
    assert root.gene_product == "g_galP"
    assert root.pk == (
        "fbc_constraints_v3/GeneProductRef:v2.geneProductAssociation.association"
    )


def test_reaction_without_gene_product_association() -> None:
    """A reaction which names no gene product carries no association."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "fbc_constraints_v3.xml")
    reaction = next(r for r in report.models[0].list_of_reactions if r.id == "EX_glc")
    assert reaction.fbc is not None
    assert reaction.fbc.gene_product_association is None


def test_flux_bounds_of_a_version_1_model() -> None:
    """A Version 1 document carries its flux bounds, which no later version has."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "fbc_bounds_v1.xml")
    model = report.models[0]
    assert [b.id for b in model.list_of_flux_bounds] == [
        "v1_lb",
        "v1_ub",
        "EX_glc_fixed",
    ]
    lower, upper, fixed = model.list_of_flux_bounds
    assert lower.pk == "fbc_bounds_v1/FluxBound:v1_lb"
    assert lower.sbml_type == "FluxBound"
    assert (lower.reaction, lower.operation, lower.value) == ("v1", "greaterEqual", 0.0)
    assert lower.name == "lower bound of the glycolysis"
    assert lower.notes is not None
    assert (upper.reaction, upper.operation) == ("v1", "lessEqual")
    assert upper.value == float("inf")
    assert (fixed.reaction, fixed.operation, fixed.value) == ("EX_glc", "equal", -10.0)


def test_version_2_model_has_no_flux_bound_object() -> None:
    """Version 2 replaced the flux bounds by the two attributes of a reaction."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "fbc_mass_charge.xml")
    assert report.models[0].list_of_flux_bounds == []


def test_strict_and_active_objective() -> None:
    """The model says whether it is strict and which of its objectives is optimised."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "fbc_constraints_v3.xml")
    fbc = report.models[0].fbc
    assert fbc is not None
    assert fbc.strict is False
    assert fbc.active_objective == "growth_max"


def test_version_1_model_has_no_strict() -> None:
    """The strict attribute exists from Version 2 on, a Version 1 model reports none."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "fbc_bounds_v1.xml")
    fbc = report.models[0].fbc
    assert fbc is not None
    assert fbc.strict is None
    assert fbc.active_objective == "biomass_max"


def test_flux_objective_is_an_element() -> None:
    """A flux objective carries its own identity, its variable type and its reactions."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "fbc_constraints_v3.xml")
    objectives = {o.id: o for o in report.models[0].list_of_objectives}
    linear = objectives["growth_max"].list_of_flux_objectives[0]
    assert linear.pk == "fbc_constraints_v3/FluxObjective:fo_biomass"
    assert linear.sbml_type == "FluxObjective"
    assert linear.name == "the biomass term"
    assert (linear.reaction, linear.coefficient) == ("EX_biomass", 1.0)
    assert linear.variable_type == "linear"
    assert linear.reaction2 is None

    quadratic = objectives["uptake_min"].list_of_flux_objectives[0]
    assert quadratic.variable_type == "quadratic"
    assert (quadratic.reaction, quadratic.reaction2) == ("v1", "v2")


def test_flux_objective_without_an_id_is_keyed_by_its_objective() -> None:
    """A flux objective which carries no id is named by its objective and its reaction."""
    report = SBMLDocumentInfo.from_sbml(FBC_ECOLI_CORE_SBML)
    flux_objective = report.models[0].list_of_objectives[0].list_of_flux_objectives[0]
    assert flux_objective.pk == (
        "e_coli_core/FluxObjective:obj.fluxObjective.R_BIOMASS_Ecoli_core_w_GAM"
    )
    assert flux_objective.variable_type is None


FLUX_OBJECTIVES_OF_ONE_REACTION_SBML = """<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" level="3" version="1"
      xmlns:fbc="http://www.sbml.org/sbml/level3/version1/fbc/version3"
      fbc:required="false">
  <model id="m" fbc:strict="true">
    <listOfCompartments><compartment id="c" constant="true"/></listOfCompartments>
    <listOfSpecies>
      <species id="A" compartment="c" hasOnlySubstanceUnits="false"
               boundaryCondition="false" constant="false"/>
      <species id="B" compartment="c" hasOnlySubstanceUnits="false"
               boundaryCondition="false" constant="false"/>
    </listOfSpecies>
    <listOfParameters>
      <parameter id="lb" value="-1000" constant="true"/>
      <parameter id="ub" value="1000" constant="true"/>
    </listOfParameters>
    <listOfReactions>
      <reaction id="R1" reversible="false" fast="false"
                fbc:lowerFluxBound="lb" fbc:upperFluxBound="ub">
        <listOfReactants>
          <speciesReference species="A" stoichiometry="1" constant="true"/>
        </listOfReactants>
        <listOfProducts>
          <speciesReference species="B" stoichiometry="1" constant="true"/>
        </listOfProducts>
      </reaction>
      <reaction id="R2" reversible="false" fast="false"
                fbc:lowerFluxBound="lb" fbc:upperFluxBound="ub">
        <listOfReactants>
          <speciesReference species="B" stoichiometry="1" constant="true"/>
        </listOfReactants>
      </reaction>
    </listOfReactions>
    <fbc:listOfObjectives fbc:activeObjective="obj">
      <fbc:objective fbc:id="obj" fbc:type="maximize">
        <fbc:listOfFluxObjectives>
          <fbc:fluxObjective fbc:reaction="R1" fbc:coefficient="3"
                             fbc:variableType="linear"/>
          <fbc:fluxObjective fbc:reaction="R1" fbc:coefficient="1"
                             fbc:variableType="quadratic"/>
          <fbc:fluxObjective fbc:reaction="R1" fbc:reaction2="R2"
                             fbc:coefficient="2" fbc:variableType="quadratic"/>
          <fbc:fluxObjective fbc:reaction="R1" fbc:coefficient="4"
                             fbc:variableType="linear"/>
        </fbc:listOfFluxObjectives>
      </fbc:objective>
    </fbc:listOfObjectives>
  </model>
</sbml>"""


def test_flux_objectives_of_one_reaction_have_a_key_each() -> None:
    """The terms of one objective on one reaction are told apart by their key.

    fbc Version 3 lets an objective weigh one flux in several terms, a linear
    and a quadratic one, or a product with a second flux, and the id of a flux
    objective is optional (fbc §3.7), so the reaction alone keys none of them.
    A term is keyed by the fluxes it multiplies, which the file does not
    change when it reorders its terms, and a term which repeats another one
    of the same fluxes is told apart by its occurrence.
    """
    doc: libsbml.SBMLDocument = read_sbml(FLUX_OBJECTIVES_OF_ONE_REACTION_SBML)
    doc.checkConsistency()
    assert doc.getNumErrors(libsbml.LIBSBML_SEV_ERROR) == 0
    report = SBMLDocumentInfo.from_doc(doc)
    (objective,) = report.models[0].list_of_objectives
    assert [f.pk for f in objective.list_of_flux_objectives] == [
        "m/FluxObjective:obj.fluxObjective.R1",
        "m/FluxObjective:obj.fluxObjective.R1.R1",
        "m/FluxObjective:obj.fluxObjective.R1.R2",
        "m/FluxObjective:obj.fluxObjective.R1.1",
    ]
    assert all(
        f.pk in report.link_graph.nodes for f in objective.list_of_flux_objectives
    )


def test_a_species_twice_among_the_reactants_has_two_keys() -> None:
    """Two references of one reaction to one species are two elements of the report.

    A species may occur more than once in the reactants or the products of a
    reaction, the stoichiometries add up (core §4.11.3), so the species does
    not key the reference alone: the second one is told apart by its
    occurrence and the first keeps the key it always had.
    """
    sbml = """<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core"
      level="3" version="2">
      <model id="m">
        <listOfCompartments><compartment id="c" constant="true"/></listOfCompartments>
        <listOfSpecies>
          <species id="s" compartment="c" hasOnlySubstanceUnits="false"
                   boundaryCondition="false" constant="false"/>
        </listOfSpecies>
        <listOfReactions>
          <reaction id="r" reversible="false">
            <listOfReactants>
              <speciesReference species="s" stoichiometry="1" constant="true"/>
              <speciesReference species="s" stoichiometry="2" constant="true"/>
            </listOfReactants>
            <listOfModifiers>
              <modifierSpeciesReference species="s"/>
              <modifierSpeciesReference species="s"/>
            </listOfModifiers>
          </reaction>
        </listOfReactions>
      </model>
    </sbml>"""
    report = SBMLDocumentInfo.from_sbml(sbml)
    (reaction,) = report.models[0].list_of_reactions
    assert [sr.pk for sr in reaction.list_of_reactants] == [
        "m/SpeciesReference:r.reactant.s",
        "m/SpeciesReference:r.reactant.s.1",
    ]
    assert [sr.pk for sr in reaction.list_of_modifiers] == [
        "m/ModifierSpeciesReference:r.modifier.s",
        "m/ModifierSpeciesReference:r.modifier.s.1",
    ]
    assert [
        (e.source, e.kind.value)
        for e in report.link_graph.edges
        if e.kind in {EdgeKind.REACTANT, EdgeKind.MODIFIER}
    ] == [
        ("m/Reaction:r", "reactant"),
        ("m/SpeciesReference:r.reactant.s", "reactant"),
        ("m/Reaction:r", "reactant"),
        ("m/SpeciesReference:r.reactant.s.1", "reactant"),
        ("m/Reaction:r", "modifier"),
        ("m/ModifierSpeciesReference:r.modifier.s", "modifier"),
        ("m/Reaction:r", "modifier"),
        ("m/ModifierSpeciesReference:r.modifier.s.1", "modifier"),
    ]


def test_user_defined_constraints_of_a_version_3_model() -> None:
    """A Version 3 document carries its user defined constraints with their components."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "fbc_constraints_v3.xml")
    model = report.models[0]
    assert [c.id for c in model.list_of_user_defined_constraints] == ["ratio", "budget"]
    ratio = model.list_of_user_defined_constraints[0]
    assert ratio.pk == "fbc_constraints_v3/UserDefinedConstraint:ratio"
    assert ratio.name == "the growth is twice the uptake"
    assert (ratio.lower_bound, ratio.upper_bound) == ("ratio_lb", "ratio_ub")
    assert ratio.notes is not None
    first, second = ratio.list_of_user_defined_constraint_components
    assert first.pk == "fbc_constraints_v3/UserDefinedConstraintComponent:ratio_v1"
    assert first.sbml_type == "UserDefinedConstraintComponent"
    assert (first.variable, first.coefficient) == ("v1", "c_two")
    assert first.variable_type == "linear"
    assert first.variable2 is None
    assert second.variable == "v2"

    quadratic = model.list_of_user_defined_constraints[1]
    # every constraint is bounded by parameters of its own
    assert (quadratic.lower_bound, quadratic.upper_bound) == ("budget_lb", "budget_ub")
    component = quadratic.list_of_user_defined_constraint_components[0]
    assert (component.variable, component.variable2) == ("v2", "maintenance")
    assert component.variable_type == "quadratic"


def test_key_value_pairs_of_an_element() -> None:
    """The controlled annotation of fbc Version 3 is carried by every element."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "fbc_constraints_v3.xml")
    model = report.models[0]
    assert [(p.key, p.value, p.uri) for p in model.key_value_pairs] == [
        ("reconstruction", "manual", "https://sbml.org/fbc/keyvaluepair"),
        ("solver", "glpk", None),
    ]
    parameter = next(p for p in model.list_of_parameters if p.id == "maintenance")
    assert [(p.key, p.value) for p in parameter.key_value_pairs] == [
        ("source", "measured")
    ]
    assert model.list_of_species[0].key_value_pairs == []


def test_charge_of_a_version_3_species_is_a_double() -> None:
    """Version 3 widened the charge to a double, for a pseudoisomer."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "fbc_constraints_v3.xml")
    species = {s.id: s for s in report.models[0].list_of_species}
    assert species["pi"].fbc is not None
    assert species["pi"].fbc.charge == -1.5
    assert species["glc"].fbc is not None
    assert species["glc"].fbc.charge == 0.0


def test_charge_of_a_version_2_species_is_read_as_an_integer() -> None:
    """Before Version 3 the charge is an integer, which libsbml reads with its own getter."""
    report = SBMLDocumentInfo.from_sbml(FBC_ECOLI_CORE_SBML)
    species = next(s for s in report.models[0].list_of_species if s.id == "M_atp_c")
    assert species.fbc is not None
    assert species.fbc.charge == -4.0
    assert species.fbc.chemical_formula == "C10H12N5O13P3"


def test_fbc_block_of_an_element_which_sets_nothing() -> None:
    """An element of an fbc document which sets no fbc attribute carries no fbc block."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "fbc_bounds_v1.xml")
    model = report.models[0]
    # a Version 1 reaction has neither a bound nor an association, the attributes
    # do not exist in that version of the package
    assert all(r.fbc is None for r in model.list_of_reactions)
    biomass = next(s for s in model.list_of_species if s.id == "biomass")
    assert biomass.fbc is None
    glucose = next(s for s in model.list_of_species if s.id == "glc")
    assert glucose.fbc is not None


@pytest.fixture(scope="module")
def qual_example() -> Report:
    """The report of the qualitative example model."""
    return SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "qual_example.xml")


def test_qualitative_species_of_a_model(qual_example: Report) -> None:
    """A qualitative species carries its compartment and its levels."""
    model = qual_example.models[0]
    species = model.list_of_qualitative_species
    assert [s.id for s in species] == ["S", "G", "P"]
    signal, gene, protein = species
    assert signal.sbml_type == "QualitativeSpecies"
    assert signal.pk == "qual_example/QualitativeSpecies:S"
    assert signal.name == "signal"
    assert signal.compartment == "cell"
    assert signal.constant is True
    # an unset level is None and not the maximum integer libsbml answers with
    assert signal.initial_level is None
    assert signal.max_level == 1
    assert gene.constant is False
    assert (gene.initial_level, gene.max_level) == (0, 1)
    assert (protein.initial_level, protein.max_level) == (1, 2)


def test_qualitative_species_carries_its_sbase_fields(qual_example: Report) -> None:
    """The notes and the annotation of a qualitative species are part of the report."""
    signal = qual_example.models[0].list_of_qualitative_species[0]
    assert signal.meta_id == "meta_S"
    # an extracellular signal which an experiment sets is a perturbing agent, the
    # term the example carried before named a polypeptide chain
    assert signal.sbo == "SBO:0000405"
    assert signal.notes is not None
    assert "input of the system" in signal.notes
    assert [term.qualifier for term in signal.cvterms] == [
        "BQB_IS",
        "BQB_IS_VERSION_OF",
    ]
    assert signal.xml is not None


def test_transition_with_its_inputs_and_outputs(qual_example: Report) -> None:
    """A transition carries its inputs, its outputs and their attributes."""
    model = qual_example.models[0]
    assert [t.id for t in model.list_of_transitions] == ["tr_G", "tr_P"]
    transition = model.list_of_transitions[0]
    assert transition.sbml_type == "Transition"
    assert transition.pk == "qual_example/Transition:tr_G"
    assert transition.name == "expression of the gene"

    signal, protein, gene = transition.list_of_inputs
    assert signal.sbml_type == "Input"
    assert signal.pk == "qual_example/Input:theta_G_S"
    assert signal.qualitative_species == "S"
    assert signal.threshold_level == 1
    # the word of the specification, which libsbml answers as an integer
    assert signal.transition_effect == "none"
    assert signal.sign == "positive"
    assert protein.sign == "negative"
    assert gene.qualitative_species == "G"

    (output,) = transition.list_of_outputs
    assert output.sbml_type == "Output"
    assert output.pk == "qual_example/Output:out_G"
    assert output.qualitative_species == "G"
    assert output.transition_effect == "assignmentLevel"
    assert output.output_level is None


@pytest.mark.parametrize(
    "sign", ["positive", "negative", "dual", "unknown"], ids=lambda sign: sign
)
def test_every_sign_of_an_input_is_the_word_of_the_specification(sign: str) -> None:
    """The four signs of qual §3.6.1 reach the report as the words they are.

    libsbml answers the sign as the integer of its constant, and the report
    maps it; no shipped model uses `dual` or `unknown`.
    """
    sbml = f"""<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core"
      xmlns:qual="http://www.sbml.org/sbml/level3/version1/qual/version1"
      level="3" version="1" qual:required="true">
      <model id="m">
        <listOfCompartments><compartment id="c" constant="true"/></listOfCompartments>
        <qual:listOfQualitativeSpecies>
          <qual:qualitativeSpecies qual:id="A" qual:compartment="c"
                                   qual:constant="false"/>
        </qual:listOfQualitativeSpecies>
        <qual:listOfTransitions>
          <qual:transition qual:id="t">
            <qual:listOfInputs>
              <qual:input qual:qualitativeSpecies="A" qual:transitionEffect="none"
                          qual:sign="{sign}"/>
            </qual:listOfInputs>
            <qual:listOfOutputs>
              <qual:output qual:qualitativeSpecies="A"
                           qual:transitionEffect="assignmentLevel"/>
            </qual:listOfOutputs>
            <qual:listOfFunctionTerms>
              <qual:defaultTerm qual:resultLevel="0"/>
            </qual:listOfFunctionTerms>
          </qual:transition>
        </qual:listOfTransitions>
      </model>
    </sbml>"""
    doc: libsbml.SBMLDocument = read_sbml(sbml)
    doc.checkConsistency()
    assert doc.getNumErrors(libsbml.LIBSBML_SEV_ERROR) == 0
    report = SBMLDocumentInfo.from_doc(doc)
    (transition,) = report.models[0].list_of_transitions
    (qual_input,) = transition.list_of_inputs
    assert qual_input.sign == sign


def test_petri_net_transition_consumes_and_produces(qual_example: Report) -> None:
    """The second transition carries the two effects of the Petri net formalism."""
    transition = qual_example.models[0].list_of_transitions[1]
    gene, protein = transition.list_of_inputs
    assert gene.transition_effect == "consumption"
    assert protein.transition_effect == "none"
    (output,) = transition.list_of_outputs
    assert output.transition_effect == "production"
    assert output.output_level == 1


def test_function_terms_and_default_term(qual_example: Report) -> None:
    """The function terms of a transition carry their result level and their math."""
    transition = qual_example.models[0].list_of_transitions[0]
    terms = transition.list_of_function_terms
    assert [t.result_level for t in terms] == [1, 1]
    first = terms[0]
    assert first.sbml_type == "FunctionTerm"
    assert first.pk == "qual_example/FunctionTerm:tr_G.functionTerm.0"
    assert first.math is not None
    assert first.math.formula == "(S >= theta_G_S) && (P < theta_G_P)"

    default = transition.default_term
    assert default is not None
    assert default.sbml_type == "DefaultTerm"
    assert default.pk == "qual_example/DefaultTerm:tr_G.defaultTerm"
    assert default.result_level == 0


def test_model_without_qual_carries_no_qual_lists(repressilator: Report) -> None:
    """A model which does not use the package has neither list."""
    model = repressilator.models[0]
    assert model.list_of_qualitative_species == []
    assert model.list_of_transitions == []
