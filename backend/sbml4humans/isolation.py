"""The child processes which run the validation, bounded in time and memory.

The validation of libsbml of untrusted content is not bounded by the size of
the content, so all of it, from reading the source on, runs in a child process
of its own, one per request, which the server ends when it takes too long:
after `VALIDATION_TIMEOUT` seconds from the call on, the wait for a free child
included. The address space of a child is limited to `VALIDATION_MEMORY`
bytes, and at most `MAX_CONCURRENT_VALIDATIONS` children run at a time.

A server admits at most `MAX_CONCURRENT_VALIDATIONS + MAX_WAITING_VALIDATIONS`
validations at a time (`admission`), a request beyond them is answered at once
as `"busy"`, and so is one which got no child before its timeout: a validation
is `"timeout"` only when its child ran out of time.

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
of it as `"memory"`.

The python interface runs the same server on the machine of the user: where
there is no forkserver (Windows) a child is spawned, a fresh interpreter which
imports the validation itself, and where the address space cannot be limited
(Windows, macOS) the child runs without the memory limit.
"""

import logging
import multiprocessing
import os
import signal
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

    `os.process_cpu_count` counts the cpus this process may use, which a
    container limits.
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

Interruption = Literal["timeout", "memory", "busy"]

if "forkserver" in multiprocessing.get_all_start_methods():
    _CONTEXT = multiprocessing.get_context("forkserver")
    _CONTEXT.set_forkserver_preload(["sbml4humans.forkserver", "sbml4humans.report"])
else:
    _CONTEXT = multiprocessing.get_context("spawn")

_SEMAPHORES: dict[int, threading.BoundedSemaphore] = {}
_LOCK = threading.Lock()
_admitted = 0


class ValidationProcessError(RuntimeError):
    """Raised when a child ends without its results for another reason."""


@dataclass
class IsolatedRun:
    """What a function yielded in a child, and why it stopped early if it did.

    Attributes:
        results: the pairs the function yielded, in their order.
        interruption: None when the function ran to its end, else `"timeout"`,
            `"memory"` or `"busy"` (it did not run at all).
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


def _child(
    function: Callable[[Any], Iterable[tuple[str, Any]]],
    argument: Any,
    memory: int,
    connection: Connection,
) -> None:
    """Run in the child: send every result of the function, then `_DONE`.

    The address space is limited to `memory`; when python runs out of it, the
    limit is lifted again so that the child can say so. Another exception is
    sent with its traceback.
    """
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
    memory: int,
    connection: Connection,
) -> BaseProcess:
    """Start a child which runs the function and sends on the connection."""
    process = _CONTEXT.Process(
        target=_child, args=(function, argument, memory, connection), daemon=True
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
        ValidationProcessError: if the child ended without its results, neither by
            the deadline nor for lack of memory.
        Exception: the exception the function raised in the child.
    """
    run = IsolatedRun()
    receiver, sender = _CONTEXT.Pipe(duplex=False)
    try:
        process = _start(function, argument, VALIDATION_MEMORY, sender)
    except BaseException:
        receiver.close()
        raise
    finally:
        # the child holds the sending end, which the server closes so that it
        # reads the end of the pipe when the child has ended
        sender.close()
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
                process.join()
                if process.exitcode != -signal.SIGABRT:
                    raise ValidationProcessError(
                        "The validation ended unexpectedly (exit code "
                        f"{process.exitcode})."
                    ) from None
                logger.warning("the validation was aborted, out of memory")
                run.interruption = "memory"
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
    return run


def run_isolated(
    function: Callable[[Any], Iterable[tuple[str, Any]]], argument: Any
) -> IsolatedRun:
    """Run a function in a child process, bounded in time, memory and number.

    The function yields its results as pairs of a key and a value; it and its
    argument are pickled, so the function is one of a module the child imports.
    The time counts from the call on, the wait for a free child included; a
    call which gets no child before its timeout is busy.

    Args:
        function: what the child runs.
        argument: the argument of the function.

    Returns:
        The results the function yielded, and why it stopped early if it did.

    Raises:
        ValidationProcessError: if the child ended without its results for
            another reason.
        Exception: the exception the function raised in the child.
    """
    deadline = time.monotonic() + VALIDATION_TIMEOUT
    semaphore = _semaphore()
    if not semaphore.acquire(timeout=VALIDATION_TIMEOUT):
        logger.warning("no child was free for a validation before its timeout")
        return IsolatedRun(interruption="busy")
    try:
        return _run_child(function, argument, deadline)
    finally:
        semaphore.release()
