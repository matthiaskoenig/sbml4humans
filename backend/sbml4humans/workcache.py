"""Bounded, coalesced immutable results without retaining native model objects."""

import threading
from collections import OrderedDict, namedtuple
from collections.abc import Callable
from concurrent.futures import Future, TimeoutError

from sbml4humans import isolation


CacheInfo = namedtuple("CacheInfo", "hits misses maxsize currsize")


class WorkCache[R]:
    """Share one bounded computation per key across threads and request loops."""

    def __init__(
        self,
        *,
        weight: Callable[[R], int],
        maxsize: int = 32,
        maxbytes: int = 64 * 1024**2,
        budget: isolation.Budget = isolation.REPORT_BUDGET,
    ) -> None:
        """Bound stored bytes and entries; callers retain normal work admission."""
        self.maxsize, self.maxbytes = maxsize, maxbytes
        self.weight, self.budget = weight, budget
        self._lock = threading.Lock()
        self._entries: OrderedDict[str, tuple[R, int]] = OrderedDict()
        self._pending: dict[str, Future[R]] = {}
        self._bytes = self._hits = self._misses = self._generation = 0

    def peek(self, key: str) -> R | None:
        """Return a completed result without starting or joining native work."""
        with self._lock:
            found = self._entries.get(key)
            if found is None:
                return None
            self._hits += 1
            self._entries.move_to_end(key)
            return found[0]

    def get(self, key: str, build: Callable[[], R]) -> R:
        """Coalesce misses, with cancellable waits and no cached failures."""
        with self._lock:
            found = self._entries.get(key)
            if found is not None:
                self._hits += 1
                self._entries.move_to_end(key)
                return found[0]
            future = self._pending.get(key)
            owner = future is None
            if future is None:
                future = Future()
                self._pending[key] = future
                self._misses += 1
            generation = self._generation
        if not owner:
            while True:
                isolation._check_cancelled(self.budget)
                try:
                    return future.result(timeout=isolation.CANCEL_INTERVAL)
                except TimeoutError:
                    if future.done():
                        return future.result()
                    continue
                except isolation.IsolatedRunCancelledError:
                    isolation._check_cancelled(self.budget)
                    return self.get(key, build)
        try:
            value = build()
            weight = self.weight(value)
            with self._lock:
                if self._pending.get(key) is future:
                    del self._pending[key]
                if generation == self._generation and weight <= self.maxbytes:
                    self._entries[key] = value, weight
                    self._bytes += weight
                    while (
                        len(self._entries) > self.maxsize or self._bytes > self.maxbytes
                    ):
                        _, (_, removed) = self._entries.popitem(last=False)
                        self._bytes -= removed
        except BaseException as error:
            with self._lock:
                if self._pending.get(key) is future:
                    del self._pending[key]
            future.set_exception(error)
            raise
        future.set_result(value)
        return value

    def cache_clear(self) -> None:
        """Invalidate results while existing subscribers can still finish."""
        with self._lock:
            self._entries.clear()
            self._pending.clear()
            self._bytes = self._hits = self._misses = 0
            self._generation += 1

    def cache_info(self) -> CacheInfo:
        """Return familiar cache statistics for transport diagnostics."""
        with self._lock:
            return CacheInfo(self._hits, self._misses, self.maxsize, len(self._entries))


class CachedWork[R]:
    """A unary immutable operation with coalescing and observable cache bounds."""

    def __init__(
        self,
        build: Callable[[str], R],
        *,
        weight: Callable[[R], int],
        key: Callable[[str], str] = str,
        maxsize: int = 32,
    ) -> None:
        """Wrap work which itself retains native process isolation."""
        self.build, self.key = build, key
        self.cache = WorkCache(weight=weight, maxsize=maxsize)

    def __call__(self, argument: str) -> R:
        """Return a result or join its one admitted computation."""
        return self.cache.get(self.key(argument), lambda: self.build(argument))

    def peek(self, argument: str) -> R | None:
        """Read completed work without acquiring a native work slot."""
        return self.cache.peek(self.key(argument))

    def cache_clear(self) -> None:
        """Invalidate stored results."""
        self.cache.cache_clear()

    def cache_info(self) -> CacheInfo:
        """Expose operation cache statistics."""
        return self.cache.cache_info()
