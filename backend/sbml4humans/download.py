"""The download of the model behind a url, from public addresses alone.

The url of `GET /api/url` is chosen by whoever sends the request, so the server
must not become a way into the network it runs in (server side request
forgery): the cloud metadata service, a database on localhost, a service of the
internal network. A url is downloaded when its scheme is http or https and every
address its host resolves to is a public address of the internet (`is_public`).

The check happens where the connection is made: the network backend of the http
client (`PublicNetworkBackend`) resolves the host, refuses it unless all of its
addresses are public and connects to the address it checked, so that a name
which resolves to another address a moment later (DNS rebinding) cannot slip in
between check and connection. The url keeps its host, which is the `Host` header
and the server name of TLS. Redirects are followed one by one, each one through
the same backend, at most `MAX_REDIRECTS`. No proxy of the environment is used,
it would make the connection to an address which was never checked.

The end to end tests of the frontend serve a model on the loopback interface,
which is allowed when the environment of the server sets
`SBML4HUMANS_ALLOW_PRIVATE_URLS=1` (`ALLOW_PRIVATE_URLS_VARIABLE`), read once on
import. It is never set by default, neither for the public service nor for the
local server of `sbml4humans.show`, which downloads from public addresses alone
as well: a model on the machine is opened by its path.

The download is limited by `limits.py`: it ends after `DOWNLOAD_TIMEOUT` in
total and a step (the name resolution, the connection, the handshake of TLS, a
read or a write) after `DOWNLOAD_STEP_TIMEOUT` or at the deadline, whichever
comes first, and it reads at most `MAX_CONTENT_SIZE` bytes after the content
encoding of the response is undone. The name resolution of the system has no
timeout, so it runs in a thread of its own which the download stops waiting
for; a resolution which hangs ends by the timeouts of the resolver of the
system.
"""

import ipaddress
import logging
import os
import socket
import ssl
import threading
import time
from collections.abc import Iterable
from typing import Any

import httpcore
import httpx

from sbml4humans import limits
from sbml4humans.limits import ContentTooLargeError, format_size


type IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address

logger = logging.getLogger(__name__)

# the variable of the environment which allows the addresses which are not
# public, for the end to end tests alone
ALLOW_PRIVATE_URLS_VARIABLE = "SBML4HUMANS_ALLOW_PRIVATE_URLS"
ALLOW_PRIVATE_URLS = os.environ.get(ALLOW_PRIVATE_URLS_VARIABLE) == "1"
if ALLOW_PRIVATE_URLS:
    logger.warning(
        "%s=1: urls of every address are downloaded, which is meant for tests",
        ALLOW_PRIVATE_URLS_VARIABLE,
    )

SCHEMES = ("http", "https")
# the well-known prefix of NAT64 (RFC 6052), whose last 32 bits are an IPv4 address
NAT64_PREFIX = ipaddress.ip_network("64:ff9b::/96")


class UrlNotAllowedError(ValueError):
    """Raised for a url which is not downloaded: no http(s) or no public address."""


class DownloadTimeoutError(TimeoutError):
    """Raised for a download which takes longer than `DOWNLOAD_TIMEOUT`."""

    def __str__(self) -> str:
        """Message for the frontend."""
        return f"The download took longer than {limits.DOWNLOAD_TIMEOUT:g} s."


def resolve(host: str, port: int) -> list[IPAddress]:
    """The addresses of a host, which is a name or an address itself."""
    return [
        ipaddress.ip_address(str(info[4][0]))
        for info in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    ]


def _embedded_ipv4(address: IPAddress) -> ipaddress.IPv4Address | None:
    """The IPv4 address an IPv6 address carries (mapped, 6to4, NAT64), if any."""
    if not isinstance(address, ipaddress.IPv6Address):
        return None
    if address.ipv4_mapped is not None:
        return address.ipv4_mapped
    if address.sixtofour is not None:
        return address.sixtofour
    if address in NAT64_PREFIX:
        return ipaddress.IPv4Address(int(address) & 0xFFFFFFFF)
    return None


def is_public(address: IPAddress) -> bool:
    """Whether an address is one of the internet, which may be downloaded from.

    Loopback, private, link local (the cloud metadata service), shared (carrier
    grade NAT), reserved, multicast and unspecified addresses are not, and
    neither is an IPv6 address which carries an IPv4 address which is not.
    """
    embedded = _embedded_ipv4(address)
    if embedded is not None and not is_public(embedded):
        return False
    return address.is_global and not (
        address.is_loopback
        or address.is_private
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    )


class _Deadline:
    """The deadline of a download, which bounds the timeout of every step."""

    def __init__(self, at: float) -> None:
        """The deadline at the time `at` of `time.monotonic`."""
        self.at = at

    def passed(self) -> bool:
        """Whether the deadline has passed."""
        return time.monotonic() >= self.at

    def bound(self, timeout: float | None) -> float:
        """The timeout of a step: its own, at most the time left until the deadline.

        Raises:
            DownloadTimeoutError: if the deadline has passed.
        """
        remaining = self.at - time.monotonic()
        if remaining <= 0:
            raise DownloadTimeoutError
        return remaining if timeout is None else min(timeout, remaining)


def _resolve_within(host: str, port: int, timeout: float) -> list[IPAddress] | None:
    """The addresses of a host, None when the resolution takes longer than `timeout`.

    `socket.getaddrinfo` has no timeout, so `resolve` runs in a daemon thread,
    which is left to end by itself when it takes longer.
    """
    addresses: list[list[IPAddress]] = []
    errors: list[OSError] = []

    def run() -> None:
        """Resolve the host, keep the addresses or the error."""
        try:
            addresses.append(resolve(host, port))
        except OSError as exc:
            errors.append(exc)

    thread = threading.Thread(target=run, name=f"resolve {host}", daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        return None
    if errors:
        raise errors[0]
    return addresses[0]


class _DeadlineStream(httpcore.NetworkStream):
    """A network stream whose every step ends at the deadline at the latest."""

    def __init__(self, stream: httpcore.NetworkStream, deadline: _Deadline) -> None:
        """Wrap the stream."""
        self._stream = stream
        self._deadline = deadline

    def read(self, max_bytes: int, timeout: float | None = None) -> bytes:
        """Read, until the deadline at the latest."""
        return self._stream.read(max_bytes, self._deadline.bound(timeout))

    def write(self, buffer: bytes, timeout: float | None = None) -> None:
        """Write, until the deadline at the latest."""
        self._stream.write(buffer, self._deadline.bound(timeout))

    def close(self) -> None:
        """Close the stream."""
        self._stream.close()

    def start_tls(
        self,
        ssl_context: ssl.SSLContext,
        server_hostname: str | None = None,
        timeout: float | None = None,
    ) -> httpcore.NetworkStream:
        """The handshake of TLS, until the deadline at the latest."""
        stream = self._stream.start_tls(
            ssl_context, server_hostname, self._deadline.bound(timeout)
        )
        return _DeadlineStream(stream, self._deadline)

    def get_extra_info(self, info: str) -> Any:
        """The information of the wrapped stream."""
        return self._stream.get_extra_info(info)


class PublicNetworkBackend(httpcore.SyncBackend):
    """The network backend which connects to public addresses alone.

    Every step of a connection, the name resolution included, ends after its
    timeout or at the deadline of the download, whichever comes first.
    """

    def __init__(self, deadline: float) -> None:
        """The backend of a download which ends at `deadline` (`time.monotonic`)."""
        super().__init__()
        self._deadline = _Deadline(deadline)

    def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: Iterable[httpcore.SOCKET_OPTION] | None = None,
    ) -> httpcore.NetworkStream:
        """Connect to the checked address of the host.

        Raises:
            UrlNotAllowedError: if an address of the host is not public.
            DownloadTimeoutError: if the deadline passes.
            httpx.ConnectTimeout: if the name resolution takes longer than the
                timeout of its step.
        """
        step = self._deadline.bound(timeout)
        try:
            addresses = _resolve_within(host, port, step)
        except OSError as exc:
            raise httpx.ConnectError(f"The host '{host}' is unknown: {exc}") from exc
        if addresses is None:
            if self._deadline.passed():
                raise DownloadTimeoutError
            raise httpx.ConnectTimeout(
                f"The name resolution of the host '{host}' took longer than {step:g} s."
            )
        if not addresses or not (
            ALLOW_PRIVATE_URLS or all(is_public(address) for address in addresses)
        ):
            raise UrlNotAllowedError(
                f"The host '{host}' is no public address of the internet, it is "
                "not downloaded."
            )
        stream = super().connect_tcp(
            str(addresses[0]),
            port,
            self._deadline.bound(timeout),
            local_address,
            socket_options,
        )
        return _DeadlineStream(stream, self._deadline)


class PublicTransport(httpx.HTTPTransport):
    """The transport of httpx through `PublicNetworkBackend`."""

    def __init__(self, deadline: float) -> None:
        """Create the transport of a download which ends at `deadline`.

        No proxy of the environment is used.
        """
        super().__init__(trust_env=False)
        # httpx offers no option for the network backend of its connection
        # pool, so the pool is created again with the backend
        self._pool = httpcore.ConnectionPool(
            ssl_context=httpx.create_ssl_context(),
            network_backend=PublicNetworkBackend(deadline),
        )


def _check_url(url: httpx.URL) -> None:
    """Refuse a url with another scheme than http(s) or without host."""
    if url.scheme not in SCHEMES or not url.host:
        raise UrlNotAllowedError(
            f"The url '{url}' is not downloaded, only http and https urls are."
        )


def _read(response: httpx.Response, deadline: float) -> bytes:
    """Read the body of the response, up to the size and the time of the limits."""
    limit = limits.MAX_CONTENT_SIZE
    too_large = ContentTooLargeError(
        f"The download is larger than the limit of {format_size(limit)}."
    )
    declared = response.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > limit:
        raise too_large
    chunks: list[bytes] = []
    size = 0
    for chunk in response.iter_bytes():
        size += len(chunk)
        if size > limit:
            raise too_large
        if time.monotonic() > deadline:
            raise DownloadTimeoutError
        chunks.append(chunk)
    return b"".join(chunks)


def download(url: str) -> bytes:
    """Download the content behind a public http(s) url.

    Raises:
        UrlNotAllowedError: if the url, or a url it redirects to, is not http(s)
            or not public, or if it redirects more than `MAX_REDIRECTS` times.
        ContentTooLargeError: if the content exceeds `MAX_CONTENT_SIZE`.
        DownloadTimeoutError: if the download takes longer than `DOWNLOAD_TIMEOUT`.
        httpx.HTTPError: if the download fails.
    """
    deadline = time.monotonic() + limits.DOWNLOAD_TIMEOUT
    try:
        target = httpx.URL(url)
    except httpx.InvalidURL as exc:
        raise UrlNotAllowedError(
            f"The url is invalid, it is not downloaded: {exc}"
        ) from exc
    try:
        return _download(target, deadline)
    except httpx.TimeoutException as exc:
        # a step which ended at the deadline
        if time.monotonic() >= deadline:
            raise DownloadTimeoutError from exc
        raise


def _download(target: httpx.URL, deadline: float) -> bytes:
    """Download the content of `download`, following the redirects one by one."""
    with httpx.Client(
        transport=PublicTransport(deadline),
        timeout=limits.DOWNLOAD_STEP_TIMEOUT,
        follow_redirects=False,
    ) as client:
        for _ in range(limits.MAX_REDIRECTS + 1):
            _check_url(target)
            if time.monotonic() > deadline:
                raise DownloadTimeoutError
            with client.stream("GET", target) as response:
                if response.next_request is None:
                    response.raise_for_status()
                    return _read(response, deadline)
                target = response.next_request.url
    raise UrlNotAllowedError(
        f"The url redirects more than {limits.MAX_REDIRECTS} times, it is not "
        "downloaded."
    )
