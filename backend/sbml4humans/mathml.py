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

Every walk over an AST of this module is iterative, over an explicit stack. The
MathML reader of libsbml keeps no flat n-ary operator: it builds a right nested
binary tree, so the AST of a sum of 800 terms is 800 levels deep while its root
has two children. A recursive walk therefore raises `RecursionError` a few
hundred terms into a math a real model brings, and with the stack exhausted
there is nothing left to answer with. These are the only walks over an AST in
python of the backend, nothing else below `sbml4humans/` calls `getChild`.
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


def unwritable_mathml(astnode: libsbml.ASTNode) -> str | None:
    """Why libsbml cannot write the MathML of a node, None when it can.

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

    `SBase.toSBML()` is the other writer of libsbml which dies on the shape,
    and the report calls it for the `xml` of every element. It is unreachable
    today: the shape arises in a Level 1 document alone, where `toSBML()`
    writes the attribute `formula` and never the math, and nothing converts
    the document of a report to another level. Should a conversion ever be
    added, that writer needs this guard as well.
    """
    stack: list[libsbml.ASTNode] = [astnode]
    while stack:
        node = stack.pop()
        if node.getType() == libsbml.AST_LAMBDA and node.getNumChildren() == 0:
            return "it holds a lambda without children"
        stack.extend(node.getChild(k) for k in range(node.getNumChildren()))
    return None


def astnode_to_latex(astnode: libsbml.ASTNode) -> str:
    """Convert an ASTNode to latex.

    Raises:
        UnwritableMathError: if libsbml cannot write the MathML of the node.
            The node is never handed to `writeMathMLToString`, which crashes
            the process rather than raising, so it is checked beforehand.
    """
    if (reason := unwritable_mathml(astnode)) is not None:
        raise UnwritableMathError(
            f"libsbml cannot write the MathML of this math, {reason}"
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


def math_info(astnode: libsbml.ASTNode, owner_pk: str) -> Math:
    """The math of the element `owner_pk` as latex and as L3 formula string.

    The latex is absent where it cannot be produced: where libsbml cannot write
    the MathML of the node, and where the conversion of that MathML fails,
    which lxml refuses beyond a document depth of 256. The infix formula is
    written for any node at any depth, so it is always reported, and the report
    of the document is never lost over one math. The pk of the owner names the
    element in the log, so that the math can be found in the model.
    """
    formula: str = libsbml.formulaToL3String(astnode)
    latex: str | None
    try:
        latex = astnode_to_latex(astnode)
    except (UnwritableMathError, ET.LxmlError) as err:
        logger.warning(
            "The math of %s is reported without latex, as its formula alone: "
            "%s (%.60s)",
            owner_pk,
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
    symbols: set[str] = set()
    # every node with the variables the lambdas around it bind, which are local
    # to their body and are no references of the model
    stack: list[tuple[libsbml.ASTNode, frozenset[str]]] = [(astnode, frozenset())]
    while stack:
        node, bvars = stack.pop()
        children = node.getNumChildren()
        if node.getType() == libsbml.AST_LAMBDA and children > 0:
            # the children of a lambda are its bound variables and, as last
            # child, its body, the only child which references anything
            last = children - 1
            bound = bvars | {node.getChild(k).getName() for k in range(last)}
            stack.append((node.getChild(last), bound))
            continue
        if node.isName() or (node.isFunction() and node.isUserFunction()):
            name: str = node.getName()
            if name not in bvars:
                symbols.add(name)
        stack.extend((node.getChild(k), bvars) for k in range(children))
    return symbols


def math_units(astnode: libsbml.ASTNode) -> set[str]:
    """The units the numbers of a math name with the attribute `sbml:units`.

    Level 3 lets a `cn` element say which units its number has (core §3.4.2),
    by the identifier of a unit definition of the model or of a base unit.
    """
    units: set[str] = set()
    stack: list[libsbml.ASTNode] = [astnode]
    while stack:
        node = stack.pop()
        if node.isNumber() and node.isSetUnits():
            units.add(node.getUnits())
        stack.extend(node.getChild(k) for k in range(node.getNumChildren()))
    return units
