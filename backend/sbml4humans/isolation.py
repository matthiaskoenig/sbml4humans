"""The child processes which run the validation, bounded in time and memory.

The validation of libsbml of untrusted content is not bounded by the size of
the content, so it runs in a child process of its own, one per request, which
the server ends when it takes too long: after `VALIDATION_TIMEOUT` seconds
from the start of the request, waiting for a free child included. The address
space of a child is limited to `VALIDATION_MEMORY` bytes, and at most
`MAX_CONCURRENT_VALIDATIONS` children run at a time.

The children are forked by the forkserver of `multiprocessing`, a process of
its own which imported `sbml4humans.validation` once and is single threaded,
so that a child starts at once, without the threads of the server and with the
resolver of the report installed in the registry of libsbml. A child gets the
function it runs and its argument pickled, which is why the documents go to it
as paths of files and not as objects of libsbml, and sends every result back
as soon as it has it, so that a timeout keeps the results before it.

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
from collections.abc import Callable, Iterable
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess
from typing import Any, Literal


logger = logging.getLogger(__name__)

# the time a validation may take from its request on, in seconds
VALIDATION_TIMEOUT = 60.0
# the address space of a child process, in bytes
VALIDATION_MEMORY = 2 * 1024**3
# the children which validate at a time, the other requests wait for one
MAX_CONCURRENT_VALIDATIONS = max(1, (os.cpu_count() or 1) // 2)

Interruption = Literal["timeout", "memory"]

if "forkserver" in multiprocessing.get_all_start_methods():
    _CONTEXT = multiprocessing.get_context("forkserver")
    _CONTEXT.set_forkserver_preload(["sbml4humans.isolation", "sbml4humans.validation"])
else:
    _CONTEXT = multiprocessing.get_context("spawn")

_SEMAPHORES: dict[int, threading.BoundedSemaphore] = {}
_SEMAPHORES_LOCK = threading.Lock()


class ValidationProcessError(RuntimeError):
    """Raised when a child ends without its results for another reason."""


# the messages of a child to the server, besides a result
_DONE = "done"
_MEMORY = "memory"


def _semaphore() -> threading.BoundedSemaphore:
    """The semaphore of `MAX_CONCURRENT_VALIDATIONS`, read when it is used."""
    with _SEMAPHORES_LOCK:
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
    limit is lifted again so that the child can say so.
    """
    lift = _limit_memory(memory)
    try:
        for result in function(argument):
            connection.send(result)
        connection.send(_DONE)
    except MemoryError:
        lift()
        connection.send(_MEMORY)
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
    keys: list[str],
    deadline: float,
) -> dict[str, Any]:
    """Run the function in a child until it is done or the deadline has passed.

    Returns:
        The result of every key, `"timeout"` or `"memory"` for a key without.

    Raises:
        ValidationProcessError: if the child ended without its results, neither by
            the deadline nor for lack of memory.
    """
    results: dict[str, Any] = {}
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
    interruption: Interruption = "timeout"
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not receiver.poll(remaining):
                logger.warning("the validation was ended after its timeout")
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
                interruption = "memory"
                break
            if message == _DONE:
                break
            if message == _MEMORY:
                logger.warning("the validation ran out of memory")
                interruption = "memory"
                break
            key, result = message
            results[key] = result
    finally:
        receiver.close()
        if process.is_alive():
            process.kill()
        process.join()
    return {key: results.get(key, interruption) for key in keys}


def run_isolated(
    function: Callable[[Any], Iterable[tuple[str, Any]]],
    argument: Any,
    keys: list[str],
) -> dict[str, Any]:
    """Run a function in a child process, bounded in time, memory and number.

    The function yields its results as pairs of a key and a value; it and its
    argument are pickled, so the function is one of a module the child imports.
    The time of the request counts from the call on, the wait for a free child
    included.

    Args:
        function: what the child runs.
        argument: the argument of the function.
        keys: the keys of the results the function yields.

    Returns:
        The result of every key, `"timeout"` for a key the function did not
        yield in time and `"memory"` for one it did not yield for lack of
        memory.

    Raises:
        ValidationProcessError: if the child ended without its results for another
            reason.
    """
    deadline = time.monotonic() + VALIDATION_TIMEOUT
    semaphore = _semaphore()
    if not semaphore.acquire(timeout=VALIDATION_TIMEOUT):
        logger.warning("no child was free for a validation before its timeout")
        return dict.fromkeys(keys, "timeout")
    try:
        return _run_child(function, argument, keys, deadline)
    finally:
        semaphore.release()
