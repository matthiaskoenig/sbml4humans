"""Public requests cannot bypass admission, coalescing or streaming bounds."""

import asyncio
import gzip
import threading

import httpx
import pytest

from sbml4humans import api, isolation


def test_a_busy_request_is_refused_without_reading_its_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Admission precedes both raw body allocation and multipart parsing."""
    monkeypatch.setattr(isolation.REPORT_BUDGET, "concurrency", 1)
    monkeypatch.setattr(isolation.REPORT_BUDGET, "waiting", 0)
    received: list[int] = []

    async def app(scope, receive, send):
        """Record every byte the backend asks the transport to deliver."""

        async def counted():
            """Forward the transport while observing body consumption."""
            message = await receive()
            if message["type"] == "http.request":
                received.append(len(message.get("body", b"")))
            return message

        await api.api(scope, counted, send)

    async def requests():
        """Exercise both ways FastAPI receives potentially large files."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            with isolation.admission(isolation.REPORT_BUDGET) as occupied:
                assert occupied
                raw = await client.post("/api/content", content=b"x" * 4096)
                file = await client.post(
                    "/api/file", files={"source": ("m.xml", b"x" * 4096)}
                )
            assert "busy" in raw.json()["errors"][0]
            assert "busy" in file.json()["errors"][0]

    asyncio.run(requests())
    assert received == []


def test_concurrent_cold_example_requests_share_one_bounded_build(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The same immutable example costs one computation, not one per caller."""
    started, release = threading.Event(), threading.Event()
    builds: list[int] = []
    packed = gzip.compress(b'{"uid":"shared","reports":{},"manifest":{"entries":[]}}')

    def build(_: str) -> bytes:
        """Stand in for one isolated native operation without expensive inputs."""
        builds.append(threading.get_ident())
        started.set()
        assert release.wait(5)
        return packed

    cache = api.CachedWork(build, weight=len)
    monkeypatch.setattr(api, "example_report_gzip", cache)
    monkeypatch.setattr(isolation.REPORT_BUDGET, "concurrency", 1)
    monkeypatch.setattr(isolation.REPORT_BUDGET, "waiting", 4)

    async def requests():
        """Overlap requests at the HTTP boundary, then release the sole owner."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=api.api), base_url="http://test"
        ) as client:
            tasks = [
                asyncio.create_task(client.get("/api/examples/shared"))
                for _ in range(4)
            ]
            try:
                assert await asyncio.to_thread(started.wait, 5)
                await asyncio.sleep(0.05)
                release.set()
                responses = await asyncio.gather(*tasks)
                assert all(response.json()["uid"] == "shared" for response in responses)
            finally:
                release.set()
                await asyncio.gather(*tasks, return_exceptions=True)

    asyncio.run(requests())
    assert len(builds) == 1


def test_expanded_responses_do_not_allocate_or_emit_a_whole_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Identity transport remains bounded even for highly compressible JSON."""
    content = b'{"large":"' + b"a" * 300_000 + b'"}'
    sent: list[int] = []

    def forbidden(*args, **kwargs):
        """A full decompression would recreate the parent-process allocation bug."""
        raise AssertionError("whole-report decompression")

    monkeypatch.setattr(gzip, "decompress", forbidden)

    async def response():
        """Consume chunks as ASGI does instead of joining them on the server."""
        from starlette.requests import Request
        from starlette.responses import StreamingResponse

        result = await api.report_response(
            Request({"type": "http", "headers": []}), gzip.compress(content)
        )
        assert isinstance(result, StreamingResponse)
        received = []
        async for chunk in result.body_iterator:
            assert isinstance(chunk, bytes)
            sent.append(len(chunk))
            received.append(chunk)
        assert b"".join(received) == content

    asyncio.run(response())
    assert max(sent) <= 64 * 1024
    assert len(sent) > 1


def test_stalled_body_expires_and_releases_its_admission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A slow sender cannot retain source capacity indefinitely."""
    from sbml4humans import limits

    monkeypatch.setattr(limits, "SOURCE_RECEIVE_TIMEOUT", 0.01)
    monkeypatch.setattr(isolation.REPORT_BUDGET, "concurrency", 1)
    monkeypatch.setattr(isolation.REPORT_BUDGET, "waiting", 0)

    async def request():
        """Stall the HTTP body itself, before any native work is possible."""

        async def content():
            await asyncio.sleep(1)
            yield b"<sbml/>"

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=api.api), base_url="http://test"
        ) as client:
            response = await client.post("/api/content", content=content())
            assert response.status_code == 200
            assert "source body took longer" in response.json()["errors"][0]

    asyncio.run(request())
    with isolation.admission(isolation.REPORT_BUDGET) as admitted:
        assert admitted
