"""Tests of the budgets of the isolated work of a request."""

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from sbml4humans import isolation


def _tempdir(_: object) -> Iterator[tuple[str, str | None]]:
    """The temporary directory of the child process, of python and of the system."""
    yield "tempdir", tempfile.gettempdir()
    for variable in ("TMPDIR", "TEMP", "TMP"):
        yield variable, os.environ.get(variable)


def test_a_budget_reads_its_concurrency_from_its_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The environment sets how many children of a budget run at a time."""
    monkeypatch.setenv("SBML4HUMANS_REPORTS", "3")
    assert isolation.budget_concurrency("SBML4HUMANS_REPORTS") == 3


@pytest.mark.parametrize("value", [None, "", "0", "-1", "two"])
def test_a_budget_without_a_number_runs_half_the_cpus(
    monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    """Without a number in its variable a budget runs half the cpus it may run on."""
    if value is None:
        monkeypatch.delenv("SBML4HUMANS_REPORTS", raising=False)
    else:
        monkeypatch.setenv("SBML4HUMANS_REPORTS", value)
    cpus = isolation._process_cpu_count()
    assert isolation.budget_concurrency("SBML4HUMANS_REPORTS") == max(1, cpus // 2)


def test_the_budgets_hold_the_values_of_the_design() -> None:
    """The validation and the report are bounded as the design says."""
    validation = isolation.VALIDATION_BUDGET
    report = isolation.REPORT_BUDGET
    assert (validation.timeout, validation.memory) == (60.0, 2 * 1024**3)
    assert (report.timeout, report.memory) == (180.0, 4 * 1024**3)
    assert validation.variable == "SBML4HUMANS_VALIDATIONS"
    assert report.variable == "SBML4HUMANS_REPORTS"
    assert validation.waiting == 2 * validation.concurrency
    assert report.waiting == 2 * report.concurrency


def test_two_budgets_have_semaphores_of_their_own() -> None:
    """One budget never holds the children of the other."""
    assert isolation._semaphore(isolation.REPORT_BUDGET) is not isolation._semaphore(
        isolation.VALIDATION_BUDGET
    )


def test_the_admission_of_one_budget_leaves_the_other_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A budget full of work refuses its own and admits that of the other."""
    monkeypatch.setattr(isolation.REPORT_BUDGET, "concurrency", 1)
    monkeypatch.setattr(isolation.REPORT_BUDGET, "waiting", 0)
    with isolation.admission(isolation.REPORT_BUDGET) as admitted:
        assert admitted
        with isolation.admission(isolation.REPORT_BUDGET) as again:
            assert not again
        with isolation.admission(isolation.VALIDATION_BUDGET) as other:
            assert other


def test_an_admission_is_free_again_after_its_context() -> None:
    """The count of a budget is back where it was when its work has ended."""
    name = isolation.REPORT_BUDGET.name
    before = isolation._admitted.get(name, 0)
    with isolation.admission(isolation.REPORT_BUDGET) as admitted:
        assert admitted
        assert isolation._admitted[name] == before + 1
    assert isolation._admitted.get(name, 0) == before


def test_a_child_of_a_budget_names_its_temporary_directory() -> None:
    """The temporary directory of a child says which kind of work it runs."""
    run = isolation.run_isolated(_tempdir, None, isolation.REPORT_BUDGET)
    results = dict(run.results)
    assert run.interruption is None
    assert "report" in Path(results["tempdir"]).name
