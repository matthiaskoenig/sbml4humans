"""The validation rules of SBML, resolved from their number with libsbml.

The glossary cites a rule by the number libsbml gives it and never writes its
text: the message, the severity and the section of the specification are read
from the tables of the library which also validates the model of a user.
"""

import re
from dataclasses import dataclass

import libsbml


PACKAGES = ("comp", "distrib", "fbc", "qual")

# the versions of core a rule is looked up in, the newest first: a rule which
# is not applicable there belongs to an older one, which the report reads too
_CORE_VERSIONS = ((3, 2), (3, 1), (2, 5))
_REFERENCE = re.compile(r"\s*Reference:\s*(?P<section>.+?)\s*$")
_SEVERITIES = {
    libsbml.LIBSBML_SEV_ERROR: "error",
    libsbml.LIBSBML_SEV_FATAL: "error",
    libsbml.LIBSBML_SEV_SCHEMA_ERROR: "error",
    libsbml.LIBSBML_SEV_WARNING: "warning",
    libsbml.LIBSBML_SEV_GENERAL_WARNING: "warning",
}


class UnknownRuleError(ValueError):
    """A number which is no validation rule of libsbml."""


@dataclass(frozen=True, slots=True)
class Rule:
    """One validation rule of a specification, as libsbml states it."""

    id: int
    package: str
    severity: str
    message: str
    section: str | None


def _message(text: str) -> tuple[str, str | None]:
    """Split the message libsbml gives into its text and its trailing section.

    Args:
        text: The raw message of a `libsbml.SBMLError` or of a package error table,
            possibly ending in a `Reference: ...` line.

    Returns:
        The whitespace-joined message without the reference line, and the
        section of the specification the reference names, or `None` when the
        message has no reference.
    """
    joined = " ".join(text.split())
    match = _REFERENCE.search(joined)
    if match is None:
        return joined, None
    section = match.group("section")
    return joined[: match.start()].rstrip(), section


def rule_package(code: int) -> str:
    """Resolve the package a rule number belongs to.

    Args:
        code: The number of a validation rule as libsbml numbers it.

    Returns:
        `"core"` when the code is below the smallest offset of a package, else
        the package whose `getErrorIdOffset()` is the largest one not above
        the code.

    Raises:
        UnknownRuleError: The code is below 10000, which is no rule of core
            nor of a package.
    """
    if code < 10000:
        raise UnknownRuleError(f"{code} is not a validation rule of libsbml")
    registry = libsbml.SBMLExtensionRegistry.getInstance()
    package = "core"
    offset = 0
    for name in PACKAGES:
        extension: libsbml.SBMLExtension = registry.getExtension(name)
        package_offset = extension.getErrorIdOffset()
        if package_offset <= code and package_offset > offset:
            package = name
            offset = package_offset
    return package


def _resolve_core_rule(code: int) -> Rule:
    """Resolve a core validation rule from the newest applicable version of core.

    Args:
        code: The number of a core validation rule.

    Returns:
        The resolved rule.

    Raises:
        UnknownRuleError: No version of `_CORE_VERSIONS` knows the rule.
    """
    for level, version in _CORE_VERSIONS:
        error: libsbml.SBMLError = libsbml.SBMLError(code, level, version)
        if error.getCategoryAsString() == "Internal" or not error.getMessage():
            continue
        severity = _SEVERITIES.get(error.getSeverity())
        if severity is None:
            continue
        message, section = _message(error.getMessage())
        return Rule(
            id=code, package="core", severity=severity, message=message, section=section
        )
    raise UnknownRuleError(f"{code} is not a validation rule of libsbml")


def _package_versions(extension: libsbml.SBMLExtension) -> list[int]:
    """List the versions an extension supports, deduplicated, newest first.

    Args:
        extension: The extension of a package.

    Returns:
        The distinct version numbers the extension supports, descending.
    """
    versions = {
        extension.getPackageVersion(extension.getSupportedPackageURI(i))
        for i in range(extension.getNumOfSupportedPackageURI())
    }
    return sorted(versions, reverse=True)


def _resolve_package_rule(code: int, package: str) -> Rule:
    """Resolve a package validation rule from the error table of its extension.

    Args:
        code: The number of a package validation rule.
        package: The package the rule belongs to, as `rule_package` names it.

    Returns:
        The resolved rule.

    Raises:
        UnknownRuleError: The code has no entry in the error table of the
            package, or no version of the package knows the rule.
    """
    extension: libsbml.SBMLExtension = (
        libsbml.SBMLExtensionRegistry.getInstance().getExtension(package)
    )
    index = extension.getErrorTableIndex(code)
    if index == 0:
        raise UnknownRuleError(f"{code} is not a validation rule of libsbml")
    for version in _package_versions(extension):
        severity = _SEVERITIES.get(extension.getSeverity(index, version))
        if severity is None:
            continue
        message, section = _message(extension.getMessage(index, version, ""))
        return Rule(
            id=code,
            package=package,
            severity=severity,
            message=message,
            section=section,
        )
    raise UnknownRuleError(f"{code} is not a validation rule of libsbml")


def resolve_rule(code: int) -> Rule:
    """Resolve a validation rule of SBML from its libsbml number.

    Args:
        code: The number of a validation rule as libsbml numbers it.

    Returns:
        The message, severity and specification section of the rule.

    Raises:
        UnknownRuleError: The code is no validation rule of libsbml, in any
            version of core or of the package it falls into.
    """
    package = rule_package(code)
    if package == "core":
        return _resolve_core_rule(code)
    return _resolve_package_rule(code, package)
