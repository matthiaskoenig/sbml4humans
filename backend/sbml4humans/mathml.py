"""Rendering of the math of a model as latex.

The content MathML of libsbml is converted with xslt stylesheets to
presentation MathML and then to latex, followed by heuristic cleanups of the
latex for a better rendering. The stylesheets live in `sbml4humans.resources`.

Compiling a stylesheet costs about twenty times its application, so each is
compiled once per thread: an `XSLT` object of lxml must not be shared between
threads, and the api builds its reports in the threads of its threadpool.

Not every math can be typeset: libsbml cannot write the MathML of a node whose
shape its writer does not expect, and lxml refuses a MathML document deeper
than 256 elements. Such a math costs its latex and nothing else, `math_info`
reports it with the latex absent and the infix formula alone, which libsbml
writes for any node at any depth.
"""

import logging
import re
import threading
from functools import lru_cache

import libsbml
import lxml.etree as ET  # ty: ignore[unresolved-import]

from sbml4humans.model import Math
from sbml4humans.resources import XSLT_DIR


logger = logging.getLogger(__name__)

xslt_cmml2pmml = ET.parse(str(XSLT_DIR / "ctopff.xsl"))
xslt_pmml2tex = ET.parse(str(XSLT_DIR / "xsltml" / "mmltex.xsl"))


class _Transforms(threading.local):
    """The compiled stylesheets of the current thread, compiled on first use."""

    def __init__(self) -> None:
        """Compile the stylesheets for the thread which first uses them."""
        self.cmml2pmml = ET.XSLT(xslt_cmml2pmml)
        self.pmml2tex = ET.XSLT(xslt_pmml2tex)


_transforms = _Transforms()

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


class UnwritableMathError(ValueError):
    """A math whose MathML libsbml cannot write, so it cannot be typeset."""


def writes_as_mathml(astnode: libsbml.ASTNode) -> bool:
    """Whether libsbml can write the MathML of a node and of all its children.

    It cannot write a lambda without children: `writeLambda` reads the number
    of bound variables as the number of children less one, which wraps to
    `UINT_MAX` for a childless node, and dereferences the null child it then
    asks for, so `writeMathMLToString` ends the process with SIGSEGV
    (sbmlteam/libsbml#521). Of the 156 node types of libsbml a childless node
    crashes the writer for that one alone.

    The shape is invalid SBML, and the MathML reader and the Level 3 parser
    both refuse it; the Level 1 attribute `formula`, which `KineticLaw.getMath`
    parses with the Level 1 parser, is the one route into it from a document.
    It can sit anywhere inside a larger math, `1 + lambda()` crashes the writer
    just as `lambda()` does, so the whole tree is walked.
    """
    if astnode.getType() == libsbml.AST_LAMBDA and astnode.getNumChildren() == 0:
        return False
    return all(
        writes_as_mathml(astnode.getChild(k)) for k in range(astnode.getNumChildren())
    )


def astnode_to_latex(astnode: libsbml.ASTNode) -> str:
    """Convert an ASTNode to latex.

    Raises:
        UnwritableMathError: if libsbml cannot write the MathML of the node.
            The node is never handed to `writeMathMLToString`, which crashes
            the process rather than raising, so it is checked beforehand.
    """
    if not writes_as_mathml(astnode):
        raise UnwritableMathError(
            "libsbml cannot write the MathML of this math, it holds a lambda "
            "without children"
        )
    cmml_str: str = libsbml.writeMathMLToString(astnode)
    cmml_str = cmml_str.replace('<?xml version="1.0" encoding="UTF-8"?>', "")
    return cmathml_to_latex(cmml_str)


@lru_cache(maxsize=10000)
def cmathml_to_latex(cmml_str: str) -> str:
    """Convert content MathML to latex with the xslt transformations."""
    cmml_dom = ET.fromstring(cmml_str)
    transforms = _transforms
    pmml_dom = transforms.cmml2pmml(cmml_dom)
    tex_str = str(transforms.pmml2tex(pmml_dom))

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
    """The math of a node as latex and as L3 formula string.

    The latex is absent where it cannot be produced: where libsbml cannot write
    the MathML of the node, and where the conversion of that MathML fails,
    which lxml refuses beyond a document depth of 256. The infix formula is
    written for any node at any depth, so it is always reported, and the report
    of the document is never lost over one math.
    """
    formula: str = libsbml.formulaToL3String(astnode)
    latex: str | None
    try:
        latex = astnode_to_latex(astnode)
    except (UnwritableMathError, ET.LxmlError) as err:
        logger.warning(
            "The math is reported without latex, as its formula alone: %s (%.60s)",
            err,
            formula,
        )
        latex = None
    return Math(latex=latex, formula=formula)


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


def math_units(astnode: libsbml.ASTNode) -> set[str]:
    """The units the numbers of a math name with the attribute `sbml:units`.

    Level 3 lets a `cn` element say which units its number has (core §3.4.2),
    by the identifier of a unit definition of the model or of a base unit.
    """
    units: set[str] = set()
    if astnode.isNumber() and astnode.isSetUnits():
        units.add(astnode.getUnits())
    for k in range(astnode.getNumChildren()):
        units |= math_units(astnode.getChild(k))
    return units
