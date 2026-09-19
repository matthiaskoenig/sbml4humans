"""Formatting of units as strings and latex."""

import contextlib
import math

import libsbml
import numpy as np
import pint


ureg = pint.UnitRegistry()
ureg.define("item = dimensionless")
ureg.define("avogadro = 6.02214179E23 dimensionless")
Q_ = ureg.Quantity

# the symbols of the base units which pint does not write. A units attribute
# which names a base unit shows its identifier next to the rendering, and
# `dimensionless` has no symbol shorter than that identifier, so its rendering
# as an attribute is the placeholder which leaves the identifier alone
short_names = {
    "metre": "m",
    "meter": "m",
    "liter": "l",
    "litre": "l",
    "dimensionless": "-",
    "second": "s",
}

# the rendering of a quantity without dimension, which is a unit of its own
# and not the dash of units which are not declared or cannot be derived
DIMENSIONLESS = "dimensionless"


def _factor(u: libsbml.Unit) -> tuple[str, float] | None:
    """The rendering of one unit of a definition and its exponent.

    A unit is `(multiplier * 10^scale * kind)^exponent` (core §4.4.2). Level 3
    requires the three numbers, and libsbml answers a missing one with NaN or,
    for the scale, with the largest integer, which a power of ten does not
    survive; a missing number is read as the value Level 2 gives it. A
    fractional exponent of Level 3 is read as the double it is. A dimensionless
    unit of magnitude one is no factor of the product and gives None.
    """
    kind = libsbml.UnitKind_toString(u.getKind())
    exponent = u.getExponentAsDouble()
    exponent = exponent if math.isfinite(exponent) else 1.0
    scale = u.getScale() if u.isSetScale() else 0
    multiplier = u.getMultiplier()
    multiplier = multiplier if math.isfinite(multiplier) else 1.0
    try:
        magnitude = multiplier * 10.0**scale
    except OverflowError:
        magnitude = math.inf
    if not math.isfinite(magnitude):
        # beyond the range of a double pint cannot compact the unit, so the
        # power of ten is written as the file gives it
        us = f"10^{{{scale}}}*{ureg.Unit(kind):~}"
        if abs(exponent) != 1.0:
            us = f"({us})^{abs(exponent):g}"
        return us, exponent

    # (m * 10^s *k)^e, parsed with pint
    term = Q_(magnitude, kind) ** abs(exponent)
    with contextlib.suppress(KeyError):
        term = term.to_compact()

    if np.isclose(term.magnitude, 1.0):
        term = Q_(1, term.units)

    us = f"{term:~}"  # short formating
    if us == "1":
        return None
    # handle min and hr
    us = us.replace("60.0 s", "1 min")
    us = us.replace("3600.0 s", "1 hr")
    us = us.replace("3.6 ks", "1 hr")
    us = us.replace("86.4 ks", "1 day")
    us = us.replace("10.0 mm", "1 cm")

    # remove 1.0 prefixes
    us = us.replace("1 ", "")
    # exponent
    us = us.replace(" ** ", "^")
    return us, exponent


def udef_to_string(
    udef: libsbml.UnitDefinition | str | None,
    model: libsbml.Model | None = None,
) -> str | None:
    """Render a unit definition as latex.

    Units have the general format
        (multiplier * 10^scale *ukind)^exponent
        (m * 10^s *k)^e

    Args:
        udef: the unit definition, or the id of a base unit or of a unit
            definition of the model.
        model: required to resolve the id of a unit definition.

    Returns None if udef is None.
    """
    if udef is None:
        return None

    ud: libsbml.UnitDefinition
    if isinstance(udef, str):
        # check for internal unit
        if libsbml.UnitKind_forName(udef) != libsbml.UNIT_KIND_INVALID:
            return short_names.get(udef, udef)
        if model is None:
            raise ValueError(
                f"A model is required to resolve the unit definition '{udef}'."
            )
        ud = model.getUnitDefinition(udef)
    else:
        ud = udef

    # collect nominators and denominators
    nom: str = ""
    denom: str = ""
    dimensionless = False
    if ud:
        for u in ud.getListOfUnits():
            factor = _factor(u)
            if factor is None:
                dimensionless = True
                continue
            us, exponent = factor
            if exponent >= 0.0:
                nom = us if nom == "" else f"{nom}*{us}"
            else:
                denom = us if denom == "" else f"{denom}*{us}"

    nom = nom.replace("*", " \\cdot ")
    denom = denom.replace("*", " \\cdot ")
    if nom and denom:
        ustr = f"\\frac{{{nom}}}{{{denom}}}"
    elif nom:
        ustr = nom
    elif denom:
        ustr = f"\\frac{{1}}{{{denom}}}"
    else:
        ustr = DIMENSIONLESS if dimensionless else "-"

    return "-" if ustr == "1" else ustr
