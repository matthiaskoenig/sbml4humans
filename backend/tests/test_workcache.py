"""Byte bounds, failures and cancellation keep shared work predictable."""

import pytest

from sbml4humans.workcache import WorkCache


def test_weighted_eviction_and_uncached_failures() -> None:
    """Large values cannot evade the byte limit through a small entry count."""
    cache = WorkCache[bytes](weight=len, maxsize=10, maxbytes=5)
    assert cache.get("a", lambda: b"aaa") == b"aaa"
    cache.get("b", lambda: b"bbb")
    assert cache.peek("a") is None
    assert cache.peek("b") == b"bbb"
    cache.get("oversized", lambda: b"x" * 10)
    assert cache.peek("oversized") is None
    with pytest.raises(TimeoutError):
        cache.get("error", lambda: (_ for _ in ()).throw(TimeoutError("failed")))
    assert cache.get("error", lambda: b"ok") == b"ok"
