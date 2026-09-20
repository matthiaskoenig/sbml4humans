"""Tests of the resolution of the validation rules of libsbml."""

import pytest

from sbml4humans.glossaryrules import Rule, UnknownRuleError, resolve_rule, rule_package


def test_resolves_a_core_rule() -> None:
    """The message, severity and section of a core rule are read from libsbml."""
    rule = resolve_rule(20609)
    assert rule == Rule(
        id=20609,
        package="core",
        severity="error",
        message=(
            "A <species> cannot set values for both 'initialConcentration' and "
            "'initialAmount' because they are mutually exclusive."
        ),
        section="L3V2 Section 4.6.4",
    )


def test_resolves_a_warning() -> None:
    """A rule whose severity is a warning resolves as one."""
    assert resolve_rule(20608).severity == "warning"


def test_resolves_a_package_rule_from_the_table_of_its_extension() -> None:
    """A package rule is read from the error table of its extension."""
    rule = resolve_rule(1020101)
    assert rule.package == "comp"
    assert rule.severity == "error"
    assert rule.message.startswith("Any object derived from the extended SBase class")
    assert rule.section == "L3V1 Comp V1 Section 3.6"


def test_the_severity_of_a_package_rule_is_the_one_of_the_rule() -> None:
    """The severity of a package rule comes from the table, not from the caller libsbml echoes."""
    assert resolve_rule(1090110).severity == "warning"


def test_a_rule_without_a_reference_has_no_section() -> None:
    """A message with no trailing 'Reference:' line has no section."""
    assert resolve_rule(1090101).section is None


def test_a_rule_of_an_older_fbc_version_is_resolved_there() -> None:
    """The flux bounds rules exist in fbc version 1 only, which the report reads as well."""
    rules = [resolve_rule(code) for code in range(2020401, 2020410)]
    assert all(rule.message for rule in rules)


def test_a_core_rule_of_an_older_version_is_resolved_there() -> None:
    """A core rule not applicable at L3V2 is looked up at L3V1 or L2V5 instead."""
    rule = resolve_rule(10209)
    assert rule.package == "core"
    assert rule.severity == "error"
    assert rule.section == "L3V1 Section 3.4.9"


@pytest.mark.parametrize(
    ("code", "package"),
    [
        (20609, "core"),
        (1020101, "comp"),
        (1520101, "distrib"),
        (2020301, "fbc"),
        (3020101, "qual"),
    ],
)
def test_the_package_follows_from_the_number(code: int, package: str) -> None:
    """The package of a rule follows from the offset its number falls into."""
    assert rule_package(code) == package


@pytest.mark.parametrize("code", [99999, 12345, 1029999, 2099999, 0, -1])
def test_an_unknown_number_is_an_error(code: int) -> None:
    """A number which is no validation rule of libsbml raises."""
    with pytest.raises(UnknownRuleError, match=str(code)):
        resolve_rule(code)
