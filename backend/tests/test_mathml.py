"""Tests of the math rendering."""

import sys
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor

import libsbml
import pytest

from sbml4humans import mathml


# the pk `math_info` names in its log, which a unit test does not read
PK = "m/AssignmentRule:r"

formulas = [
    "1 dimensionless",
    "power(3, 5) / x * glc",
    "GK_Vmax * GK_gc_free * (atp/(GK_k_atp + atp)) * f_gly * "
    "(power(glc,GK_n)/(power(glc,GK_n) + power(GK_k_glc, GK_n)))",
    "piecewise(3, x>3, 5)",
    "piecewise(x, x > y, y)",
    "lambda(x, y, piecewise(x, x > y, y))",
    "lambda(x, y, x+y)",
    "(1 - gamma) * GSn + gamma * GSp",
    "piecewise(0, (delay(dClk, tau1) - delay(Per, tau1)) < 0, "
    "delay(dClk, tau1) - delay(Per, tau1))",
    "piecewise(VmaxM, exercise_level == 1, "
    "piecewise(VmaxH, exercise_level == 2, VmaxVH))",
    "Gamma(v, u, J, K)",
    "lambda(r, C, k, r * C * (1 - C / k))",
]

cmathmls = [
    """
    <math xmlns="http://www.w3.org/1998/Math/MathML">
    <apply>
    <divide/>
    <apply>
        <times/>
        <cn>243</cn>
        <ci>glc</ci>
    </apply>
    <ci>x</ci>
    </apply>
    </math>
    """,
    """
    <math xmlns="http://www.w3.org/1998/Math/MathML">
      <apply>
        <times></times>
        <ci> f_gly </ci>
        <ci> GK_Vmax </ci>
        <apply>
          <divide></divide>
          <ci> atp </ci>
          <apply>
            <plus></plus>
            <ci> GK_k_atp </ci>
            <ci> atp </ci>
          </apply>
        </apply>
      </apply>
    </math>
    """,
]


def formula_to_latex(formula: str) -> str:
    """Render the formula as latex."""
    astnode = libsbml.parseL3Formula(formula)
    assert astnode is not None, libsbml.getLastParseL3Error()
    return mathml.astnode_to_latex(astnode)


@pytest.mark.parametrize("formula", formulas)
def test_astnode_to_latex(formula: str) -> None:
    """The math of a formula is rendered as latex."""
    latex = formula_to_latex(formula)
    assert latex
    assert "$" not in latex


@pytest.mark.parametrize("cmathml", cmathmls)
def test_cmathml_to_latex(cmathml: str) -> None:
    """Content MathML is rendered as latex."""
    latex = mathml.cmathml_to_latex(cmathml)
    assert r"\mathit{" in latex


def test_piecewise_to_latex() -> None:
    """A piecewise function is rendered as cases."""
    latex = formula_to_latex("piecewise(x, x > y, y)").strip()
    assert latex.startswith(r"\begin{cases}")
    assert latex.endswith(r"\end{cases}")
    assert "otherwise" in latex


@pytest.mark.parametrize(
    "symbol, expected",
    [
        ("x", r"\mathit{x}"),
        ("alpha", r"\mathit{\alpha}"),
        ("Gamma", r"\mathit{\Gamma}"),
        ("delta", r"\mathit{\delta}"),
        ("pi", r"\mathit{\pi}"),
        ("rho", r"\mathit{\rho}"),
        ("lambda", r"\mathit{lambda}"),
        ("k_glc", r"\mathit{k_{glc}}"),
        ("k_glc_1", r"\mathit{k\_glc\_1}"),
    ],
)
def test_symbol_to_latex(symbol: str, expected: str) -> None:
    """Symbols are rendered with greek letters and subscripts."""
    assert mathml.symbol_to_latex(symbol) == expected


def test_math_info() -> None:
    """The math of a node is rendered as latex and as formula."""
    astnode = libsbml.parseL3Formula("k1 * S1 / (KM + S1)")
    info = mathml.math_info(astnode, PK)
    assert info.formula == "k1 * S1 / (KM + S1)"
    assert info.latex is not None
    assert r"\mathit{S1}" in info.latex


def test_math_symbols() -> None:
    """The symbols of a math are the names of its ASTNodes, without functions."""
    astnode = libsbml.parseL3Formula("piecewise(f(x, 2), x > y, time)")
    assert mathml.math_symbols(astnode) == {"f", "x", "y", "time"}


def test_math_symbols_of_lambda_without_bound_variables() -> None:
    """The bound variables of a lambda are no symbols of the math."""
    astnode = libsbml.parseL3Formula("lambda(x, y, x * k + y)")
    assert mathml.math_symbols(astnode) == {"k"}


def test_math_symbols_of_nested_lambda() -> None:
    """The bound variables of a nested lambda are no symbols either."""
    astnode = libsbml.parseL3Formula("lambda(x, lambda(y, x * y * k))")
    assert mathml.math_symbols(astnode) == {"k"}


def test_math_symbols_of_a_bound_variable_which_is_free_outside_its_lambda() -> None:
    """A name a lambda binds is still a symbol where it occurs outside that lambda."""
    astnode = libsbml.parseL3Formula("x + lambda(x, x * q)")
    assert mathml.math_symbols(astnode) == {"q", "x"}


@pytest.mark.parametrize(
    "formula, expected",
    [
        ("and(geq(S, t1), lt(P, t2))", r"\wedge "),
        ("or(geq(S, 1), lt(P, 2))", r"\vee "),
        ("not(gt(a, b))", r"\neg "),
        ("xor(a, b)", r"\oplus "),
    ],
)
def test_logical_connectives_are_rendered_as_operators(
    formula: str, expected: str
) -> None:
    """A connective is the symbol of logic, which latex spaces as an operator.

    The stylesheet wrote the word of the operator into the latex, where it ended
    up glued to its operands ("(S >= t1)and(P < t2)"), which is what the
    condition of every function term of a qualitative model is built from.
    """
    latex = mathml.math_info(libsbml.parseL3Formula(formula), PK).latex
    assert latex is not None
    assert expected in latex
    assert "and(" not in latex


@pytest.mark.parametrize(
    "cmathml, expected",
    [
        (
            "<math xmlns='http://www.w3.org/1998/Math/MathML'>"
            "<apply><times/><ci>Vmax</ci><ci>S1</ci></apply></math>",
            r"\mathit{Vmax}\cdot \mathit{S1}",
        ),
        (
            "<math xmlns='http://www.w3.org/1998/Math/MathML'>"
            "<cn type='e-notation'>6.02<sep/>23</cn></math>",
            r"6.02\cdot {10}^{23}",
        ),
    ],
)
def test_a_product_is_set_with_the_operator_of_latex(
    cmathml: str, expected: str
) -> None:
    r"""The dot of a product is the binary operator `\cdot`.

    The stylesheet wrote the middle dot U+00B7, which KaTeX sets as an
    ordinary symbol glued to its left operand: `Vmax· S1` next to a spaced
    `Km + S1`.
    """
    latex = mathml.cmathml_to_latex(cmathml)
    assert expected in latex
    assert "\u00b7" not in latex


def test_latex_in_threads() -> None:
    """Threads render the math as one thread does, each with its stylesheets.

    The api builds its reports in a threadpool, and a compiled stylesheet of
    lxml must not be shared between threads.
    """
    astnodes = [libsbml.parseL3Formula(formula) for formula in formulas]
    expected = [mathml.astnode_to_latex(astnode) for astnode in astnodes]

    def render(_: int) -> list[str]:
        """Render all formulas without the cache of the results."""
        return [
            mathml._convert_cmathml(
                libsbml.writeMathMLToString(astnode).replace(
                    '<?xml version="1.0" encoding="UTF-8"?>', ""
                )
            )
            for astnode in astnodes
        ]

    with ThreadPoolExecutor(max_workers=8) as executor:
        for latex in executor.map(render, range(32)):
            assert latex == expected


# -------------------------------------------------------------------------------------
# a math which cannot be typeset
# -------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "formula", ["lambda()", "1 + lambda()", "k * lambda()", "abs(lambda())"]
)
def test_a_childless_lambda_is_no_mathml(formula: str) -> None:
    """A childless lambda is refused wherever it sits in the tree.

    The Level 1 parser accepts `lambda()` as an `AST_LAMBDA` without children,
    whose MathML libsbml cannot write: `writeMathMLToString` ends the process
    with SIGSEGV (sbmlteam/libsbml#521), so the node is never handed to it.
    """
    astnode = libsbml.parseFormula(formula)
    assert astnode is not None
    assert mathml.unwritable_mathml(astnode) == "it holds a lambda without children"
    with pytest.raises(mathml.UnwritableMathError, match="lambda without children"):
        mathml.astnode_to_latex(astnode)


@pytest.mark.parametrize(
    "formula", ["lambda(x)", "lambda(x, x)", "lambda(x, y, x + y)"]
)
def test_a_lambda_with_children_is_mathml(formula: str) -> None:
    """A lambda with children is written and typeset as every other math is."""
    astnode = libsbml.parseFormula(formula)
    assert mathml.unwritable_mathml(astnode) is None
    assert mathml.astnode_to_latex(astnode)


@pytest.mark.parametrize(
    "formula", ["lambda()", "1 + lambda()", "k * lambda()", "abs(lambda())"]
)
def test_math_info_of_an_unwritable_math_is_its_formula(formula: str) -> None:
    """The math of a node libsbml cannot write is its formula without latex.

    `formulaToL3String` and `formulaToString` write the node without trouble,
    so the formula side of the report is unaffected.
    """
    astnode = libsbml.parseFormula(formula)
    info = mathml.math_info(astnode, PK)
    assert info.formula == formula
    assert info.latex is None


@pytest.mark.parametrize(("applies", "has_latex"), [(254, True), (255, False)])
def test_math_info_of_a_math_too_deep_for_lxml_is_its_formula(
    applies: int, has_latex: bool
) -> None:
    """The math of a node lxml refuses to parse is its formula without latex.

    lxml refuses a document deeper than 256 elements, which the MathML of 255
    nested applies is; at 254 the latex is still produced. libsbml writes the
    MathML of either depth, the wall is the parser of lxml.
    """
    deep = libsbml.parseL3Formula(
        "a - " + "(a - " * (applies - 1) + "a" + ")" * (applies - 1)
    )
    assert deep is not None
    assert mathml.unwritable_mathml(deep) is None
    info = mathml.math_info(deep, PK)
    assert info.formula.startswith("a - (a - (a")
    assert (info.latex is not None) == has_latex


# -------------------------------------------------------------------------------------
# the walks over an AST, which are iterative because an AST is deep
# -------------------------------------------------------------------------------------
def _wide_sum(terms: int) -> libsbml.ASTNode:
    """The AST of a flat MathML sum of `terms` names.

    The MathML reader of libsbml keeps no flat n-ary operator: it answers a
    right nested binary tree, so the root of a sum of `terms` names has two
    children and the tree is `terms` levels deep. A sum of a few hundred terms
    is what a real model brings, and it is what a recursive walk dies on.
    """
    cis = "".join(f"<ci> x{k} </ci>" for k in range(terms))
    astnode = libsbml.readMathMLFromString(
        '<math xmlns="http://www.w3.org/1998/Math/MathML">'
        f"<apply><plus/>{cis}</apply></math>"
    )
    assert astnode is not None
    return astnode


def test_a_flat_sum_is_read_as_a_deep_tree() -> None:
    """The premise of the walks: a wide sum of MathML is a deep AST."""
    astnode = _wide_sum(800)
    assert astnode.getNumChildren() == 2
    assert mathml.math_depth(astnode, {}) == 800


@pytest.mark.parametrize(
    ("formula", "depth"),
    [("a", 1), ("1 mole", 1), ("-a", 2), ("abs(a)", 2), ("abs(abs(a - 1))", 4)],
)
def test_math_depth(formula: str, depth: int) -> None:
    """The depth of an AST counts its levels, a node without children as one."""
    astnode = libsbml.parseL3Formula(formula)
    assert astnode is not None
    assert mathml.math_depth(astnode, {}) == depth


def test_math_depth_of_a_lambda_counts_its_body() -> None:
    """The deepest branch decides, which is the body of a lambda, not its bvars."""
    astnode = libsbml.parseL3Formula("lambda(x, y, abs(x - y))")
    assert astnode is not None
    assert mathml.math_depth(astnode, {}) == 4


# -------------------------------------------------------------------------------------
# the depth of a math with the calls of its function definitions expanded
# -------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("formula", "depth"),
    [
        # the call of `f` costs the levels of its body in place of the one level
        # the node would cost, and its argument is walked below the body
        ("f(a)", 11),
        ("f(abs(a))", 12),
        ("g(a)", 21),
        # nesting the calls multiplies the levels of the bodies, as the unit
        # inference walks the argument of a call below the body it expanded
        ("f(f(a))", 21),
        ("f(f(f(a)))", 31),
        ("f(g(a))", 31),
        # a name is no call, and a function nothing defines costs one level
        ("abs(f)", 2),
        ("h(a)", 2),
        ("1 + f(a)", 12),
    ],
)
def test_math_depth_expands_the_call_of_a_function_definition(
    formula: str, depth: int
) -> None:
    """A call of a function definition costs the levels of that definition."""
    astnode = libsbml.parseL3Formula(formula)
    assert astnode is not None
    assert mathml.math_depth(astnode, {"f": 10, "g": 20}) == depth


def _definitions(bodies: dict[str, str]) -> dict[str, libsbml.ASTNode]:
    """The math of a function definition of one bound variable per body."""
    definitions = {}
    for name, body in bodies.items():
        math = libsbml.parseL3Formula(f"lambda(y, {body})")
        assert math is not None, libsbml.getLastParseL3Error()
        definitions[name] = math
    return definitions


def test_function_depths_of_a_chain_of_definitions() -> None:
    """A definition which calls another costs the levels of that one as well."""
    links = 50
    bodies = {f"f{k}": (f"f{k + 1}(y)" if k + 1 < links else "y") for k in range(links)}
    depths = mathml.function_depths(_definitions(bodies))
    assert depths["f49"] == 1
    assert depths["f48"] == 2
    assert depths["f0"] == links


def test_function_depths_of_definitions_which_call_nothing() -> None:
    """A definition which calls none costs the levels of its body alone.

    The number of definitions is no cost of its own: 45,000 of them which call
    nothing were measured to leave the unit inference of libsbml untroubled,
    while a chain of 45,000 crashes it.
    """
    depths = mathml.function_depths(
        _definitions({f"f{k}": "abs(y - 1)" for k in range(100)})
    )
    assert set(depths.values()) == {3}


def test_function_depths_leaves_out_a_definition_which_calls_itself() -> None:
    """A cycle has no depth, so the definitions of it are missing from the result.

    Direct recursion, mutual recursion and a definition which calls into a
    cycle are all left out; a definition which has nothing to do with the cycle
    keeps its depth.
    """
    depths = mathml.function_depths(
        _definitions(
            {
                "self": "self(y)",
                "mutual1": "mutual2(y)",
                "mutual2": "mutual1(y)",
                "caller": "mutual1(y)",
                "plain": "abs(y)",
            }
        )
    )
    assert set(depths) == {"plain"}
    assert depths["plain"] == 2


def test_function_depths_of_a_math_which_is_no_lambda() -> None:
    """A definition without a body stands for itself, as its own math.

    The math of a function definition is a lambda whose last child is the
    body; a math which is none, and the childless lambda a Level 1 `formula`
    can hold, have no body to expand and cost their own levels.
    """
    plain = libsbml.parseL3Formula("abs(a)")
    childless = libsbml.parseFormula("lambda()")
    assert plain is not None and childless is not None
    depths = mathml.function_depths({"plain": plain, "childless": childless})
    assert depths == {"plain": 2, "childless": 1}


def test_the_walks_answer_a_wide_sum() -> None:
    """Every walk answers a sum far beyond the recursion limit of python."""
    terms = 2000
    astnode = _wide_sum(terms)
    assert mathml.unwritable_mathml(astnode) is None
    assert mathml.math_symbols(astnode) == {f"x{k}" for k in range(terms)}
    assert mathml.math_units(astnode) == set()


def test_the_walks_answer_a_deep_math() -> None:
    """Every walk answers a math nested far beyond the recursion limit."""
    applies = 2000
    astnode = libsbml.parseL3Formula(
        "a - " + "(a - " * (applies - 1) + "1 mole" + ")" * (applies - 1)
    )
    assert astnode is not None
    assert mathml.math_depth(astnode, {}) == applies + 1
    assert mathml.unwritable_mathml(astnode) is None
    assert mathml.math_symbols(astnode) == {"a"}
    assert mathml.math_units(astnode) == {"mole"}


def test_a_childless_lambda_is_found_at_the_bottom_of_a_deep_math() -> None:
    """The guard reaches the whole tree, not the levels a recursion survives."""
    astnode = libsbml.parseFormula("abs(" * 2000 + "lambda()" + ")" * 2000)
    assert astnode is not None
    assert mathml.math_depth(astnode, {}) == 2001
    assert mathml.unwritable_mathml(astnode) == "it holds a lambda without children"
    assert mathml.math_info(astnode, PK).latex is None


# -------------------------------------------------------------------------------------
# the cache of the latex, which is bounded in bytes
# -------------------------------------------------------------------------------------
def _entry_size(key: str, value: str) -> int:
    """The bytes the cache counts for one entry."""
    return sys.getsizeof(key) + sys.getsizeof(value)


@pytest.fixture
def latex_cache() -> Iterator[mathml._LatexCache]:
    """The cache of the module, emptied before and after the test."""
    mathml._latex_cache.clear()
    yield mathml._latex_cache
    mathml._latex_cache.clear()


def test_the_latex_of_a_math_is_served_from_the_cache(
    latex_cache: mathml._LatexCache, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The second conversion of one MathML converts nothing, it reads the cache."""
    cmathml = (
        "<math xmlns='http://www.w3.org/1998/Math/MathML'>"
        "<apply><times/><ci>Vmax</ci><ci>S1</ci></apply></math>"
    )
    latex = mathml.cmathml_to_latex(cmathml)
    assert r"\mathit{Vmax}" in latex
    assert len(latex_cache) == 1
    assert cmathml in latex_cache
    assert latex_cache.nbytes == _entry_size(cmathml, latex)

    def refuse(_: str) -> str:
        """Fail where the cache should have answered."""
        raise AssertionError("the math was converted a second time")

    monkeypatch.setattr(mathml, "_convert_cmathml", refuse)
    assert mathml.cmathml_to_latex(cmathml) == latex
    assert len(latex_cache) == 1


def test_the_cache_stays_under_its_bound_in_bytes() -> None:
    """More than fits is kept as much as fits, counted in bytes."""
    value = "x" * 1000
    cap = 10 * _entry_size("k" * 1000, value)
    cache = mathml._LatexCache(max_bytes=cap, max_entries=1000)
    for n in range(100):
        cache.put(f"{n:04d}" + "k" * 996, value)
        assert cache.nbytes <= cap
    assert len(cache) == 10
    assert cache.nbytes <= cap


def test_the_cache_stays_under_its_bound_in_entries() -> None:
    """A flood of small maths is bounded by the number of entries."""
    cache = mathml._LatexCache(max_bytes=32 * 1024 * 1024, max_entries=7)
    for n in range(100):
        cache.put(str(n), "a")
    assert len(cache) == 7
    assert [key in cache for key in ("92", "93", "99")] == [False, True, True]


def test_the_cache_evicts_the_least_recently_used_entry() -> None:
    """Reading an entry saves it, the one not read is the one which goes."""
    value = "x" * 100
    cache = mathml._LatexCache(max_bytes=3 * _entry_size("a", value), max_entries=100)
    for key in ["a", "b", "c"]:
        cache.put(key, value)
    # "a" is the oldest, reading it makes "b" the least recently used
    assert cache.get("a") == value
    cache.put("d", value)
    assert len(cache) == 3
    assert [key in cache for key in ("a", "b", "c", "d")] == [True, False, True, True]


def test_the_cache_keeps_no_entry_larger_than_itself() -> None:
    """A math too large for the whole cache does not empty it either."""
    value = "x" * 100
    cache = mathml._LatexCache(max_bytes=4 * _entry_size("a", value), max_entries=100)
    cache.put("a", value)
    cache.put("b", "x" * 10_000)
    assert len(cache) == 1
    assert "a" in cache
    assert "b" not in cache
    assert cache.nbytes == _entry_size("a", value)


def test_the_cache_replaces_an_entry_without_counting_it_twice() -> None:
    """A key put again holds its new value alone, whatever the old one was."""
    cache = mathml._LatexCache(max_bytes=32 * 1024, max_entries=100)
    cache.put("a", "x" * 100)
    cache.put("a", "y" * 10)
    assert len(cache) == 1
    assert cache.get("a") == "y" * 10
    assert cache.nbytes == _entry_size("a", "y" * 10)


def test_the_cache_is_used_by_threads_at_once() -> None:
    """Every thread gets the same latex, whichever of them converted it.

    The cache is the one structure the threads of the threadpool share, unlike
    the stylesheets, which are compiled per thread.
    """
    cache = mathml._LatexCache(max_bytes=1024 * 1024, max_entries=1000)
    keys = [f"math{n}" for n in range(200)]

    def fill(_: int) -> list[str | None]:
        """Put every key and read every key back."""
        for key in keys:
            cache.put(key, key.upper())
        return [cache.get(key) for key in keys]

    with ThreadPoolExecutor(max_workers=8) as executor:
        for values in executor.map(fill, range(16)):
            assert values == [key.upper() for key in keys]
    assert len(cache) == len(keys)
    assert cache.nbytes == sum(_entry_size(key, key.upper()) for key in keys)
