"""Formatting of units as strings and latex."""

import contextlib

import libsbml
import numpy as np
import pint


ureg = pint.UnitRegistry()
ureg.define("item = dimensionless")
ureg.define("avogadro = 6.02214179E23 dimensionless")
Q_ = ureg.Quantity

short_names = {
    "metre": "m",
    "meter": "m",
    "liter": "l",
    "litre": "l",
    "dimensionless": "-",
    "second": "s",
}


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
    if ud:
        for u in ud.getListOfUnits():
            m = u.getMultiplier()
            s: int = u.getScale()
            e = u.getExponent()
            k = libsbml.UnitKind_toString(u.getKind())

            # (m * 10^s *k)^e
            # parse with pint
            term = Q_(float(m) * 10**s, k) ** float(abs(e))
            with contextlib.suppress(KeyError):
                term = term.to_compact()

            if np.isclose(term.magnitude, 1.0):
                term = Q_(1, term.units)

            us = f"{term:~}"  # short formating
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

            if e >= 0.0:
                nom = us if nom == "" else f"{nom}*{us}"
            else:
                denom = us if denom == "" else f"{denom}*{us}"

    else:
        nom = "-"

    nom = nom.replace("*", " \\cdot ")
    denom = denom.replace("*", " \\cdot ")
    if nom and denom:
        ustr = f"\\frac{{{nom}}}{{{denom}}}"
    elif nom:
        ustr = nom
    elif denom:
        ustr = f"\\frac{{1}}{{{denom}}}"
    else:
        ustr = "-"

    return "-" if ustr == "1" else ustr
