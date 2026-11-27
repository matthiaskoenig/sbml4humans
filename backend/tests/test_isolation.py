"""Tests of the budgets of the isolated work of a request."""

import os
import signal
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


@pytest.mark.parametrize(
    ("exitcode", "written"),
    [
        pytest.param(
            -signal.SIGABRT,
            "terminate called after throwing an instance of 'std::bad_alloc'\n"
            "  what():  std::bad_alloc",
            id="the abort of an uncaught bad_alloc of libstdc++",
        ),
        pytest.param(
            -signal.SIGABRT,
            "terminate called after throwing an instance of 'St9bad_alloc'",
            id="the abort of a bad_alloc libstdc++ could not demangle",
        ),
        pytest.param(
            -signal.SIGABRT,
            "libc++abi: terminating due to uncaught exception of type "
            "std::bad_alloc: std::bad_alloc",
            id="the abort of an uncaught bad_alloc of libc++",
        ),
        pytest.param(
            -signal.SIGABRT,
            "memory allocation of 7200432 bytes failed\n",
            id="Rust allocation failure",
        ),
        pytest.param(
            127,
            "cannot allocate memory for thread-local data: ABORT",
            id="the exit of a glibc which could not allocate thread-local data",
        ),
    ],
)
def test_a_child_which_ran_out_of_memory_says_so(exitcode: int, written: str) -> None:
    """Every end of a child for lack of memory is `"memory"`, not a crash.

    The whole standard error of a child of a report at its bound, as it was
    captured: the C++ runtime aborts the child where it threw a `std::bad_alloc`
    nobody caught, and glibc ends it itself, without a signal and with the exit
    code 127, where it could not place the thread-local storage of a library.
    A client which reads of a crash instead is told that the process ended
    unexpectedly where the work needed more memory than it may use.
    """
    assert isolation._abnormal_end(exitcode, written, "report") == "memory"


@pytest.mark.parametrize(
    ("exitcode", "written"),
    [
        pytest.param(
            -signal.SIGSEGV,
            "",
            id="a signal which leaves nothing, the crash of libsbml or the OOM killer",
        ),
        pytest.param(
            -signal.SIGABRT,
            "terminate called after throwing an instance of 'std::logic_error'",
            id="an abort of another uncaught exception",
        ),
        pytest.param(
            1,
            "memory allocation of 7200432 bytes failed",
            id="allocation text without abort",
        ),
        pytest.param(1, "Traceback (most recent call last):", id="an exit of python"),
        pytest.param(None, "", id="a child whose exit code the server never got"),
    ],
)
def test_an_end_which_is_no_lack_of_memory_is_a_crash(
    exitcode: int | None, written: str
) -> None:
    """Only what the runtime names a failed allocation reads as memory."""
    assert isolation._abnormal_end(exitcode, written, "report") == "crashed"


@pytest.mark.parametrize(
    ("exitcode", "reads"),
    [
        pytest.param(-signal.SIGABRT, "signal 6 SIGABRT", id="an abort"),
        pytest.param(-signal.SIGSEGV, "signal 11 SIGSEGV", id="a segmentation fault"),
        pytest.param(127, "exit code 127", id="an exit of the C library"),
        pytest.param(0, "exit code 0", id="an exit without the results"),
        pytest.param(None, "no exit code", id="a child without an exit code"),
    ],
)
def test_the_end_of_a_child_reads_as_a_signal_or_an_exit_code(
    exitcode: int | None, reads: str
) -> None:
    """A signal is logged as a signal, not as a negative exit code.

    `multiprocessing` reports the signal which killed a child as the negative
    of its number, which read as "exit code -6" in the log of an abort.
    """
    assert isolation._end_of(exitcode) == reads


def test_a_child_of_a_budget_names_its_temporary_directory() -> None:
    """The temporary directory of a child says which kind of work it runs."""
    run = isolation.run_isolated(_tempdir, None, isolation.REPORT_BUDGET)
    results = dict(run.results)
    assert run.interruption is None
    assert "report" in Path(results["tempdir"]).name
