"""The child processes which run the validation, bounded in time and memory.

The validation of libsbml of untrusted content is not bounded by the size of
the content, so all of it, from reading the source on, runs in a child process
of its own, one per request, which the server ends when it takes too long:
after `VALIDATION_TIMEOUT` seconds from the call on, the wait for a free child
included. The address space of a child is limited to `VALIDATION_MEMORY`
bytes, and at most `MAX_CONCURRENT_VALIDATIONS` children run at a time.

A server admits at most `MAX_CONCURRENT_VALIDATIONS + MAX_WAITING_VALIDATIONS`
validations at a time (`admission`), a request beyond them is answered at once
as `"busy"`, and so is one which got no child while at least `MIN_CHILD_TIME`
of its timeout was left: a validation is `"timeout"` only when its child ran
out of time.

The children are forked by the forkserver of `multiprocessing`, a process of
its own which imported the report and the validation once and is single
threaded (`forkserver.py` keeps the thread pool of numpy out of it), so that a
child starts at once and small, without the threads of the server and with the
resolver of the report installed in the registry of libsbml. A child
gets the function it runs and its argument pickled, which is why the source
goes to it as the path of a file and not as objects of libsbml, and sends
every result back as soon as it has it, so that a timeout keeps the results
before it. An exception of the function is sent back and raised by the server,
with the traceback of the child as a note.

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
its `TMPDIR`, `TEMP` and `TMP`, for native libraries) and
removes when it has ended, so that a child which was killed or aborted leaves
nothing of the content on the server. The cpu time of a child is limited to
twice the timeout, so that a child ends itself also when its server died
without ending it.

The python interface runs the same server on the machine of the user: where
there is no forkserver (Windows) a child is spawned, a fresh interpreter which
imports the validation itself, and where the address space cannot be limited
(Windows, macOS) the child runs without the memory limit.
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
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess
from typing import Any, Literal


logger = logging.getLogger(__name__)

# the environment variable which sets the number of concurrent validations
VALIDATIONS_VARIABLE = "SBML4HUMANS_VALIDATIONS"


def _concurrent_validations() -> int:
    """The children which validate at a time: the environment, else half the cpus.

    `os.process_cpu_count` counts the cpus this process may run on, its cpu
    affinity: in a container all cpus of the host unless a cpuset restricts
    them, a cpu quota does not change it. Each child may use up to
    `VALIDATION_MEMORY`, so a server sets the number to what its memory allows.
    """
    value = os.environ.get(VALIDATIONS_VARIABLE, "")
    if value.isdigit() and int(value) > 0:
        return int(value)
    return max(1, (os.process_cpu_count() or 1) // 2)


# the time a validation may take from its call on, in seconds
VALIDATION_TIMEOUT = 60.0
# the address space of a child process, in bytes
VALIDATION_MEMORY = 2 * 1024**3
# the children which validate at a time
MAX_CONCURRENT_VALIDATIONS = _concurrent_validations()
# the validations which may wait for a child, beyond them a request is busy
MAX_WAITING_VALIDATIONS = 2 * MAX_CONCURRENT_VALIDATIONS
# the time a child has at least, a validation which got a child later is busy
MIN_CHILD_TIME = 1.0

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
# what the C++ runtime writes when an uncaught std::bad_alloc aborts the child
_BAD_ALLOC = "bad_alloc"

_SEMAPHORES: dict[int, threading.BoundedSemaphore] = {}
_LOCK = threading.Lock()
_admitted = 0


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


def admission_capacity() -> int:
    """The validations a server admits at a time, running or waiting."""
    return MAX_CONCURRENT_VALIDATIONS + MAX_WAITING_VALIDATIONS


@contextmanager
def admission() -> Iterator[bool]:
    """Admit a validation if there is room for it, for the time of the context.

    Yields:
        Whether the validation was admitted; one which was not is busy.
    """
    global _admitted
    with _LOCK:
        admitted = _admitted < admission_capacity()
        if admitted:
            _admitted += 1
    try:
        yield admitted
    finally:
        if admitted:
            with _LOCK:
                _admitted -= 1


def start_forkserver() -> None:
    """Start the forkserver, if the children are forked by one.

    The forkserver imports the report and the validation once it runs, which
    the first validation would otherwise wait for within its timeout. A
    forkserver which runs already is kept.
    """
    if _CONTEXT.get_start_method() == "forkserver":
        from multiprocessing import forkserver

        forkserver.ensure_running()


def _semaphore() -> threading.BoundedSemaphore:
    """The semaphore of `MAX_CONCURRENT_VALIDATIONS`, read when it is used."""
    with _LOCK:
        limit = MAX_CONCURRENT_VALIDATIONS
        if limit not in _SEMAPHORES:
            _SEMAPHORES[limit] = threading.BoundedSemaphore(limit)
        return _SEMAPHORES[limit]


def _limit_memory(memory: int) -> Callable[[], None]:
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
        logger.warning("the memory of the validation is not limited: %s", exc)
        return lambda: None

    def lift() -> None:
        """Raise the soft limit to the hard limit again."""
        resource.setrlimit(resource.RLIMIT_AS, (hard, hard))

    return lift


def _limit_cpu(seconds: int) -> None:
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
        logger.warning("the cpu time of the validation is not limited: %s", exc)


def _child(
    function: Callable[[Any], Iterable[tuple[str, Any]]],
    argument: Any,
    memory: int,
    cpu: int,
    tempdir: str,
    connection: Connection,
) -> None:
    """Run in the child: send every result of the function, then `_DONE`.

    The temporary files of the child go to `tempdir`, which the server
    removes: those of python by `tempfile` and those of native libraries by
    the variables of the environment they read (`TMPDIR`, `TEMP`, `TMP`). The cpu time is limited to `cpu` seconds and the address space to
    `memory`; when python runs out of memory, the limit is lifted again so that
    the child can say so. Another exception is sent with its traceback. The
    standard error goes to the file `_STDERR` of `tempdir`, which the server
    reads after the end of the child, together with the traceback of python
    `faulthandler` writes when the child ends by a fatal signal.
    """
    sys.stderr.flush()
    stderr = os.open(
        os.path.join(tempdir, _STDERR), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600
    )
    os.dup2(stderr, 2)
    os.close(stderr)
    faulthandler.enable()
    tempfile.tempdir = tempdir
    for variable in ("TMPDIR", "TEMP", "TMP"):
        os.environ[variable] = tempdir
    _limit_cpu(cpu)
    lift = _limit_memory(memory)
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
    tempdir: str,
    connection: Connection,
) -> BaseProcess:
    """Start a child which runs the function and sends on the connection.

    The limits of the child are read when it starts: `VALIDATION_MEMORY` and
    twice `VALIDATION_TIMEOUT` of cpu time.
    """
    cpu = math.ceil(2 * VALIDATION_TIMEOUT)
    process = _CONTEXT.Process(
        target=_child,
        args=(function, argument, VALIDATION_MEMORY, cpu, tempdir, connection),
        daemon=True,
    )
    process.start()
    return process


def _run_child(
    function: Callable[[Any], Iterable[tuple[str, Any]]],
    argument: Any,
    deadline: float,
) -> IsolatedRun:
    """Run the function in a child until it is done or the deadline has passed.

    Raises:
        Exception: the exception the function raised in the child.
    """
    # the temporary directory of the child, which the server removes after the
    # child has ended, whether it ended by itself, was killed or aborted
    tempdir = tempfile.mkdtemp(prefix="sbml4humans_validation_")
    try:
        return _communicate(function, argument, deadline, tempdir)
    finally:
        shutil.rmtree(tempdir, ignore_errors=True)


def _communicate(
    function: Callable[[Any], Iterable[tuple[str, Any]]],
    argument: Any,
    deadline: float,
    tempdir: str,
) -> IsolatedRun:
    """Start the child of `_run_child` and receive its results until it has ended.

    Raises:
        Exception: the exception the function raised in the child.
    """
    run = IsolatedRun()
    receiver, sender = _CONTEXT.Pipe(duplex=False)
    try:
        process = _start(function, argument, tempdir, sender)
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
            if remaining <= 0 or not receiver.poll(remaining):
                logger.warning("the validation was ended after its timeout")
                run.interruption = "timeout"
                break
            try:
                message = receiver.recv()
            except EOFError:
                # the child ended without saying it is done
                ended = True
                break
            if message == _DONE:
                break
            if message == _MEMORY:
                logger.warning("the validation ran out of memory")
                run.interruption = "memory"
                break
            if message[0] == _ERROR:
                _, exc, text = message
                exc.add_note(f"in the child process of the validation:\n{text}")
                raise exc
            run.results.append(message)
    finally:
        receiver.close()
        if process.is_alive():
            process.kill()
        process.join()
        written = _written(tempdir)
        if written:
            logger.warning("the child of the validation wrote:\n%s", written)
    if ended:
        run.interruption = _abnormal_end(process.exitcode, written)
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


def _abnormal_end(exitcode: int | None, written: str) -> Interruption:
    """Why a child ended without its results: `"memory"` or `"crashed"`.

    An abort is for lack of memory when the C++ runtime wrote that a
    `std::bad_alloc` ended the child, every other end is `"crashed"`.
    """
    if exitcode == -signal.SIGABRT and _BAD_ALLOC in written:
        logger.warning("the validation was aborted, out of memory")
        return "memory"
    logger.warning("the validation ended unexpectedly (exit code %s)", exitcode)
    return "crashed"


def run_isolated(
    function: Callable[[Any], Iterable[tuple[str, Any]]], argument: Any
) -> IsolatedRun:
    """Run a function in a child process, bounded in time, memory and number.

    The function yields its results as pairs of a key and a value; it and its
    argument are pickled, so the function is one of a module the child imports.
    The time counts from the call on, the wait for a free child included; a
    call which gets no child before less than `MIN_CHILD_TIME` of its timeout
    is left is busy, without a child.

    Args:
        function: what the child runs.
        argument: the argument of the function.

    Returns:
        The results the function yielded, and why it stopped early if it did.

    Raises:
        Exception: the exception the function raised in the child.
    """
    deadline = time.monotonic() + VALIDATION_TIMEOUT
    semaphore = _semaphore()
    if not semaphore.acquire(timeout=max(0.0, deadline - time.monotonic())):
        logger.warning("no child was free for a validation before its timeout")
        return IsolatedRun(interruption="busy")
    if deadline - time.monotonic() < MIN_CHILD_TIME:
        # a child which got next to no time would only run out of it
        semaphore.release()
        logger.warning("a child was free for a validation too late before its timeout")
        return IsolatedRun(interruption="busy")
    try:
        return _run_child(function, argument, deadline)
    finally:
        semaphore.release()
