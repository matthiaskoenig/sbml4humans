"""Rendering of the math of a model as latex.

The content MathML of libsbml is converted with xslt stylesheets to
presentation MathML and then to latex, followed by heuristic cleanups of the
latex for a better rendering. The stylesheets live in `sbml4humans.resources`.
"""

import re
from functools import lru_cache

import libsbml
import lxml.etree as ET  # ty: ignore[unresolved-import]

from sbml4humans.model import Math
from sbml4humans.resources import XSLT_DIR


xslt_cmml2pmml = ET.parse(str(XSLT_DIR / "ctopff.xsl"))
xslt_pmml2tex = ET.parse(str(XSLT_DIR / "xsltml" / "mmltex.xsl"))

# greek symbols rendered in latex, without the small lambda which marks
# function definitions
GREEK_SYMBOLS = [
    "alpha",
    "beta",
    "gamma",
    "Gamma",
    "delta",
    "Delta",
    "epsilon",
    "zeta",
    "eta",
    "theta",
    "iota",
    "kappa",
    "Lambda",
    "mu",
    "nu",
    "omicron",
    "pi",
    "rho",
    "sigma",
    "tau",
    "upsilon",
    "Upsilon",
    "phi",
    "Phi",
    "chi",
    "psi",
    "Psi",
    "omega",
    "Omega",
]


def astnode_to_latex(astnode: libsbml.ASTNode) -> str:
    """Convert an ASTNode to latex."""
    cmml_str: str = libsbml.writeMathMLToString(astnode)
    cmml_str = cmml_str.replace('<?xml version="1.0" encoding="UTF-8"?>', "")
    return cmathml_to_latex(cmml_str)


@lru_cache(maxsize=10000)
def cmathml_to_latex(cmml_str: str) -> str:
    """Convert content MathML to latex with the xslt transformations."""
    cmml_dom = ET.fromstring(cmml_str)
    pmml_dom = ET.XSLT(xslt_cmml2pmml)(cmml_dom)
    tex_str = str(ET.XSLT(xslt_pmml2tex)(pmml_dom))

    # remove equation symbols
    tex_str = tex_str.replace("$", "")

    # fix piecewise
    tex_str = tex_str.replace(r"\hfill", "")
    tex_str = tex_str.replace(r"\multicolumn{2}{c}", "")
    tex_str = tex_str.replace(r"\left(\{\begin{array}{ccc}", r"\begin{cases} ")
    tex_str = tex_str.replace(r"\end{array}\right)", r"\end{cases}")
    tex_str = tex_str.replace(r"\{\begin{array}{ccc}", r"\begin{cases} ")
    tex_str = tex_str.replace(r"\end{array}", r"\end{cases}")

    # fix lambda function
    tex_str = tex_str.replace(r"}\mathit", r"}, \mathit")
    tex_str = tex_str.replace(r"\lambda ", r"\lambda(")
    tex_str = tex_str.replace(r"}.", "}) =")

    return _fix_mathit_symbols(tex_str)


def symbol_to_latex(symbol: str) -> str:
    """Convert a symbol to latex: mathit with escaped underscores."""
    symbol = symbol.replace(r"_", r"\_")
    return _fix_mathit_symbols(r"\mathit{" + symbol + "}")


def _fix_mathit_symbols(tex_str: str) -> str:
    """Heuristic replacements for a better latex rendering.

    A single underscore in a name becomes a subscript, greek symbols are
    rendered as such.
    """
    # \mathit{group1\_group2} -> \mathit{group1_{group2}}
    for m in re.findall(r"\\mathit{([a-zA-Z0-9]+)\\_([a-zA-Z0-9]+)}", tex_str):
        tex_str = tex_str.replace(
            r"\mathit{" + m[0] + r"\_" + m[1] + "}",
            r"\mathit{" + m[0] + r"_{" + m[1] + "}}",
        )

    for symbol in GREEK_SYMBOLS:
        tex_str = tex_str.replace(
            r"\mathit{" + symbol + "}", r"\mathit{" + f"\\{symbol}" + "}"
        )

    return tex_str


def math_info(astnode: libsbml.ASTNode) -> Math:
    """The math of a node as latex and as L3 formula string."""
    return Math(
        latex=astnode_to_latex(astnode), formula=libsbml.formulaToL3String(astnode)
    )


def math_symbols(astnode: libsbml.ASTNode) -> set[str]:
    """The names referenced by a math: variables, function names and csymbols.

    The bound variables of a lambda are local to it and are no references, only
    the symbols of its body are reported.

    The `time` csymbol is reported by libsbml as name `time`, it is kept and
    simply never resolves to an element.
    """
    if astnode.getType() == libsbml.AST_LAMBDA and astnode.getNumChildren() > 0:
        # the children of a lambda are its bound variables and, as last child,
        # its body
        last = astnode.getNumChildren() - 1
        bvars = {astnode.getChild(k).getName() for k in range(last)}
        return math_symbols(astnode.getChild(last)) - bvars

    symbols: set[str] = set()
    if astnode.isName() or (astnode.isFunction() and astnode.isUserFunction()):
        symbols.add(astnode.getName())
    for k in range(astnode.getNumChildren()):
        symbols |= math_symbols(astnode.getChild(k))
    return symbols
