"""Tests of the math rendering."""

import libsbml
import pytest

from sbml4humans import mathml


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
    info = mathml.math_info(astnode)
    assert info.formula == "k1 * S1 / (KM + S1)"
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
