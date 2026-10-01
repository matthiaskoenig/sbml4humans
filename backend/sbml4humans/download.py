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
total and a step (connect, a read) after `DOWNLOAD_STEP_TIMEOUT`, so the
deadline is exceeded by at most one step, and it reads at most
`MAX_CONTENT_SIZE` bytes after the content encoding of the response is undone.
"""

import ipaddress
import logging
import os
import socket
import time
from collections.abc import Iterable

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


class PublicNetworkBackend(httpcore.SyncBackend):
    """The network backend which connects to public addresses alone."""

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
        """
        try:
            addresses = resolve(host, port)
        except OSError as exc:
            raise httpx.ConnectError(f"The host '{host}' is unknown: {exc}") from exc
        if not addresses or not (
            ALLOW_PRIVATE_URLS or all(is_public(address) for address in addresses)
        ):
            raise UrlNotAllowedError(
                f"The host '{host}' is no public address of the internet, it is "
                "not downloaded."
            )
        return super().connect_tcp(
            str(addresses[0]), port, timeout, local_address, socket_options
        )


class PublicTransport(httpx.HTTPTransport):
    """The transport of httpx through `PublicNetworkBackend`."""

    def __init__(self) -> None:
        """Create the transport, without a proxy of the environment."""
        super().__init__(trust_env=False)
        # httpx offers no option for the network backend of its connection
        # pool, so the pool is created again with the backend
        self._pool = httpcore.ConnectionPool(
            ssl_context=httpx.create_ssl_context(),
            network_backend=PublicNetworkBackend(),
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
    with httpx.Client(
        transport=PublicTransport(),
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
