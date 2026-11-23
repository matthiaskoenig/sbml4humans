"""The child processes which run the work of a request, bounded in time and memory.

What libsbml does with untrusted content is not bounded by the size of the
content, neither its validation nor its report, so all of that work, from
reading the source on, runs in a child process of its own, one per request,
which the server ends when it takes too long.

Every kind of work has a `Budget` of its own, which holds what one of its
children may take and how many of them run: `VALIDATION_BUDGET` (60 seconds,
2 GiB of address space, `SBML4HUMANS_VALIDATIONS` children) and `REPORT_BUDGET`
(180 seconds, 4 GiB, `SBML4HUMANS_REPORTS` children); without its variable a
budget runs half the cpus the server may run on. A call of `run_isolated` is
given the budget of the work it runs, and the children, the admission and the
semaphore of a budget are counted by its name alone, so that one kind of work
never starves the other.

A child is a boundary of resources, not a sandbox: it bounds the time, the
memory and the temporary files of one run and keeps a crash of libsbml out of
the server, but it runs as the user of the server, with its file system and its
network. What a run may read is confined by the code it runs (the resolver of
the report in `validation.py`, the limits of the content in `limits.py`), not by
the process.

A server admits at most `budget.concurrency + budget.waiting` runs of a budget
at a time (`admission`), a request beyond them is answered at once as `"busy"`,
and so is one which got no child while at least `MIN_CHILD_TIME` of its timeout
was left: a run is `"timeout"` only when its child ran out of time.

The children are forked by the forkserver of `multiprocessing`, a process of
its own which imported the report and the validation once and is single
threaded (`forkserver.py` keeps the thread pool of numpy out of it), so that a
child starts at once and small, without the threads of the server and with the
resolver of the report installed in the registry of libsbml. A child
gets the function it runs, its argument and its budget pickled, which is why
the source goes to it as the path of a file and not as objects of libsbml, and
sends every result back as soon as it has it, so that a timeout keeps the
results before it. An exception of the function is sent back and raised by the
server, with the traceback of the child as a note.

A child which runs out of memory either raises `MemoryError` in python or is
aborted by the `std::bad_alloc` libsbml does not catch, both end what is left
of it as `"memory"`. The abort is told apart from one of another cause by what
the C++ runtime writes to the standard error before it aborts: libstdc++ (and
libc++) names the `std::bad_alloc` which ended the program. The child writes
its standard error to a file of its temporary directory, which the server
reads and logs after the child has ended. Any other abnormal end of a child, a
signal (also the SIGKILL of the OOM killer of the kernel, which leaves no trace
the server could read), another abort or an exit without its results, keeps
the results the child sent before and ends what is left of it as
`"crashed"`.

A child keeps its temporary files, the archive of the source extracted by
pymetadata among them, in a temporary directory the server makes for it (also
its `TMPDIR`, `TEMP` and `TMP`, for native libraries), names after the budget
and removes when it has ended, so that a child which was killed or aborted
leaves nothing of the content on the server. The cpu time of a child is limited
to twice the timeout of its budget, so that a child ends itself also when its
server died without ending it.

A run is cancelled when nobody waits for it any more, its client left
(`run_cancellable`): it stops waiting for a child, or its child is killed, at
once, which frees the child, the admission and the temporary directory.

The python interface runs the same server on the machine of the user: where
there is no forkserver (Windows) a child is spawned, a fresh interpreter which
imports the code of the work itself, and where the address space cannot be
limited (Windows, macOS) the child runs without the memory limit.
"""

import faulthandler
import logging
import math
import multiprocessing
import os
import shutil
import signal
import sys
import tempfile
import threading
import time
import traceback
from collections.abc import Callable, Generator, Iterable
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess
from typing import Any, Literal


logger = logging.getLogger(__name__)


@dataclass
class Budget:
    """What one kind of isolated work may take, and how much of it runs at a time.

    A budget is read when it applies and goes to the child as it is, so that a
    test lowers one of its fields with `monkeypatch.setattr` and the child sees
    the value of the server; it is therefore not frozen.

    Attributes:
        name: the kind of work, in the log, in the name of the temporary
            directory of a child and as the key of its children and of its
            admission, which it shares with no other budget.
        timeout: the time one run may take from its call on, in seconds.
        memory: the address space of one child, in bytes.
        variable: the environment variable which sets `concurrency`.
        concurrency: the children which run at a time.
        waiting: the runs which may wait for a child, beyond them a request is
            busy.
    """

    name: str
    timeout: float
    memory: int
    variable: str
    concurrency: int
    waiting: int


def budget_concurrency(variable: str) -> int:
    """The children which run at a time: the environment, else half the cpus.

    `os.process_cpu_count` counts the cpus this process may run on, its cpu
    affinity: in a container all cpus of the host unless a cpuset restricts
    them, a cpu quota does not change it. Each child may use up to the memory
    of its budget, so a server sets the number to what its memory allows.

    Args:
        variable: the environment variable which holds the number.

    Returns:
        The number of children, one at least.
    """
    value = os.environ.get(variable, "")
    if value.isdigit() and int(value) > 0:
        return int(value)
    return max(1, _process_cpu_count() // 2)


def _process_cpu_count() -> int:
    """The cpus this process may run on, `os.process_cpu_count` from python 3.13.

    Python 3.12 has the affinity of the process where the platform has it (Linux),
    else the cpus of the machine.
    """
    if sys.version_info >= (3, 13):
        return os.process_cpu_count() or 1
    if hasattr(os, "sched_getaffinity"):
        return len(os.sched_getaffinity(0)) or 1
    return os.cpu_count() or 1


def _budget(name: str, timeout: float, memory: int, variable: str) -> Budget:
    """A budget whose concurrency is read from its variable.

    Args:
        name: the kind of work.
        timeout: the time one run may take, in seconds.
        memory: the address space of one child, in bytes.
        variable: the environment variable which sets the concurrency.

    Returns:
        The budget, twice as many runs waiting for a child as children.
    """
    concurrency = budget_concurrency(variable)
    return Budget(
        name=name,
        timeout=timeout,
        memory=memory,
        variable=variable,
        concurrency=concurrency,
        waiting=2 * concurrency,
    )


# the budget of the validation of libsbml of a source
VALIDATION_BUDGET = _budget(
    name="validation",
    timeout=60.0,
    memory=2 * 1024**3,
    variable="SBML4HUMANS_VALIDATIONS",
)
# the budget of the report of an untrusted source, which takes more of both
REPORT_BUDGET = _budget(
    name="report",
    timeout=180.0,
    memory=4 * 1024**3,
    variable="SBML4HUMANS_REPORTS",
)

# the time a child has at least, a run which got a child later is busy
MIN_CHILD_TIME = 1.0
# the interval in which a waiting run looks whether it was cancelled, s
CANCEL_INTERVAL = 0.1

Interruption = Literal["timeout", "memory", "busy", "crashed"]

if "forkserver" in multiprocessing.get_all_start_methods():
    _CONTEXT = multiprocessing.get_context("forkserver")
    _CONTEXT.set_forkserver_preload(["sbml4humans.forkserver", "sbml4humans.report"])
else:
    _CONTEXT = multiprocessing.get_context("spawn")

# the file of the temporary directory of a child which holds its standard error
_STDERR = "stderr.txt"
# the bytes of the end of the standard error of a child the server reads
_STDERR_TAIL = 64 * 1024
# the characters of the end of the standard error of a child the server logs
_STDERR_LOGGED = 4 * 1024
# what the C++ runtime writes when an uncaught std::bad_alloc aborts the child:
# libstdc++ (the name mangled when it cannot demangle it) and libc++
_BAD_ALLOC = (
    "terminate called after throwing an instance of 'std::bad_alloc'",
    "terminate called after throwing an instance of 'St9bad_alloc'",
    "uncaught exception of type std::bad_alloc",
)

# the cancellation of the isolated run of this thread, None where none can cancel
_CANCEL: ContextVar[threading.Event | None] = ContextVar("cancel", default=None)

# the semaphore of the children of a budget, by its name and its concurrency
_SEMAPHORES: dict[tuple[str, int], threading.BoundedSemaphore] = {}
_LOCK = threading.Lock()
# the runs a server admitted, by the name of their budget
_admitted: dict[str, int] = {}


class IsolatedRunCancelledError(Exception):
    """Raised by an isolated run which was cancelled, nobody waits for it any more."""


def run_cancellable[R](
    cancel: threading.Event, function: Callable[..., R], *args: Any
) -> R:
    """Run a function whose `run_isolated` ends as soon as `cancel` is set.

    Raises:
        IsolatedRunCancelledError: if `cancel` was set before the end.
    """
    token = _CANCEL.set(cancel)
    try:
        return function(*args)
    finally:
        _CANCEL.reset(token)


def _check_cancelled(budget: Budget) -> None:
    """Raise if the run of this thread was cancelled.

    Raises:
        IsolatedRunCancelledError: if it was.
    """
    cancel = _CANCEL.get()
    if cancel is not None and cancel.is_set():
        logger.info("a %s was cancelled", budget.name)
        raise IsolatedRunCancelledError


@dataclass
class IsolatedRun:
    """What a function yielded in a child, and why it stopped early if it did.

    Attributes:
        results: the pairs the function yielded, in their order.
        interruption: None when the function ran to its end, else `"timeout"`,
            `"memory"`, `"crashed"` (the child ended abnormally for another
            reason) or `"busy"` (it did not run at all).
    """

    results: list[tuple[str, Any]] = field(default_factory=list)
    interruption: Interruption | None = None


# the messages of a child to the server, besides a result
_DONE = "done"
_MEMORY = "memory"
_ERROR = "error"


def admission_capacity(budget: Budget) -> int:
    """The runs of a budget a server admits at a time, running or waiting."""
    return budget.concurrency + budget.waiting


@contextmanager
def admission(budget: Budget) -> Generator[bool]:
    """Admit a run of a budget if there is room for it, for the time of the context.

    The runs of a budget are counted by its name, so that a budget full of work
    never refuses the work of another.

    Yields:
        Whether the run was admitted; one which was not is busy.
    """
    with _LOCK:
        admitted = _admitted.get(budget.name, 0) < admission_capacity(budget)
        if admitted:
            _admitted[budget.name] = _admitted.get(budget.name, 0) + 1
    try:
        yield admitted
    finally:
        if admitted:
            with _LOCK:
                _admitted[budget.name] -= 1


def start_forkserver() -> None:
    """Start the forkserver, if the children are forked by one.

    The forkserver imports the report and the validation once it runs, which
    the first child would otherwise wait for within its timeout. A forkserver
    which runs already is kept.
    """
    if _CONTEXT.get_start_method() == "forkserver":
        from multiprocessing import forkserver

        forkserver.ensure_running()


def _semaphore(budget: Budget) -> threading.BoundedSemaphore:
    """The semaphore of the children of a budget, read when it is used."""
    with _LOCK:
        key = (budget.name, budget.concurrency)
        if key not in _SEMAPHORES:
            _SEMAPHORES[key] = threading.BoundedSemaphore(budget.concurrency)
        return _SEMAPHORES[key]


def _limit_memory(memory: int, name: str) -> Callable[[], None]:
    """Limit the address space of this process, return how to lift the limit.

    Only the soft limit is lowered, which the process may raise again up to the
    hard limit. Without a limit of the address space nothing is limited.
    """
    try:
        # there is no module `resource` on Windows
        import resource

        _, hard = resource.getrlimit(resource.RLIMIT_AS)
        soft = memory if hard == resource.RLIM_INFINITY else min(memory, hard)
        resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
    except (ImportError, AttributeError, ValueError, OSError) as exc:
        logger.warning("the memory of the %s is not limited: %s", name, exc)
        return lambda: None

    def lift() -> None:
        """Raise the soft limit to the hard limit again."""
        resource.setrlimit(resource.RLIMIT_AS, (hard, hard))

    return lift


def _limit_cpu(seconds: int, name: str) -> None:
    """Limit the cpu time of this process, after which it is ended by SIGXCPU.

    Only the soft limit is lowered. Without a limit of the cpu time nothing is
    limited.
    """
    try:
        # there is no module `resource` on Windows
        import resource

        _, hard = resource.getrlimit(resource.RLIMIT_CPU)
        soft = seconds if hard == resource.RLIM_INFINITY else min(seconds, hard)
        resource.setrlimit(resource.RLIMIT_CPU, (soft, hard))
    except (ImportError, AttributeError, ValueError, OSError) as exc:
        logger.warning("the cpu time of the %s is not limited: %s", name, exc)


def _child(
    function: Callable[[Any], Iterable[tuple[str, Any]]],
    argument: Any,
    budget: Budget,
    tempdir: str,
    connection: Connection,
) -> None:
    """Run in the child: send every result of the function, then `_DONE`.

    The temporary files of the child go to `tempdir`, which the server
    removes: those of python by `tempfile` and those of native libraries by
    the variables of the environment they read (`TMPDIR`, `TEMP`, `TMP`). The
    cpu time is limited to twice the timeout of the budget and the address space
    to its memory; when python runs out of memory, the limit is lifted again so
    that the child can say so. Another exception is sent with its traceback.
    The standard error goes to the file `_STDERR` of `tempdir`, which the server
    reads after the end of the child, together with the traceback of python
    `faulthandler` writes when the child ends by a fatal signal.
    """
    if (
        sys.stderr is not None
    ):  # None in a child of a parent without a console (pythonw)
        sys.stderr.flush()
    stderr = os.open(
        os.path.join(tempdir, _STDERR), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600
    )
    os.dup2(stderr, 2)
    os.close(stderr)
    # an explicit file: without one faulthandler needs sys.stderr, which may be None
    faulthandler.enable(file=os.fdopen(2, "w", closefd=False))
    tempfile.tempdir = tempdir
    for variable in ("TMPDIR", "TEMP", "TMP"):
        os.environ[variable] = tempdir
    _limit_cpu(math.ceil(2 * budget.timeout), budget.name)
    lift = _limit_memory(budget.memory, budget.name)
    try:
        for result in function(argument):
            connection.send(result)
        connection.send(_DONE)
    except MemoryError:
        lift()
        connection.send(_MEMORY)
    except Exception as exc:
        lift()
        text = "".join(traceback.format_exception(exc))
        try:
            connection.send((_ERROR, exc, text))
        except Exception:
            # an exception which cannot be pickled is sent as its message
            connection.send((_ERROR, RuntimeError(str(exc)), text))
    finally:
        connection.close()


def _start(
    function: Callable[[Any], Iterable[tuple[str, Any]]],
    argument: Any,
    budget: Budget,
    tempdir: str,
    connection: Connection,
) -> BaseProcess:
    """Start a child which runs the function and sends on the connection.

    The budget goes to the child as it is, which reads the limits of the child
    from it when it starts: its memory and twice its timeout of cpu time.
    """
    process = _CONTEXT.Process(
        target=_child,
        args=(function, argument, budget, tempdir, connection),
        daemon=True,
    )
    process.start()
    return process


def _run_child(
    function: Callable[[Any], Iterable[tuple[str, Any]]],
    argument: Any,
    budget: Budget,
    deadline: float,
) -> IsolatedRun:
    """Run the function in a child until it is done or the deadline has passed.

    Raises:
        Exception: the exception the function raised in the child.
    """
    # the temporary directory of the child, which the server removes after the
    # child has ended, whether it ended by itself, was killed or aborted
    tempdir = tempfile.mkdtemp(prefix=f"sbml4humans_{budget.name}_")
    try:
        return _communicate(function, argument, budget, deadline, tempdir)
    finally:
        shutil.rmtree(tempdir, ignore_errors=True)


def _communicate(
    function: Callable[[Any], Iterable[tuple[str, Any]]],
    argument: Any,
    budget: Budget,
    deadline: float,
    tempdir: str,
) -> IsolatedRun:
    """Start the child of `_run_child` and receive its results until it has ended.

    Raises:
        IsolatedRunCancelledError: if the run was cancelled.
        Exception: the exception the function raised in the child.
    """
    run = IsolatedRun()
    receiver, sender = _CONTEXT.Pipe(duplex=False)
    try:
        process = _start(function, argument, budget, tempdir, sender)
    except BaseException:
        receiver.close()
        raise
    finally:
        # the child holds the sending end, which the server closes so that it
        # reads the end of the pipe when the child has ended
        sender.close()
    ended = False
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                logger.warning("the %s was ended after its timeout", budget.name)
                run.interruption = "timeout"
                break
            if not receiver.poll(min(remaining, CANCEL_INTERVAL)):
                # the child is killed below
                _check_cancelled(budget)
                continue
            try:
                message = receiver.recv()
            except EOFError:
                # the child ended without saying it is done
                ended = True
                break
            if message == _DONE:
                break
            if message == _MEMORY:
                logger.warning("the %s ran out of memory", budget.name)
                run.interruption = "memory"
                break
            if message[0] == _ERROR:
                _, exc, text = message
                exc.add_note(f"in the child process of the {budget.name}:\n{text}")
                raise exc
            run.results.append(message)
    finally:
        receiver.close()
        if process.is_alive():
            process.kill()
        process.join()
        written = _written(tempdir)
        if written:
            # the end of it, its control characters escaped, so that the child
            # cannot write lines of its own into the log
            logger.warning(
                "the child of the %s wrote: %r",
                budget.name,
                written[-_STDERR_LOGGED:],
            )
    if ended:
        run.interruption = _abnormal_end(process.exitcode, written, budget.name)
    return run


def _written(tempdir: str) -> str:
    """The end of what a child wrote to its standard error, `_STDERR_TAIL` at most."""
    try:
        with open(os.path.join(tempdir, _STDERR), "rb") as f:
            size = f.seek(0, os.SEEK_END)
            f.seek(max(0, size - _STDERR_TAIL))
            return f.read().decode(errors="replace").strip()
    except OSError:
        return ""


def _abnormal_end(exitcode: int | None, written: str, name: str) -> Interruption:
    """Why a child ended without its results: `"memory"` or `"crashed"`.

    An abort is for lack of memory when the C++ runtime wrote that a
    `std::bad_alloc` ended the child, every other end is `"crashed"`.
    """
    if exitcode == -signal.SIGABRT and any(text in written for text in _BAD_ALLOC):
        logger.warning("the %s was aborted, out of memory", name)
        return "memory"
    logger.warning("the %s ended unexpectedly (exit code %s)", name, exitcode)
    return "crashed"


def run_isolated(
    function: Callable[[Any], Iterable[tuple[str, Any]]],
    argument: Any,
    budget: Budget,
) -> IsolatedRun:
    """Run a function in a child process, bounded in time, memory and number.

    The function yields its results as pairs of a key and a value; it, its
    argument and the budget are pickled, so the function is one of a module the
    child imports. The time counts from the call on, the wait for a free child
    included; a call which gets no child before less than `MIN_CHILD_TIME` of
    its timeout is left is busy, without a child.

    Args:
        function: what the child runs.
        argument: the argument of the function.
        budget: what the run may take and how many of its kind run at a time.

    Returns:
        The results the function yielded, and why it stopped early if it did.

    Raises:
        IsolatedRunCancelledError: if the run was cancelled
            (`run_cancellable`), while it waited for a child or while its
            child ran, which is killed.
        Exception: the exception the function raised in the child.
    """
    deadline = time.monotonic() + budget.timeout
    _check_cancelled(budget)
    semaphore = _semaphore(budget)
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            logger.warning("no child was free for a %s before its timeout", budget.name)
            return IsolatedRun(interruption="busy")
        if semaphore.acquire(timeout=min(remaining, CANCEL_INTERVAL)):
            break
        _check_cancelled(budget)
    if deadline - time.monotonic() < MIN_CHILD_TIME:
        # a child which got next to no time would only run out of it
        semaphore.release()
        logger.warning(
            "a child was free for a %s too late before its timeout", budget.name
        )
        return IsolatedRun(interruption="busy")
    try:
        return _run_child(function, argument, budget, deadline)
    finally:
        semaphore.release()
