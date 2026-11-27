"""Rule documentation from the same Rust/libSBML tables used by validation."""

import json
from dataclasses import dataclass
from functools import lru_cache

from sbml4humans.native import _reader


PACKAGES = ("comp", "distrib", "fbc", "qual")


class UnknownRuleError(ValueError):
    """A number which is no validation rule of libSBML."""


@dataclass(frozen=True, slots=True)
class Rule:
    """One native validation rule and its specification reference."""

    id: int
    package: str
    severity: str
    message: str
    section: str | None


@lru_cache(maxsize=4096)
def resolve_rule(code: int) -> Rule:
    """Resolve rule text without a Python libSBML dependency."""
    try:
        return Rule(**json.loads(_reader().rule_json(code)))
    except (ValueError, OverflowError) as error:
        raise UnknownRuleError(f"{code} is not a validation rule of libsbml") from error


@lru_cache(maxsize=4096)
def rule_package(code: int) -> str:
    """Identify the specification a validation rule belongs to."""
    try:
        return _reader().rule_package(code)
    except (ValueError, OverflowError) as error:
        raise UnknownRuleError(f"{code} is not a validation rule of libsbml") from error
