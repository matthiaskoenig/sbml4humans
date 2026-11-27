"""Rule documentation is read through the mandatory native validator."""

import pytest

from sbml4humans.glossaryrules import UnknownRuleError, resolve_rule, rule_package


@pytest.mark.parametrize(
    ("code", "package"),
    [
        (10703, "core"),
        (1010101, "comp"),
        (1510101, "distrib"),
        (2010101, "fbc"),
        (3010101, "qual"),
    ],
)
def test_rule_package_uses_native_offsets(code: int, package: str) -> None:
    """Package identity comes from the validator's registry, not hard-coded offsets."""
    assert rule_package(code) == package


@pytest.mark.parametrize("code", [-1, 42, 9999, 123456789])
def test_unknown_rules_are_rejected(code: int) -> None:
    """Invalid and unknown codes have the same public error contract."""
    with pytest.raises(UnknownRuleError):
        resolve_rule(code)


def test_rule_text_and_reference_come_from_native_tables() -> None:
    """The model and glossary show the validator's exact specification text."""
    rule = resolve_rule(10703)
    assert rule.id == 10703
    assert rule.package == "core"
    assert rule.message
    assert "Reference:" not in rule.message
    assert rule.section
